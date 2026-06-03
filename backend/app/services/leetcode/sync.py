from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.leetcode_profile import LeetCodeProfile
from app.models.problem import Problem, ProblemTopic
from app.models.user import User
from app.models.user_submission import UserSubmission
from app.services.leetcode.client import LeetCodeClient, LeetCodeClientError

SYNC_STATUS_SYNCING = "syncing"
SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_FAILED = "failed"
RECENT_ACCEPTED_LIMIT = 50
METADATA_FETCH_DELAY_SECONDS = 0.2


class LeetCodeSyncError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class LeetCodeSyncResult:
    profile_id: uuid.UUID
    username: str
    sync_status: str
    synced_at: datetime
    profile_stats_updated: bool
    problems_upserted: int
    topics_upserted: int
    submissions_inserted: int
    submissions_skipped: int


def sync_leetcode_profile(
    clerk_user_id: str,
    db: Session,
    client: LeetCodeClient | None = None,
) -> LeetCodeSyncResult:
    client = client or LeetCodeClient()
    user, profile = _get_user_and_profile(clerk_user_id, db)
    username = profile.username.strip()
    if not username:
        raise LeetCodeSyncError("LeetCode username is required.", status_code=422)

    attempted_at = _utc_now()
    _mark_syncing(profile, attempted_at, db)

    try:
        profile_stats = client.get_profile_stats(username)
        accepted_submissions = client.get_recent_accepted_submissions(username, limit=RECENT_ACCEPTED_LIMIT)
        distinct_slugs = _extract_distinct_slugs(accepted_submissions)
        problems_by_slug = _load_existing_problems(distinct_slugs, db)

        missing_slugs = [slug for slug in distinct_slugs if slug not in problems_by_slug]
        metadata_by_slug = _fetch_missing_problem_metadata(missing_slugs, client)

        result = _apply_sync_data(
            user=user,
            profile=profile,
            profile_stats=profile_stats,
            accepted_submissions=accepted_submissions,
            problems_by_slug=problems_by_slug,
            metadata_by_slug=metadata_by_slug,
            db=db,
        )
        db.commit()
        return result
    except LeetCodeClientError as exc:
        db.rollback()
        _mark_failed(profile.id, str(exc), db)
        raise LeetCodeSyncError(str(exc), status_code=exc.status_code) from exc
    except LeetCodeSyncError as exc:
        db.rollback()
        _mark_failed(profile.id, str(exc), db)
        raise
    except Exception as exc:
        db.rollback()
        _mark_failed(profile.id, "Unexpected LeetCode sync failure.", db)
        raise LeetCodeSyncError("Unexpected LeetCode sync failure.", status_code=500) from exc


def _get_user_and_profile(clerk_user_id: str, db: Session) -> tuple[User, LeetCodeProfile]:
    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        raise LeetCodeSyncError("User not found.", status_code=404)

    profile = db.scalar(select(LeetCodeProfile).where(LeetCodeProfile.user_id == user.id))
    if profile is None:
        raise LeetCodeSyncError("LeetCode profile not found.", status_code=404)

    return user, profile


def _mark_syncing(profile: LeetCodeProfile, attempted_at: datetime, db: Session) -> None:
    profile.sync_status = SYNC_STATUS_SYNCING
    profile.last_sync_attempted_at = attempted_at
    profile.last_sync_error = None
    db.commit()
    db.refresh(profile)


def _mark_failed(profile_id: uuid.UUID, message: str, db: Session) -> None:
    profile = db.get(LeetCodeProfile, profile_id)
    if profile is None:
        return

    profile.sync_status = SYNC_STATUS_FAILED
    profile.last_sync_attempted_at = _utc_now()
    profile.last_sync_error = message[:512]
    db.commit()


