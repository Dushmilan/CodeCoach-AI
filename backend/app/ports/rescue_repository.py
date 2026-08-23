"""RescueRepository - port for the durable rescue re-surface queue."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence

from app.models.rescue_schemas import RescueItem, RescueStatus


class RescueRepository(ABC):
    """Interface for persisting abandoned problems that must resurface.

    Invariants owned by storage:
      * exactly ONE open row (``status='abandoned'``) per (user, question),
        enforced by a partial unique index;
      * closed rows (completed/dismissed) never surface as due again.
    """

    @abstractmethod
    async def create_abandoned(
        self, *, user_id: str, question_id: str, due_at: datetime, now: datetime
    ) -> RescueItem:
        """Create the open row for an abandonment (raises if one exists)."""

    @abstractmethod
    async def get(self, user_id: str, question_id: str) -> Optional[RescueItem]:
        """Return the OPEN row for (user, question), if any."""

    @abstractmethod
    async def latest(self, user_id: str, question_id: str) -> Optional[RescueItem]:
        """Return the most recent row for (user, question), any status.

        The service uses this to honour dismissals forever (a dismissed
        question must never be re-opened by a later abandonment).
        """

    @abstractmethod
    async def reschedule(
        self, *, user_id: str, question_id: str, due_at: datetime, now: datetime
    ) -> Optional[RescueItem]:
        """Push an open row's due date out and bump resurface_count."""

    @abstractmethod
    async def close(
        self,
        *,
        user_id: str,
        question_id: str,
        status: RescueStatus,
        now: datetime,
    ) -> Optional[RescueItem]:
        """Transition the open row to completed/dismissed (None if absent)."""

    @abstractmethod
    async def list_due(
        self, *, user_id: str, now: datetime, limit: int = 50
    ) -> Sequence[RescueItem]:
        """Open rows whose time has come, oldest due_at first."""
