"""DailyLimitService — hot-path daily request counting with Redis fallback.

The Redis counter is keyed by user id and UTC date with a TTL that expires at
the next UTC midnight, so each user's daily quota resets automatically. The
counter is incremented before an LLM call (atomic INCR reserves a slot).
Denied attempts are refunded with a DECR so they do not burn quota.

When Redis is unavailable the service degrades to the DB daily counter (read
only; persistence of the increment happens via UsageService after a call).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.ports.usage_repository import UsageRepository
from app.services.redis_service import RedisCache


class DailyLimitService:
    """Enforce per-user daily request caps with an atomic Redis counter."""

    def __init__(self, cache: Optional[RedisCache], repo: UsageRepository):
        self.cache = cache
        self.repo = repo

    @staticmethod
    def ttl_to_midnight(now: datetime) -> int:
        """Seconds until the next UTC midnight boundary (min 1)."""
        midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return max(1, int((midnight - now).total_seconds()))

    @staticmethod
    def _key(user_id: str, day) -> str:
        return RedisCache.key("dl", "user", user_id, day.isoformat())

    async def remaining(
        self,
        user_id: str,
        cap: int,
        now: Optional[datetime] = None,
    ) -> int:
        """Return how many calls the user may still make today (>= 0)."""
        now = now or datetime.now(timezone.utc)
        day = now.date()
        if self.cache is not None:
            value = await self.cache.get(self._key(user_id, day))
            if value is not None:
                return max(0, cap - int(value))
        daily = await self.repo.get_daily(user_id, day)
        used = (daily.request_count if daily else 0) or 0
        return max(0, cap - used)

    async def consume(
        self,
        user_id: str,
        cap: int,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, int]:
        """Reserve one request slot. Returns (allowed, remaining).

        Allowed and denied attempts both reserve a slot, but a denied attempt
        is immediately refunded so it does not consume the daily quota.
        """
        now = now or datetime.now(timezone.utc)
        day = now.date()
        if self.cache is not None:
            key = self._key(user_id, day)
            value = await self.cache.incr(key, self.ttl_to_midnight(now))
            if value is not None:
                if value > cap:
                    await self.cache.decr(key)
                    return False, 0
                return True, cap - value
        daily = await self.repo.get_daily(user_id, day)
        used = (daily.request_count if daily else 0) or 0
        if used >= cap:
            return False, 0
        return True, cap - used - 1