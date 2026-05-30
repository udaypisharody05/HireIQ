from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="SET NULL"))
    resume_upload_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_uploads.id", ondelete="SET NULL"),
    )
    topic: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), default="open", server_default="open")
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)

    user: Mapped[User] = relationship(back_populates="recommendations")
    problem: Mapped[Problem | None] = relationship(back_populates="recommendations")
    resume_upload: Mapped[ResumeUpload | None] = relationship(back_populates="recommendations")
