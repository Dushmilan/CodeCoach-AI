"""Issue #317: "Practice next" must not surface one question twice.

Different skills can legitimately map to the same question (e.g.
``trees`` and ``recursion`` both suggest ``invert-binary-tree``); the
panel must show it once. The recommendation payload is de-duplicated by
question id (first skill in ranked order keeps the card), and the
frontend renders a composite key as the safety net (frontend-side test).
"""

import asyncio
from datetime import datetime, timedelta, timezone

from app.models.schemas import Difficulty, Question
from app.models.skill_graph_schemas import (
    LearningEvent,
    LearningEventType,
    QuestionSkill,
    Skill,
)
from app.services.skill_graph_service import SkillGraphService

from tests.simulation.in_memory_repo import InMemorySkillGraphRepository


def _pass_skill(skill: str) -> LearningEvent:
    return LearningEvent(
        id=f"dedupe-{skill}",
        user_id="u-dup",
        event_type=LearningEventType.SUBMISSION_PASSED,
        question_id=None,
        skill_slug=skill,
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


def _build_service() -> SkillGraphService:
    repo = InMemorySkillGraphRepository()
    repo.seed_skills(
        [
            Skill(
                slug="trees",
                name="Trees",
                description="",
                parent_id=None,
                prerequisite_ids=[],
            ),
            Skill(
                slug="recursion",
                name="Recursion",
                description="",
                parent_id=None,
                prerequisite_ids=[],
            ),
        ]
    )
    # The shared-question mapping from the bug report: both skills
    # legitimately recommend the same question.
    repo.seed_question_skills(
        [
            QuestionSkill(
                question_id="invert-binary-tree", skill_slug="trees", weight=0.8
            ),
            QuestionSkill(
                question_id="invert-binary-tree", skill_slug="recursion", weight=0.2
            ),
        ]
    )
    service = SkillGraphService(repository=repo)
    asyncio.run(service.ingest_events([_pass_skill("trees"), _pass_skill("recursion")]))
    return service


def test_shared_question_renders_once_across_skill_recommendations():
    service = _build_service()

    async def loader(question_id: str):
        return _fake_question(question_id)

    results = asyncio.run(service.get_recommended_questions("u-dup", loader, limit=5))

    question_ids = [r.question.id for r in results]
    assert "invert-binary-tree" in question_ids, (
        "expected at least one recommendation mapped to the shared question"
    )
    assert question_ids.count("invert-binary-tree") == 1, (
        "the same question must appear at most once in the payload"
    )


def test_dedupe_is_stable_across_reruns():
    service = _build_service()

    async def loader(question_id: str):
        return _fake_question(question_id)

    for _ in range(2):
        results = asyncio.run(
            service.get_recommended_questions("u-dup", loader, limit=5)
        )
        ids = [r.question.id for r in results]
        assert len(ids) == len(set(ids)), f"duplicate question ids: {ids}"
