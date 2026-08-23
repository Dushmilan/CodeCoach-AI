"""Pydantic schemas for the durable rescue re-surface queue (Ideas #4)."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

RescueStatus = Literal["abandoned", "completed", "dismissed"]


class RescueItem(BaseModel):
    """One row of the durable re-surface queue.

    A row is "open" while ``status == "abandoned"``; whether it is *due*
    right now is derived (``due_at <= now``), so no scheduler job is needed.
    """

    id: str
    user_id: str
    question_id: str
    status: RescueStatus = "abandoned"
    first_abandoned_at: datetime
    due_at: datetime
    resurface_count: int = 0
    last_intervention_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RescueListResponse(BaseModel):
    items: list[RescueItem]
    total: int


class RescueActionResponse(BaseModel):
    """Uniform answer for abandon/complete/dismiss.

    ``item=None`` is a normal outcome (nothing was open, or the question was
    previously dismissed) - never an error.
    """

    item: Optional[RescueItem]


class RescueAbandonRequest(BaseModel):
    """Optional client context when recording an abandonment."""

    # Client UTC offset in minutes, east-positive (UTC+8 -> 480); this is
    # -1 * JS Date.getTimezoneOffset(). Used to schedule the next resurface
    # at 09:00 in the user's own morning.
    tz_offset_minutes: int = Field(default=0, ge=-840, le=840)
