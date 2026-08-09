"""Unit tests for AbuseDetectionService heuristics."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.usage_schemas import RateLimitEventOut, RateLimitBreakdownRow
from app.services.abuse_detection import AbuseDetectionService, _is_external

NOW = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)


def _event(ip: str, user_id: str, when: datetime | None = None) -> RateLimitEventOut:
    return RateLimitEventOut(
        id=f"{ip}-{user_id}",
        user_id=user_id,
        ip=ip,
        reason="daily_cap",
        endpoint="/api/coach",
        created_at=when or NOW,
    )


class _Repo:
    def __init__(self, events, by_ip=None, by_user=None, total=None):
        self.events = events
        self.by_ip = by_ip or []
        self.by_user = by_user or []
        self.total = total if total is not None else len(events)

    async def count_rate_limit_events(self, since):
        return self.total

    async def recent_rate_limit_events(self, limit=100):
        return self.events

    async def rate_limit_event_breakdown(self, since, field="reason"):
        if field == "ip":
            return self.by_ip
        if field == "user_id":
            return self.by_user
        return []


def make_service(repo, **kwargs):
    return AbuseDetectionService(
        total_events_getter=repo.count_rate_limit_events,
        breakdown_by_ip=lambda s: repo.rate_limit_event_breakdown(s, "ip"),
        breakdown_by_user=lambda s: repo.rate_limit_event_breakdown(s, "user_id"),
        recent_events=repo.recent_rate_limit_events,
        **kwargs,
    )


def test_is_external():
    assert _is_external("203.0.113.7")
    assert _is_external("8.8.8.8")
    assert not _is_external("127.0.0.1")
    assert not _is_external("10.1.2.3")
    assert not _is_external("unknown")


@pytest.mark.asyncio
async def test_no_events_no_flags():
    repo = _Repo([])
    report = await make_service(repo).analyze(NOW - timedelta(hours=24))
    assert report.total_events == 0
    assert not report.has_flags


@pytest.mark.asyncio
async def test_multi_account_farming_detected():
    events = [
        _event("203.0.113.7", "user-a"),
        _event("203.0.113.7", "user-b"),
        _event("203.0.113.7", "user-c"),
    ]
    repo = _Repo(events, by_ip=[RateLimitBreakdownRow(key="203.0.113.7", count=3)])
    report = await make_service(repo, threshold_multi_account=3).analyze(
        NOW - timedelta(hours=24)
    )
    flags = {f.rule for f in report.flags}
    assert "multi_account" in flags


@pytest.mark.asyncio
async def test_burst_denials_detected():
    events = [_event("203.0.113.9", "same-user") for _ in range(25)]
    repo = _Repo(events, by_ip=[RateLimitBreakdownRow(key="203.0.113.9", count=25)])
    report = await make_service(repo, threshold_burst=20).analyze(
        NOW - timedelta(hours=24)
    )
    flags = {f.rule for f in report.flags}
    assert "burst_denials" in flags
    assert "multi_account" not in flags  # single account, not farming


@pytest.mark.asyncio
async def test_repeat_offender_detected():
    events = [_event("203.0.113.7", "lone-user") for _ in range(12)]
    repo = _Repo(
        events,
        by_user=[RateLimitBreakdownRow(key="lone-user", count=12)],
    )
    report = await make_service(repo, threshold_repeat=10).analyze(
        NOW - timedelta(hours=24)
    )
    rules = {f.rule for f in report.flags}
    assert "repeat_offender" in rules


@pytest.mark.asyncio
async def test_loopback_ip_not_flagged():
    events = [_event("127.0.0.1", f"localhost-user-{i}") for i in range(50)]
    repo = _Repo(events, by_ip=[RateLimitBreakdownRow(key="127.0.0.1", count=50)])
    report = await make_service(repo, threshold_burst=20).analyze(
        NOW - timedelta(hours=24)
    )
    assert not report.has_flags


@pytest.mark.asyncio
async def test_old_events_excluded_from_window():
    old_event = _event("203.0.113.7", "user-a", when=NOW - timedelta(days=30))
    repo = _Repo([old_event])
    report = await make_service(repo, threshold_multi_account=1).analyze(
        NOW - timedelta(hours=24)
    )
    assert not report.has_flags
