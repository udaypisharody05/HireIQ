from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session, selectinload

from app.models.catalog_sync_state import CatalogSyncState
from app.models.problem import Problem, ProblemTopic
from app.services.catalog import CATALOG_SOURCE
from app.services.leetcode.client import LeetCodeClient, LeetCodeClientError

CATALOG_PAGE_SIZE = 100
CATALOG_PAGE_DELAY_SECONDS = 0.5
CATALOG_LOCK_NAME = "hireiq_leetcode_catalog_sync"
SYNC_STATUS_SYNCING = "syncing"
SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_FAILED = "failed"


class CatalogSyncError(Exception):
    pass


@dataclass(frozen=True)
class CatalogRecord:
    leetcode_problem_id: int
    title: str
    slug: str
    difficulty: str
    acceptance_rate: Decimal | None
    is_paid_only: bool
    topics: tuple[str, ...]


@dataclass(frozen=True)
class CatalogSyncResult:
    reported_total: int
    imported_count: int
    skipped_count: int
    created_count: int
    updated_count: int
    deactivated_count: int
    topics_created: int
    topics_removed: int
    completed_at: datetime


def sync_problem_catalog(
    db: Session,
    client: LeetCodeClient | None = None,
) -> CatalogSyncResult:
    client = client or LeetCodeClient(max_attempts=5, retry_delay_seconds=1.0)
    lock_connection = db.get_bind().connect()
    if not _acquire_lock(lock_connection):
        lock_connection.close()
        raise CatalogSyncError("Another catalog sync is already running.")

    try:
        _mark_syncing(db)
        reported_total, raw_questions = _fetch_complete_catalog(client)
        records, skipped_count = _validate_catalog(raw_questions)
        result = _apply_catalog(
            records=records,
            reported_total=reported_total,
            skipped_count=skipped_count,
            db=db,
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _mark_failed(db, str(exc))
        if isinstance(exc, CatalogSyncError):
            raise
        if isinstance(exc, LeetCodeClientError):
            raise CatalogSyncError(str(exc)) from exc
        raise CatalogSyncError("Unexpected catalog sync failure.") from exc
    finally:
        _release_lock(lock_connection)
        lock_connection.close()


def _acquire_lock(connection: Connection) -> bool:
    return bool(
        connection.scalar(
            text("SELECT pg_try_advisory_lock(hashtext(:lock_name))"),
            {"lock_name": CATALOG_LOCK_NAME},
        )
    )


def _release_lock(connection: Connection) -> None:
    try:
        connection.execute(
            text("SELECT pg_advisory_unlock(hashtext(:lock_name))"),
            {"lock_name": CATALOG_LOCK_NAME},
        )
    except Exception:
        connection.rollback()


def _get_or_create_state(db: Session) -> CatalogSyncState:
    state = db.scalar(select(CatalogSyncState).where(CatalogSyncState.source == CATALOG_SOURCE))
    if state is None:
        state = CatalogSyncState(source=CATALOG_SOURCE)
        db.add(state)
        db.flush()
    return state


def _mark_syncing(db: Session) -> None:
    state = _get_or_create_state(db)
    state.status = SYNC_STATUS_SYNCING
    state.started_at = _utc_now()
    state.completed_at = None
    state.last_error = None
    db.commit()


def _mark_failed(db: Session, message: str) -> None:
    state = _get_or_create_state(db)
    state.status = SYNC_STATUS_FAILED
    state.completed_at = _utc_now()
    state.last_error = message[:512]
    db.commit()


def _fetch_complete_catalog(client: LeetCodeClient) -> tuple[int, list[dict[str, Any]]]:
    questions: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    reported_total: int | None = None
    skip = 0

    while reported_total is None or skip < reported_total:
        if skip > 0:
            time.sleep(CATALOG_PAGE_DELAY_SECONDS)

        page_total, page = client.get_problem_catalog_page(skip=skip, limit=CATALOG_PAGE_SIZE)
        if reported_total is None:
            reported_total = page_total
        elif page_total != reported_total:
            raise CatalogSyncError("LeetCode catalog total changed during pagination.")

        if not page:
            raise CatalogSyncError("LeetCode catalog pagination ended before the reported total.")

        page_slugs = {
            item.get("titleSlug")
            for item in page
            if isinstance(item.get("titleSlug"), str)
        }
        if page_slugs & seen_slugs:
            raise CatalogSyncError("LeetCode returned a duplicate catalog page.")

        seen_slugs.update(page_slugs)
        questions.extend(page)
        skip += len(page)

    if reported_total is None or len(questions) != reported_total:
        raise CatalogSyncError("LeetCode catalog count did not match the fetched records.")

    return reported_total, questions


def _validate_catalog(raw_questions: list[dict[str, Any]]) -> tuple[list[CatalogRecord], int]:
    records: list[CatalogRecord] = []
    seen_ids: set[int] = set()
    seen_slugs: set[str] = set()
    skipped_count = 0

    for question in raw_questions:
        frontend_id = question.get("questionFrontendId")
        if not isinstance(frontend_id, str) or not frontend_id.isdigit():
            skipped_count += 1
            continue

        problem_id = int(frontend_id)
        title = _required_string(question.get("title"), "title")
        slug = _required_string(question.get("titleSlug"), "titleSlug")
        difficulty = _required_string(question.get("difficulty"), "difficulty")
        is_paid_only = question.get("isPaidOnly")
        if not isinstance(is_paid_only, bool):
            raise CatalogSyncError(f"LeetCode catalog problem '{slug}' had invalid premium metadata.")

        if problem_id in seen_ids or slug in seen_slugs:
            raise CatalogSyncError(f"LeetCode catalog contained a duplicate ID or slug for '{slug}'.")
        seen_ids.add(problem_id)
        seen_slugs.add(slug)

        topic_tags = question.get("topicTags")
        if not isinstance(topic_tags, list):
            raise CatalogSyncError(f"LeetCode catalog problem '{slug}' had invalid topics.")
        topics = tuple(
            sorted(
                {
                    name
                    for tag in topic_tags
                    if isinstance(tag, dict)
                    and isinstance((name := tag.get("name")), str)
                    and name
                }
            )
        )

        records.append(
            CatalogRecord(
                leetcode_problem_id=problem_id,
                title=title,
                slug=slug,
                difficulty=difficulty,
                acceptance_rate=_decimal_or_none(question.get("acRate")),
                is_paid_only=is_paid_only,
                topics=topics,
            )
        )

    return records, skipped_count


def _apply_catalog(
    records: list[CatalogRecord],
    reported_total: int,
    skipped_count: int,
    db: Session,
) -> CatalogSyncResult:
    existing_problems = list(
        db.scalars(select(Problem).options(selectinload(Problem.topics))).all()
    )
    by_id = {problem.leetcode_problem_id: problem for problem in existing_problems}
    by_slug = {problem.slug: problem for problem in existing_problems}
    active_problem_ids: set[int] = set()
    created_count = 0
    updated_count = 0
    deactivated_count = 0
    topics_created = 0
    topics_removed = 0

    for record in records:
        id_match = by_id.get(record.leetcode_problem_id)
        slug_match = by_slug.get(record.slug)
        if id_match is not None and slug_match is not None and id_match.id != slug_match.id:
            raise CatalogSyncError(
                f"Catalog identity conflict for LeetCode problem '{record.slug}'."
            )

        problem = id_match or slug_match
        if record.is_paid_only:
            if problem is not None and problem.is_active:
                problem.is_active = False
                deactivated_count += 1
            continue

        active_problem_ids.add(record.leetcode_problem_id)
        if problem is None:
            problem = Problem(
                leetcode_problem_id=record.leetcode_problem_id,
                title=record.title,
                slug=record.slug,
                difficulty=record.difficulty,
                acceptance_rate=record.acceptance_rate,
                is_active=True,
            )
            db.add(problem)
            db.flush()
            problem.topics = [
                ProblemTopic(problem_id=problem.id, topic=topic)
                for topic in record.topics
            ]
            topics_created += len(record.topics)
            by_id[problem.leetcode_problem_id] = problem
            by_slug[problem.slug] = problem
            created_count += 1
            continue

        old_slug = problem.slug
        changed = (
            problem.leetcode_problem_id != record.leetcode_problem_id
            or problem.title != record.title
            or problem.slug != record.slug
            or problem.difficulty != record.difficulty
            or problem.acceptance_rate != record.acceptance_rate
            or not problem.is_active
        )
        problem.leetcode_problem_id = record.leetcode_problem_id
        problem.title = record.title
        problem.slug = record.slug
        problem.difficulty = record.difficulty
        problem.acceptance_rate = record.acceptance_rate
        problem.is_active = True
        if old_slug != record.slug:
            by_slug.pop(old_slug, None)
            by_slug[record.slug] = problem

        existing_topics = {topic.topic: topic for topic in problem.topics}
        desired_topics = set(record.topics)
        for topic_name in desired_topics - set(existing_topics):
            problem.topics.append(ProblemTopic(problem_id=problem.id, topic=topic_name))
            topics_created += 1
            changed = True
        for topic_name in set(existing_topics) - desired_topics:
            problem.topics.remove(existing_topics[topic_name])
            topics_removed += 1
            changed = True

        if changed:
            updated_count += 1

    for problem in existing_problems:
        if problem.leetcode_problem_id not in active_problem_ids and problem.is_active:
            problem.is_active = False
            deactivated_count += 1

    completed_at = _utc_now()
    state = _get_or_create_state(db)
    state.status = SYNC_STATUS_SUCCESS
    state.completed_at = completed_at
    state.last_successful_at = completed_at
    state.last_error = None
    state.reported_total = reported_total
    state.imported_count = len(active_problem_ids)
    state.skipped_count = skipped_count + sum(1 for record in records if record.is_paid_only)

    return CatalogSyncResult(
        reported_total=reported_total,
        imported_count=state.imported_count,
        skipped_count=state.skipped_count,
        created_count=created_count,
        updated_count=updated_count,
        deactivated_count=deactivated_count,
        topics_created=topics_created,
        topics_removed=topics_removed,
        completed_at=completed_at,
    )


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogSyncError(f"LeetCode catalog record was missing '{field_name}'.")
    return value


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise CatalogSyncError("LeetCode catalog record had invalid acceptance rate.") from exc


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
