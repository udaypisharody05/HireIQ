from datetime import datetime

from pydantic import BaseModel


class CatalogStatusResponse(BaseModel):
    catalog_size: int
    active_topic_count: int
    last_refreshed_at: datetime | None
    sync_status: str
    reported_total: int | None
    skipped_count: int
