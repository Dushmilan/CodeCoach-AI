"""LearningAnalyticsService — read-only plateau detection over recent submissions."""

from datetime import datetime, timezone

from app.models.analytics_schemas import AnalyticsSignalsResponse
from app.ports.submission_repository import SubmissionRepository
from app.services.learning_analytics_rules import derive_signals

MAX_HISTORY = 1000


class LearningAnalyticsService:
    def __init__(self, repo: SubmissionRepository):
        self.repo = repo

    async def signals(
        self, *, user_id: str, now: datetime | None = None
    ) -> AnalyticsSignalsResponse:
        now = now or datetime.now(timezone.utc)
        subs = await self.repo.list_by_user(user_id, limit=MAX_HISTORY)
        nodes = derive_signals(subs, now=now)
        return AnalyticsSignalsResponse(signals=nodes, total=len(nodes))
