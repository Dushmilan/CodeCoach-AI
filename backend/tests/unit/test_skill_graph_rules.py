import pytest
from datetime import datetime, timedelta, timezone

from app.models.skill_graph_schemas import (
    LearningEvent,
    LearningEventType,
    RecommendationReason,
    SkillStatus,
    Trend,
    UserSkillState,
)
from app.services.skill_graph_rules import (
    apply_event,
    decay_state,
    mastery_for_status,
    recommend,
    should_be_reviewed,
)
from app.services.skill_taxonomy import (
    MAX_MASTERY_DELTA_PER_EVENT,
)


def _now() -> datetime:
    return datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def _state(
    user="u1",
    slug="arrays",
    mastery=0.4,
    confidence=0.3,
    evidence=2,
    errors=0,
    distinct=None,
):
    return UserSkillState(
        user_id=user,
        skill_slug=slug,
        mastery_score=mastery,
        confidence=confidence,
        evidence_count=evidence,
        recent_error_count=errors,
        # A state with non-trivial mastery must already show question breadth;
        # the breadth cap (0.3 per distinct question) then stays consistent.
        distinct_question_ids=distinct if distinct is not None else ["q1", "q2"],
        last_seen_at=_now(),
    )


def _event(
    etype: LearningEventType,
    metadata=None,
    occurred=None,
    user="u1",
    question="q1",
):
    return LearningEvent(
        id=f"{etype.value}-{user}-{question}",
        user_id=user,
        event_type=etype,
        question_id=question,
        metadata=metadata or {},
        occurred_at=occurred or _now(),
    )


class TestMasteryStatus:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.0, SkillStatus.NEW),
            (0.1, SkillStatus.NEW),
            (0.2, SkillStatus.LEARNING),
            (0.44, SkillStatus.LEARNING),
            (0.45, SkillStatus.DEVELOPING),
            (0.74, SkillStatus.DEVELOPING),
            (0.75, SkillStatus.STRONG),
            (1.0, SkillStatus.STRONG),
        ],
    )
    def test_thresholds(self, score, expected):
        assert mastery_for_status(score) == expected