def _apply_sync_data(
    user: User,
    profile: LeetCodeProfile,
    profile_stats: dict[str, Any],
    accepted_submissions: list[dict[str, Any]],
    problems_by_slug: dict[str, Problem],
    metadata_by_slug: dict[str, dict[str, Any]],
    db: Session,
) -> LeetCodeSyncResult:
    synced_at = _utc_now()
    _update_profile_stats(profile, profile_stats)

    problems_upserted = 0
    for slug, metadata in metadata_by_slug.items():
        problem = _build_problem_from_metadata(metadata)
        db.add(problem)
        db.flush()
        problems_by_slug[slug] = problem
        problems_upserted += 1

    topics_upserted = _insert_missing_topics(problems_by_slug, metadata_by_slug, db)
    submissions_inserted, submissions_skipped = _insert_missing_submissions(user, problems_by_slug, accepted_submissions, db)

    profile.sync_status = SYNC_STATUS_SUCCESS
    profile.last_synced_at = synced_at
    profile.last_sync_error = None

    return LeetCodeSyncResult(
        profile_id=profile.id,
        username=profile.username,
        sync_status=SYNC_STATUS_SUCCESS,
        synced_at=synced_at,
        profile_stats_updated=True,
        problems_upserted=problems_upserted,
        topics_upserted=topics_upserted,
        submissions_inserted=submissions_inserted,
        submissions_skipped=submissions_skipped,
    )


def _update_profile_stats(profile: LeetCodeProfile, profile_stats: dict[str, Any]) -> None:
    profile_data = profile_stats.get("profile") if isinstance(profile_stats.get("profile"), dict) else {}
    profile.ranking = _int_or_none(profile_data.get("ranking"))
    profile.reputation = _int_or_none(profile_data.get("reputation"))

    submit_stats = profile_stats.get("submitStatsGlobal")
    ac_counts = submit_stats.get("acSubmissionNum") if isinstance(submit_stats, dict) else []
    counts_by_difficulty = {
        item.get("difficulty"): _int_or_zero(item.get("count"))
        for item in ac_counts
        if isinstance(item, dict)
    }

    profile.total_solved = counts_by_difficulty.get("All", 0)
    profile.easy_solved = counts_by_difficulty.get("Easy", 0)
    profile.medium_solved = counts_by_difficulty.get("Medium", 0)
    profile.hard_solved = counts_by_difficulty.get("Hard", 0)


def _extract_distinct_slugs(submissions: list[dict[str, Any]]) -> list[str]:
    slugs: list[str] = []
    seen: set[str] = set()
    for submission in submissions:
        slug = submission.get("titleSlug")
        if isinstance(slug, str) and slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return slugs


def _load_existing_problems(slugs: list[str], db: Session) -> dict[str, Problem]:
    if not slugs:
        return {}

    problems = db.scalars(select(Problem).where(Problem.slug.in_(slugs))).all()
    return {problem.slug: problem for problem in problems}


def _fetch_missing_problem_metadata(slugs: list[str], client: LeetCodeClient) -> dict[str, dict[str, Any]]:
    metadata_by_slug: dict[str, dict[str, Any]] = {}
    for index, slug in enumerate(slugs):
        if index > 0:
            time.sleep(METADATA_FETCH_DELAY_SECONDS)
        metadata = client.get_problem_metadata(slug)
        metadata_slug = metadata.get("titleSlug")
        if metadata_slug != slug:
            raise LeetCodeSyncError(f"LeetCode metadata slug mismatch for '{slug}'.", status_code=502)
        metadata_by_slug[slug] = metadata
    return metadata_by_slug


def _build_problem_from_metadata(metadata: dict[str, Any]) -> Problem:
    frontend_id = _required_int(metadata.get("questionFrontendId"), "questionFrontendId")
    title = _required_string(metadata.get("title"), "title")
    slug = _required_string(metadata.get("titleSlug"), "titleSlug")
    difficulty = _required_string(metadata.get("difficulty"), "difficulty")

    return Problem(
        leetcode_problem_id=frontend_id,
        title=title,
        slug=slug,
        difficulty=difficulty,
        acceptance_rate=_decimal_or_none(metadata.get("acRate")),
        is_active=True,
    )


