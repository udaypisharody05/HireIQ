from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.catalog_sync_state import CatalogSyncState
from app.models.problem import Problem, ProblemTopic
from app.schemas.catalog import CatalogStatusResponse

CATALOG_SOURCE = "leetcode"


def get_catalog_status(db: Session) -> CatalogStatusResponse:
    state = db.scalar(select(CatalogSyncState).where(CatalogSyncState.source == CATALOG_SOURCE))
    catalog_size = db.scalar(
        select(func.count()).select_from(Problem).where(Problem.is_active.is_(True))
    ) or 0
    active_topic_count = db.scalar(
        select(func.count(distinct(ProblemTopic.topic)))
        .select_from(ProblemTopic)
        .join(Problem, Problem.id == ProblemTopic.problem_id)
        .where(Problem.is_active.is_(True))
    ) or 0

    return CatalogStatusResponse(
        catalog_size=catalog_size,
        active_topic_count=active_topic_count,
        last_refreshed_at=state.last_successful_at if state else None,
        sync_status=state.status if state else "never_synced",
        reported_total=state.reported_total if state else None,
        skipped_count=state.skipped_count if state else 0,
    )
