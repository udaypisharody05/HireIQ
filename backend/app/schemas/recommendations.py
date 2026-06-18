import uuid

from pydantic import BaseModel


class RecommendedTopic(BaseModel):
    topic: str
    priority_score: int
    reason: str


class RecommendedProblem(BaseModel):
    problem_id: uuid.UUID
    title: str
    slug: str
    difficulty: str
    topics: list[str]
    recommendation_reason: str


class RecommendationResponse(BaseModel):
    recommended_topics: list[RecommendedTopic]
    recommended_problems: list[RecommendedProblem]
