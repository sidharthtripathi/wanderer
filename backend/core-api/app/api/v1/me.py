from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_session
from app.schemas.user import UserPublic, UserUpdate
from app.services.users import get_or_create_user, update_user

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserPublic)
async def get_me(
    auth: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserPublic:
    user = await get_or_create_user(session, auth.firebase_uid)
    return UserPublic.model_validate(user)


@router.patch("", response_model=UserPublic)
async def patch_me(
    body: UserUpdate,
    auth: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserPublic:
    user = await get_or_create_user(session, auth.firebase_uid)
    updated = await update_user(
        session,
        user.id,
        display_name=body.display_name,
        language=body.language,
        home_city_id=body.home_city_id,
    )
    return UserPublic.model_validate(updated)
