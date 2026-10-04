"""Whats-next must never re-recommend an already-solved question (Issue #297).

Before the fix, ``recommend()`` picked ``question_by_skill[slug][0]``: after
solving Two Sum the reason text updated with progress but the suggested
question stayed ``two-sum``. The skill's suggested question now skips solved
ids, an all-solved skill yields no question (the slot falls through to other
content — per parent #294, solved questions are NEVER re-recommended as
"next"), and both cold-start fallbacks skip solved ids too.

Attempted-but-unsolved questions stay eligible here: they retry through the
Issue #233 easier-fill, which already excludes passed attempts.
"""

import asyncio
from datetime import datetime, timezone

from app.models.schemas import Difficulty, Question
from app.models.skill_graph_schemas import QuestionSkill, Skill
from app.models.submission_schemas import Submission
from app.services.skill_graph_rules import recommend
from app.services.skill_graph_service import SkillGraphService
from app.services.skill_taxonomy import DEFAULT_COLD_START_QUESTION_IDS

from tests.simulation.harness import build_seeded_repo
from tests.simulation.in_memory_repo import InMemorySkillGraphRepository


def _now() -> datetime:
    return datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)


def _repo() -> InMemorySkillGraphRepository:
    """One skill with two questions — the #297 branch-bank shape."""
    repo = InMemorySkillGraphRepository()
    repo.seed_skills([Skill(slug="arrays", name="Arrays")])
    repo.seed_question_skills(
        [
            QuestionSkill(question_id="two-sum", skill_slug="arrays", weight=1.0),
            QuestionSkill(
                question_id="contains-duplicate", skill_slug="arrays", weight=1.0
            ),
        ]
    )
    return repo


class FakeSubmissions:
    """SubmissionRepository fake: submissions + solved-id lookup."""

    def __init__(self, subs):
        self._subs = list(subs)

    async def list_by_user(self, user_id, *, limit=50):
        return [s for s in self._subs if s.user_id == user_id][:limit]

    async def list_solved_question_ids(self, user_id):
        return {
            s.question_id
            for s in self._subs
            if s.user_id == user_id and s.passed and s.question_id
        }


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


def _question(question_id: str) -> Question:
    return Question(
        id=question_id,
        title=question_id.replace("-", " ").title(),
        difficulty=Difficulty.EASY,
        category="arrays",
        company_tags=[],
        description="A sample question for testing.",
        starter={"python": "def solve():\n    pass"},
        examples=[],
        test_cases=[],
    )


async def _loader(question_id: str):
    return _question(question_id)


def _service(subs) -> SkillGraphService:
    return SkillGraphService(
        repository=_repo(), submission_repository=FakeSubmissions(subs)
    )


class TestRecommendSolvedExclusion:
    """Pure rule layer: solved ids are skipped when picking a question."""

    def _questions(self):
        return {"arrays": ["two-sum", "contains-duplicate"]}

    def test_solved_candidate_is_skipped_for_the_next_unsolved(self):
        result = recommend(
            {},
            {"arrays": "Arrays"},
            {},
            self._questions(),
            _now(),
            solved_question_ids={"two-sum"},
        )
        assert result[0].suggested_question_id == "contains-duplicate"

    def test_every_candidate_solved_yields_no_question(self):
        result = recommend(
            {},
            {"arrays": "Arrays"},
            {},
            self._questions(),
            _now(),
            solved_question_ids={"two-sum", "contains-duplicate"},
        )
        # Slot falls through to other content — never a solved repeat.
        assert result[0].suggested_question_id is None

    def test_without_solved_context_first_candidate_is_suggested(self):
        # Regression pin: callers that pass no solved set keep old behaviour.
        result = recommend({}, {"arrays": "Arrays"}, {}, self._questions(), _now())
        assert result[0].suggested_question_id == "two-sum"


