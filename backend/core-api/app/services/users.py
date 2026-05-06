"""User-related operations: provisioning a row on first auth, updating profile."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create_user(session: AsyncSession, firebase_uid: str) -> User:
    """Return the user row for a Firebase UID, creating it on first sign-in.

    Concurrency-safe via INSERT ... ON CONFLICT DO NOTHING + SELECT.
    """
    stmt = (
        pg_insert(User)
        .values(firebase_uid=firebase_uid)
        .on_conflict_do_nothing(index_elements=[User.firebase_uid])
    )
    await session.execute(stmt)
    await session.commit()

    result = await session.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one()
    return user


async def update_last_seen(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(last_seen_at=datetime.utcnow())
    )
    await session.commit()


async def update_user(
    session: AsyncSession,
    user_id: UUID,
    *,
    display_name: str | None = None,
    language: str | None = None,
    home_city_id: UUID | None = None,
) -> User:
    values: dict[str, object] = {}
    if display_name is not None:
        values["display_name"] = display_name
    if language is not None:
        values["language"] = language
    if home_city_id is not None:
        values["home_city_id"] = home_city_id
    if values:
        await session.execute(update(User).where(User.id == user_id).values(**values))
        await session.commit()
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one()
