"""Default whats-next questions for brand-new users (Issue #232).

A fresh user with no skill states and no classroom enrollment gets [] from
the skill-graph recs + programme starters chain. This suite pins the final
fallback: 4 curated default questions resolved via the injected
question_loader (never fabricated), in deterministic order.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.models.schemas import Difficulty, Question
from app.models.skill_graph_schemas import LearningEvent, LearningEventType
from app.services.skill_graph_service import SkillGraphService
from app.services.skill_taxonomy import (
    DEFAULT_COLD_START_QUESTION_IDS,
    QUESTION_SKILLS,
)

from tests.simulation.harness import build_seeded_repo


def _fake_question(question_id: str) -> Question:
    return Question(
        id=question_id,
        title=question_id.replace("-", " ").title(),
        difficulty=Difficulty.EASY,
        category="arrays",
        company_tags=[],
        description="Default starter.",
        starter={"python": "def solve():\n    pass"},
        examples=[],
        test_cases=[],
    )


def _isolated_service() -> SkillGraphService:
    """Seeded service with skill recs forced empty to isolate the fallback."""
    service = SkillGraphService(repository=build_seeded_repo())

    async def no_recs(*args, **kwargs):
        return []

    service.get_recommendations = no_recs  # type: ignore[method-assign]
    return service


class TestDefaultFallback:
    def test_fresh_user_with_no_starters_gets_four_defaults_in_order(self):
        service = _isolated_service()

        async def loader(qid: str):
            if qid in DEFAULT_COLD_START_QUESTION_IDS:
                return _fake_question(qid)
            return None

        results = asyncio.run(
            service.get_recommended_questions("fresh-232", loader, limit=4)
        )
        assert [r.question.id for r in results] == list(DEFAULT_COLD_START_QUESTION_IDS)
        assert all(r.reason_text for r in results)

    def test_missing_default_ids_are_skipped_never_fabricated(self):
        service = _isolated_service()
        missing = DEFAULT_COLD_START_QUESTION_IDS[0]

        async def loader(qid: str):
            if qid == missing:
                return None
            if qid in DEFAULT_COLD_START_QUESTION_IDS:
                return _fake_question(qid)
            return None

        results = asyncio.run(
            service.get_recommended_questions("fresh-232", loader, limit=4)
        )
        ids = [r.question.id for r in results]
        assert missing not in ids
        assert ids == [q for q in DEFAULT_COLD_START_QUESTION_IDS if q != missing]

    def test_programme_starters_take_precedence_over_defaults(self):
        service = _isolated_service()

        async def starters(uid, limit=5):
            return ["two-sum", "contains-duplicate"][:limit]

        service.get_enrolled_programme_starters = starters  # type: ignore[method-assign]

        async def loader(qid: str):
            return _fake_question(qid)

        results = asyncio.run(
            service.get_recommended_questions("fresh-232", loader, limit=4)
        )
        assert [r.question.id for r in results] == [
            "two-sum",
            "contains-duplicate",
        ]

    def test_users_with_states_never_get_defaults(self):
        service = SkillGraphService(repository=build_seeded_repo())

        async def loader(qid: str):
            return None

        async def run():
            await service.ingest_events(
                [
                    LearningEvent(
                        id="ev-232",
                        user_id="active-232",
                        event_type=LearningEventType.SUBMISSION_PASSED,
                        question_id="two-sum",
                        occurred_at=datetime.now(timezone.utc) - timedelta(minutes=10),
                    )
                ]
            )
            return await service.get_recommended_questions(
                "active-232", loader, limit=4
            )

        assert asyncio.run(run()) == []


class TestDefaultInventory:
    def test_exactly_four_curated_defaults(self):
        assert len(DEFAULT_COLD_START_QUESTION_IDS) == 4
        assert len(set(DEFAULT_COLD_START_QUESTION_IDS)) == 4

    def test_defaults_exist_in_bank_and_skill_mappings(self):
        live_ids = set(
            json.loads(
                (
                    Path(__file__).resolve().parents[1]
                    / "fixtures"
                    / "live_question_ids.json"
                ).read_text()
            )["question_ids"]
        )
        for qid in DEFAULT_COLD_START_QUESTION_IDS:
            assert qid in live_ids, f"{qid} missing from live bank snapshot"
            assert qid in QUESTION_SKILLS, f"{qid} missing skill mapping"
