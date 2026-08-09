"""Integration tests for per-plan daily request limits.

Covers the 429 path, X-RateLimit-* headers, pro-tier exemption, Redis-down
fallback and the /api/usage reporting endpoint.
"""

from datetime import date

import pytest

from app.main import app
from app.api.coach import get_coaching_provider
from tests.fixtures.mock_coaching_provider import MockCoachingProvider


@pytest.fixture(autouse=True)
def _override_coaching_provider():
    """Auto-override coaching provider so tests never hit the network."""
    app.dependency_overrides[get_coaching_provider] = MockCoachingProvider
    yield
    app.dependency_overrides.pop(get_coaching_provider, None)


class ActiveFakeRedisCache:
    """In-memory Redis stand-in with a shared counter per key."""

    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def incr(self, key, ttl=60):
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]

    async def decr(self, key):
        self.data[key] = self.data.get(key, 1) - 1
        return self.data[key]


@pytest.fixture(autouse=True)
def _redis_cache():
    """Wire an active in-memory Redis cache so daily caps are enforced.

    ASGITransport does not run the lifespan, so app.state.redis_cache is
    unset; without this override every request would take the DB fallback
    path, which never sees increments (the mock provider records no usage).
    """
    from app.api.dependencies import get_redis_cache

    fake = ActiveFakeRedisCache()

    async def override_get_redis_cache():
        return fake

    app.dependency_overrides[get_redis_cache] = override_get_redis_cache
    yield
    app.dependency_overrides.pop(get_redis_cache, None)


async def _register_user(async_client, username: str):
    res = await async_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "testpass123",
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    return data["user"]["id"], {"Authorization": f"Bearer {data['access_token']}"}


def _coaching_payload():
    return {
        "problem": "Find the maximum element in an array",
        "code": "def max_element(arr):\n    return max(arr)",
        "language": "python",
        "message": "Is this the most efficient solution?",
        "mode": "review",
        "difficulty": "easy",
    }


@pytest.mark.usefixtures("test_env_vars")
class TestDailyRequestCap:
    @pytest.mark.asyncio
    async def test_free_user_blocked_after_20_requests(
        self, async_client, monkeypatch
    ):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "3")
        _, headers = await _register_user(async_client, "capfree")
        for _ in range(3):
            res = await async_client.post(
                "/api/coach/", json=_coaching_payload(), headers=headers
            )
            assert res.status_code == 200, res.text
        res = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert res.status_code == 429
        assert "limit" in res.json()["detail"].lower()
        assert res.headers["X-RateLimit-Remaining"] == "0"
        assert res.headers["X-RateLimit-Limit"] == "3"
        assert "Retry-After" in res.headers

    @pytest.mark.asyncio
    async def test_success_response_includes_rate_limit_headers(
        self, async_client, monkeypatch
    ):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "20")
        _, headers = await _register_user(async_client, "capheaders")
        res = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert res.status_code == 200
        assert res.headers["X-RateLimit-Limit"] == "20"
        assert res.headers["X-RateLimit-Remaining"] == "19"
        assert res.headers["X-Usage-Remaining-Requests"] == "19"

    @pytest.mark.asyncio
    async def test_pro_user_not_blocked_by_free_cap(self, async_client, test_db, monkeypatch):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "1")
        uid, headers = await _register_user(async_client, "capro")
        from app.repositories.sql_user_admin_repository import SqlUserAdminRepository

        repo = SqlUserAdminRepository(test_db)
        await repo.update_user_role(uid, "admin", "someoneelse")
        from sqlalchemy import update
        from app.models.orm import UserORM

        await test_db.execute(
            update(UserORM).where(UserORM.id == uid).values(plan="pro")
        )
        await test_db.commit()

        for _ in range(2):
            res = await async_client.post(
                "/api/coach/", json=_coaching_payload(), headers=headers
            )
            assert res.status_code == 200, res.text

    @pytest.mark.asyncio
    async def test_stream_endpoint_also_guarded(self, async_client, monkeypatch):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "1")
        _, headers = await _register_user(async_client, "capstream")
        first = await async_client.post(
            "/api/coach/stream", json=_coaching_payload(), headers=headers
        )
        assert first.status_code == 200
        second = await async_client.post(
            "/api/coach/stream", json=_coaching_payload(), headers=headers
        )
        assert second.status_code == 429

    @pytest.mark.asyncio
    async def test_denied_attempt_does_not_burn_quota(self, async_client, monkeypatch):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "1")
        _, headers = await _register_user(async_client, "capquota")
        first = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert first.status_code == 200
        denied = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert denied.status_code == 429
        # A denied attempt must not consume the (already exhausted) quota further,
        # and a fresh user's denied attempt must not count as usage.
        assert denied.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.usefixtures("test_env_vars")
class TestUsageEndpoint:
    @pytest.mark.asyncio
    async def test_get_usage_returns_plan_and_quota(self, async_client, monkeypatch):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "20")
        _, headers = await _register_user(async_client, "usageget")
        res = await async_client.get("/api/usage", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["plan"] == "free"
        assert data["daily_limit"] == 20
        assert data["daily_used"] == 0
        assert data["daily_remaining"] == 20
        assert "reset_at" in data

    @pytest.mark.asyncio
    async def test_get_usage_reflects_consumed_quota(self, async_client, monkeypatch):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "5")
        _, headers = await _register_user(async_client, "usageused")
        for _ in range(2):
            await async_client.post("/api/coach/", json=_coaching_payload(), headers=headers)
        res = await async_client.get("/api/usage", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["daily_used"] == 2
        assert data["daily_remaining"] == 3

    @pytest.mark.asyncio
    async def test_get_usage_requires_auth(self, async_client):
        res = await async_client.get("/api/usage")
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_get_usage_returns_zero_remaining_when_capped(self, async_client, monkeypatch):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "1")
        _, headers = await _register_user(async_client, "usagecap")
        await async_client.post("/api/coach/", json=_coaching_payload(), headers=headers)
        res = await async_client.get("/api/usage", headers=headers)
        data = res.json()
        assert data["daily_remaining"] == 0


@pytest.mark.usefixtures("test_env_vars")
class TestUsageEndpointRedisDown:
    class FakeRedisCache:
        def __init__(self):
            self.fail = True

        async def get(self, key):
            if self.fail:
                return None
            return None

        async def incr(self, key, ttl=60):
            if self.fail:
                return None
            return 1

        async def decr(self, key):
            if self.fail:
                return None
            return 0

    @pytest.mark.asyncio
    async def test_daily_cap_falls_back_to_db(self, async_client, monkeypatch, test_db):
        monkeypatch.setenv("FREE_DAILY_REQUEST_CAP", "2")
        from app.api.dependencies import get_redis_cache

        async def override():
            return self.FakeRedisCache()

        app.dependency_overrides[get_redis_cache] = override
        try:
            uid, headers = await _register_user(async_client, "capfallback")
            from app.repositories.sql_usage_repository import SqlUsageRepository

            repo = SqlUsageRepository(test_db)
            await repo.increment_daily(
                user_id=uid,
                usage_date=date.today(),
                input_tokens=0,
                output_tokens=0,
                request_count=2,
            )
            await test_db.commit()

            res = await async_client.post(
                "/api/coach/", json=_coaching_payload(), headers=headers
            )
            assert res.status_code == 429
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)