class TestApplyEvent:
    def test_independent_pass_increases_mastery(self):
        state = _state()
        new_state = apply_event(state, _event(LearningEventType.SUBMISSION_PASSED))
        assert new_state.mastery_score > state.mastery_score
        assert new_state.status == SkillStatus.DEVELOPING

    def test_independent_pass_beats_hinted_pass(self):
        base = _state(mastery=0.3)
        independent = apply_event(base, _event(LearningEventType.SUBMISSION_PASSED))
        hinted = apply_event(
            base,
            _event(
                LearningEventType.SUBMISSION_PASSED,
                metadata={"hint_count": 2},
            ),
        )
        assert independent.mastery_score > hinted.mastery_score

    def test_solution_reveal_gives_minimal_credit(self):
        base = _state(mastery=0.3)
        revealed = apply_event(
            base,
            _event(
                LearningEventType.SUBMISSION_PASSED,
                metadata={"solution_revealed": True},
            ),
        )
        independent = apply_event(base, _event(LearningEventType.SUBMISSION_PASSED))
        assert independent.mastery_score > revealed.mastery_score
        # Still registers evidence, but must not reach strong from a reveal.
        assert revealed.mastery_score < 0.75

    def test_single_pass_cannot_jump_to_strong(self):
        base = _state(mastery=0.0, evidence=0, confidence=0.0)
        new_state = apply_event(base, _event(LearningEventType.SUBMISSION_PASSED))
        assert new_state.mastery_score < 0.75

    def test_failure_decreases_mastery(self):
        base = _state(mastery=0.7, errors=0)
        new_state = apply_event(base, _event(LearningEventType.SUBMISSION_FAILED))
        assert new_state.mastery_score < base.mastery_score
        assert new_state.recent_error_count == 1

    def test_single_failure_does_not_destroy_strong_skill(self):
        base = _state(mastery=0.9, evidence=8, confidence=0.8)
        new_state = apply_event(base, _event(LearningEventType.SUBMISSION_FAILED))
        assert new_state.mastery_score >= 0.75

    def test_repeated_error_penalises_more(self):
        base = _state(mastery=0.7)
        repeated = apply_event(
            base,
            _event(
                LearningEventType.SUBMISSION_FAILED, metadata={"repeated_error": True}
            ),
        )
        single = apply_event(base, _event(LearningEventType.SUBMISSION_FAILED))
        assert repeated.mastery_score < single.mastery_score

    def test_event_delta_capped(self):
        base = _state(mastery=0.5, evidence=0)
        new_state = apply_event(base, _event(LearningEventType.SUBMISSION_PASSED))
        assert abs(new_state.mastery_score - base.mastery_score) <= (
            MAX_MASTERY_DELTA_PER_EVENT + 1e-9
        )

    def test_confidence_accumulates_and_saturates(self):
        base = _state(mastery=0.5, confidence=0.0, evidence=0)
        for _ in range(20):
            base = apply_event(base, _event(LearningEventType.SUBMISSION_PASSED))
        assert base.confidence <= 0.9

    def test_review_passed_reduces_error_count_and_increases_mastery(self):
        base = _state(mastery=0.3, errors=3)
        new_state = apply_event(
            base, _event(LearningEventType.REVIEW_COMPLETED, metadata={"passed": True})
        )
        assert new_state.recent_error_count == 2
        assert new_state.mastery_score > base.mastery_score
        assert new_state.last_reviewed_at is not None

    def test_review_failed_keeps_error_pressure(self):
        base = _state(mastery=0.3, errors=2)
        new_state = apply_event(
            base, _event(LearningEventType.REVIEW_COMPLETED, metadata={"passed": False})
        )
        assert new_state.recent_error_count == 1
        assert new_state.mastery_score < base.mastery_score

    def test_hint_requested_lowers_mastery_slightly(self):
        base = _state(mastery=0.5)
        new_state = apply_event(base, _event(LearningEventType.HINT_REQUESTED))
        assert new_state.mastery_score <= base.mastery_score

    def test_lesson_completed_small_gain(self):
        base = _state(mastery=0.5)
        new_state = apply_event(base, _event(LearningEventType.LESSON_COMPLETED))
        assert new_state.mastery_score > base.mastery_score

    def test_trend_improving_after_pass(self):
        base = _state()
        new_state = apply_event(base, _event(LearningEventType.SUBMISSION_PASSED))
        assert new_state.trend == Trend.IMPROVING

    def test_trend_declining_after_fail(self):
        base = _state()
        new_state = apply_event(base, _event(LearningEventType.SUBMISSION_FAILED))
        assert new_state.trend == Trend.DECLINING

    def test_lucky_guesser_never_reaches_strong(self):
        base = _state(mastery=0.0, evidence=0, confidence=0.0)
        for _ in range(2):
            base = apply_event(base, _event(LearningEventType.SUBMISSION_PASSED))
            base = apply_event(base, _event(LearningEventType.SUBMISSION_FAILED))
        assert base.status != SkillStatus.STRONG


class TestDecay:
    def test_no_decay_within_grace_period(self):
        base = _state(mastery=0.7)
        new_state = decay_state(base, base.last_seen_at + timedelta(days=5))
        assert new_state.mastery_score == base.mastery_score

    def test_decay_after_grace_period(self):
        base = _state(mastery=0.7, confidence=0.6)
        new_state = decay_state(base, base.last_seen_at + timedelta(days=30))
        assert new_state.mastery_score < base.mastery_score
        assert new_state.confidence < base.confidence

    def test_decay_bounded_at_zero(self):
        base = _state(mastery=0.1)
        new_state = decay_state(base, base.last_seen_at + timedelta(days=400))
        assert new_state.mastery_score >= 0.0

    def test_decay_same_sequence_is_reproducible(self):
        base = _state(mastery=0.7)
        a = decay_state(base, base.last_seen_at + timedelta(days=20))
        b = decay_state(base, base.last_seen_at + timedelta(days=20))
        assert a.mastery_score == b.mastery_score

    def test_decay_handles_naive_datetime(self):
        """Naive datetimes must not crash decay (legacy row formats)."""
        from datetime import datetime as dt

        base = _state(mastery=0.7)
        naive_state = base.model_copy(update={"last_seen_at": dt(2026, 7, 1, 9, 0, 0)})
        aware_now = dt(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)
        decayed = decay_state(naive_state, aware_now)
        assert decayed.mastery_score < naive_state.mastery_score


