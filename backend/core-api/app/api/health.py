from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness — always returns 200 if the process is up."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(
    session: Annotated[AsyncSession, Depends(get_session)],
    rds: Annotated[redis.Redis, Depends(get_redis)],
) -> dict[str, str]:
    """Readiness — checks Postgres + Redis."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"postgres unavailable: {exc}"
        ) from exc
    try:
        pong = await rds.ping()
        if not pong:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "redis ping failed")
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"redis unavailable: {exc}"
        ) from exc
    return {"status": "ready"}
