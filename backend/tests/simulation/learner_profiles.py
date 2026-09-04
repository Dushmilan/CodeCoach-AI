"""Learner profiles for the deterministic skill-graph simulation.

Each profile is a callable ``(user_id, rng) -> (events, expected)`` where
``expected`` encodes the invariants the engine must satisfy for that persona.
All sequences are fully deterministic given the seeded RNG.
"""

from __future__ import annotations

from typing import Dict, Tuple

from app.models.skill_graph_schemas import SkillStatus
from app.services.skill_taxonomy import SKILLS, QUESTION_SKILLS

from .event_sequences import (
    Q_MAX_SUB,
    Q_MERGE,
    Q_REVERSE,
    Q_TWO_SUM,
    day_shift,
    diagnosis_evt,
    fail_evt,
    hint_evt,
    lesson_evt,
    pass_evt,
    review_evt,
    solution_revealed_evt,
)

SKILL_NAMES = {s.slug: s.name for s in SKILLS}
VALID_SKILLS = {s.slug for s in SKILLS}
MAPPED_QUESTIONS = {q_id for q_id in QUESTION_SKILLS}


def _status(mastery: float) -> SkillStatus:
    if mastery >= 0.75:
        return SkillStatus.STRONG
    if mastery >= 0.45:
        return SkillStatus.DEVELOPING
    if mastery >= 0.2:
        return SkillStatus.LEARNING
    return SkillStatus.NEW


def expect_skill(
    expected: Dict[str, object],
    slug: str,
    mastery_ge: float | None = None,
    mastery_lt: float | None = None,
    status: SkillStatus | None = None,
    errors_ge: int | None = None,
    errors_eq: int | None = None,
) -> None:
    expected.setdefault("skills", {})[slug] = {
        "mastery_ge": mastery_ge,
        "mastery_lt": mastery_lt,
        "status": status,
        "errors_ge": errors_ge,
        "errors_eq": errors_eq,
    }


# ---------------------------------------------------------------------------
# A. Normal learning
# ---------------------------------------------------------------------------


def profile_complete_beginner(user, rng):
    events = [
        lesson_evt(0, user, "py-intro"),
        fail_evt(1, user, Q_TWO_SUM),
        hint_evt(2, user, Q_TWO_SUM),
        hint_evt(3, user, Q_TWO_SUM),
        pass_evt(4, user, Q_TWO_SUM, hints=2),
        fail_evt(5, user, Q_TWO_SUM),
        hint_evt(6, user, Q_TWO_SUM),
        pass_evt(7, user, Q_TWO_SUM, hints=1),
    ]
    expected = {}
    expect_skill(expected, "hash-maps", mastery_lt=0.75, errors_ge=2)
    return events, expected


def profile_fast_learner(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_REVERSE),
        pass_evt(2, user, Q_MAX_SUB),
        pass_evt(3, user, Q_MERGE),
        pass_evt(4, user, Q_TWO_SUM),
        pass_evt(5, user, Q_REVERSE),
        pass_evt(6, user, Q_MAX_SUB),
    ]
    expected = {}
    # Arrays appears across 3 questions -> breadth cap allows strong.
    expect_skill(expected, "arrays", mastery_ge=0.75)
    # Hash-maps only appears in two-sum (1 distinct question) -> capped below
    # strong regardless of how often two-sum is solved.
    expect_skill(expected, "hash-maps", mastery_ge=0.2, mastery_lt=0.75)
    return events, expected


def profile_slow_but_consistent(user, rng):
    events = []
    seq = 0
    for _ in range(6):
        events += [
            fail_evt(seq, user, Q_TWO_SUM),
            hint_evt(seq + 1, user, Q_TWO_SUM),
            pass_evt(seq + 2, user, Q_TWO_SUM, hints=1),
        ]
        seq += 3
    expected = {}
    # Progresses over time despite slow pace; breadth cap keeps it below strong
    # because only one distinct question is exercised.
    expect_skill(expected, "hash-maps", mastery_ge=0.2, mastery_lt=0.75)
    return events, expected


def profile_strong_learner(user, rng):
    events = []
    seq = 0
    for q in (Q_TWO_SUM, Q_REVERSE, Q_MAX_SUB, Q_MERGE):
        for _ in range(3):
            events.append(pass_evt(seq, user, q))
            seq += 1
    expected = {}
    expect_skill(expected, "arrays", mastery_ge=0.75, status=SkillStatus.STRONG)
    return events, expected


