from collections.abc import AsyncIterator

import redis.asyncio as redis

from app.core.config import get_settings

_pool: redis.ConnectionPool | None = None


def get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(get_settings().redis_url, decode_responses=True)
    return _pool


async def get_redis() -> AsyncIterator[redis.Redis]:
    client = redis.Redis(connection_pool=get_pool())
    try:
        yield client
    finally:
        await client.aclose()
