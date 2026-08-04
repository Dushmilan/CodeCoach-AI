"""Pydantic schemas for LLM usage metering."""

from datetime import date, datetime

from pydantic import BaseModel


class DailyUsage(BaseModel):
    """Per-user, per-day token totals (input + output)."""

    user_id: str
    usage_date: date
    input_tokens: int = 0
    output_tokens: int = 0


class UsageEventOut(BaseModel):
    """A single metered LLM call."""

    id: str
    user_id: str
    provider: str
    model: str
    endpoint: str
    input_tokens: int
    output_tokens: int
    created_at: datetime


class UserUsageTotals(BaseModel):
    """Aggregated token totals for a single user over a period."""

    user_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    call_count: int = 0


class UsageSummary(BaseModel):
    """Admin usage dashboard payload."""

    users: list[UserUsageTotals]
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_calls: int = 0


class UserUsageDetail(BaseModel):
    """Admin per-user usage detail."""

    user_id: str
    daily: list[DailyUsage]
    events: list[UsageEventOut]
    total_input_tokens: int = 0
    total_output_tokens: int = 0
