"""Integration tests for /health/monitoring deep probe."""

import pytest

from app.main import app
from app.api.dependencies import get_redis_cache, get_usage_repo


class _UsageRepo:
    def __init__(self):
        self.events = []

    async def count_rate_limit_events(self, since):
        return 0

    async def recent_rate_limit_events(self, limit=100):
        return []

    async def rate_limit_event_breakdown(self, since, field="reason"):
        return []


@pytest.mark.usefixtures("test_env_vars")
class TestMonitoringEndpoint:
    @pytest.mark.asyncio
    async def test_monitoring_returns_snapshot(self, async_client, test_db):
        from tests.integration.test_daily_request_limits import ActiveFakeRedisCache

        fake = ActiveFakeRedisCache()

        async def override_cache():
            return fake

        app.dependency_overrides[get_redis_cache] = override_cache
        app.dependency_overrides[get_usage_repo] = lambda: _UsageRepo()
        try:
            res = await async_client.get("/health/monitoring")
            assert res.status_code == 200, res.text
            data = res.json()
            assert "healthy" in data
            assert isinstance(data["dependencies"], list)
            assert "abuse" in data
            assert "alert_fired" in data
            assert data["abuse"]["flags"] == 0
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)
            app.dependency_overrides.pop(get_usage_repo, None)

    @pytest.mark.asyncio
    async def test_monitoring_marks_redis_unhealthy_when_disabled(
        self, async_client, test_db
    ):
        class _DisabledRedis:
            _enabled = False

        async def override_cache():
            return _DisabledRedis()

        app.dependency_overrides[get_redis_cache] = override_cache
        app.dependency_overrides[get_usage_repo] = lambda: _UsageRepo()
        try:
            res = await async_client.get("/health/monitoring")
            assert res.status_code == 200
            data = res.json()
            redis = next(d for d in data["dependencies"] if d["name"] == "redis")
            assert redis["ok"] is False
            assert data["healthy"] is False
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)
            app.dependency_overrides.pop(get_usage_repo, None)
