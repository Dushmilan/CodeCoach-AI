"""Pydantic schemas for persisted code submissions (attempt history)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Submission(BaseModel):
    """A single persisted code attempt."""

    id: str
    user_id: str
    question_id: str
    code: str
    language: str
    passed: bool
    error_signature: Optional[str] = None
    attempt_index: int = 0
    created_at: datetime


class SubmissionIn(BaseModel):
    """Payload captured from a graded submit request."""

    question_id: str
    code: str
    language: str
    passed: bool
    error_signature: Optional[str] = None


class SubmissionsListResponse(BaseModel):
    submissions: list[Submission]
    total: int
