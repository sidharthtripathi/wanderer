"""Conversation session endpoints. Spec §4.2.

POST   /v1/sessions                    create session
POST   /v1/sessions/{id}/messages      text turn (SSE streaming)
POST   /v1/sessions/{id}/end           graceful end + summary
GET    /v1/sessions/{id}/horizon       current horizon (stub — Slice 5)
"""

import orjson
from typing import Annotated
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.gemini import get_client
from app.conversation.planner import ConversationPlanner
from app.conversation.streaming import stream_sse
from app.core.auth import CurrentUser
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.db.session import get_session
from app.memory.summarizer import extract_profile_updates, generate_session_summary
from app.models.user import User
from app.services.sessions import (
    create_session,
    end_session_record,
    get_active_session,
    get_conversation_history,
    save_turn,
)

log = get_logger(__name__)

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


# ── Request / response schemas ──────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    mode: str = "text"
    city_id: str | None = None
    user_lat: float | None = None
    user_lng: float | None = None


class CreateSessionResponse(BaseModel):
    session_id: str


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class EndSessionResponse(BaseModel):
    session_id: str
    summary: str
    earned_points: int


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("", response_model=CreateSessionResponse)
async def create_session_endpoint(
    body: CreateSessionRequest,
    auth: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    rds: Annotated[redis.Redis, Depends(get_redis)],
) -> CreateSessionResponse:
    """Create a new wandering session. Returns the session_id."""
    # Ensure user row exists (idempotent — matches core-api's get_or_create_user)
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    db_session = session
    stmt = (
        pg_insert(User)
        .values(firebase_uid=auth.firebase_uid)
        .on_conflict_do_nothing(index_elements=[User.firebase_uid])
    )
    await db_session.execute(stmt)
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.firebase_uid == auth.firebase_uid)
    )
    user = result.scalar_one()

    sess = await create_session(
        db_session,
        rds,
        user_id=str(user.id),
        mode=body.mode,
        city_id=body.city_id,
    )
    return CreateSessionResponse(session_id=str(sess.id))


@router.post("/{session_id}/messages")
async def send_message(
    session_id: UUID,
    body: SendMessageRequest,
    auth: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    rds: Annotated[redis.Redis, Depends(get_redis)],
):
    """Process a text turn. Returns SSE streaming response with tokens + tool events."""
    # Verify session
    sess = await get_active_session(session, str(session_id))
    if sess is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "session not found or already ended")

    # Verify ownership (user row guaranteed by create_session or prior exchange)
    from sqlalchemy import select

    user_result = await session.execute(
        select(User).where(User.firebase_uid == auth.firebase_uid)
    )
    user = user_result.scalar_one()
    if str(sess.user_id) != str(user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "session does not belong to this user")

    # Load conversation history
    history = await get_conversation_history(rds, str(session_id))

    # Determine city name
    city_name = "this city"
    if sess.city_id:
        from app.models.city import City
        from uuid import UUID as _UUID

        city_result = await session.execute(
            select(City.name).where(City.id == sess.city_id)
        )
        city_row = city_result.scalar_one_or_none()
        if city_row:
            city_name = city_row

    # Plan and stream the turn
    planner = ConversationPlanner(
        gemini_client=get_client(),
        db_session=session,
        redis_client=rds,
    )

    # Wrap the generator to save the turn after completion
    async def turn_with_save():
        full_response_parts: list[str] = []
        async for event in planner.plan_turn(
            session_id=session_id,
            user_id=user.id,
            user_message=body.text,
            city_name=city_name,
            conversation_history=history,
        ):
            yield event
            if event.get("type") == "token":
                full_response_parts.append(event["delta"])

        # Save turn to conversation history
        full_response = "".join(full_response_parts)
        if full_response.strip():
            await save_turn(rds, str(session_id), body.text, full_response)

    return stream_sse(turn_with_save())


@router.post("/{session_id}/end", response_model=EndSessionResponse)
async def end_session(
    session_id: UUID,
    auth: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    rds: Annotated[redis.Redis, Depends(get_redis)],
) -> EndSessionResponse:
    """End a session gracefully. Generates summary, extracts profile updates."""
    # Verify
    sess = await get_active_session(session, str(session_id))
    if sess is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "session not found or already ended")

    from sqlalchemy import select

    user_result = await session.execute(
        select(User).where(User.firebase_uid == auth.firebase_uid)
    )
    user = user_result.scalar_one()
    if str(sess.user_id) != str(user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "session does not belong to this user")

    # Load conversation history
    history = await get_conversation_history(rds, str(session_id))

    # Generate summary
    client = get_client()
    summary = await generate_session_summary(client, history)

    # Extract profile updates
    from app.memory.profile import get_profile, update_profile

    existing_profile = await get_profile(session, user.id)
    profile_updates = await extract_profile_updates(client, history, existing_profile)

    if profile_updates:
        await update_profile(session, user.id, profile_updates)
        log.info(
            "profile_updates_from_session",
            user_id=str(user.id),
            keys=list(profile_updates.keys()),
        )

    # End session
    await end_session_record(session, rds, str(session_id), summary=summary)

    return EndSessionResponse(
        session_id=str(session_id),
        summary=summary,
        earned_points=0,  # Slice 7 wires this
    )


@router.get("/{session_id}/horizon")
async def get_horizon(session_id: UUID) -> dict:
    """Current planned horizon. Stub — fully implemented in Slice 5."""
    return {"session_id": str(session_id), "pois": [], "message": "horizon tracking not yet available"}
