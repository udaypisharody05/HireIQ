from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/sync", response_model=UserRead)
def sync_user(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.clerk_user_id == user_in.clerk_user_id))

    if user is None:
        user = User(
            clerk_user_id=user_in.clerk_user_id,
            email=user_in.email,
            full_name=user_in.full_name,
        )
        db.add(user)
    else:
        user.email = user_in.email
        user.full_name = user_in.full_name

    db.commit()
    db.refresh(user)
    return user