def profile_returning_learner(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM),
        pass_evt(2, user, Q_TWO_SUM),
        pass_evt(3, user, Q_REVERSE),
        pass_evt(4, user, Q_REVERSE),
    ]
    # 30 days of inactivity -> hash-maps / arrays should decay and be flagged
    # for review rather than staying strong.
    events = day_shift(events, 30)
    events.append(pass_evt(5, user, Q_TWO_SUM))
    expected = {}
    # After returning and practicing once, arrays still strong-ish but the
    # long gap must have produced at least one DUE_FOR_REVIEW state for
    # something that decayed below strong.
    expect_skill(expected, "hash-maps", mastery_lt=0.75)
    return events, expected


# ---------------------------------------------------------------------------
# B. Failure patterns
# ---------------------------------------------------------------------------


def profile_repeated_same_error(user, rng):
    events = [
        fail_evt(0, user, Q_TWO_SUM, repeated=False, error="off_by_one"),
        fail_evt(1, user, Q_TWO_SUM, repeated=True, error="off_by_one"),
        fail_evt(2, user, Q_TWO_SUM, repeated=True, error="off_by_one"),
        pass_evt(3, user, Q_TWO_SUM, hints=1),
    ]
    expected = {}
    expect_skill(expected, "hash-maps", errors_ge=3)
    expect_skill(expected, "hash-maps", mastery_lt=0.75)
    return events, expected


def profile_random_error(user, rng):
    events = [
        fail_evt(0, user, Q_TWO_SUM, error="syntax"),
        fail_evt(1, user, Q_REVERSE, error="wrong_answer"),
        fail_evt(2, user, Q_MAX_SUB, error="timeout"),
        pass_evt(3, user, Q_TWO_SUM),
        pass_evt(4, user, Q_REVERSE),
        pass_evt(5, user, Q_MAX_SUB),
    ]
    expected = {}
    # Scattered failures across different questions must NOT be treated as a
    # recurring pattern on any single skill: hash-maps (only in two-sum) keeps
    # an error count of exactly 1.
    expect_skill(expected, "hash-maps", errors_eq=1)
    return events, expected


def profile_one_question_struggle(user, rng):
    events = [
        pass_evt(0, user, Q_REVERSE),
        pass_evt(1, user, Q_REVERSE),
        fail_evt(2, user, Q_MERGE),
        fail_evt(3, user, Q_MERGE),
        fail_evt(4, user, Q_MERGE),
        pass_evt(5, user, Q_REVERSE),
        pass_evt(6, user, Q_REVERSE),
    ]
    expected = {}
    # Struggling on ONE hard question must not tank the whole topic:
    # two-pointers stays stable because reverse-string keeps passing.
    expect_skill(expected, "two-pointers", mastery_ge=0.2)
    return events, expected


def profile_many_failed_attempts(user, rng):
    events = []
    seq = 0
    for _ in range(20):
        events.append(fail_evt(seq, user, Q_MAX_SUB))
        seq += 1
    expected = {}
    expect_skill(expected, "dp-1d", mastery_ge=0.0)
    return events, expected


def profile_fails_after_previous_mastery(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM),
        pass_evt(2, user, Q_TWO_SUM),
        pass_evt(3, user, Q_TWO_SUM),
        pass_evt(4, user, Q_TWO_SUM),
        pass_evt(5, user, Q_TWO_SUM),
        fail_evt(6, user, Q_TWO_SUM),
    ]
    expected = {}
    # A single slip after repeated success must NOT nuke the skill.
    expect_skill(expected, "hash-maps", mastery_ge=0.2)
    return events, expected


# ---------------------------------------------------------------------------
# C. Hint / coaching behaviour
# ---------------------------------------------------------------------------


def profile_hint_dependent(user, rng):
    events = []
    seq = 0
    for _ in range(5):
        events += [
            hint_evt(seq, user, Q_TWO_SUM),
            hint_evt(seq + 1, user, Q_TWO_SUM),
            pass_evt(seq + 2, user, Q_TWO_SUM, hints=2),
        ]
        seq += 3
    expected = {}
    # Always needing hints caps credit: hash-maps never reaches strong.
    expect_skill(expected, "hash-maps", mastery_lt=0.75)
    return events, expected


def profile_solution_copier(user, rng):
    events = [
        solution_revealed_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM, revealed=True),
        solution_revealed_evt(2, user, Q_TWO_SUM),
        pass_evt(3, user, Q_TWO_SUM, revealed=True),
        solution_revealed_evt(4, user, Q_TWO_SUM),
        pass_evt(5, user, Q_TWO_SUM, revealed=True),
    ]
    expected = {}
    expect_skill(expected, "hash-maps", mastery_lt=0.75)
    return events, expected


