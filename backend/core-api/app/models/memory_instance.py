from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MemoryInstance(Base):
    __tablename__ = "memory_instance"

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    poi_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("pois.id"), primary_key=True
    )
    sentiment: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
