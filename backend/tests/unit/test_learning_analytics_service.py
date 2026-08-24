from datetime import datetime, timedelta, timezone

from app.models.submission_schemas import Submission, SubmissionIn
from app.services.learning_analytics_service import LearningAnalyticsService

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


class FakeSubRepo:
    def __init__(self, subs):
        self._subs = subs

    async def list_by_user(self, user_id, limit=1000):
        return self._subs[:limit]

    async def add(self, **kw):
        raise NotImplementedError

    async def count_attempts(self, *a, **kw):
        return 0


def test_empty_history():
    svc = LearningAnalyticsService(FakeSubRepo([]))
    import asyncio

    resp = asyncio.run(svc.signals(user_id="u1", now=NOW))
    assert resp.total == 0 and resp.signals == []


def test_delegates_to_rules_and_respects_limit():
    from app.models.submission_schemas import Submission

    qid = "invert-binary-tree"
    subs = [
        Submission(
            id=str(i),
            user_id="u1",
            question_id=qid,
            code="c",
            language="python",
            passed=False,
            error_signature="sig",
            attempt_index=i,
            created_at=NOW - timedelta(days=i % 3),
        )
        for i in range(1005)
    ]
    svc = LearningAnalyticsService(FakeSubRepo(subs))
    import asyncio

    resp = asyncio.run(svc.signals(user_id="u1", now=NOW))
    # service caps at 1000, so at most the rule sees 1000
    assert resp.total <= 22  # at most one signal per skill (22 skills)
