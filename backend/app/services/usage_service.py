"""UsageService — token metering + daily cap helpers.

The service is the per-request recorder wired into the coaching provider so
GroqService can meter input/output tokens per user. Cap checking and the
X-Usage-* response headers live here as pure helpers for testability.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

from app.models.usage_schemas import DailyUsage
from app.ports.usage_repository import UsageRepository


class UsageService:
    """Record LLM usage and read per-user daily counters."""

    def __init__(self, repo: UsageRepository):
        self.repo = repo

    async def record(
        self,
        *,
        user_id: str,
        provider: str,
        model: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Persist one metered call (event + daily counter increment)."""
        await self.repo.add_event(
            user_id=user_id,
            provider=provider,
            model=model,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        await self.repo.increment_daily(
            user_id=user_id,
            usage_date=datetime.now(timezone.utc).date(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    async def get_daily_usage(
        self, user_id: str, usage_date: Optional[date] = None
    ) -> DailyUsage:
        """Return today's usage for a user, defaulting to zeros."""
        usage_date = usage_date or datetime.now(timezone.utc).date()
        daily = await self.repo.get_daily(user_id, usage_date)
        if daily is None:
            return DailyUsage(user_id=user_id, usage_date=usage_date)
        return daily


def check_caps(
    daily: DailyUsage, input_cap: int, output_cap: int
) -> Tuple[bool, int, int]:
    """Return (allowed, remaining_input, remaining_output) against daily caps."""
    remaining_in = max(0, input_cap - (daily.input_tokens or 0))
    remaining_out = max(0, output_cap - (daily.output_tokens or 0))
    allowed = remaining_in > 0 and remaining_out > 0
    return allowed, remaining_in, remaining_out


def usage_headers(daily: DailyUsage, input_cap: int, output_cap: int) -> dict:
    """Build X-Usage-* response headers from current daily usage and caps."""
    _, remaining_in, remaining_out = check_caps(daily, input_cap, output_cap)
    now = datetime.now(timezone.utc)
    reset = (
        now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).isoformat()
    return {
        "X-Usage-Input": str(daily.input_tokens or 0),
        "X-Usage-Output": str(daily.output_tokens or 0),
        "X-Usage-Remaining-Input": str(remaining_in),
        "X-Usage-Remaining-Output": str(remaining_out),
        "X-Usage-Reset": reset,
    }
