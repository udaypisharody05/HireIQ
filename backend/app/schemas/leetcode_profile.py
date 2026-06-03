import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LeetCodeProfileCreate(BaseModel):
    clerk_user_id: str
    leetcode_username: str = Field(min_length=1, max_length=255)


class LeetCodeProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    ranking: int | None = None
    reputation: int | None = None
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
