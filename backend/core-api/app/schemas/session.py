from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    city_id: UUID | None = None
    mode: str
    started_at: datetime
    ended_at: datetime | None = None
    summary: str | None = None
    cost_points: int = 0
