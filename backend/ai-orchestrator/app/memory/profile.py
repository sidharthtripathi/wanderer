"""Long-term user preferences. Stored as JSONB in memory_profile.

Profile is broad (vegetarian, likes quiet places, prefers hill drives).
Updated only when confidence is high (3+ consistent signals).
Never written from a single session moment. Spec §4.2 memory model.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.memory_profile import MemoryProfile

log = get_logger(__name__)


async def get_profile(session: AsyncSession, user_id: UUID) -> dict:
    result = await session.execute(
        select(MemoryProfile.data).where(MemoryProfile.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    return row or {}


async def ensure_profile(session: AsyncSession, user_id: UUID) -> dict:
    """Create profile row if it doesn't exist, return current data."""
    stmt = (
        pg_insert(MemoryProfile)
        .values(user_id=user_id, data={})
        .on_conflict_do_nothing(index_elements=[MemoryProfile.user_id])
    )
    await session.execute(stmt)
    await session.commit()
    return await get_profile(session, user_id)


async def update_profile(session: AsyncSession, user_id: UUID, updates: dict) -> None:
    """Merge updates into existing profile JSONB. Only called with high-confidence deltas."""
    profile = await get_profile(session, user_id)
    merged = {**profile, **updates}

    await session.execute(
        pg_insert(MemoryProfile)
        .values(user_id=user_id, data=merged)
        .on_conflict_do_update(
            index_elements=[MemoryProfile.user_id],
            set_={"data": merged, "updated_at": None},  # None lets trigger fire
        )
    )
    await session.commit()
    log.info("profile_updated", user_id=str(user_id), keys=list(updates.keys()))


async def profile_to_prompt_fragment(session: AsyncSession, user_id: UUID) -> str:
    """Format profile as a short system prompt fragment. Returns empty string if profile sparse."""
    profile = await get_profile(session, user_id)
    if not profile:
        return ""

    lines = []
    dietary = profile.get("dietary")
    if dietary:
        lines.append(f"Dietary: {dietary}.")

    pace = profile.get("pace")
    if pace:
        lines.append(f"Pace: {pace}.")

    budget = profile.get("budget")
    if budget:
        lines.append(f"Budget: {budget}.")

    mobility = profile.get("mobility")
    if mobility:
        lines.append(f"Mobility note: {mobility}.")

    if "dislikes_loud_nightlife" in profile and profile["dislikes_loud_nightlife"]:
        lines.append("Prefers quiet places over loud nightlife.")

    if "prefers_hill_drives" in profile and profile["prefers_hill_drives"]:
        lines.append("Likes hill drives and scenic routes.")

    if not lines:
        return ""

    return "User profile: " + " ".join(lines)
