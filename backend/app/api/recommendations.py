from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.recommendations import RecommendationResponse
from app.services.analytics import AnalyticsNotFoundError
from app.services.recommendations import get_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{clerk_user_id}", response_model=RecommendationResponse)
def recommendations(clerk_user_id: str, db: Session = Depends(get_db)) -> RecommendationResponse:
    try:
        return get_recommendations(clerk_user_id=clerk_user_id, db=db)
    except AnalyticsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