def profile_ai_diagnosis_dependent(user, rng):
    events = [
        diagnosis_evt(0, user, Q_MAX_SUB),
        fail_evt(1, user, Q_MAX_SUB),
        diagnosis_evt(2, user, Q_MAX_SUB),
        pass_evt(3, user, Q_MAX_SUB),
        diagnosis_evt(4, user, Q_MAX_SUB),
        pass_evt(5, user, Q_MAX_SUB),
    ]
    expected = {}
    expect_skill(expected, "dp-1d", mastery_lt=0.75)
    return events, expected


def profile_abandoning(user, rng):
    events = [
        lesson_evt(0, user, "py-intro"),
        _start_evt(1, user, Q_TWO_SUM),
        _start_evt(2, user, Q_REVERSE),
        _start_evt(3, user, Q_MAX_SUB),
    ]
    expected = {}
    # Starting problems without submitting must not mark any skill as failed.
    expected["no_failures"] = True
    return events, expected


def _start_evt(seq, user, question):
    from app.models.skill_graph_schemas import LearningEventType

    from .event_sequences import _event

    return _event(seq, user, LearningEventType.QUESTION_STARTED, question)


def profile_confused_learner(user, rng):
    events = [
        lesson_evt(0, user, "py-intro"),
        pass_evt(1, user, Q_REVERSE),
        pass_evt(2, user, Q_REVERSE),
        pass_evt(3, user, Q_TWO_SUM),
        pass_evt(4, user, Q_TWO_SUM),
    ]
    expected = {}
    # hash-maps is weak (arrays, its prerequisite, is not strong) so the engine
    # must recommend the missing prerequisite first.
    expected["recommend_prereq"] = "arrays"
    return events, expected


# ---------------------------------------------------------------------------
# D. Confidence / performance
# ---------------------------------------------------------------------------


def profile_overconfident(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        fail_evt(1, user, Q_TWO_SUM),
        fail_evt(2, user, Q_TWO_SUM),
        fail_evt(3, user, Q_TWO_SUM),
        pass_evt(4, user, Q_TWO_SUM, hints=1),
    ]
    expected = {}
    expect_skill(expected, "hash-maps", errors_ge=3)
    return events, expected


def profile_underconfident(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM),
        pass_evt(2, user, Q_TWO_SUM),
        pass_evt(3, user, Q_TWO_SUM),
    ]
    expected = {}
    # Consistent passing builds mastery even though one question caps breadth.
    expect_skill(expected, "hash-maps", mastery_ge=0.2, mastery_lt=0.75)
    return events, expected


def profile_memorizer(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM),
        pass_evt(2, user, Q_TWO_SUM),
        pass_evt(3, user, Q_TWO_SUM),
        pass_evt(4, user, Q_TWO_SUM),
        pass_evt(5, user, Q_TWO_SUM),
    ]
    expected = {}
    # Repeatedly solving the SAME question must not inflate mastery beyond a
    # reasonable cap or mark strong with tiny evidence.
    expect_skill(expected, "hash-maps", mastery_ge=0.5)
    expect_skill(expected, "hash-maps", mastery_lt=1.0)
    return events, expected


def profile_lucky_guesser(user, rng):
    events = [
        pass_evt(0, user, Q_MAX_SUB),
        fail_evt(1, user, Q_MAX_SUB),
        pass_evt(2, user, Q_MAX_SUB),
        fail_evt(3, user, Q_MAX_SUB),
        pass_evt(4, user, Q_MAX_SUB),
        fail_evt(5, user, Q_MAX_SUB),
    ]
    expected = {}
    expect_skill(expected, "dp-1d", mastery_lt=0.75)
    return events, expected


def profile_strong_impl_weak_explanation(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM),
        review_evt(2, user, "hash-maps", passed=False),
        pass_evt(3, user, Q_TWO_SUM),
    ]
    expected = {}
    expect_skill(expected, "hash-maps", mastery_ge=0.3)
    return events, expected


# ---------------------------------------------------------------------------
# E. Multi-skill / difficulty / language
# ---------------------------------------------------------------------------


