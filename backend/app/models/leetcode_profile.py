from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class LeetCodeProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "leetcode_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    ranking: Mapped[int | None] = mapped_column(Integer)
    reputation: Mapped[int | None] = mapped_column(Integer)
    total_solved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    easy_solved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    medium_solved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    hard_solved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(32), default="never_synced", server_default="never_synced", index=True)
    last_sync_error: Mapped[str | None] = mapped_column(String(512))

    user: Mapped[User] = relationship(back_populates="leetcode_profile")
