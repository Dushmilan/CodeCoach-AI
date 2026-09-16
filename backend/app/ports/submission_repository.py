"""SubmissionRepository — port for persisting graded code attempts."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence

from app.models.submission_schemas import Submission, SubmissionIn


class SubmissionRepository(ABC):
    """Interface for persisting per-user code attempts (submit history)."""

    @abstractmethod
    async def add(self, *, user_id: str, submission: SubmissionIn) -> Submission:
        """Persist one graded attempt and return it (with attempt_index)."""

    @abstractmethod
    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> Sequence[Submission]:
        """Return the user's most recent submissions, newest first."""

    async def list_by_users(
        self, user_ids: Sequence[str], *, limit: int = 1000
    ) -> dict[str, Sequence[Submission]]:
        """Return recent submissions per user in ONE round trip.

        Keys cover every requested id (unknown users map to ``[]``); each
        value is newest-first and capped at ``limit`` — identical figures to
        calling :meth:`list_by_user` per id. The default loops for fakes;
        the SQL implementation uses a single ROW_NUMBER() window query.
        """
        return {
            user_id: await self.list_by_user(user_id, limit=limit)
            for user_id in user_ids
        }

    @abstractmethod
    async def count_attempts(self, user_id: str, question_id: str) -> int:
        """Return how many attempts the user has made on a question."""

    async def get(self, submission_id: str) -> Optional[Submission]:
        """Return one submission by id, or None (default for fakes)."""
        return None

    async def create_sent(
        self, *, user_id: str, submission: SubmissionIn
    ) -> Submission:
        """Persist one attempt in sent state before grading."""
        return await self.add(user_id=user_id, submission=submission)

    async def mark_graded(
        self,
        submission_id: str,
        *,
        passed: bool,
        error_signature: Optional[str] = None,
    ) -> Submission:
        """Transition sent/submitted -> graded (must be overridden for state)."""
        raise NotImplementedError

    async def mark_failed(self, submission_id: str) -> Submission:
        """Transition sent/submitted -> failed (must be overridden for state)."""
        raise NotImplementedError

    async def list_stale(
        self, *, older_than: datetime, limit: int = 100
    ) -> Sequence[Submission]:
        """Return sent/submitted rows older than the cutoff (default empty)."""
        return []
