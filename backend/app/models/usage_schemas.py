"""Pydantic schemas for LLM usage metering."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DailyUsage(BaseModel):
    """Per-user, per-day token totals (input + output + request count)."""

    user_id: str
    usage_date: date
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0


class RateLimitEventOut(BaseModel):
    """A recorded denial or abuse flag."""

    id: str
    user_id: Optional[str] = None
    ip: str
    reason: str
    endpoint: str
    created_at: datetime


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


class RateLimitBreakdownRow(BaseModel):
    """One group of rate-limit events by reason (or IP/user)."""

    key: str
    count: int


class RateLimitAnalytics(BaseModel):
    """Admin analytics payload for denial / abuse events."""

    since_hours: int
    total_events: int
    recent_events: list[RateLimitEventOut]
    by_reason: list[RateLimitBreakdownRow]
    by_ip: list[RateLimitBreakdownRow]
    by_endpoint: list[RateLimitBreakdownRow]


class AbuseFlagOut(BaseModel):
    """One detected abuse signal."""

    rule: str
    key: str
    count: int
    severity: str
    detail: str


class AbuseReportOut(BaseModel):
    """Admin payload for the abuse-detection report."""

    since_hours: int
    total_events: int
    flags: list[AbuseFlagOut]
