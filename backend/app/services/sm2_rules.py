"""Deterministic SM-2 scheduler for mistake-memory review cards.

Pure functions only — no I/O. Implements the classic SuperMemo-2 algorithm:
successive successful recalls grow the inter-review interval multiplicatively
by an ease factor that adapts to grade quality; any failure resets the card
to a short relearn step and counts a lapse. All clock input is explicit
(``now=``) so behaviour is deterministic and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

# --- Tunables ---------------------------------------------------------------
INITIAL_EASE = 2.5
MIN_EASE = 1.3
FIRST_INTERVAL_DAYS = 1
SECOND_INTERVAL_DAYS = 6
RELEARN_INTERVAL_DAYS = 1
FAILURE_EASE_PENALTY = 0.2
SUCCESS_QUALITY_THRESHOLD = 3

# SM-2 easiness deltas: EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
_EASE_DELTA_TABLE = {
    quality: 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02) for quality in range(6)
}


@dataclass(frozen=True)
class CardMemory:
    """The schedulable memory state of a review card."""

    ease: float
    interval_days: int
    repetitions: int
    lapses: int


@dataclass(frozen=True)
class ReviewOutcome:
    """The next memory state after applying a graded review."""

    ease: float
    interval_days: int
    repetitions: int
    lapses: int
    due_at: datetime


def new_card_memory() -> CardMemory:
    """Fresh card state (SM-2 initial conditions)."""
    return CardMemory(ease=INITIAL_EASE, interval_days=0, repetitions=0, lapses=0)


def is_success(quality: int) -> bool:
    """SM-2 treats grades >= 3 as a successful recall."""
    return quality >= SUCCESS_QUALITY_THRESHOLD


def _clamp_ease(ease: float) -> float:
    return max(MIN_EASE, ease)


def _next_ease(card: CardMemory, quality: int) -> float:
    if is_success(quality):
        return _clamp_ease(card.ease + _EASE_DELTA_TABLE[quality])
    return _clamp_ease(card.ease - FAILURE_EASE_PENALTY)


def _next_interval(card: CardMemory, ease: float, quality: int) -> int:
    if not is_success(quality):
        return RELEARN_INTERVAL_DAYS
    repetitions = card.repetitions + 1
    if repetitions == 1:
        return FIRST_INTERVAL_DAYS
    if repetitions == 2:
        return SECOND_INTERVAL_DAYS
    return max(1, round(card.interval_days * ease))


def review(card: CardMemory, quality: int, now: datetime) -> ReviewOutcome:
    """Apply one graded recall and return the next memory state.

    Raises ``ValueError`` when ``quality`` is outside 0..5.
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"quality must be within 0..5, got {quality}")

    ease = _next_ease(card, quality)
    interval_days = _next_interval(card, ease, quality)
    repetitions = card.repetitions + 1 if is_success(quality) else 0
    lapses = card.lapses + (0 if is_success(quality) else 1)

    return ReviewOutcome(
        ease=ease,
        interval_days=interval_days,
        repetitions=repetitions,
        lapses=lapses,
        due_at=now + timedelta(days=interval_days),
    )