def _insert_missing_topics(
    problems_by_slug: dict[str, Problem],
    metadata_by_slug: dict[str, dict[str, Any]],
    db: Session,
) -> int:
    topics_inserted = 0
    for slug, metadata in metadata_by_slug.items():
        problem = problems_by_slug.get(slug)
        if problem is None:
            continue

        topic_tags = metadata.get("topicTags")
        if not isinstance(topic_tags, list):
            continue

        existing_topics = set(
            db.scalars(select(ProblemTopic.topic).where(ProblemTopic.problem_id == problem.id)).all()
        )

        for tag in topic_tags:
            if not isinstance(tag, dict):
                continue
            topic = tag.get("name")
            if not isinstance(topic, str) or not topic or topic in existing_topics:
                continue
            db.add(ProblemTopic(problem_id=problem.id, topic=topic))
            existing_topics.add(topic)
            topics_inserted += 1

    return topics_inserted


def _insert_missing_submissions(
    user: User,
    problems_by_slug: dict[str, Problem],
    submissions: list[dict[str, Any]],
    db: Session,
) -> tuple[int, int]:
    submissions_inserted = 0
    submissions_skipped = 0

    submission_ids = [
        str(submission_id)
        for submission in submissions
        if (submission_id := submission.get("id")) is not None
    ]
    existing_submission_ids = set()
    if submission_ids:
        existing_submission_ids = set(
            db.scalars(
                select(UserSubmission.leetcode_submission_id).where(
                    UserSubmission.user_id == user.id,
                    UserSubmission.leetcode_submission_id.in_(submission_ids),
                )
            ).all()
        )

    for submission in submissions:
        slug = submission.get("titleSlug")
        if not isinstance(slug, str):
            submissions_skipped += 1
            continue

        problem = problems_by_slug.get(slug)
        if problem is None:
            submissions_skipped += 1
            continue

        submitted_at = _timestamp_to_datetime(submission.get("timestamp"))
        submission_id_value = submission.get("id")
        leetcode_submission_id = str(submission_id_value) if submission_id_value is not None else None

        if leetcode_submission_id and leetcode_submission_id in existing_submission_ids:
            submissions_skipped += 1
            continue

        if leetcode_submission_id is None and _fallback_submission_exists(user.id, problem.id, submitted_at, db):
            submissions_skipped += 1
            continue

        db.add(
            UserSubmission(
                user_id=user.id,
                problem_id=problem.id,
                leetcode_submission_id=leetcode_submission_id,
                source="leetcode",
                status="Accepted",
                language=None,
                runtime_ms=None,
                memory_kb=None,
                submission_url=_submission_url(leetcode_submission_id),
                submitted_at=submitted_at,
            )
        )

        if leetcode_submission_id:
            existing_submission_ids.add(leetcode_submission_id)
        submissions_inserted += 1

    return submissions_inserted, submissions_skipped


def _fallback_submission_exists(user_id: uuid.UUID, problem_id: uuid.UUID, submitted_at: datetime, db: Session) -> bool:
    existing = db.scalar(
        select(UserSubmission.id).where(
            UserSubmission.user_id == user_id,
            UserSubmission.problem_id == problem_id,
            UserSubmission.submitted_at == submitted_at,
            UserSubmission.status == "Accepted",
            UserSubmission.source == "leetcode",
        )
    )
    return existing is not None


def _submission_url(leetcode_submission_id: str | None) -> str | None:
    if leetcode_submission_id is None:
        return None
    return f"https://leetcode.com/submissions/detail/{leetcode_submission_id}/"


def _timestamp_to_datetime(value: Any) -> datetime:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError) as exc:
        raise LeetCodeSyncError("LeetCode submission timestamp was invalid.", status_code=502) from exc


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise LeetCodeSyncError(f"LeetCode problem metadata was missing '{field_name}'.", status_code=502)
    return value


def _required_int(value: Any, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise LeetCodeSyncError(f"LeetCode problem metadata was missing '{field_name}'.", status_code=502) from exc


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
