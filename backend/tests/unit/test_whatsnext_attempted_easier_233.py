"""Whats-next attempted-but-unsolved easier fill (Issue #233).

A user with attempts on question Q but NO passed attempt gets an easier
same-skill question appended AFTER the skill recs, filling remaining slots
only (total <= limit), deduped, resolved via question_loader.
"""

import asyncio
from datetime import datetime, timezone

from app.models.schemas import Difficulty, Question
from app.models.skill_graph_schemas import (
    QuestionSkill,
    Recommendation,
    RecommendationReason,
    Skill,
)
from app.models.submission_schemas import Submission
from app.services.skill_graph_service import SkillGraphService

from tests.simulation.in_memory_repo import InMemorySkillGraphRepository


def _seeded_repo() -> InMemorySkillGraphRepository:
    repo = InMemorySkillGraphRepository()
    repo.seed_skills([Skill(slug="arrays", name="Arrays")])
    repo.seed_question_skills(
        [
            QuestionSkill(question_id="hard-q", skill_slug="arrays", weight=1.0),
            QuestionSkill(question_id="mid-q", skill_slug="arrays", weight=1.0),
            QuestionSkill(question_id="easy-q", skill_slug="arrays", weight=1.0),
        ]
    )
    return repo


class FakeSubmissions:
    """Minimal SubmissionRepository fake (newest-first)."""

    def __init__(self, subs):
        self._subs = list(subs)

    async def list_by_user(self, user_id, limit=50):
        return [s for s in self._subs if s.user_id == user_id][:limit]


def _sub(user: str, question_id: str, passed: bool, seq: int = 0) -> Submission:
    return Submission(
        id=f"sub-{user}-{question_id}-{seq}",
        user_id=user,
        question_id=question_id,
        code="code",
        language="python",
        passed=passed,
        attempt_index=seq,
        created_at=datetime.now(timezone.utc),
    )


def _question(question_id: str, difficulty: Difficulty) -> Question:
    return Question(
        id=question_id,
        title=question_id.replace("-", " ").title(),
        difficulty=difficulty,
        category="arrays",
        company_tags=[],
        description="A sample question for testing.",
        starter={"python": "def solve():\n    pass"},
        examples=[],
        test_cases=[],
    )


def _loader(mapping):
    async def load(question_id: str):
        if question_id not in mapping:
            return None
        return _question(question_id, mapping[question_id])

    return load


def _rec(question_id: str) -> Recommendation:
    return Recommendation(
        skill_slug="arrays",
        name="Arrays",
        reason=RecommendationReason.WEAK_SKILL,
        reason_text="Arrays needs practice to become a strength.",
        suggested_question_id=question_id,
    )


def _run(service, loader, limit=5):
    async def run():
        return await service.get_recommended_questions("u-1", loader, limit=limit)

    return asyncio.run(run())


LOADER_ALL = _loader(
    {
        "hard-q": Difficulty.HARD,
        "mid-q": Difficulty.MEDIUM,
        "easy-q": Difficulty.EASY,
    }
)


class TestAttemptedEasierFill:
    def _service(self, subs):
        service = SkillGraphService(
            repository=_seeded_repo(), submission_repository=FakeSubmissions(subs)
        )

        async def recs(*args, **kwargs):
            return [_rec("hard-q")]

        service.get_recommendations = recs  # type: ignore[method-assign]
        return service

    def test_appends_easier_same_skill_question_after_skill_recs(self):
        service = self._service([_sub("u-1", "mid-q", passed=False)])
        results = _run(service, LOADER_ALL, limit=5)
        assert [r.question.id for r in results] == ["hard-q", "easy-q"]
        assert results[1].skill_slug == "arrays"
        assert results[1].reason == RecommendationReason.RETRY_EASIER
        assert results[1].reason_text

    def test_solved_attempts_are_excluded(self):
        service = self._service([_sub("u-1", "mid-q", passed=True)])
        results = _run(service, LOADER_ALL, limit=5)
        assert [r.question.id for r in results] == ["hard-q"]

    def test_mixed_history_only_unsolved_trigger_fill(self):
        service = self._service(
            [
                _sub("u-1", "hard-q", passed=True, seq=1),
                _sub("u-1", "mid-q", passed=False, seq=0),
            ]
        )
        results = _run(service, LOADER_ALL, limit=5)
        assert [r.question.id for r in results] == ["hard-q", "easy-q"]

    def test_already_recommended_ids_are_not_duplicated(self):
        service = SkillGraphService(
            repository=_seeded_repo(),
            submission_repository=FakeSubmissions([_sub("u-1", "mid-q", passed=False)]),
        )

        async def recs(*args, **kwargs):
            return [_rec("easy-q")]

        service.get_recommendations = recs  # type: ignore[method-assign]
        # easy-q already recommended; hard-q is not easier than mid-q → no fill.
        results = _run(service, LOADER_ALL, limit=5)
        assert [r.question.id for r in results] == ["easy-q"]

    def test_unresolvable_loader_ids_are_skipped(self):
        service = self._service([_sub("u-1", "mid-q", passed=False)])
        loader = _loader({"hard-q": Difficulty.HARD, "mid-q": Difficulty.MEDIUM})
        results = _run(service, loader, limit=5)
        assert [r.question.id for r in results] == ["hard-q"]

    def test_fills_remaining_slots_only(self):
        service = self._service([_sub("u-1", "mid-q", passed=False)])
        results = _run(service, LOADER_ALL, limit=1)
        assert [r.question.id for r in results] == ["hard-q"]
        assert len(results) <= 1

    def test_no_fill_when_nothing_is_easier_than_attempt(self):
        service = self._service([_sub("u-1", "easy-q", passed=False)])

        async def recs(*args, **kwargs):
            return [_rec("hard-q")]

        service.get_recommendations = recs  # type: ignore[method-assign]
        # easy-q attempted (unsolved, easiest): mid-q is not easier → no fill.
        loader = _loader(
            {
                "hard-q": Difficulty.HARD,
                "mid-q": Difficulty.MEDIUM,
                "easy-q": Difficulty.EASY,
            }
        )
        results = _run(service, loader, limit=5)
        assert [r.question.id for r in results] == ["hard-q"]

    def test_unmapped_attempted_question_is_skipped(self):
        service = self._service([_sub("u-1", "ghost-q", passed=False)])
        loader = _loader(
            {
                "hard-q": Difficulty.HARD,
                "mid-q": Difficulty.MEDIUM,
                "easy-q": Difficulty.EASY,
                "ghost-q": Difficulty.HARD,
            }
        )
        results = _run(service, loader, limit=5)
        assert [r.question.id for r in results] == ["hard-q"]

    def test_no_submission_repository_is_noop(self):
        service = SkillGraphService(repository=_seeded_repo())

        async def recs(*args, **kwargs):
            return [_rec("hard-q")]

        service.get_recommendations = recs  # type: ignore[method-assign]
        results = _run(service, LOADER_ALL, limit=5)
        assert [r.question.id for r in results] == ["hard-q"]