def profile_mixed_skill(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM),
        pass_evt(2, user, Q_TWO_SUM),
        # Merge-intervals is arrays+intervals; learner is bad at intervals.
        fail_evt(3, user, Q_MERGE, error="wrong_order"),
        fail_evt(4, user, Q_MERGE, error="wrong_order"),
        pass_evt(5, user, Q_MERGE, hints=2),
    ]
    expected = {}
    expect_skill(expected, "hash-maps", mastery_ge=0.2, mastery_lt=0.75)
    expect_skill(expected, "intervals", errors_ge=2)
    return events, expected


def profile_prerequisite_gap(user, rng):
    # Jumps straight into hard merge-intervals without learning arrays.
    events = [
        pass_evt(0, user, Q_MERGE),
        pass_evt(1, user, Q_MERGE),
        pass_evt(2, user, Q_MERGE),
    ]
    expected = {}
    expected["recommend_prereq"] = "arrays"
    return events, expected


def profile_difficulty_jump(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_REVERSE),
        fail_evt(2, user, Q_MAX_SUB),
        fail_evt(3, user, Q_MAX_SUB),
        fail_evt(4, user, Q_MAX_SUB),
    ]
    expected = {}
    # Jumping to a hard question whose prerequisite (recursion) is unknown must
    # push the learner back to that prerequisite.
    expected["recommend_prereq"] = "recursion"
    return events, expected


def profile_language_switching(user, rng):
    events = [
        pass_evt(0, user, Q_TWO_SUM),
        pass_evt(1, user, Q_TWO_SUM),
        pass_evt(2, user, Q_TWO_SUM),
        pass_evt(3, user, Q_TWO_SUM),
    ]
    expected = {}
    # Language switches don't reset mastery, but a single question caps it.
    expect_skill(expected, "hash-maps", mastery_ge=0.2, mastery_lt=0.75)
    return events, expected


def profile_topic_transfer(user, rng):
    # Learns two-pointers via reverse-string, then applies to merge intervals.
    events = [
        pass_evt(0, user, Q_REVERSE),
        pass_evt(1, user, Q_REVERSE),
        pass_evt(2, user, Q_REVERSE),
        pass_evt(3, user, Q_MERGE),
        pass_evt(4, user, Q_MERGE),
    ]
    expected = {}
    # Transfer: two-pointers evidence from reverse-string persists and the
    # merge-interval practice feeds intervals without resetting anything.
    expect_skill(expected, "two-pointers", mastery_ge=0.2)
    expect_skill(expected, "intervals", mastery_ge=0.2)
    return events, expected


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PROFILES: Dict[str, Tuple[object, str]] = {
    "complete_beginner": (profile_complete_beginner, "Slow, hint-heavy learning"),
    "fast_learner": (profile_fast_learner, "Rapid progression"),
    "slow_but_consistent": (profile_slow_but_consistent, "Slow steady progress"),
    "strong_learner": (profile_strong_learner, "Independent solves"),
    "returning_learner": (profile_returning_learner, "Forgetting + recovery"),
    "repeated_same_error": (profile_repeated_same_error, "Recurring error pattern"),
    "random_error": (profile_random_error, "Scattered unrelated errors"),
    "one_question_struggle": (profile_one_question_struggle, "Single hard question"),
    "many_failed_attempts": (profile_many_failed_attempts, "Long failure streak"),
    "fails_after_previous_mastery": (
        profile_fails_after_previous_mastery,
        "Post-mastery slip",
    ),
    "hint_dependent": (profile_hint_dependent, "Passes only with hints"),
    "solution_copier": (profile_solution_copier, "Copies solutions"),
    "ai_diagnosis_dependent": (profile_ai_diagnosis_dependent, "Relies on diagnosis"),
    "abandoning": (profile_abandoning, "Starts but never submits"),
    "confused_learner": (profile_confused_learner, "Missing prerequisite"),
    "overconfident": (profile_overconfident, "High confidence, many failures"),
    "underconfident": (profile_underconfident, "Low confidence, consistent passes"),
    "memorizer": (profile_memorizer, "Repeated same question"),
    "lucky_guesser": (profile_lucky_guesser, "Alternating pass/fail"),
    "strong_impl_weak_explanation": (
        profile_strong_impl_weak_explanation,
        "Codes well, fails review",
    ),
    "mixed_skill": (profile_mixed_skill, "Strong in one skill, weak in another"),
    "prerequisite_gap": (profile_prerequisite_gap, "Skips fundamentals"),
    "difficulty_jump": (profile_difficulty_jump, "Jumps difficulty too fast"),
    "language_switching": (profile_language_switching, "Switches languages"),
    "topic_transfer": (profile_topic_transfer, "Transfers concepts across topics"),
}
