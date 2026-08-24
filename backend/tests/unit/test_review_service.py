"""Unit tests for ReviewService — mistake-memory spaced-repetition orchestration.

Card lifecycle (Ideas #1):
  * failing a question with a stable error signature opens/refreshes an
    ``active`` card keyed by (user, question, signature);
  * passing the question promotes that question's active cards into the SM-2
    rotation (state ``scheduled``, first review tomorrow);
  * re-failing a scheduled bug flips it back to ``active`` and counts a lapse;
  * grading a due card applies the pure SM-2 rules.

All clock input is explicit (`now=`) so behaviour is deterministic.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.mistake_schemas import ReviewCard
from app.services.review_service import CardNotFoundError, ReviewService

NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
USER = "user-1"
Q1 = "q-1"
SIG = "expected True, got False"


def _card(
    *,
    question_id: str = Q1,
    signature: str = SIG,
    state: str = "scheduled",
    ease: float = 2.5,
    interval_days: int = 1,
    repetitions: int = 1,
    lapses: int = 0,
    due_at: datetime | None = None,
) -> ReviewCard:
    return ReviewCard(
        id=f"card-{question_id}-{abs(hash(signature)) % 1000}",
        user_id=USER,
        question_id=question_id,
        error_signature=signature,
        state=state,
        ease=ease,
        interval_days=interval_days,
        repetitions=repetitions,
        lapses=lapses,
        due_at=due_at or NOW,
        last_reviewed_at=None,
        created_at=NOW - timedelta(days=2),
        updated_at=NOW - timedelta(days=2),
    )


class InMemoryReviewRepo:
    """Fake mirroring SqlReviewRepository semantics."""

    def __init__(self):
        self.rows: list[ReviewCard] = []

    @staticmethod
    def _matches(row: ReviewCard, user_id: str, question_id: str, signature: str):
        return (
            row.user_id == user_id
            and row.question_id == question_id
            and row.error_signature == signature
        )

    async def get(self, user_id: str, card_id: str) -> ReviewCard | None:
        for row in self.rows:
            if row.user_id == user_id and row.id == card_id:
                return row.model_copy()
        return None

    async def list_for_question(
        self, user_id: str, question_id: str
    ) -> list[ReviewCard]:
        return [
            r.model_copy()
            for r in self.rows
            if r.user_id == user_id and r.question_id == question_id
        ]

    async def list_due(
        self, *, user_id: str, now: datetime, limit: int = 20
    ) -> list[ReviewCard]:
        due = [
            r
            for r in self.rows
            if r.user_id == user_id and r.state == "scheduled" and r.due_at <= now
        ]
        due.sort(key=lambda r: r.due_at)
        return due[:limit]

    async def save(self, card: ReviewCard) -> ReviewCard:
        for i, row in enumerate(self.rows):
            if self._matches(row, card.user_id, card.question_id, card.error_signature):
                self.rows[i] = card.model_copy()
                return card.model_copy()
        stored = card.model_copy()
        if not any(r.id == card.id for r in self.rows):
            self.rows.append(stored)
        return stored.model_copy()


@pytest.fixture()
def service():
    return ReviewService(repo=InMemoryReviewRepo())


@pytest.fixture()
def repo(service):
    return service.repo


class TestObserveFailure:
    async def test_failure_without_signature_persists_nothing(self, service, repo):
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=False, error_signature=None, now=NOW
        )
        assert repo.rows == []

    async def test_first_failure_opens_active_card(self, service, repo):
        await service.observe_submission(
            user_id=USER,
            question_id=Q1,
            passed=False,
            error_signature=SIG,
            now=NOW,
        )

        assert len(repo.rows) == 1
        card = repo.rows[0]
        assert card.user_id == USER
        assert card.question_id == Q1
        assert card.error_signature == SIG
        assert card.state == "active"
        assert card.repetitions == 0
        assert card.interval_days == 0
        assert card.lapses == 0
        assert card.ease == 2.5
        assert card.due_at == NOW

    async def test_repeat_failure_keeps_single_card_active(self, service, repo):
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=False, error_signature=SIG, now=NOW
        )
        later = NOW + timedelta(hours=1)
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=False, error_signature=SIG, now=later
        )

        assert len(repo.rows) == 1
        assert repo.rows[0].due_at == later

    async def test_refailing_scheduled_bug_flips_back_and_counts_lapse(
        self, service, repo
    ):
        repo.rows.append(_card(state="scheduled", lapses=0))
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=False, error_signature=SIG, now=NOW
        )

        card = repo.rows[0]
        assert card.state == "active"
        assert card.lapses == 1
        assert card.repetitions == 0
        assert card.interval_days == 0
        assert card.due_at == NOW


class TestObservePass:
    async def test_pass_promotes_active_cards_into_rotation(self, service, repo):
        repo.rows.append(_card(state="active", repetitions=0, interval_days=0))
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=True, error_signature=None, now=NOW
        )

        card = repo.rows[0]
        assert card.state == "scheduled"
        assert card.repetitions == 1
        assert card.interval_days == 1
        assert card.due_at == NOW + timedelta(days=1)
        assert card.last_reviewed_at == NOW

    async def test_pass_leaves_scheduled_cards_untouched(self, service, repo):
        original = _card(
            state="scheduled",
            due_at=NOW + timedelta(days=6),
            interval_days=6,
            repetitions=2,
        )
        repo.rows.append(original)
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=True, error_signature=None, now=NOW
        )

        card = repo.rows[0]
        assert card.state == "scheduled"
        assert card.interval_days == 6
        assert card.repetitions == 2
        assert card.due_at == NOW + timedelta(days=6)

    async def test_pass_only_touches_that_questions_cards(self, service, repo):
        other = _card(question_id="q-other", state="active")
        repo.rows.append(other)
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=True, error_signature=None, now=NOW
        )
        assert repo.rows[0].state == "active"

    async def test_pass_without_cards_is_a_noop(self, service, repo):
        await service.observe_submission(
            user_id=USER, question_id=Q1, passed=True, error_signature=None, now=NOW
        )
        assert repo.rows == []


class TestDue:
    async def test_due_delegates_to_repo_ordered_by_due_date(self, service):
        # Both are past-due; "early" simply became due first.
        late = _card(signature="late", due_at=NOW - timedelta(minutes=1))
        early = _card(signature="early", due_at=NOW - timedelta(minutes=5))
        service.repo.rows.extend([late, early])

        cards = await service.due(user_id=USER, now=NOW)
        assert [c.error_signature for c in cards] == ["early", "late"]


class TestGrade:
    async def test_grade_applies_sm2_and_saves(self, service, repo):
        repo.rows.append(
            _card(state="scheduled", ease=2.5, interval_days=1, repetitions=1)
        )
        card_id = repo.rows[0].id

        graded = await service.grade(user_id=USER, card_id=card_id, quality=4, now=NOW)

        assert graded.repetitions == 2
        assert graded.interval_days == 6
        assert graded.state == "scheduled"
        assert graded.last_reviewed_at == NOW
        assert repo.rows[0].interval_days == 6

    async def test_failed_grade_returns_card_to_active(self, service, repo):
        repo.rows.append(_card(state="scheduled"))
        graded = await service.grade(
            user_id=USER, card_id=repo.rows[0].id, quality=2, now=NOW
        )
        assert graded.state == "active"
        assert graded.lapses == 1

    async def test_unknown_or_foreign_card_raises_not_found(self, service):
        with pytest.raises(CardNotFoundError):
            await service.grade(user_id=USER, card_id="missing", quality=4, now=NOW)

    async def test_cannot_grade_another_users_card(self, service, repo):
        repo.rows.append(_card())
        with pytest.raises(CardNotFoundError):
            await service.grade(
                user_id="someone-else", card_id=repo.rows[0].id, quality=4, now=NOW
            )
