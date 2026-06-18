from datetime import datetime

from pydantic import BaseModel


class TopicStat(BaseModel):
    topic: str
    solved_count: int


class RecentSubmission(BaseModel):
    problem_title: str
    problem_slug: str
    difficulty: str
    status: str
    submitted_at: datetime


class AnalyticsSummary(BaseModel):
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    last_synced_at: datetime | None
    sync_status: str
    topic_stats: list[TopicStat]
    recent_submissions: list[RecentSubmission]


class StrongTopic(BaseModel):
    topic: str
    solved_count: int
    mastery_score: int


class WeakTopic(StrongTopic):
    reason: str


class FocusTopic(BaseModel):
    topic: str
    reason: str


class WeaknessAnalyticsResponse(BaseModel):
    strongest_topics: list[StrongTopic]
    weakest_topics: list[WeakTopic]
    recommended_focus_topics: list[FocusTopic]
