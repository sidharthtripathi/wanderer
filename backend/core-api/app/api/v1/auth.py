"""POST /v1/auth/exchange — provisions a user row on first sign-in.

Spec §5.1. The Firebase ID token is verified by `require_auth`. On first call,
we ensure a `users` row exists for this Firebase UID.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_session
from app.schemas.user import UserPublic
from app.services.users import get_or_create_user, update_last_seen

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/exchange", response_model=UserPublic)
async def exchange(
    auth: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserPublic:
    user = await get_or_create_user(session, auth.firebase_uid)
    await update_last_seen(session, user.id)
    return UserPublic.model_validate(user)
