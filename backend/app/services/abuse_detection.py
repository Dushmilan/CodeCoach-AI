"""Abuse detection for rate-limit events.

Consumes the recorded denial/abuse events (groupings from UsageRepository)
and flags suspicious patterns:

- multi-account farming: the same IP recorded several distinct user accounts
- denial burst: a single IP producing many rate-limit events in the window
- repeat offender: a single user hitting limits many times

Detection is intentionally heuristic and fails open: it never blocks traffic
itself (enforcement already happens upstream). It only *reports* so operators
can react.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Sequence

from app.core.config import get_settings
from app.models.usage_schemas import RateLimitEventOut


@dataclass
class AbuseFlag:
    """One detected abuse signal."""

    rule: str
    key: str
    count: int
    severity: str
    detail: str


@dataclass
class AbuseReport:
    """Aggregate of abuse flags for a window."""

    since: datetime
    total_events: int
    flags: list[AbuseFlag] = field(default_factory=list)

    @property
    def has_flags(self) -> bool:
        return len(self.flags) > 0


def _is_external(ip: str) -> bool:
    """Treat loopback / private-range IPs (and unknown) as non-external."""
    if not ip or ip in ("127.0.0.1", "::1", "unknown", "localhost"):
        return False
    if ip.startswith("10."):
        return False
    return True


def _aware(dt: datetime) -> datetime:
    """Return a timezone-aware datetime (MySQL rows come back naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AbuseDetectionService:
    def __init__(
        self,
        *,
        total_events_getter: Callable[[datetime], int],
        breakdown_by_ip: Callable[[datetime], Sequence],
        breakdown_by_user: Callable[[datetime], Sequence],
        recent_events: Callable[[int], Sequence[RateLimitEventOut]],
        threshold_burst: int | None = None,
        threshold_repeat: int | None = None,
        threshold_multi_account: int | None = None,
    ):
        self._total = total_events_getter
        self._by_ip = breakdown_by_ip
        self._by_user = breakdown_by_user
        self._recent = recent_events
        settings = get_settings()
        self.burst_min = threshold_burst or settings.ABUSE_BURST_MIN_EVENTS
        self.repeat_min = threshold_repeat or settings.ABUSE_REPEAT_MIN_EVENTS
        self.multi_account_min = (
            threshold_multi_account or settings.ABUSE_MULTI_ACCOUNT_MIN_ACCOUNTS
        )

    async def analyze(self, since: datetime) -> AbuseReport:
        """Return abuse flags observed since `since`."""
        total = await self._total(since)
        flags: list[AbuseFlag] = []

        events = await self._recent(500)

        windowed = [e for e in events if _aware(e.created_at) >= since]

        # Multi-account farming: a single external IP backing several accounts.
        ip_to_users: dict[str, set] = defaultdict(set)
        for evt in windowed:
            if evt.user_id and _is_external(evt.ip):
                ip_to_users[evt.ip].add(evt.user_id)
        for ip, users in ip_to_users.items():
            if len(users) >= self.multi_account_min:
                flags.append(
                    AbuseFlag(
                        rule="multi_account",
                        key=ip,
                        count=len(users),
                        severity="high",
                        detail=f"IP {ip} served {len(users)} distinct accounts",
                    )
                )

        by_ip = {row.key: row.count for row in await self._by_ip(since)}
        for ip, count in by_ip.items():
            if _is_external(ip) and count >= self.burst_min:
                flags.append(
                    AbuseFlag(
                        rule="burst_denials",
                        key=ip,
                        count=count,
                        severity="warning",
                        detail=f"{count} denials from {ip} in window",
                    )
                )

        by_user = {row.key: row.count for row in await self._by_user(since)}
        for uid, count in by_user.items():
            if uid and count >= self.repeat_min:
                flags.append(
                    AbuseFlag(
                        rule="repeat_offender",
                        key=uid,
                        count=count,
                        severity="warning",
                        detail=f"{count} denials for user {uid} in window",
                    )
                )

        # De-dup: a single (rule,key) may appear via both guards.
        seen = set()
        unique: list[AbuseFlag] = []
        for flag in flags:
            tag = (flag.rule, flag.key)
            if tag in seen:
                continue
            seen.add(tag)
            unique.append(flag)

        unique.sort(key=lambda f: f.count, reverse=True)
        return AbuseReport(since=since, total_events=total, flags=unique)
