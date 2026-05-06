from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    firebase_uid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String)
    language: Mapped[str] = mapped_column(String, nullable=False, default="en")
    home_city_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    reputation_tier: Mapped[str] = mapped_column(String, nullable=False, default="bronze")
    reputation_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
