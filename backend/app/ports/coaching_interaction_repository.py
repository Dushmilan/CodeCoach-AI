"""CoachingInteractionRepository — port for durable coaching intents."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Sequence

from app.models.adapter_state_schemas import CoachingInteraction


class CoachingInteractionRepository(ABC):
    """Interface for persisting coaching adapter state (sent -> terminal)."""

    @abstractmethod
    async def create_sent(
        self,
        *,
        user_id: str,
        question_id: Optional[str],
        mode: str,
        language: str,
        problem_hash: str,
        code_hash: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
        lesson_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CoachingInteraction:
        """Persist one coaching intent in sent state and return it."""

    @abstractmethod
    async def get(self, interaction_id: str) -> Optional[CoachingInteraction]:
        """Return one interaction by id, or None."""

    @abstractmethod
    async def get_by_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Optional[CoachingInteraction]:
        """Return the existing row for an idempotency key, or None."""

    @abstractmethod
    async def mark_completed(
        self,
        interaction_id: str,
        *,
        response_payload: Optional[dict[str, Any]] = None,
    ) -> CoachingInteraction:
        """Transition sent/submitted -> completed."""

    @abstractmethod
    async def mark_failed(
        self,
        interaction_id: str,
        *,
        status: str = "failed",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> CoachingInteraction:
        """Transition sent/submitted -> failed/timeout/rate_limited."""

    @abstractmethod
    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> Sequence[CoachingInteraction]:
        """Return the user's most recent interactions, newest first."""

    @abstractmethod
    async def list_stale(
        self, *, older_than: datetime, limit: int = 100
    ) -> Sequence[CoachingInteraction]:
        """Return sent/submitted rows older than the cutoff, oldest first."""
