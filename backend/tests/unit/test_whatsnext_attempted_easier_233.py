"""Whats-next attempted-but-unsolved easier fill (Issue #233).

A user with attempts on question Q but NO passed attempt gets an easier
same-skill question appended AFTER the skill recs, filling remaining slots
only (total <= limit), deduped, resolved via question_loader.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from app.models.schemas import Difficulty, Question
from app.models.skill_graph_schemas import (
    LearningEvent,
    LearningEventType,
    QuestionSkill,
    Recommendation,
    RecommendationReason,
    Skill,
)
from app.models.submission_schemas import Submission
from app.services.skill_graph_service import SkillGraphService
from app.services.skill_taxonomy import DEFAULT_COLD_START_QUESTION_IDS

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


class TestAttemptedEasierCombined:
    """Senior edge coverage for #232 × #233 fallback interaction."""

    def _service_no_recs(self, subs, recs_list=None):
        service = SkillGraphService(
            repository=_seeded_repo(), submission_repository=FakeSubmissions(subs)
        )

        async def recs(*args, **kwargs):
            return list(recs_list) if recs_list is not None else []

        service.get_recommendations = recs  # type: ignore[method-assign]
        return service

    def test_attempted_id_unresolvable_by_loader_uses_easiest_candidate(self):
        # mid-q attempted but loader cannot resolve it: rank unknown, so the
        # easiest same-skill candidate (easy-q) is still recommended.
        service = self._service_no_recs(
            [_sub("u-1", "mid-q", passed=False)], [_rec("hard-q")]
        )
        loader = _loader({"hard-q": Difficulty.HARD, "easy-q": Difficulty.EASY})
        results = _run(service, loader, limit=5)
        assert [r.question.id for r in results] == ["hard-q", "easy-q"]
        assert results[1].reason == RecommendationReason.RETRY_EASIER

    def test_all_same_skill_candidates_attempted_yields_no_fill(self):
        service = self._service_no_recs(
            [
                _sub("u-1", "mid-q", passed=False),
                _sub("u-1", "easy-q", passed=False),
            ],
            [_rec("hard-q")],
        )
        results = _run(service, LOADER_ALL, limit=5)
        assert [r.question.id for r in results] == ["hard-q"]

    def test_limit_one_fill_wins_single_slot_no_defaults(self):
        service = self._service_no_recs([_sub("u-1", "mid-q", passed=False)])
        mapping = {
            "hard-q": Difficulty.HARD,
            "mid-q": Difficulty.MEDIUM,
            "easy-q": Difficulty.EASY,
        }

        async def loader(question_id: str):
            if question_id in mapping:
                return _question(question_id, mapping[question_id])
            if question_id in DEFAULT_COLD_START_QUESTION_IDS:
                return _question(question_id, Difficulty.EASY)
            return None

        results = _run(service, loader, limit=1)
        assert [r.question.id for r in results] == ["easy-q"]

    def test_states_block_defaults_even_when_fill_unresolvable(self):
        service = self._service_no_recs([_sub("u-1", "mid-q", passed=False)])
        # easy-q unresolvable → fill finds nothing; states exist → no defaults.
        loader = _loader({"hard-q": Difficulty.HARD, "mid-q": Difficulty.MEDIUM})

        async def run():
            await service.ingest_events(
                [
                    LearningEvent(
                        id="ev-combo",
                        user_id="u-1",
                        event_type=LearningEventType.SUBMISSION_PASSED,
                        question_id="hard-q",
                        occurred_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                    )
                ]
            )
            return await service.get_recommended_questions("u-1", loader, limit=5)

        assert asyncio.run(run()) == []

    def test_no_states_falls_through_to_defaults_when_fill_unresolvable(self):
        service = self._service_no_recs([_sub("u-1", "mid-q", passed=False)])

        # easy-q unresolvable → fill finds nothing; no states → defaults.
        async def loader(question_id: str):
            if question_id in ("hard-q", "mid-q"):
                return _question(
                    question_id,
                    Difficulty.HARD if question_id == "hard-q" else Difficulty.MEDIUM,
                )
            if question_id in DEFAULT_COLD_START_QUESTION_IDS:
                return _question(question_id, Difficulty.EASY)
            return None

        results = _run(service, loader, limit=4)
        assert [r.question.id for r in results] == list(DEFAULT_COLD_START_QUESTION_IDS)


