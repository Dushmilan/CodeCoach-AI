"""RescueService - rules engine for the durable rescue re-surface queue.

Product contract (Ideas #4, the "never-alone" rescue contract):
  * every abandoned problem resurfaces tomorrow at 09:00 in the user's
    timezone as a tiny re-entry step;
  * re-abandoning while already queued pushes the next nudge a day further
    out (no daily nagging for the same unresolved problem);
  * solving closes the row; "leave me alone" (dismiss) is honoured forever.

All clock input is explicit (`now=`) so behaviour is deterministic in tests.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Sequence

from app.models.rescue_schemas import RescueItem
from app.ports.rescue_repository import RescueRepository

logger = logging.getLogger(__name__)

# How far a repeat abandonment pushes the next resurface out.
REPEAT_ABANDON_PENALTY = timedelta(days=1)


def next_nine_am_utc(now: datetime, *, tz_offset_minutes: int = 0) -> datetime:
    """Tomorrow 09:00 in the client's fixed-offset timezone, as UTC.

    ``tz_offset_minutes`` follows the JS `Date.getTimezoneOffset()` sign
    convention reversed: positive minutes mean the client is EAST of UTC
    (e.g. 480 == UTC+8), so local = utc + offset.
    """
    local_now = now + timedelta(minutes=tz_offset_minutes)
    local_due = (local_now + timedelta(days=1)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    return local_due - timedelta(minutes=tz_offset_minutes)


class RescueService:
    """Orchestrates abandon / due / complete / dismiss over the queue."""

    def __init__(self, repo: RescueRepository):
        self.repo = repo

    async def abandon(
        self,
        *,
        user_id: str,
        question_id: str,
        now: datetime,
        tz_offset_minutes: int = 0,
    ) -> Optional[RescueItem]:
        """Record an abandonment and schedule the next re-surface.

        Returns None when the user previously dismissed this question -
        dismissals are permanent by contract.
        """
        latest = await self.repo.latest(user_id, question_id)
        if latest is not None and latest.status == "dismissed":
            logger.debug(
                "rescue: question %s dismissed by user %s; not resurfacing",
                question_id,
                user_id,
            )
            return None

        existing = await self.repo.get(user_id, question_id)
        if existing is not None:
            pushed_due = max(
                existing.due_at + REPEAT_ABANDON_PENALTY,
                next_nine_am_utc(now, tz_offset_minutes=tz_offset_minutes),
            )
            return await self.repo.reschedule(
                user_id=user_id, question_id=question_id, due_at=pushed_due, now=now
            )

        return await self.repo.create_abandoned(
            user_id=user_id,
            question_id=question_id,
            due_at=next_nine_am_utc(now, tz_offset_minutes=tz_offset_minutes),
            now=now,
        )

    async def due(
        self, *, user_id: str, now: datetime, limit: int = 50
    ) -> Sequence[RescueItem]:
        """Open rows whose re-surface time has come, oldest first."""
        return await self.repo.list_due(user_id=user_id, now=now, limit=limit)

    async def open_item(
        self, *, user_id: str, question_id: str
    ) -> Optional[RescueItem]:
        """The currently open row for (user, question), if any.

        Used by the API layer to answer a lost concurrent-abandon race
        idempotently instead of surfacing a unique-violation error.
        """
        return await self.repo.get(user_id=user_id, question_id=question_id)

    async def complete(
        self, *, user_id: str, question_id: str, now: datetime
    ) -> Optional[RescueItem]:
        """Close the open row because the user solved the problem."""
        return await self.repo.close(
            user_id=user_id, question_id=question_id, status="completed", now=now
        )

    async def dismiss(
        self, *, user_id: str, question_id: str, now: datetime
    ) -> Optional[RescueItem]:
        """Honour "never show me this problem's nudges again"."""
        return await self.repo.close(
            user_id=user_id, question_id=question_id, status="dismissed", now=now
        )
