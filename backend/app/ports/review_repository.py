"""ReviewRepository - port for spaced-repetition review cards."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence

from app.models.mistake_schemas import ReviewCard


class ReviewRepository(ABC):
    """Interface for persisting per-user SM-2 review cards.

    Cards are keyed by (user_id, question_id, error_signature); ``save``
    upserts on that natural key.
    """

    @abstractmethod
    async def get(self, user_id: str, card_id: str) -> Optional[ReviewCard]:
        """Return one of the user's cards by id, or None."""

    @abstractmethod
    async def list_for_question(
        self, user_id: str, question_id: str
    ) -> Sequence[ReviewCard]:
        """Return all of the user's cards for one question."""

    @abstractmethod
    async def list_due(
        self, *, user_id: str, now: datetime, limit: int = 20
    ) -> Sequence[ReviewCard]:
        """Return the user's scheduled cards whose due date has passed."""

    @abstractmethod
    async def save(self, card: ReviewCard) -> ReviewCard:
        """Insert or update a card (upsert on the natural key)."""
