"""Pydantic schemas for persisted code submissions (attempt history)."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SubmissionStatus(str, Enum):
    SENT = "sent"
    SUBMITTED = "submitted"
    GRADED = "graded"
    FAILED = "failed"


class CoachingInteractionStatus(str, Enum):
    SENT = "sent"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class ExecutionJobStatus(str, Enum):
    SENT = "sent"
    SUBMITTED = "submitted"
    EXECUTED = "executed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


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
    status: str = SubmissionStatus.GRADED.value
    idempotency_key: Optional[str] = None
    execution_job_id: Optional[str] = None
    request_id: Optional[str] = None
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