class TestShouldBeReviewed:
    def test_strong_never_reviewed(self):
        assert not should_be_reviewed(_state(mastery=0.9), _now())

    def test_new_never_reviewed(self):
        assert not should_be_reviewed(_state(mastery=0.0), _now())

    def test_three_errors_triggers_review(self):
        assert should_be_reviewed(_state(mastery=0.5, errors=3), _now())

    def test_long_inactivity_triggers_review(self):
        base = _state(mastery=0.5)
        assert should_be_reviewed(base, base.last_seen_at + timedelta(days=30))

    def test_recent_developing_not_reviewed(self):
        assert not should_be_reviewed(_state(mastery=0.5, errors=0), _now())


class TestRecommend:
    def _skill_names(self):
        return {
            "arrays": "Arrays",
            "hash-maps": "Hash Maps",
            "two-pointers": "Two Pointers",
            "sliding-window": "Sliding Window",
            "sorting": "Sorting",
        }

    def _prereqs(self):
        return {
            "hash-maps": ["arrays"],
            "two-pointers": ["arrays"],
            "sliding-window": ["two-pointers", "hash-maps"],
            "sorting": ["arrays"],
        }

    def _questions(self):
        return {"hash-maps": ["test-two-sum"], "arrays": ["test-max-subarray"]}

    def test_missing_prerequisite_blocks_dependent(self):
        states = {"arrays": _state(mastery=0.3, slug="arrays")}
        result = recommend(
            states, self._skill_names(), self._prereqs(), self._questions(), _now()
        )
        slugs = [r.skill_slug for r in result]
        # sliding-window's prereqs not strong -> arrays/two-pointers/hash-maps recommended
        assert "sliding-window" not in [r for r in slugs if r == "sliding-window"]
        assert any(r.skill_slug == "arrays" for r in result)

    def test_weak_prerequisite_recommended_first(self):
        states = {"arrays": _state(mastery=0.3, slug="arrays")}
        result = recommend(
            states, self._skill_names(), self._prereqs(), self._questions(), _now()
        )
        top = result[0]
        assert top.skill_slug == "arrays"
        assert top.reason == RecommendationReason.MISSING_PREREQUISITE

    def test_review_ranks_above_weak(self):
        states = {
            "arrays": _state(mastery=0.9, slug="arrays", evidence=5),
            "hash-maps": _state(mastery=0.4, slug="hash-maps", errors=3),
            "two-pointers": _state(mastery=0.5, slug="two-pointers", errors=0),
        }
        result = recommend(
            states, self._skill_names(), self._prereqs(), self._questions(), _now()
        )
        assert result[0].reason == RecommendationReason.DUE_FOR_REVIEW

    def test_empty_history_recommends_new_skill(self):
        result = recommend(
            {}, self._skill_names(), self._prereqs(), self._questions(), _now()
        )
        assert result
        assert result[0].reason == RecommendationReason.NEW_SKILL

    def test_every_recommendation_has_reason_text(self):
        states = {"arrays": _state(mastery=0.3, slug="arrays")}
        result = recommend(
            states, self._skill_names(), self._prereqs(), self._questions(), _now()
        )
        assert all(r.reason_text for r in result)

    def test_limit_respected(self):
        result = recommend(
            {}, self._skill_names(), self._prereqs(), self._questions(), _now(), limit=2
        )
        assert len(result) == 2

    def test_deduplicates_skills(self):
        states = {}
        result = recommend(
            states,
            self._skill_names(),
            self._prereqs(),
            self._questions(),
            _now(),
            limit=20,
        )
        slugs = [r.skill_slug for r in result]
        assert len(slugs) == len(set(slugs))
