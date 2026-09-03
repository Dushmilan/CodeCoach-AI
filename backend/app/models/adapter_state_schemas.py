"""Pydantic schemas for adapter state persistence (coaching + execution)."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CoachingInteraction(BaseModel):
    """One durable coaching intent with explicit state."""

    id: str
    user_id: str
    question_id: Optional[str] = None
    lesson_id: Optional[str] = None
    mode: str
    language: str
    problem_hash: str
    code_hash: str
    idempotency_key: str
    status: str = "sent"
    request_payload: dict[str, Any] = {}
    response_payload: Optional[dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    retry_count: int = 0
    request_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class ExecutionJob(BaseModel):
    """One durable execution intent with explicit state."""

    id: str
    user_id: str
    question_id: Optional[str] = None
    language: str
    code_hash: str
    idempotency_key: str
    status: str = "sent"
    request_payload: dict[str, Any] = {}
    response_payload: Optional[dict[str, Any]] = None
    test_results: Optional[list[dict[str, Any]]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    retry_count: int = 0
    request_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class CoachingInteractionListResponse(BaseModel):
    interactions: list[CoachingInteraction]
    total: int


class ExecutionJobListResponse(BaseModel):
    jobs: list[ExecutionJob]
    total: int
