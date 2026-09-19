"""Issue #210: RedisCache failure-mode hardening.

RED tests: corrupt cached values must not latch-disable the cache;
exists()/ttl() connection errors must trip the breaker like every
other op. Must FAIL before the fix, PASS after.
"""

import os

import pytest

from tests.unit.test_redis_cache import REDIS_URL, needs_redis


class _FailingFakeClient:
    """aioredis stand-in whose ops raise a connection error."""

    def __init__(self, exc=None):
        import redis.exceptions as redis_exc

        self._exc = exc or redis_exc.ConnectionError("connection refused")

    async def get(self, key):
        raise self._exc

    async def exists(self, key):
        raise self._exc

    async def ttl(self, key):
        raise self._exc

    async def aclose(self):
        pass


@needs_redis
@pytest.mark.asyncio
async def test_corrupt_value_returns_miss_without_disabling():
    """A non-JSON value is a data problem, not an outage: miss + drop key."""
    import redis.asyncio as aioredis

    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    key = f"codecoach:test:{os.getpid()}:corrupt"
    raw = aioredis.from_url(REDIS_URL, socket_timeout=1)
    try:
        await raw.set(key, "{not valid json", ex=60)
        assert await cache.get(key) is None
        assert cache._enabled is True
        assert await raw.get(key) is None  # poison key removed
    finally:
        await raw.delete(key)
        await raw.aclose()
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_exists_disables_on_connection_error(monkeypatch):
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    fake = _FailingFakeClient()

    async def _fake_client():
        return fake

    monkeypatch.setattr(cache, "_client", _fake_client)
    try:
        assert await cache.exists("codecoach:test:missing") is False
        assert cache._enabled is False
    finally:
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_ttl_disables_on_connection_error(monkeypatch):
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    fake = _FailingFakeClient()

    async def _fake_client():
        return fake

    monkeypatch.setattr(cache, "_client", _fake_client)
    try:
        assert await cache.ttl("codecoach:test:missing") == -2
        assert cache._enabled is False
    finally:
        await cache.close()
