"""Unit tests for the SM-2 spaced-repetition scheduler (mistake-memory #1).

Pure-function contract: ``review`` maps a card's memory state + a recall
quality grade to the next memory state and due date. All clock input is
explicit so behaviour is deterministic.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.sm2_rules import (
    FIRST_INTERVAL_DAYS,
    MIN_EASE,
    SECOND_INTERVAL_DAYS,
    CardMemory,
    is_success,
    new_card_memory,
    review,
)

NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)


class TestIsSuccess:
    def test_quality_three_and_above_is_success(self):
        assert is_success(3) is True
        assert is_success(5) is True

    def test_quality_below_three_is_failure(self):
        assert is_success(2) is False
        assert is_success(0) is False


class TestNewCardMemory:
    def test_defaults_match_sm2_initial_state(self):
        card = new_card_memory()
        assert card.ease == 2.5
        assert card.interval_days == 0
        assert card.repetitions == 0
        assert card.lapses == 0


class TestSuccessfulReviews:
    def test_first_success_schedules_one_day_out(self):
        outcome = review(new_card_memory(), quality=5, now=NOW)

        assert outcome.repetitions == 1
        assert outcome.interval_days == FIRST_INTERVAL_DAYS == 1
        assert outcome.due_at == NOW + timedelta(days=1)
        assert outcome.lapses == 0

    def test_second_success_schedules_six_days_out(self):
        card = CardMemory(ease=2.5, interval_days=1, repetitions=1, lapses=0)
        outcome = review(card, quality=4, now=NOW)

        assert outcome.repetitions == 2
        assert outcome.interval_days == SECOND_INTERVAL_DAYS == 6
        assert outcome.due_at == NOW + timedelta(days=6)

    def test_third_success_grows_interval_by_ease(self):
        card = CardMemory(ease=2.5, interval_days=6, repetitions=2, lapses=0)
        outcome = review(card, quality=4, now=NOW)

        # interval = round(previous_interval * ease) = round(6 * 2.5)
        assert outcome.repetitions == 3
        assert outcome.interval_days == 15
        assert outcome.due_at == NOW + timedelta(days=15)

    def test_quality_five_improves_ease(self):
        outcome = review(new_card_memory(), quality=5, now=NOW)
        assert outcome.ease == pytest.approx(2.6)

    def test_quality_three_penalises_ease(self):
        outcome = review(new_card_memory(), quality=3, now=NOW)
        # ease += 0.1 - 2 * (0.08 + 2 * 0.02) = -0.14
        assert outcome.ease == pytest.approx(2.36)


class TestFailedReviews:
    def test_failure_resets_to_relearn_and_counts_lapse(self):
        card = CardMemory(ease=2.5, interval_days=15, repetitions=3, lapses=0)
        outcome = review(card, quality=1, now=NOW)

        assert outcome.repetitions == 0
        assert outcome.interval_days == 1  # relearn step
        assert outcome.lapses == 1
        assert outcome.due_at == NOW + timedelta(days=1)

    def test_failure_penalises_ease(self):
        outcome = review(new_card_memory(), quality=2, now=NOW)
        assert outcome.ease == pytest.approx(2.3)

    def test_ease_never_drops_below_floor(self):
        card = CardMemory(ease=MIN_EASE, interval_days=15, repetitions=3, lapses=2)
        outcome = review(card, quality=0, now=NOW)
        assert outcome.ease == MIN_EASE


class TestValidation:
    @pytest.mark.parametrize("quality", [-1, 6])
    def test_out_of_range_quality_raises(self, quality: int):
        with pytest.raises(ValueError):
            review(new_card_memory(), quality=quality, now=NOW)
