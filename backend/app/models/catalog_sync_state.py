from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CatalogSyncState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "catalog_sync_states"

    source: Mapped[str] = mapped_column(String(32), unique=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default="never_synced",
        server_default="never_synced",
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_successful_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(512))
    reported_total: Mapped[int | None] = mapped_column(Integer)
    imported_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    skipped_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
