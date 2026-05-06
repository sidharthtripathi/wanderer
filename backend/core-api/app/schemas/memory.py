from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MemoryProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: dict = Field(default_factory=dict)
    updated_at: datetime


class MemoryInstancePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    poi_id: UUID
    sentiment: float
    note: str | None = None
    updated_at: datetime
