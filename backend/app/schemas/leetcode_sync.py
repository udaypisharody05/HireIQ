import uuid
from datetime import datetime

from pydantic import BaseModel


class LeetCodeSyncResponse(BaseModel):
    profile_id: uuid.UUID
    username: str
    sync_status: str
    synced_at: datetime
    profile_stats_updated: bool
    problems_upserted: int
    topics_upserted: int
    submissions_inserted: int
    submissions_skipped: int
