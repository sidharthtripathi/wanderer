from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    centroid: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    bbox: Mapped[object | None] = mapped_column(Geography(geometry_type="POLYGON", srid=4326))
    flavor_pack_v: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_seed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
