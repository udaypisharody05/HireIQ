import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.problem import Problem, ProblemTopic
from app.models.user_submission import UserSubmission
from app.schemas.recommendations import (
    RecommendationResponse,
    RecommendedProblem,
    RecommendedTopic,
)
from app.services.analytics import (
    MASTERY_POINTS_PER_SOLVED_PROBLEM,
    MAX_MASTERY_SCORE,
    MINIMUM_TOPICS_FOR_INSIGHTS,
    WEAK_SOLVED_COUNT_MAX,
    get_topic_solved_counts,
    get_user_and_profile,
)

RECOMMENDED_TOPIC_LIMIT = 3
RECOMMENDED_PROBLEM_LIMIT = 5
DIFFICULTY_BONUSES = {"Easy": 20, "Medium": 10, "Hard": 0}
DIFFICULTY_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}


@dataclass(frozen=True)
class ScoredTopic:
    topic: str
    solved_count: int
    mastery_score: int
    priority_score: int
    is_strict_weakness: bool


@dataclass(frozen=True)
class ScoredProblem:
    problem: Problem
    topics: list[str]
    overlapping_topics: list[str]
    score: int


def get_recommendations(clerk_user_id: str, db: Session) -> RecommendationResponse:
    user, _ = get_user_and_profile(clerk_user_id, db)
    topic_counts = get_topic_solved_counts(user.id, db)

    if len(topic_counts) < MINIMUM_TOPICS_FOR_INSIGHTS:
        return RecommendationResponse(recommended_topics=[], recommended_problems=[])

    selected_topics = _select_recommended_topics(topic_counts)
    topic_priorities = {topic.topic: topic.priority_score for topic in selected_topics}
    problem_candidates = _load_unsolved_problem_candidates(
        user_id=user.id,
        recommended_topics=list(topic_priorities),
        db=db,
    )
    scored_problems = _score_problems(problem_candidates, topic_priorities)

    return RecommendationResponse(
        recommended_topics=[
            RecommendedTopic(
                topic=topic.topic,
                priority_score=topic.priority_score,
                reason=_topic_reason(topic),
            )
            for topic in selected_topics
        ],
        recommended_problems=[
            RecommendedProblem(
                problem_id=item.problem.id,
                title=item.problem.title,
                slug=item.problem.slug,
                difficulty=item.problem.difficulty,
                topics=item.topics,
                recommendation_reason=_problem_reason(item),
            )
            for item in scored_problems[:RECOMMENDED_PROBLEM_LIMIT]
        ],
    )


def _select_recommended_topics(topic_counts: list[tuple[str, int]]) -> list[ScoredTopic]:
    scored_topics = [
        ScoredTopic(
            topic=topic,
            solved_count=solved_count,
            mastery_score=min(MAX_MASTERY_SCORE, solved_count * MASTERY_POINTS_PER_SOLVED_PROBLEM),
            priority_score=MAX_MASTERY_SCORE
            - min(MAX_MASTERY_SCORE, solved_count * MASTERY_POINTS_PER_SOLVED_PROBLEM),
            is_strict_weakness=solved_count <= WEAK_SOLVED_COUNT_MAX,
        )
        for topic, solved_count in topic_counts
    ]

    return sorted(
        scored_topics,
        key=lambda item: (
            not item.is_strict_weakness,
            -item.priority_score,
            item.solved_count,
            item.topic,
        ),
    )[:RECOMMENDED_TOPIC_LIMIT]


def _load_unsolved_problem_candidates(
    user_id: uuid.UUID,
    recommended_topics: list[str],
    db: Session,
) -> list[Problem]:
    if not recommended_topics:
        return []

    accepted_submission_exists = (
        select(UserSubmission.id)
        .where(
            UserSubmission.user_id == user_id,
            UserSubmission.problem_id == Problem.id,
            UserSubmission.status == "Accepted",
        )
        .exists()
    )

    return list(
        db.scalars(
            select(Problem)
            .join(ProblemTopic, ProblemTopic.problem_id == Problem.id)
            .where(
                Problem.is_active.is_(True),
                ProblemTopic.topic.in_(recommended_topics),
                ~accepted_submission_exists,
            )
            .options(selectinload(Problem.topics))
            .distinct()
        ).all()
    )


def _score_problems(
    problems: list[Problem],
    topic_priorities: dict[str, int],
) -> list[ScoredProblem]:
    scored: list[ScoredProblem] = []
    for problem in problems:
        topics = sorted(topic.topic for topic in problem.topics)
        overlapping_topics = sorted(topic for topic in topics if topic in topic_priorities)
        score = sum(topic_priorities[topic] for topic in overlapping_topics)
        score += DIFFICULTY_BONUSES.get(problem.difficulty, 0)
        scored.append(
            ScoredProblem(
                problem=problem,
                topics=topics,
                overlapping_topics=overlapping_topics,
                score=score,
            )
        )

    return sorted(
        scored,
        key=lambda item: (
            -item.score,
            -len(item.overlapping_topics),
            DIFFICULTY_ORDER.get(item.problem.difficulty, 3),
            item.problem.slug,
        ),
    )


def _topic_reason(topic: ScoredTopic) -> str:
    if topic.is_strict_weakness:
        return (
            f"Only {topic.solved_count} accepted "
            f"{'problem is' if topic.solved_count == 1 else 'problems are'} represented "
            "for this topic in your recent synced data."
        )
    return (
        f"This is one of your lowest-mastery observed topics, with {topic.solved_count} "
        "accepted problems represented in recent synced data."
    )


def _problem_reason(problem: ScoredProblem) -> str:
    matching_topics = ", ".join(problem.overlapping_topics)
    difficulty_reason = (
        f"Its {problem.problem.difficulty} difficulty is preferred for focused practice."
        if problem.problem.difficulty in {"Easy", "Medium"}
        else "It is included because it strongly overlaps your recommended topics."
    )
    return f"Matches recommended topics: {matching_topics}. {difficulty_reason}"