class TestGetRecommendationsSolvedExclusion:
    """``/me/recommendations`` must not point at a passed question."""

    def test_solved_top_candidate_is_not_suggested(self):
        service = _service([_sub("u-1", "two-sum", passed=True)])
        recs = asyncio.run(service.get_recommendations("u-1"))
        assert recs
        assert recs[0].suggested_question_id == "contains-duplicate"

    def test_no_submission_repository_keeps_legacy_behaviour(self):
        # Onboarding previews wire no submission repo — must not crash.
        service = SkillGraphService(repository=_repo())
        recs = asyncio.run(service.get_recommendations("u-1"))
        assert recs
        assert recs[0].suggested_question_id == "two-sum"


class TestGetRecommendedQuestionsSolvedExclusion:
    """The concrete "Practice next" payload (``/me/recommended-questions``)."""

    def test_solved_question_never_appears_in_practice_next(self):
        service = _service([_sub("u-1", "two-sum", passed=True)])
        results = asyncio.run(
            service.get_recommended_questions("u-1", _loader, limit=5)
        )
        ids = [r.question.id for r in results]
        assert "two-sum" not in ids
        assert "contains-duplicate" in ids

    def test_all_skill_questions_solved_falls_through_to_unsolved_content(self):
        service = _service(
            [
                _sub("u-1", "two-sum", passed=True, seq=1),
                _sub("u-1", "contains-duplicate", passed=True, seq=0),
            ]
        )
        results = asyncio.run(
            service.get_recommended_questions("u-1", _loader, limit=5)
        )
        # Both skill candidates are solved → slot falls through to the next
        # best unsolved content (the curated cold-start defaults minus the
        # two solved ids), never a solved repeat.
        ids = [r.question.id for r in results]
        assert "two-sum" not in ids
        assert "contains-duplicate" not in ids
        assert ids == [
            qid
            for qid in DEFAULT_COLD_START_QUESTION_IDS
            if qid not in ("two-sum", "contains-duplicate")
        ]

    def test_all_solved_and_no_other_content_yields_empty(self):
        service = _service(
            [
                _sub("u-1", "two-sum", passed=True, seq=1),
                _sub("u-1", "contains-duplicate", passed=True, seq=0),
            ]
        )
        loader_ids = {"two-sum", "contains-duplicate"}

        async def loader(question_id: str):
            if question_id in loader_ids:
                return _question(question_id)
            return None

        results = asyncio.run(service.get_recommended_questions("u-1", loader, limit=5))
        # Nothing unsolved exists in the bank → empty state, no solved repeat.
        assert results == []

    def test_other_users_solved_ids_do_not_leak_into_this_user(self):
        service = _service(
            [
                _sub("u-2", "two-sum", passed=True),
            ]
        )
        results = asyncio.run(
            service.get_recommended_questions("u-1", _loader, limit=5)
        )
        ids = [r.question.id for r in results]
        assert ids == ["two-sum"]


class TestColdStartSolvedExclusion:
    """Cold-start fallbacks must skip solved ids (``two-sum`` leads the
    curated default list — exactly the #297 reproduction)."""

    def test_default_cold_start_skips_solved_ids(self):
        solved_default = DEFAULT_COLD_START_QUESTION_IDS[0]
        service = SkillGraphService(
            repository=build_seeded_repo(),
            submission_repository=FakeSubmissions(
                [_sub("u-1", solved_default, passed=True)]
            ),
        )

        async def no_recs(*args, **kwargs):
            return []

        service.get_recommendations = no_recs  # type: ignore[method-assign]

        async def loader(qid: str):
            if qid in DEFAULT_COLD_START_QUESTION_IDS:
                return _question(qid)
            return None

        results = asyncio.run(service.get_recommended_questions("u-1", loader, limit=4))
        ids = [r.question.id for r in results]
        expected = [
            qid for qid in DEFAULT_COLD_START_QUESTION_IDS if qid != solved_default
        ][:4]
        assert ids == expected
        assert solved_default not in ids
