"""ExecutionJobRepository — port for durable execution intents."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Sequence

from app.models.adapter_state_schemas import ExecutionJob


class ExecutionJobRepository(ABC):
    """Interface for persisting execution adapter state (sent -> terminal)."""

    @abstractmethod
    async def create_sent(
        self,
        *,
        user_id: str,
        question_id: Optional[str],
        language: str,
        code_hash: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
        request_id: Optional[str] = None,
    ) -> ExecutionJob:
        """Persist one execution intent in sent state and return it."""

    @abstractmethod
    async def get(self, job_id: str) -> Optional[ExecutionJob]:
        """Return one job by id, or None."""

    @abstractmethod
    async def get_by_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Optional[ExecutionJob]:
        """Return the existing row for an idempotency key, or None."""

    @abstractmethod
    async def mark_executed(
        self,
        job_id: str,
        *,
        response_payload: Optional[dict[str, Any]] = None,
        test_results: Optional[list[dict[str, Any]]] = None,
        execution_time_ms: Optional[int] = None,
    ) -> ExecutionJob:
        """Transition sent/submitted -> executed."""

    @abstractmethod
    async def mark_failed(
        self,
        job_id: str,
        *,
        status: str = "failed",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ExecutionJob:
        """Transition sent/submitted -> failed/timeout/cancelled."""

    @abstractmethod
    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> Sequence[ExecutionJob]:
        """Return the user's most recent jobs, newest first."""

    @abstractmethod
    async def list_stale(
        self, *, older_than: datetime, limit: int = 100
    ) -> Sequence[ExecutionJob]:
        """Return sent/submitted rows older than the cutoff, oldest first."""
