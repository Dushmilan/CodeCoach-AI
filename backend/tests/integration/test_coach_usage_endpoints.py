"""Integration tests for coach usage metering, daily caps and per-user rate limiting."""

from datetime import datetime, timezone

import pytest

from app.main import app
from app.api.coach import get_coaching_provider
from tests.fixtures.auth_helpers import aregister_headers
from tests.fixtures.mock_coaching_provider import MockCoachingProvider


@pytest.fixture(autouse=True)
def _override_coaching_provider():
    """Auto-override coaching provider so tests never hit the network."""
    app.dependency_overrides[get_coaching_provider] = MockCoachingProvider
    yield
    app.dependency_overrides.pop(get_coaching_provider, None)


async def _register_user(async_client, username: str):
    return await aregister_headers(async_client, username)


async def _register_user_plain(async_client, username: str):
    return await _register_user(async_client, username)


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
class TestNoTokenCaps:
    """Issue #184: token-cap enforcement removed; usage still recorded."""

    @pytest.mark.asyncio
    async def test_coach_response_has_no_token_cap_headers(self, async_client):
        _, headers = await _register_user_plain(async_client, "usagehdr")
        response = await async_client.post(
            "/api/coach/", json=_coaching_payload(), headers=headers
        )
        assert response.status_code == 200
        assert "X-Usage-Remaining-Input" not in response.headers
        assert "X-Usage-Remaining-Output" not in response.headers

    @pytest.mark.asyncio
    async def test_high_token_usage_still_allowed_and_recorded(
        self, async_client, test_db
    ):
        from app.repositories.sql_usage_repository import SqlUsageRepository

        uid, headers = await _register_user_plain(async_client, "biguser")
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
        assert response.status_code == 200


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
            _, headers = await _register_user_plain(async_client, "ratelimited")
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
        _, headers = await _register_user_plain(async_client, "noeredis")
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
        _, headers = await _register_user_plain(async_client, "oversized")

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
    async def test_no_token_usage_headers_on_coach_response(
        self, async_client, test_db
    ):
        uid, headers = await _register_user_plain(async_client, "useduser")
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
        assert "X-Usage-Input" not in response.headers
        assert "X-Usage-Remaining-Input" not in response.headers


async def _promote_user(test_db, username: str) -> None:
    """Promote a registered user to admin directly in the DB."""
    from tests.db_helpers import promote_to_admin

    await promote_to_admin(username)
