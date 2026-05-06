from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country: str
    flavor_pack_v: int
    is_seed: bool
