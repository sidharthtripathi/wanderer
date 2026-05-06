from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    """User fields returned to the client.

    Matches GET /v1/me. firebase_uid is intentionally not exposed to clients.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None = None
    language: str = "en"
    home_city_id: UUID | None = None
    reputation_tier: str
    reputation_score: int
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=64)
    language: str | None = Field(default=None, pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    home_city_id: UUID | None = None
