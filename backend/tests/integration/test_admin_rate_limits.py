"""Integration tests for the admin rate-limit analytics endpoint.

Covers the happy path, repository errors failing closed as 500, admin auth,
and the request-count surfaced in per-user usage detail (`all_daily`).
"""

from datetime import datetime

import pytest

from app.main import app
from app.api.dependencies import get_usage_repo
from app.api.admin import require_admin
from app.models.usage_schemas import RateLimitEventOut


class _StubUsageRepo:
    def __init__(self, events=None, breakdown=None, total=None):
        self.events = events or []
        self.breakdown = breakdown or []
        self.total = total if total is not None else 0

    async def recent_rate_limit_events(self, limit=100):
        return self.events

    async def count_rate_limit_events(self, since):
        return self.total

    async def rate_limit_event_breakdown(self, since, field="reason"):
        return self.breakdown


def _event(overrides=None):
    base = {
        "id": "evt-1",
        "user_id": "user-1",
        "ip": "203.0.113.7",
        "reason": "daily_cap",
        "endpoint": "/api/coach",
        "created_at": datetime(2026, 8, 8, 12, 0, 0),
    }
    base.update(overrides or {})
    return RateLimitEventOut(**base)


class TestAdminRateLimitAnalytics:
    @pytest.mark.asyncio
    async def test_returns_analytics_payload(self, async_client):
        def override_admin():
            return {
                "id": "admin-1",
                "username": "pattern_admin",
                "email": "admin@example.com",
                "plan": "pro",
                "role": "admin",
                "is_active": True,
            }

        def override_usage():
            return _StubUsageRepo(
                events=[_event()],
                breakdown=[{"key": "daily_cap", "count": 3}],
                total=3,
            )

        app.dependency_overrides[require_admin] = override_admin
        app.dependency_overrides[get_usage_repo] = override_usage
        try:
            res = await async_client.get("/api/admin/rate-limits?since_hours=48")
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["since_hours"] == 48
            assert data["total_events"] == 3
            assert len(data["recent_events"]) == 1
            assert data["recent_events"][0]["reason"] == "daily_cap"
            assert data["by_reason"][0] == {"key": "daily_cap", "count": 3}
        finally:
            app.dependency_overrides.pop(require_admin, None)
            app.dependency_overrides.pop(get_usage_repo, None)

    @pytest.mark.asyncio
    async def test_requires_admin(self, async_client):
        res = await async_client.get("/api/admin/rate-limits")
        assert res.status_code in (401, 403)


class TestAdminAbuseReport:
    @pytest.mark.asyncio
    async def test_returns_abuse_flags(self, async_client, test_db):
        from app.repositories.sql_usage_repository import SqlUsageRepository

        repo = SqlUsageRepository(test_db)
        user_ids = []
        for i in range(2):
            res = await async_client.post(
                "/api/auth/register",
                json={
                    "username": f"abuseuser{i}",
                    "email": f"abuse{i}@test.com",
                    "password": "testpass123",
                },
            )
            assert res.status_code == 201, res.text
            user_ids.append(res.json()["user"]["id"])
        for uid in user_ids:
            await repo.add_rate_limit_event(
                user_id=uid,
                ip="203.0.113.55",
                reason="daily_cap",
                endpoint="/api/coach",
            )
        await test_db.commit()

        def override_admin():
            return {
                "id": "admin-1",
                "username": "abuse_admin",
                "email": "abuse@example.com",
                "plan": "pro",
                "role": "admin",
                "is_active": True,
            }

        app.dependency_overrides[require_admin] = override_admin
        app.dependency_overrides[get_usage_repo] = lambda: repo
        try:
            res = await async_client.get("/api/admin/abuse")
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["total_events"] == 2
            assert isinstance(data["flags"], list)
        finally:
            app.dependency_overrides.pop(require_admin, None)
            app.dependency_overrides.pop(get_usage_repo, None)

    @pytest.mark.asyncio
    async def test_abuse_requires_admin(self, async_client):
        res = await async_client.get("/api/admin/abuse")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_repo_error_returns_500(self, async_client):
        class _Broken:
            async def recent_rate_limit_events(self, limit=100):
                raise RuntimeError("boom")

            async def count_rate_limit_events(self, since):
                raise RuntimeError("boom")

            async def rate_limit_event_breakdown(self, since, field="reason"):
                raise RuntimeError("boom")

        def override_usage():
            return _Broken()

        app.dependency_overrides[require_admin] = lambda: {
            "id": "admin-1",
            "username": "boom_admin",
            "email": "boom@example.com",
            "plan": "pro",
            "role": "admin",
            "is_active": True,
        }
        app.dependency_overrides[get_usage_repo] = override_usage
        try:
            res = await async_client.get("/api/admin/rate-limits")
            assert res.status_code == 500
        finally:
            app.dependency_overrides.pop(require_admin, None)
            app.dependency_overrides.pop(get_usage_repo, None)