from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import AnalyticsSummary, WeaknessAnalyticsResponse
from app.services.analytics import (
    AnalyticsNotFoundError,
    get_analytics_summary,
    get_weakness_analytics,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary/{clerk_user_id}", response_model=AnalyticsSummary)
def analytics_summary(clerk_user_id: str, db: Session = Depends(get_db)) -> AnalyticsSummary:
    try:
        return get_analytics_summary(clerk_user_id=clerk_user_id, db=db)
    except AnalyticsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/weaknesses/{clerk_user_id}", response_model=WeaknessAnalyticsResponse)
def weakness_analytics(clerk_user_id: str, db: Session = Depends(get_db)) -> WeaknessAnalyticsResponse:
    try:
        return get_weakness_analytics(clerk_user_id=clerk_user_id, db=db)
    except AnalyticsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
