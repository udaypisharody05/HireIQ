from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))

    leetcode_profile: Mapped[LeetCodeProfile | None] = relationship(back_populates="user", cascade="all, delete-orphan")
    submissions: Mapped[list[UserSubmission]] = relationship(back_populates="user", cascade="all, delete-orphan")
    topic_stats: Mapped[list[UserTopicStat]] = relationship(back_populates="user", cascade="all, delete-orphan")
    resume_uploads: Mapped[list[ResumeUpload]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="user", cascade="all, delete-orphan")
