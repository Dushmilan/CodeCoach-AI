"""ReviewService - orchestration for mistake-memory spaced repetition.

Product contract (Ideas #1):
  * failing a question with a stable error signature opens/refreshes an
    ``active`` card keyed by (user, question, signature);
  * passing the question promotes that question's active cards into the
    SM-2 rotation with a first review tomorrow;
  * re-failing a scheduled bug flips it back to ``active`` and counts a lapse;
  * grading a due card applies the pure SM-2 rules.

All clock input is explicit (`now=`) so behaviour is deterministic in tests.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Sequence

from app.models.mistake_schemas import ReviewCard
from app.ports.review_repository import ReviewRepository
from app.services.sm2_rules import (
    FIRST_INTERVAL_DAYS,
    INITIAL_EASE,
    CardMemory,
    is_success,
    review as sm2_review,
)

logger = logging.getLogger(__name__)

FIRST_REVIEW_DELAY = timedelta(days=FIRST_INTERVAL_DAYS)


class CardNotFoundError(Exception):
    """Raised when a grade targets a card the user does not own."""


class ReviewService:
    """Owns the observe / due / grade lifecycle over review cards."""

    def __init__(self, repo: ReviewRepository):
        self.repo = repo

    async def observe_submission(
        self,
        *,
        user_id: str,
        question_id: str,
        passed: bool,
        error_signature: str | None,
        now: datetime,
    ) -> None:
        """Fold one graded submit into the card set (best-effort caller)."""
        if not passed:
            if not error_signature:
                logger.debug(
                    "review: failure without a stable signature; no card opened"
                )
                return
            await self._observe_failure(
                user_id=user_id,
                question_id=question_id,
                error_signature=error_signature,
                now=now,
            )
            return
        await self._observe_pass(user_id=user_id, question_id=question_id, now=now)

    async def _observe_failure(
        self, *, user_id: str, question_id: str, error_signature: str, now: datetime
    ) -> None:
        existing = next(
            (
                c
                for c in await self.repo.list_for_question(user_id, question_id)
                if c.error_signature == error_signature
            ),
            None,
        )
        if existing is None:
            card = ReviewCard(
                id=uuid.uuid4().hex,
                user_id=user_id,
                question_id=question_id,
                error_signature=error_signature,
                state="active",
                ease=INITIAL_EASE,
                interval_days=0,
                repetitions=0,
                lapses=0,
                due_at=now,
                last_reviewed_at=None,
                created_at=now,
                updated_at=now,
            )
        else:
            was_scheduled = existing.state == "scheduled"
            card = existing.model_copy(
                update={
                    "state": "active",
                    "repetitions": 0,
                    "interval_days": 0,
                    # A lapse only counts when a conquered bug regressed.
                    "lapses": existing.lapses + (1 if was_scheduled else 0),
                    "due_at": now,
                    "updated_at": now,
                }
            )
        await self.repo.save(card)

    async def _observe_pass(
        self, *, user_id: str, question_id: str, now: datetime
    ) -> None:
        for card in await self.repo.list_for_question(user_id, question_id):
            if card.state != "active":
                continue
            promoted = card.model_copy(
                update={
                    "state": "scheduled",
                    "repetitions": 1,
                    "interval_days": FIRST_INTERVAL_DAYS,
                    "due_at": now + FIRST_REVIEW_DELAY,
                    "last_reviewed_at": now,
                    "updated_at": now,
                }
            )
            await self.repo.save(promoted)

    async def due(
        self, *, user_id: str, now: datetime, limit: int = 20
    ) -> Sequence[ReviewCard]:
        """Scheduled cards whose re-solve time has come, oldest due first."""
        return list(await self.repo.list_due(user_id=user_id, now=now, limit=limit))

    async def grade(
        self, *, user_id: str, card_id: str, quality: int, now: datetime
    ) -> ReviewCard:
        """Apply one graded recall to a card and persist the new schedule."""
        card = await self.repo.get(user_id, card_id)
        if card is None:
            raise CardNotFoundError(f"No review card {card_id!r} for user {user_id!r}")

        memory = CardMemory(
            ease=card.ease,
            interval_days=card.interval_days,
            repetitions=card.repetitions,
            lapses=card.lapses,
        )
        outcome = sm2_review(memory, quality, now)
        graded = card.model_copy(
            update={
                "ease": outcome.ease,
                "interval_days": outcome.interval_days,
                "repetitions": outcome.repetitions,
                "lapses": outcome.lapses,
                "due_at": outcome.due_at,
                "state": "scheduled" if is_success(quality) else "active",
                "last_reviewed_at": now,
                "updated_at": now,
            }
        )
        return await self.repo.save(graded)
