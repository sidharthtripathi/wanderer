from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    post_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("posts.id"), nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(String, nullable=False)
    sentiment: Mapped[float | None] = mapped_column(Float)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
