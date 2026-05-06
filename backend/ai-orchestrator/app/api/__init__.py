from fastapi import APIRouter

from app.api import health, sessions

router = APIRouter()
router.include_router(health.router)
router.include_router(sessions.router)
