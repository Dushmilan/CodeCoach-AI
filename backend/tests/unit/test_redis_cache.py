"""Unit tests for RedisCache incr/decr — atomic counters used by rate limiting."""

import os

import pytest

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")


def _cache_available() -> bool:
    try:
        import redis.asyncio as aioredis

        import asyncio

        async def _ping():
            r = aioredis.from_url(REDIS_URL, socket_timeout=1)
            try:
                await r.ping()
            finally:
                await r.aclose()

        asyncio.run(_ping())
        return True
    except Exception:
        return False


needs_redis = pytest.mark.skipif(
    not _cache_available(), reason="Redis unavailable — skipping RedisCache tests"
)


@needs_redis
@pytest.mark.asyncio
async def test_incr_sets_ttl_on_first_increment():
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    key = f"codecoach:test:{os.getpid()}:incr"
    try:
        v1 = await cache.incr(key, ttl=60)
        assert v1 == 1
        v2 = await cache.incr(key, ttl=60)
        assert v2 == 2
        ttl = await cache.ttl(key)
        assert 0 < ttl <= 60
    finally:
        await cache.delete(key)
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_decr_decrements_counter():
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    key = f"codecoach:test:{os.getpid()}:decr"
    try:
        await cache.incr(key, ttl=60)
        v = await cache.decr(key)
        assert v == 0
    finally:
        await cache.delete(key)
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_decr_missing_key_returns_negative_one():
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    key = f"codecoach:test:{os.getpid()}:decr_missing"
    try:
        v = await cache.decr(key)
        assert v == -1
    finally:
        await cache.delete(key)
        await cache.close()


class _RecordingFakeClient:
    """Minimal stand-in for aioredis client recording KEYS usage."""

    def __init__(self, keys):
        self._keys = list(keys)
        self.keys_called = False

    async def keys(self, pattern):
        self.keys_called = True
        return []

    async def scan_iter(self, match, count=100):
        import fnmatch

        for key in list(self._keys):
            if fnmatch.fnmatch(key, match):
                yield key

    async def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self._keys:
                self._keys.remove(key)
                removed += 1
        return removed

    async def aclose(self):
        pass


@needs_redis
@pytest.mark.asyncio
async def test_delete_uses_scan_not_blocking_keys(monkeypatch):
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    fake = _RecordingFakeClient(
        [f"codecoach:test:{os.getpid()}:scan:{i}" for i in range(5)]
    )

    async def _fake_client():
        return fake

    monkeypatch.setattr(cache, "_client", _fake_client)
    try:
        removed = await cache.delete(f"codecoach:test:{os.getpid()}:scan:*")
        assert removed == 5
        assert fake.keys_called is False
    finally:
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_delete_pattern_removes_all_matches_live():
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    prefix = f"codecoach:test:{os.getpid()}:bulk"
    try:
        for i in range(25):
            await cache.set(f"{prefix}:{i}", {"i": i}, ttl=60)
        removed = await cache.delete(f"{prefix}:*")
        assert removed == 25
        assert await cache.get(f"{prefix}:0") is None
    finally:
        await cache.delete(f"{prefix}:*")
        await cache.close()
