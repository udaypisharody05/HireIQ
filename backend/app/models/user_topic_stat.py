from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class UserTopicStat(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_topic_stats"
    __table_args__ = (UniqueConstraint("user_id", "topic", name="uq_user_topic_stats_user_topic"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(120))
    attempted_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    solved_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="topic_stats")
