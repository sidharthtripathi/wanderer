"""Entity-scoped memory — per-POI reactions. Spec §4.2 memory model.

"I didn't like that museum" changes the instance for that POI.
It does NOT filter out all museums. Next trip, Tokyo museums are fair game.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.memory_instance import MemoryInstance
from app.models.poi import POI

log = get_logger(__name__)


async def get_instance(
    session: AsyncSession, user_id: UUID, poi_id: UUID
) -> MemoryInstance | None:
    result = await session.execute(
        select(MemoryInstance).where(
            MemoryInstance.user_id == user_id, MemoryInstance.poi_id == poi_id
        )
    )
    return result.scalar_one_or_none()


async def get_instances_for_pois(
    session: AsyncSession, user_id: UUID, poi_ids: list[UUID]
) -> dict[UUID, MemoryInstance]:
    """Return memory instances for a set of POIs the user has reacted to."""
    if not poi_ids:
        return {}
    result = await session.execute(
        select(MemoryInstance).where(
            MemoryInstance.user_id == user_id,
            MemoryInstance.poi_id.in_(poi_ids),
        )
    )
    return {row.poi_id: row for row in result.scalars().all()}


async def upsert_instance(
    session: AsyncSession,
    user_id: UUID,
    poi_id: UUID,
    sentiment: float,
    note: str | None = None,
) -> None:
    """Create or update an instance memory for a specific POI."""
    stmt = (
        pg_insert(MemoryInstance)
        .values(user_id=user_id, poi_id=poi_id, sentiment=sentiment, note=note)
        .on_conflict_do_update(
            index_elements=[MemoryInstance.user_id, MemoryInstance.poi_id],
            set_={"sentiment": sentiment, "note": note, "updated_at": None},
        )
    )
    await session.execute(stmt)
    await session.commit()
    log.info(
        "instance_upserted",
        user_id=str(user_id),
        poi_id=str(poi_id),
        sentiment=sentiment,
    )


async def instances_to_prompt_fragment(
    session: AsyncSession, user_id: UUID, horizon_poi_ids: list[UUID]
) -> str:
    """Format instances as a short prompt fragment.

    E.g. "Things you've noted before: Cafe Mondays: you liked it (great coffee).
    That museum: you didn't enjoy it (boring)."
    """
    if not horizon_poi_ids:
        return ""

    instances = await get_instances_for_pois(session, user_id, horizon_poi_ids)
    if not instances:
        return ""

    # Enrich with POI names
    poi_ids = list(instances.keys())
    poi_result = await session.execute(select(POI.id, POI.name).where(POI.id.in_(poi_ids)))
    poi_names = {row.id: row.name for row in poi_result.all()}

    lines = []
    for poi_id, inst in instances.items():
        name = poi_names.get(poi_id, "Unknown place")
        sentiment_word = "liked" if inst.sentiment > 0 else "didn't enjoy"
        detail = f" ({inst.note})" if inst.note else ""
        lines.append(f"{name}: you {sentiment_word} it{detail}")

    if not lines:
        return ""

    return "Things you've noted before: " + " | ".join(lines) + "."
