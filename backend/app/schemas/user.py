import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    clerk_user_id: str
    email: str | None = None
    full_name: str | None = None


class UserRead(UserCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