class TestAttemptedEasierFillFanoutCap:
    """Round 2: bound ``question_loader`` fan-out in ``_attempted_easier_fill``.

    Uncapped, one unsolved attempt fans out to one loader call per
    same-skill candidate, so a many-attempts user costs
    ``attempts × candidates`` loader calls. The fill keeps best-pick
    (easiest strictly-easier, id tiebreak) in unsolved-attempt order, but
    the scan is bounded: a per-attempt candidate-load cap, a total
    loader-call budget, and early exit once rank-0 (EASY) is found.
    """

    def _service_no_recs(self, repo, subs):
        service = SkillGraphService(
            repository=repo, submission_repository=FakeSubmissions(subs)
        )

        async def recs(*args, **kwargs):
            return []

        service.get_recommendations = recs  # type: ignore[method-assign]
        return service

    def _big_repo(self, attempted_ids, candidate_ids):
        repo = InMemorySkillGraphRepository()
        repo.seed_skills([Skill(slug="arrays", name="Arrays")])
        repo.seed_question_skills(
            [
                QuestionSkill(question_id=qid, skill_slug="arrays", weight=1.0)
                for qid in attempted_ids + candidate_ids
            ]
        )
        return repo

    def _counting_loader(self, mapping, counter):
        async def load(question_id: str):
            counter["calls"] += 1
            if question_id not in mapping:
                return None
            return _question(question_id, mapping[question_id])

        return load

    def test_many_attempts_resolve_within_loader_budget(self):
        attempted = [f"hard-{i}" for i in range(25)]
        candidates = [f"easy-{i}" for i in range(40)]
        mapping = {qid: Difficulty.HARD for qid in attempted}
        mapping.update({qid: Difficulty.EASY for qid in candidates})
        counter = {"calls": 0}
        service = self._service_no_recs(
            self._big_repo(attempted, candidates),
            [_sub("u-1", qid, passed=False, seq=i) for i, qid in enumerate(attempted)],
        )
        results = _run(service, self._counting_loader(mapping, counter), limit=5)
        assert len(results) == 5  # == limit: fill never exceeds it.
        assert counter["calls"] <= SkillGraphService._ATTEMPTED_FILL_MAX_LOADER_CALLS
        assert {r.question.difficulty for r in results} == {Difficulty.EASY}
        assert len({r.question.id for r in results}) == 5

    def test_per_attempt_candidate_scan_is_bounded_but_keeps_best_pick(self):
        # All MEDIUM: every candidate is valid (strictly easier than HARD),
        # none triggers the rank-0 early exit, so the scan must hit the
        # per-attempt cap instead of loading all 100. Seed order puts a
        # larger id first: best-pick still wins over first-pick.
        attempted = ["hard-0"]
        candidates = [f"med-{i}" for i in [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
        candidates += [f"med-x{i}" for i in range(90)]
        mapping = {"hard-0": Difficulty.HARD}
        mapping.update({qid: Difficulty.MEDIUM for qid in candidates})
        counter = {"calls": 0}
        service = self._service_no_recs(
            self._big_repo(attempted, candidates),
            [_sub("u-1", "hard-0", passed=False)],
        )
        results = _run(service, self._counting_loader(mapping, counter), limit=5)
        assert [r.question.id for r in results] == ["med-0"]
        assert (
            counter["calls"]
            <= 1 + SkillGraphService._ATTEMPTED_FILL_MAX_CANDIDATE_LOADS_PER_ATTEMPT
        )

    def test_multiple_attempts_fill_in_attempt_order_within_limit(self):
        # Two skills so each unsolved attempt resolves to a distinct pick:
        # fills follow newest-first attempt order, total <= limit.
        repo = InMemorySkillGraphRepository()
        repo.seed_skills(
            [Skill(slug="arrays", name="Arrays"), Skill(slug="strings", name="Strings")]
        )
        repo.seed_question_skills(
            [
                QuestionSkill(question_id="hard-a", skill_slug="arrays", weight=1.0),
                QuestionSkill(question_id="easy-a", skill_slug="arrays", weight=1.0),
                QuestionSkill(question_id="hard-s", skill_slug="strings", weight=1.0),
                QuestionSkill(question_id="easy-s", skill_slug="strings", weight=1.0),
            ]
        )
        service = self._service_no_recs(
            repo,
            [
                _sub("u-1", "hard-s", passed=False, seq=1),
                _sub("u-1", "hard-a", passed=False, seq=0),
            ],
        )
        loader = self._counting_loader(
            {
                "hard-a": Difficulty.HARD,
                "easy-a": Difficulty.EASY,
                "hard-s": Difficulty.HARD,
                "easy-s": Difficulty.EASY,
            },
            {"calls": 0},
        )
        results = _run(service, loader, limit=2)
        assert [r.question.id for r in results] == ["easy-s", "easy-a"]
        assert [r.skill_slug for r in results] == ["strings", "arrays"]
        assert len(results) <= 2


class TestAttemptedEasierFillFairShare:
    """Round 3: the shared loader budget must not let newest attempts starve older ones.

    Newest-first scan with a single global budget means the newest attempts'
    candidate scans can consume the whole budget, leaving older attempts with
    zero candidate loads even when their best pick is resolvable. The fill
    splits the remaining budget fairly across attempts still to scan, so
    every unsolved attempt gets a candidate scan. Best-pick (easiest
    strictly-easier, id tiebreak) and newest-first attempt order are unchanged.
    """

    def _service_no_recs(self, repo, subs):
        service = SkillGraphService(
            repository=repo, submission_repository=FakeSubmissions(subs)
        )

        async def recs(*args, **kwargs):
            return []

        service.get_recommendations = recs  # type: ignore[method-assign]
        return service

    def _counting_loader(self, mapping, counter):
        async def load(question_id: str):
            counter["calls"] += 1
            if question_id not in mapping:
                return None
            return _question(question_id, mapping[question_id])

        return load

    def test_older_attempt_is_not_starved_by_newer_scans(self):
        # Newest-first history: two HARD attempts (skill "arrays") then an
        # older MEDIUM attempt (skill "strings"). Each newest attempt has 25
        # MEDIUM same-skill decoys (all strictly easier than HARD, none
        # triggers the rank-0 early exit). The older attempt's skill lists 7
        # HARD decoys (not easier: skipped, but each costs a loader call)
        # before its EASY best pick.
        arrays_candidates = [f"xmed-{i:02d}" for i in range(25)]
        strings_order = ["old-q"] + [f"yhard-{i:02d}" for i in range(7)] + ["yeasy"]
        repo = InMemorySkillGraphRepository()
        repo.seed_skills(
            [Skill(slug="arrays", name="Arrays"), Skill(slug="strings", name="Strings")]
        )
        repo.seed_question_skills(
            [
                QuestionSkill(question_id="new1-q", skill_slug="arrays", weight=1.0),
                QuestionSkill(question_id="new2-q", skill_slug="arrays", weight=1.0),
            ]
            + [
                QuestionSkill(question_id=qid, skill_slug="arrays", weight=1.0)
                for qid in arrays_candidates
            ]
            + [
                QuestionSkill(question_id=qid, skill_slug="strings", weight=1.0)
                for qid in strings_order
            ]
        )
        service = self._service_no_recs(
            repo,
            [
                _sub("u-1", "new1-q", passed=False, seq=2),
                _sub("u-1", "new2-q", passed=False, seq=1),
                _sub("u-1", "old-q", passed=False, seq=0),
            ],
        )
        mapping = {"new1-q": Difficulty.HARD, "new2-q": Difficulty.HARD}
        mapping.update({qid: Difficulty.MEDIUM for qid in arrays_candidates})
        mapping.update(
            {"old-q": Difficulty.MEDIUM, "yeasy": Difficulty.EASY},
        )
        mapping.update({f"yhard-{i:02d}": Difficulty.HARD for i in range(7)})
        counter = {"calls": 0}
        results = _run(service, self._counting_loader(mapping, counter), limit=3)
        assert counter["calls"] <= SkillGraphService._ATTEMPTED_FILL_MAX_LOADER_CALLS
        # All three unsolved attempts resolve, newest-first; the oldest
        # attempt still reaches its EASY best pick past the HARD decoys.
        assert [r.question.id for r in results] == ["xmed-00", "xmed-01", "yeasy"]
        assert len(results) <= 3
