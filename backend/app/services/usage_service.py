"""UsageService — token metering (recording only, Issue #184).

The service is the per-request recorder wired into the coaching provider so
GroqService can meter input/output tokens per user. Cap enforcement was
removed: abuse protection is the single flat daily request cap in
``app/api/daily_limits.py``.
"""

from datetime import date, datetime, timezone
from typing import Optional

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
