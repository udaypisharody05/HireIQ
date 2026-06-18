import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.leetcode_profile import LeetCodeProfile
from app.models.problem import Problem, ProblemTopic
from app.models.user import User
from app.models.user_submission import UserSubmission
from app.schemas.analytics import (
    AnalyticsSummary,
    FocusTopic,
    RecentSubmission,
    StrongTopic,
    TopicStat,
    WeaknessAnalyticsResponse,
    WeakTopic,
)

RECENT_SUBMISSIONS_LIMIT = 10
MINIMUM_TOPICS_FOR_INSIGHTS = 3
RANKED_TOPIC_LIMIT = 3
WEAK_SOLVED_COUNT_MAX = 2
MASTERY_POINTS_PER_SOLVED_PROBLEM = 10
MAX_MASTERY_SCORE = 100


class AnalyticsNotFoundError(Exception):
    pass


def get_user_and_profile(clerk_user_id: str, db: Session) -> tuple[User, LeetCodeProfile]:
    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        raise AnalyticsNotFoundError("User not found.")

    profile = db.scalar(select(LeetCodeProfile).where(LeetCodeProfile.user_id == user.id))
    if profile is None:
        raise AnalyticsNotFoundError("LeetCode profile not found.")

    return user, profile


def get_topic_solved_counts(user_id: uuid.UUID, db: Session) -> list[tuple[str, int]]:
    rows = db.execute(
        select(
            ProblemTopic.topic,
            func.count(distinct(UserSubmission.problem_id)).label("solved_count"),
        )
        .join(Problem, Problem.id == ProblemTopic.problem_id)
        .join(UserSubmission, UserSubmission.problem_id == Problem.id)
        .where(
            UserSubmission.user_id == user_id,
            UserSubmission.status == "Accepted",
        )
        .group_by(ProblemTopic.topic)
    ).all()
    return [(row.topic, row.solved_count) for row in rows]


def get_analytics_summary(clerk_user_id: str, db: Session) -> AnalyticsSummary:
    user, profile = get_user_and_profile(clerk_user_id, db)
    topic_counts = sorted(
        get_topic_solved_counts(user.id, db),
        key=lambda item: (-item[1], item[0]),
    )

    recent_rows = db.execute(
        select(
            Problem.title,
            Problem.slug,
            Problem.difficulty,
            UserSubmission.status,
            UserSubmission.submitted_at,
        )
        .join(Problem, Problem.id == UserSubmission.problem_id)
        .where(UserSubmission.user_id == user.id)
        .order_by(UserSubmission.submitted_at.desc())
        .limit(RECENT_SUBMISSIONS_LIMIT)
    ).all()

    return AnalyticsSummary(
        total_solved=profile.total_solved,
        easy_solved=profile.easy_solved,
        medium_solved=profile.medium_solved,
        hard_solved=profile.hard_solved,
        last_synced_at=profile.last_synced_at,
        sync_status=profile.sync_status,
        topic_stats=[
            TopicStat(topic=topic, solved_count=solved_count)
            for topic, solved_count in topic_counts
        ],
        recent_submissions=[
            RecentSubmission(
                problem_title=row.title,
                problem_slug=row.slug,
                difficulty=row.difficulty,
                status=row.status,
                submitted_at=row.submitted_at,
            )
            for row in recent_rows
        ],
    )


def get_weakness_analytics(clerk_user_id: str, db: Session) -> WeaknessAnalyticsResponse:
    user, _ = get_user_and_profile(clerk_user_id, db)
    topic_counts = get_topic_solved_counts(user.id, db)

    if len(topic_counts) < MINIMUM_TOPICS_FOR_INSIGHTS:
        return WeaknessAnalyticsResponse(
            strongest_topics=[],
            weakest_topics=[],
            recommended_focus_topics=[],
        )

    scored_topics = [
        StrongTopic(
            topic=topic,
            solved_count=solved_count,
            mastery_score=min(
                MAX_MASTERY_SCORE,
                solved_count * MASTERY_POINTS_PER_SOLVED_PROBLEM,
            ),
        )
        for topic, solved_count in topic_counts
    ]

    strongest_topics = sorted(
        scored_topics,
        key=lambda item: (-item.mastery_score, -item.solved_count, item.topic),
    )[:RANKED_TOPIC_LIMIT]

    weak_candidates = sorted(
        (
            topic
            for topic in scored_topics
            if topic.solved_count <= WEAK_SOLVED_COUNT_MAX
        ),
        key=lambda item: (item.mastery_score, item.solved_count, item.topic),
    )[:RANKED_TOPIC_LIMIT]

    weakest_topics = [
        WeakTopic(
            topic=topic.topic,
            solved_count=topic.solved_count,
            mastery_score=topic.mastery_score,
            reason=(
                f"Only {topic.solved_count} accepted "
                f"{'problem from this topic is' if topic.solved_count == 1 else 'problems from this topic are'} "
                "represented in your recent synced data."
            ),
        )
        for topic in weak_candidates
    ]
    recommended_focus_topics = [
        FocusTopic(
            topic=topic.topic,
            reason=f"Practice more {topic.topic} problems to build broader recent evidence.",
        )
        for topic in weak_candidates
    ]

    return WeaknessAnalyticsResponse(
        strongest_topics=strongest_topics,
        weakest_topics=weakest_topics,
        recommended_focus_topics=recommended_focus_topics,
    )
