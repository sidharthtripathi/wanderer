from fastapi import APIRouter

from app.api.v1 import auth, community, me, points, subscription

router = APIRouter(prefix="/v1")
router.include_router(auth.router)
router.include_router(me.router)
router.include_router(community.router)
router.include_router(subscription.router)
router.include_router(points.router)
