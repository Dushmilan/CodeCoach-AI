"""Pydantic schemas for mistake-memory phase 2 (Ideas #1).

Two surfaces live here:
  * ``ReviewCard`` / grading payloads — spaced-repetition cards over the
    user's own past bugs (SM-2 rotation);
  * ``ErrorSignatureNode`` / graph payloads — the per-user error graph
    derived from attempt history.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ReviewCard(BaseModel):
    """A spaced-repetition card over one recurring bug.

    Lifecycle: ``active`` means the bug is open (not yet solved since its
    last occurrence); ``scheduled`` means the bug was conquered once and is
    now in the SM-2 review rotation.
    """

    id: str
    user_id: str
    question_id: str
    error_signature: str
    state: Literal["active", "scheduled"]
    ease: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    lapses: int = 0
    due_at: datetime
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class GradeIn(BaseModel):
    """Self-assessed recall grade for a review (SM-2 quality 0..5)."""

    quality: int = Field(ge=0, le=5)


class GradeResponse(BaseModel):
    card: ReviewCard


class DueReviewsResponse(BaseModel):
    cards: List[ReviewCard]
    total: int


class ErrorSignatureNode(BaseModel):
    """One recurring error signature in the user's mistake graph."""

    signature: str
    occurrences: int
    questions: List[str]
    first_seen_at: datetime
    last_seen_at: datetime
    resolved: bool


class ErrorGraphResponse(BaseModel):
    signatures: List[ErrorSignatureNode]
    total_signatures: int
