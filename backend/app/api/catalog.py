from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.catalog import CatalogStatusResponse
from app.services.catalog import get_catalog_status

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/status", response_model=CatalogStatusResponse)
def catalog_status(db: Session = Depends(get_db)) -> CatalogStatusResponse:
    return get_catalog_status(db)
