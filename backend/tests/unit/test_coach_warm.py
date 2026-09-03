"""Unit tests for POST /api/coach/warm background cache warming (TDD red)."""

import pytest
from contextlib import contextmanager
from unittest.mock import AsyncMock

from app.main import app
from app.api.auth_deps import get_current_user
from app.api.dependencies import (
    get_learner_context_service_dependency,
    get_redis_cache,
)
from app.models.auth_schemas import UserResponse


@contextmanager
def mock_auth(user_id="warm-learner"):
    async def override():
        return UserResponse(
            id=user_id,
            username="learner",
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
            plan="premium",
        )

    app.dependency_overrides[get_current_user] = override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


class FakeCache:
    """Minimal in-memory RedisCache double with atomic set_if_absent."""

    def __init__(self):
        self.store = {}
        self.set_if_absent_calls = 0

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl=300):
        self.store[key] = value

    async def set_if_absent(self, key, value, ttl=300):
        self.set_if_absent_calls += 1
        if key in self.store:
            return False
        self.store[key] = value
        return True

    async def exists(self, key):
        return key in self.store

    async def ttl(self, key):
        return 60 if key in self.store else -2

    async def delete(self, pattern):
        self.store.pop(pattern, None)
        return 1


@pytest.mark.usefixtures("test_env_vars")
class TestCoachWarm:
    @pytest.mark.asyncio
    async def test_warm_returns_202_and_populates_cache(self, async_client):
        from app.services.learner_context_service import LearnerContextService

        fake_cache = FakeCache()
        mock_svc = AsyncMock(spec=LearnerContextService)
        mock_svc.get_context = AsyncMock(
            return_value={"skill_block": "s", "submission_block": "b"}
        )

        app.dependency_overrides[get_redis_cache] = lambda: fake_cache
        app.dependency_overrides[get_learner_context_service_dependency] = lambda: (
            mock_svc
        )
        try:
            with mock_auth():
                resp = await async_client.post("/api/coach/warm", json={})
            assert resp.status_code == 202
            assert resp.json()["status"] in ("warming", "hit")
            # Background task may not have run yet in ASGI transport;
            # endpoint must at least have attempted single-flight acquisition.
            assert fake_cache.set_if_absent_calls >= 1
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)
            app.dependency_overrides.pop(get_learner_context_service_dependency, None)

    @pytest.mark.asyncio
    async def test_warm_idempotent_second_call_returns_hit(self, async_client):
        from app.core.cache_keys import coach_context_key
        from app.services.learner_context_service import LearnerContextService

        fake_cache = FakeCache()
        user_id = "warm-learner-hit"
        fake_cache.store[coach_context_key(user_id)] = {
            "skill_block": "s",
            "submission_block": "b",
        }
        mock_svc = AsyncMock(spec=LearnerContextService)
        mock_svc.get_context = AsyncMock()

        app.dependency_overrides[get_redis_cache] = lambda: fake_cache
        app.dependency_overrides[get_learner_context_service_dependency] = lambda: (
            mock_svc
        )
        try:
            with mock_auth(user_id=user_id):
                resp = await async_client.post("/api/coach/warm", json={})
            assert resp.status_code == 202
            assert resp.json()["status"] == "hit"
            mock_svc.get_context.assert_not_called()
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)
            app.dependency_overrides.pop(get_learner_context_service_dependency, None)

    @pytest.mark.asyncio
    async def test_warm_unauth_401(self, async_client):
        app.dependency_overrides.pop(get_current_user, None)
        resp = await async_client.post("/api/coach/warm", json={})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_warm_degrades_when_redis_disabled(self, async_client):
        from app.services.learner_context_service import LearnerContextService

        mock_svc = AsyncMock(spec=LearnerContextService)
        mock_svc.get_context = AsyncMock()

        app.dependency_overrides[get_redis_cache] = lambda: None
        app.dependency_overrides[get_learner_context_service_dependency] = lambda: (
            mock_svc
        )
        try:
            with mock_auth():
                resp = await async_client.post("/api/coach/warm", json={})
            assert resp.status_code == 202
            assert resp.json()["status"] == "disabled"
            mock_svc.get_context.assert_not_called()
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)
            app.dependency_overrides.pop(get_learner_context_service_dependency, None)


@pytest.mark.asyncio
async def test_redis_set_if_absent_atomic():
    """RedisCache must expose atomic SET NX EX for warm single-flight."""
    from app.services.redis_service import RedisCache

    cache = RedisCache("redis://127.0.0.1:6379/0")
    assert hasattr(cache, "set_if_absent")
    # Mocked client to avoid needing live Redis.
    acquired = {}

    class FakeClient:
        async def set(self, key, value, ex=None, nx=False):
            if nx and key in acquired:
                return None
            acquired[key] = value
            return True

        async def aclose(self):
            return None

    cache._client = AsyncMock(return_value=FakeClient())
    first = await cache.set_if_absent("k", "1", ttl=5)
    second = await cache.set_if_absent("k", "1", ttl=5)
    assert first is True
    assert second is False
