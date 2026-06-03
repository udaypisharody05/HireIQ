from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.leetcode_profile import LeetCodeProfile
from app.models.user import User
from app.schemas.leetcode_profile import LeetCodeProfileCreate, LeetCodeProfileRead
from app.schemas.leetcode_sync import LeetCodeSyncResponse
from app.services.leetcode.sync import LeetCodeSyncError, sync_leetcode_profile

router = APIRouter(prefix="/leetcode", tags=["leetcode"])


@router.post("/profile", response_model=LeetCodeProfileRead)
def upsert_leetcode_profile(profile_in: LeetCodeProfileCreate, db: Session = Depends(get_db)) -> LeetCodeProfile:
    user = db.scalar(select(User).where(User.clerk_user_id == profile_in.clerk_user_id))

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    username = profile_in.leetcode_username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="LeetCode username is required.")

    profile = db.scalar(select(LeetCodeProfile).where(LeetCodeProfile.user_id == user.id))

    if profile is None:
        profile = LeetCodeProfile(user_id=user.id, username=username)
        db.add(profile)
    else:
        profile.username = username

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="LeetCode username is already linked to another user.",
        ) from exc

    db.refresh(profile)
    return profile


@router.get("/profile/{clerk_user_id}", response_model=LeetCodeProfileRead)
def get_leetcode_profile(clerk_user_id: str, db: Session = Depends(get_db)) -> LeetCodeProfile:
    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    profile = db.scalar(select(LeetCodeProfile).where(LeetCodeProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LeetCode profile not found.")

    return profile


@router.post("/sync/{clerk_user_id}", response_model=LeetCodeSyncResponse)
def sync_profile(clerk_user_id: str, db: Session = Depends(get_db)) -> LeetCodeSyncResponse:
    try:
        result = sync_leetcode_profile(clerk_user_id=clerk_user_id, db=db)
    except LeetCodeSyncError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return LeetCodeSyncResponse(**result.__dict__)
