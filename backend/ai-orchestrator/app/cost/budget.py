"""Per-session cost tracking. Stub for Slice 2 — full budget enforcement
with point deductions and tier limits comes in Slice 7 (Subscription & Points).
"""

from redis.asyncio import Redis

COST_KEY = "session:{sid}:cost"


async def track_tokens(redis: Redis, session_id: str, token_count: int) -> None:
    """Accumulate estimated token spend for a session."""
    current = await redis.get(COST_KEY.format(sid=session_id))
    total = (int(current) if current else 0) + token_count
    await redis.set(COST_KEY.format(sid=session_id), str(total))


async def get_session_cost(redis: Redis, session_id: str) -> int:
    current = await redis.get(COST_KEY.format(sid=session_id))
    return int(current) if current else 0
