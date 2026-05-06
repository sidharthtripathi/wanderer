from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class POIPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    city_id: UUID | None = None
    name: str
    description: str | None = None
    lat: float
    lng: float
    vibe_tags: list[str] = Field(default_factory=list)
    category: str
    is_route: bool = False
    is_closed: bool = False
    engagement_score: float = 0
    freshness_score: float = 1
