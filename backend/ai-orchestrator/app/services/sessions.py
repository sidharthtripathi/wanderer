"""Session persistence and lifecycle. Keeps API routes thin."""

import orjson
from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.session import Session

log = get_logger(__name__)

HISTORY_KEY = "session:{sid}:history"
STATE_KEY = "session:{sid}:state"
MAX_HISTORY_TURNS = 20


async def create_session(
    db: AsyncSession,
    redis: Redis,
    *,
    user_id: str,
    mode: str = "text",
    city_id: str | None = None,
) -> Session:
    """Persist a new session and initialize Redis state."""
    from uuid import UUID as _UUID

    session = Session(
        user_id=_UUID(user_id),
        city_id=_UUID(city_id) if city_id else None,
        mode=mode,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Initialize Redis state
    await redis.set(STATE_KEY.format(sid=str(session.id)), "active")
    await redis.set(HISTORY_KEY.format(sid=str(session.id)), orjson.dumps([]).decode())

    log.info("session_created", session_id=str(session.id), mode=mode)
    return session


async def get_active_session(db: AsyncSession, session_id: str) -> Session | None:
    """Return the session if it exists and hasn't ended."""
    from uuid import UUID as _UUID

    result = await db.execute(
        select(Session).where(
            Session.id == _UUID(session_id),
            Session.ended_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def end_session_record(
    db: AsyncSession,
    redis: Redis,
    session_id: str,
    summary: str | None = None,
    cost_points: int = 0,
) -> Session:
    """Mark a session as ended, write summary, clean up Redis."""
    from datetime import datetime, timezone
    from uuid import UUID as _UUID

    stmt = (
        update(Session)
        .where(Session.id == _UUID(session_id))
        .values(ended_at=datetime.now(timezone.utc), summary=summary, cost_points=cost_points)
    )
    await db.execute(stmt)
    await db.commit()

    # Clean Redis
    await redis.delete(STATE_KEY.format(sid=session_id))
    await redis.delete(HISTORY_KEY.format(sid=session_id))

    result = await db.execute(select(Session).where(Session.id == _UUID(session_id)))
    session = result.scalar_one()
    log.info("session_ended", session_id=session_id)
    return session


async def get_conversation_history(redis: Redis, session_id: str) -> list[dict]:
    """Load the last N conversation turns from Redis."""
    raw = await redis.get(HISTORY_KEY.format(sid=session_id))
    if raw is None:
        return []
    try:
        return orjson.loads(raw)
    except Exception:
        return []


async def save_turn(redis: Redis, session_id: str, user_text: str, agent_text: str) -> None:
    """Append a turn to the conversation history, trimming to MAX_HISTORY_TURNS."""
    history = await get_conversation_history(redis, session_id)
    history.append({"role": "user", "text": user_text})
    history.append({"role": "agent", "text": agent_text})
    if len(history) > MAX_HISTORY_TURNS * 2:
        history = history[-(MAX_HISTORY_TURNS * 2):]
    await redis.set(
        HISTORY_KEY.format(sid=session_id),
        orjson.dumps(history).decode(),
    )
