"""Integration tests for coach usage metering, daily caps and per-user rate limiting."""

from datetime import datetime, timezone

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


async def _register_premium_user(async_client, username: str):
    uid, headers = await _register_user(async_client, username)
    await _promote_premium(username)
    return uid, headers


async def _promote_premium(username: str) -> None:
    """Set a registered user's plan to premium directly in the DB."""
    from tests.db_helpers import set_plan

    await set_plan(username, "premium")


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
class TestUsageHeaders:
    @pytest.mark.asyncio
    async def test_coach_response_includes_usage_headers(self, async_client):
        _, headers = await _register_premium_user(async_client, "usagehdr")
        response = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert response.status_code == 200
        assert response.headers["X-Usage-Input"] == "0"
        assert response.headers["X-Usage-Output"] == "0"
        assert response.headers["X-Usage-Remaining-Input"] == "250000"
        assert response.headers["X-Usage-Remaining-Output"] == "125000"
        assert "X-Usage-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_coach_stream_includes_usage_headers(self, async_client):
        _, headers = await _register_premium_user(async_client, "usagehdrs")
        response = await async_client.post(
            "/api/coach/stream", json=_coaching_payload(), headers=headers
        )
        assert response.status_code == 200
        assert response.headers["X-Usage-Remaining-Input"] == "250000"


@pytest.mark.usefixtures("test_env_vars")
class TestDailyCaps:
    @pytest.mark.asyncio
    async def test_cap_exceeded_returns_429(self, async_client, test_db):
        uid, headers = await _register_premium_user(async_client, "cappeduser")
        from app.repositories.sql_usage_repository import SqlUsageRepository

        repo = SqlUsageRepository(test_db)
        await repo.increment_daily(
            user_id=uid,
            usage_date=datetime.now(timezone.utc).date(),
            input_tokens=999_999,
            output_tokens=999_999,
        )
        await test_db.commit()

        response = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert response.status_code == 429
        assert "token" in response.json()["detail"].lower()
        assert response.headers["X-Usage-Remaining-Input"] == "0"
        assert response.headers["X-Usage-Remaining-Output"] == "0"

    @pytest.mark.asyncio
    async def test_cap_exceeded_stream_returns_429(self, async_client, test_db):
        uid, headers = await _register_premium_user(async_client, "cappedstream")
        from app.repositories.sql_usage_repository import SqlUsageRepository

        repo = SqlUsageRepository(test_db)
        await repo.increment_daily(
            user_id=uid,
            usage_date=datetime.now(timezone.utc).date(),
            input_tokens=999_999,
            output_tokens=999_999,
        )
        await test_db.commit()

        response = await async_client.post(
            "/api/coach/stream", json=_coaching_payload(), headers=headers
        )
        assert response.status_code == 429


@pytest.mark.usefixtures("test_env_vars")
class TestPerUserRateLimit:
    class FakeRedisCache:
        def __init__(self):
            self.count = 0

        async def incr(self, key, ttl=60):
            self.count += 1
            return self.count

    @pytest.mark.asyncio
    async def test_per_user_rate_limit_blocks_after_limit(
        self, async_client, monkeypatch
    ):
        fake_cache = self.FakeRedisCache()
        from app.api.dependencies import get_redis_cache

        async def override_get_redis_cache():
            return fake_cache

        app.dependency_overrides[get_redis_cache] = override_get_redis_cache
        monkeypatch.setenv("USER_RATE_LIMIT_PER_MINUTE", "1")
        try:
            _, headers = await _register_premium_user(async_client, "ratelimited")
            first = await async_client.post(
                "/api/coach/", json=_coaching_payload(), headers=headers
            )
            assert first.status_code == 200
            second = await async_client.post(
                "/api/coach/", json=_coaching_payload(), headers=headers
            )
            assert second.status_code == 429
            assert "rate limit" in second.json()["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)

    @pytest.mark.asyncio
    async def test_per_user_rate_limit_degrades_open_without_redis(self, async_client):
        # get_redis_cache returns None when Redis is disabled -> no 429
        _, headers = await _register_premium_user(async_client, "noeredis")
        for _ in range(3):
            response = await async_client.post(
                "/api/coach/", json=_coaching_payload(), headers=headers
            )
            assert response.status_code == 200


@pytest.mark.usefixtures("test_env_vars")
class TestAuthAndValidation:
    @pytest.mark.asyncio
    async def test_coach_requires_auth(self, async_client):
        response = await async_client.post("/api/coach/", json=_coaching_payload())
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_coaching_oversized_payload_422(self, async_client):
        _, headers = await _register_premium_user(async_client, "oversized")

        cases = [
            {"problem": "x" * 20001},
            {"code": "x" * 50001},
            {"message": "x" * 5001},
            {"lesson_context": "x" * 2001},
            {"chat_history": [{"role": "user", "content": "x"} for _ in range(21)]},
        ]
        for extra in cases:
            payload = {**_coaching_payload(), **extra}
            response = await async_client.post(
                "/api/coach/", json=payload, headers=headers
            )
            assert response.status_code == 422, extra

    @pytest.mark.asyncio
    async def test_admin_usage_requires_admin(self, async_client):
        _, headers = await _register_user(async_client, "normaluser")
        response = await async_client.get("/api/admin/usage", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_usage_anonymous_401(self, async_client):
        response = await async_client.get("/api/admin/usage")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_usage_detail_unknown_user_returns_zeros(
        self, async_client, test_db
    ):
        import uuid

        _, headers = await _register_user(async_client, "adminusage")
        await _promote_user(test_db, "adminusage")
        response = await async_client.get(
            f"/api/admin/usage/{uuid.uuid4().hex}", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_input_tokens"] == 0
        assert data["total_output_tokens"] == 0
        assert data["daily"] == []
        assert data["events"] == []


@pytest.mark.usefixtures("test_env_vars")
class TestUsageHeadersReflectUsage:
    @pytest.mark.asyncio
    async def test_headers_reflect_existing_daily_usage(self, async_client, test_db):
        uid, headers = await _register_premium_user(async_client, "useduser")
        from app.repositories.sql_usage_repository import SqlUsageRepository

        repo = SqlUsageRepository(test_db)
        await repo.increment_daily(
            user_id=uid,
            usage_date=datetime.now(timezone.utc).date(),
            input_tokens=100,
            output_tokens=50,
        )
        await test_db.commit()

        response = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert response.status_code == 200
        assert response.headers["X-Usage-Input"] == "100"
        assert response.headers["X-Usage-Output"] == "50"
        assert response.headers["X-Usage-Remaining-Input"] == "249900"
        assert response.headers["X-Usage-Remaining-Output"] == "124950"


async def _promote_user(test_db, username: str) -> None:
    """Promote a registered user to admin directly in the DB."""
    from tests.db_helpers import promote_to_admin

    await promote_to_admin(username)
