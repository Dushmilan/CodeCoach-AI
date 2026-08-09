"""Unit tests for MonitoringService and AlertService."""

import pytest

from app.services.abuse_detection import AbuseFlag, AbuseReport
from app.services.monitoring import AlertService, MonitoringService, severity_value


class _FakeDB:
    async def execute(self, *args, **kwargs):
        return None


class _FakeRedis:
    _enabled = True

    async def get(self, key):
        return None


class _FakeRedisDisabled:
    _enabled = False


def _report(flags=None, total=0):
    return AbuseReport(
        since=None,
        total_events=total,
        flags=flags or [],
    )


def _flag(severity="high", rule="multi_account", key="203.0.113.7"):
    return AbuseFlag(
        rule=rule,
        key=key,
        count=5,
        severity=severity,
        detail=f"{rule} at {key}",
    )


def test_severity_value():
    assert severity_value("high") == 2
    assert severity_value("warning") == 1
    assert severity_value("none") == 0
    assert severity_value("bogus") == 0


@pytest.mark.asyncio
async def test_render_healthy_without_abuse():
    svc = MonitoringService(_FakeRedis())
    report = await svc.render(db_session=_FakeDB())
    assert report.healthy is True
    assert {d.name for d in report.dependencies} == {"redis", "database"}
    assert report.abuse_flag_count == 0


@pytest.mark.asyncio
async def test_render_unhealthy_when_db_missing():
    svc = MonitoringService(_FakeRedis())
    report = await svc.render(db_session=None)
    assert report.healthy is False


@pytest.mark.asyncio
async def test_render_unhealthy_when_redis_disabled():
    svc = MonitoringService(_FakeRedisDisabled())
    report = await svc.render(db_session=_FakeDB())
    assert not any(d.ok for d in report.dependencies if d.name == "redis")
    assert report.healthy is False


@pytest.mark.asyncio
async def test_render_unhealthy_on_high_abuse():
    svc = MonitoringService(_FakeRedis())
    report = await svc.render(
        db_session=_FakeDB(), abuse_report=_report([_flag("high")])
    )
    assert report.abuse_flag_count == 1
    assert report.abuse_severity_max == "high"
    assert report.healthy is False


@pytest.mark.asyncio
async def test_render_healthy_on_warning_only():
    from app.services.monitoring import MonitoringService as _MS

    svc = _MS(_FakeRedis())
    report = await svc.render(
        db_session=_FakeDB(),
        abuse_report=_report([_flag("warning")]),
    )
    assert report.healthy is True
    assert report.abuse_severity_max == "warning"


def test_alert_service_noop_without_url(monkeypatch):
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "")
    from app.services.monitoring import AlertService as _AS

    svc = _AS()
    assert svc.configured is False


@pytest.mark.asyncio
async def test_alert_not_sent_without_url():
    svc = AlertService("")
    sent = await svc.alert_abuse(_report([_flag("high")]))
    assert sent is False


@pytest.mark.asyncio
async def test_alert_sent_with_url(monkeypatch):
    import httpx

    class _MockTransport(httpx.AsyncBaseTransport):
        def __init__(self):
            self.posts = []

        async def handle_async_request(self, request):
            self.posts.append((str(request.url), request.content))
            return httpx.Response(200, json={})

    transport = _MockTransport()
    client = httpx.AsyncClient(transport=transport)
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout=5: client)

    svc = AlertService("https://hooks.example.com/alert")
    sent = await svc.alert_abuse(_report([_flag("high")]))
    assert sent is True
    assert len(transport.posts) == 1
    assert "rate_limit_abuse" in transport.posts[0][1].decode()
    await client.aclose()


@pytest.mark.asyncio
async def test_alert_not_sent_without_high_flags(monkeypatch):
    import httpx

    sent = []

    class _Transport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            sent.append(request)
            return httpx.Response(200, json={})

    client = httpx.AsyncClient(transport=_Transport())
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout=5: client)

    svc = AlertService("https://hooks.example.com/alert")
    assert await svc.alert_abuse(_report([_flag("warning")])) is False
    assert sent == []
    await client.aclose()
