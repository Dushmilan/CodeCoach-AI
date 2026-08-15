"""SubmissionRepository — port for persisting graded code attempts."""

from abc import ABC, abstractmethod
from typing import Sequence

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

    @abstractmethod
    async def count_attempts(self, user_id: str, question_id: str) -> int:
        """Return how many attempts the user has made on a question."""
