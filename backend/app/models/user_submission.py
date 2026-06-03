from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class UserSubmission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_submissions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "leetcode_submission_id",
            name="uq_user_submissions_user_leetcode_submission_id",
        ),
        Index("ix_user_submissions_user_submitted_at", "user_id", "submitted_at"),
        Index("ix_user_submissions_user_status", "user_id", "status"),
        Index("ix_user_submissions_user_language", "user_id", "language"),
        Index("ix_user_submissions_problem_submitted_at", "problem_id", "submitted_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    leetcode_submission_id: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(32), default="leetcode", server_default="leetcode")
    status: Mapped[str] = mapped_column(String(32))
    language: Mapped[str | None] = mapped_column(String(80))
    runtime_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    submission_url: Mapped[str | None] = mapped_column(String(512))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    user: Mapped[User] = relationship(back_populates="submissions")
    problem: Mapped[Problem] = relationship(back_populates="submissions")
