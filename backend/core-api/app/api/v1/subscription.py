"""Subscription endpoints — fully implemented in Slice 7 (spec §14)."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("")
async def get_subscription() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 7")


@router.post("/verify")
async def verify_purchase() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 7")
