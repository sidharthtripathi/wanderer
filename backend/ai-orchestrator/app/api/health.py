from fastapi import APIRouter, HTTPException, status

from app.clients.qdrant import get_qdrant
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz() -> dict[str, str]:
    settings = get_settings()
    if not settings.google_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Gemini API key not configured"
        )
    try:
        qdrant = get_qdrant()
        await qdrant.health_check()
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"Qdrant unavailable: {exc}"
        ) from exc
    return {"status": "ready"}
