"""Points endpoints — fully implemented in Slice 7 (spec §14)."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/balance")
async def get_balance() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 7")


@router.get("/ledger")
async def get_ledger() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 7")
