from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import ARRAY, Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class POI(Base):
    __tablename__ = "pois"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String)
    city_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("cities.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    vibe_tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    category: Mapped[str] = mapped_column(String, nullable=False)
    is_route: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    route_geom: Mapped[object | None] = mapped_column(
        Geography(geometry_type="LINESTRING", srid=4326)
    )
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False, default=1)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
