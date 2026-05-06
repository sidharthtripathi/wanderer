"""Community endpoints — fully implemented in Slice 6 (spec §14).

Stubs are present so the API surface is discoverable from OpenAPI. They return
501 until wired up.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/posts", tags=["community"])


@router.post("")
async def create_post() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 6")


@router.get("/{post_id}")
async def get_post(post_id: str) -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 6")


@router.get("")
async def list_posts() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 6")


@router.post("/{post_id}/reviews")
async def add_review(post_id: str) -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 6")


@router.post("/{post_id}/like")
async def like_post(post_id: str) -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 6")


@router.post("/{post_id}/flag")
async def flag_post(post_id: str) -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in Slice 6")
