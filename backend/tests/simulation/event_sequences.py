"""Deterministic event-sequence builders for the learner simulation.

Every sequence is driven by a seeded ``random.Random`` so runs are
reproducible; a failing simulation can always be re-run with the same seed.
Sequences return ``(events, expected)`` where ``expected`` is a dict of
assertions the caller must hold after ingesting the events.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Tuple

from app.models.skill_graph_schemas import (
    LearningEvent,
    LearningEventType,
)

# Question IDs known to the seeded bank + their mapped skills.
Q_TWO_SUM = "test-two-sum"  # arrays 0.4, hash-maps 0.6
Q_REVERSE = "test-reverse-string"  # strings 0.5, two-pointers 0.5
Q_MAX_SUB = "test-max-subarray"  # dp 0.7, arrays 0.3
Q_MERGE = "test-merge-intervals"  # arrays 0.6, sorting 0.4

T0 = datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc)


def _event(
    seq: int,
    user: str,
    etype: LearningEventType,
    question: str | None = None,
    meta: Dict[str, object] | None = None,
    lesson: str | None = None,
    skill_slug: str | None = None,
    occurred: datetime | None = None,
) -> LearningEvent:
    return LearningEvent(
        id=f"sim-{user}-{seq}-{etype.value}",
        user_id=user,
        event_type=etype,
        question_id=question,
        lesson_id=lesson,
        skill_slug=skill_slug,
        metadata=meta or {},
        occurred_at=occurred or (T0 + timedelta(seconds=seq * 3600)),
    )


def pass_evt(seq, user, question, hints=0, revealed=False):
    return _event(
        seq,
        user,
        LearningEventType.SUBMISSION_PASSED,
        question,
        meta={"hint_count": hints, "solution_revealed": revealed},
    )


def fail_evt(seq, user, question, repeated=False, error="runtime_error"):
    return _event(
        seq,
        user,
        LearningEventType.SUBMISSION_FAILED,
        question,
        meta={"repeated_error": repeated, "error": error},
    )


def hint_evt(seq, user, question):
    return _event(seq, user, LearningEventType.HINT_REQUESTED, question)


def review_evt(seq, user, skill_slug, passed=True):
    return _event(
        seq,
        user,
        LearningEventType.REVIEW_COMPLETED,
        meta={"passed": passed},
        skill_slug=skill_slug,
    )


def lesson_evt(seq, user, lesson):
    return _event(seq, user, LearningEventType.LESSON_COMPLETED, None, lesson=lesson)


def solution_revealed_evt(seq, user, question):
    return _event(seq, user, LearningEventType.SOLUTION_REVEALED, question)


def diagnosis_evt(seq, user, question):
    return _event(seq, user, LearningEventType.DIAGNOSIS_CREATED, question)


def day_shift(events: List[LearningEvent], days: float) -> List[LearningEvent]:
    """Shift a sequence forward by N days to simulate inactivity gaps."""
    delta = timedelta(days=days)
    return [e.model_copy(update={"occurred_at": e.occurred_at + delta}) for e in events]


Profile = Callable[[str, random.Random], Tuple[List[LearningEvent], Dict[str, object]]]
