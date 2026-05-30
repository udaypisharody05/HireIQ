from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Problem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "problems"

    leetcode_problem_id: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    difficulty: Mapped[str] = mapped_column(String(32), index=True)
    acceptance_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    topics: Mapped[list[ProblemTopic]] = relationship(back_populates="problem", cascade="all, delete-orphan")
    submissions: Mapped[list[UserSubmission]] = relationship(back_populates="problem", cascade="all, delete-orphan")
    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="problem")


class ProblemTopic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "problem_topics"
    __table_args__ = (UniqueConstraint("problem_id", "topic", name="uq_problem_topics_problem_topic"),)

    problem_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(120), index=True)

    problem: Mapped[Problem] = relationship(back_populates="topics")
