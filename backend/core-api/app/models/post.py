from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    poi_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("pois.id"), nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(String, nullable=False)
    best_time: Mapped[str | None] = mapped_column(String)
    what_to_order: Mapped[str | None] = mapped_column(String)
    who_for: Mapped[str | None] = mapped_column(String)
    vibe_tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    photos: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="live")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
