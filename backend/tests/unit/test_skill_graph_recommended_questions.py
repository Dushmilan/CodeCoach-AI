"""Fast, DB-free unit tests for SkillGraphService.get_recommended_questions.

Uses the in-memory repository (shared with the simulation suite) plus a fake
question loader so the composition logic is exercised locally and fast.
"""

import asyncio

from app.models.schemas import Difficulty, Question
from app.models.skill_graph_schemas import (
    LearningEventType,
    RecommendedQuestion,
)
from app.services.skill_graph_service import SkillGraphService

from tests.simulation.harness import build_seeded_repo


def _pass(user: str, question: str, seq: int = 0):
    from datetime import datetime, timedelta, timezone

    from app.models.skill_graph_schemas import LearningEvent

    return LearningEvent(
        id=f"rq-{user}-{seq}",
        user_id=user,
        event_type=LearningEventType.SUBMISSION_PASSED,
        question_id=question,
        metadata={},
        occurred_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )


def _fake_question(question_id: str) -> Question:
    return Question(
        id=question_id,
        title=question_id.replace("-", " ").title(),
        difficulty=Difficulty.EASY,
        category="arrays",
        company_tags=["Google"],
        description="A sample question for testing.",
        starter={"python": "def solve():\n    pass"},
        examples=[],
        test_cases=[],
    )


def _build_service():
    repo = build_seeded_repo()
    return SkillGraphService(repository=repo)


class TestGetRecommendedQuestions:
    def test_returns_full_questions_with_reason_context(self):
        service = _build_service()
        asyncio.run(service.ingest_events([_pass("u-1", "two-sum", seq=1)]))

        async def loader(question_id: str):
            return _fake_question(question_id)

        results = asyncio.run(service.get_recommended_questions("u-1", loader, limit=5))

        assert isinstance(results, list)
        assert results
        for item in results:
            assert isinstance(item, RecommendedQuestion)
            assert item.skill_slug
            assert item.skill_name
            assert item.reason
            assert item.reason_text
            assert item.question.id

    def test_skips_recommendations_whose_question_fails_to_resolve(self):
        service = _build_service()
        asyncio.run(service.ingest_events([_pass("u-1", "two-sum", seq=1)]))

        async def loader(question_id: str):
            return None

        results = asyncio.run(service.get_recommended_questions("u-1", loader, limit=5))

        # No question resolved → nothing to surface; must not fabricate data.
        assert results == []

    def test_keeps_only_resolved_questions(self):
        service = _build_service()
        asyncio.run(service.ingest_events([_pass("u-1", "two-sum", seq=1)]))

        resolved = set()

        async def loader(question_id: str):
            if question_id.startswith("test-"):
                return None
            resolved.add(question_id)
            return _fake_question(question_id)

        results = asyncio.run(service.get_recommended_questions("u-1", loader, limit=5))

        assert results, "expected at least one resolvable recommendation"
        assert {r.question.id for r in results} <= resolved

    def test_limits_results(self):
        service = _build_service()
        asyncio.run(service.ingest_events([_pass("u-1", "two-sum", seq=1)]))

        async def loader(question_id: str):
            return _fake_question(question_id)

        results = asyncio.run(service.get_recommended_questions("u-1", loader, limit=2))
        assert len(results) <= 2
