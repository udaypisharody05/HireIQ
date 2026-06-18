from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.leetcode_profile import LeetCodeProfile
from app.models.problem import Problem, ProblemTopic
from app.models.user import User
from app.models.user_submission import UserSubmission
from app.schemas.analytics import AnalyticsSummary, RecentSubmission, TopicStat

RECENT_SUBMISSIONS_LIMIT = 10


class AnalyticsNotFoundError(Exception):
    pass


def get_analytics_summary(clerk_user_id: str, db: Session) -> AnalyticsSummary:
    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        raise AnalyticsNotFoundError("User not found.")

    profile = db.scalar(select(LeetCodeProfile).where(LeetCodeProfile.user_id == user.id))
    if profile is None:
        raise AnalyticsNotFoundError("LeetCode profile not found.")

    topic_rows = db.execute(
        select(
            ProblemTopic.topic,
            func.count(distinct(UserSubmission.problem_id)).label("solved_count"),
        )
        .join(Problem, Problem.id == ProblemTopic.problem_id)
        .join(UserSubmission, UserSubmission.problem_id == Problem.id)
        .where(
            UserSubmission.user_id == user.id,
            UserSubmission.status == "Accepted",
        )
        .group_by(ProblemTopic.topic)
        .order_by(func.count(distinct(UserSubmission.problem_id)).desc(), ProblemTopic.topic.asc())
    ).all()

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
            TopicStat(topic=row.topic, solved_count=row.solved_count)
            for row in topic_rows
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
