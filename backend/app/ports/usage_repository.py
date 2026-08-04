"""UsageRepository — port for LLM token usage persistence."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional, Sequence

from app.models.usage_schemas import DailyUsage, UsageEventOut, UserUsageTotals


class UsageRepository(ABC):
    """Interface for persisting metered LLM usage (events + daily counters)."""

    @abstractmethod
    async def add_event(
        self,
        *,
        user_id: str,
        provider: str,
        model: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Append one usage event (one metered LLM call)."""
        ...

    @abstractmethod
    async def increment_daily(
        self,
        *,
        user_id: str,
        usage_date: date,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Accumulate tokens into the per-user daily counter (upsert)."""
        ...

    @abstractmethod
    async def get_daily(self, user_id: str, usage_date: date) -> Optional[DailyUsage]:
        """Return the daily counter for a user on a date, or None."""
        ...

    @abstractmethod
    async def recent_events(
        self, user_id: str, limit: int = 50
    ) -> Sequence[UsageEventOut]:
        """Return the most recent usage events for a user."""
        ...

    @abstractmethod
    async def user_totals(self, user_id: str, since: datetime) -> DailyUsage:
        """Aggregate token totals for a user since `since`."""
        ...

    @abstractmethod
    async def all_user_totals(
        self, since: datetime, limit: int = 100
    ) -> Sequence[UserUsageTotals]:
        """Aggregate token totals grouped per user since `since`."""
        ...

    @abstractmethod
    async def all_daily(
        self, user_id: str, since: date, limit: int = 30
    ) -> Sequence[DailyUsage]:
        """Return daily counters for a user since `since` (newest first)."""
        ...
