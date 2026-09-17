"""Unit tests pinning RedisCache TTL discipline (Issue #202, B8).

Every writer must attach a TTL so no cache key can live forever; the
INCR-then-EXPIRE window and the sticky-disable behavior are characterized
as known gaps (see docs/TEST_COVERAGE.md when it lands). Fake client —
no Redis needed.
"""

import pytest

from app.services import redis_service
from app.services.redis_service import RedisCache


class _FakeClient:
    def __init__(self):
        self.setex_calls = []
        self.set_calls = []
        self.expire_calls = []
        self._counter = 0
        self.fail = False

    async def setex(self, key, ttl, raw):
        if self.fail:
            raise ConnectionError("boom")
        self.setex_calls.append((key, ttl, raw))

    async def set(self, key, raw, ex=None, nx=False):
        if self.fail:
            raise ConnectionError("boom")
        self.set_calls.append((key, raw, ex, nx))
        return True

    async def incr(self, key):
        if self.fail:
            raise ConnectionError("boom")
        self._counter += 1
        return self._counter

    async def expire(self, key, ttl):
        self.expire_calls.append((key, ttl))

    async def aclose(self):
        pass


@pytest.fixture
def fake_cache(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(redis_service.aioredis, "Redis", lambda **kwargs: fake)
    cache = RedisCache("redis://127.0.0.1:6379/0")
    return cache, fake


@pytest.mark.asyncio
async def test_set_applies_default_ttl(fake_cache):
    cache, fake = fake_cache
    await cache.set("k1", {"a": 1})
    assert fake.setex_calls == [("k1", 300, '{"a": 1}')]


@pytest.mark.asyncio
async def test_set_honors_custom_ttl(fake_cache):
    cache, fake = fake_cache
    await cache.set("k1", [1, 2], ttl=86400)
    assert fake.setex_calls[0][1] == 86400


@pytest.mark.asyncio
async def test_set_if_absent_passes_ex_and_nx(fake_cache):
    cache, fake = fake_cache
    acquired = await cache.set_if_absent("lock", "1", ttl=10)
    assert acquired is True
    assert fake.set_calls == [("lock", '"1"', 10, True)]


@pytest.mark.asyncio
async def test_incr_expires_only_on_first_increment(fake_cache):
    cache, fake = fake_cache
    assert await cache.incr("ctr", ttl=60) == 1
    assert await cache.incr("ctr", ttl=60) == 2
    assert fake.expire_calls == [("ctr", 60)]


@pytest.mark.asyncio
async def test_error_disables_cache_and_stays_disabled():
    """Known gap: one transient blip disables caching until restart.

    Characterizes current fail-open behavior — no re-probe exists.
    """
    from app.services.redis_service import RedisCache as RC

    cache = RC("redis://127.0.0.1:6379/0")
    cache._enabled = False  # as after any client error
    assert await cache.get("k") is None
    assert await cache.incr("k") is None
    assert await cache.set_if_absent("k", "v") is False
    assert await cache.delete("codecoach:*") == 0
    assert cache._enabled is False  # sticky: no re-probe


@pytest.mark.asyncio
async def test_incr_expire_window_is_documented(fake_cache):
    """Known gap: INCR-then-EXPIRE is two round trips, not atomic.

    A crash between them leaves a counter key without TTL. This test pins
    the call order so any future Lua-script fix must update it deliberately.
    """
    cache, fake = fake_cache
    calls = []
    orig_incr = fake.incr
    orig_expire = fake.expire

    async def _incr(key):
        calls.append("incr")
        return await orig_incr(key)

    async def _expire(key, ttl):
        calls.append("expire")
        return await orig_expire(key, ttl)

    fake.incr = _incr
    fake.expire = _expire
    await cache.incr("ctr2", ttl=60)
    assert calls == ["incr", "expire"]
    assert fake.expire_calls == [("ctr2", 60)]


def test_key_namespacing():
    assert (
        RedisCache.key("workspace", "meta", "u", "q") == "codecoach:workspace:meta:u:q"
    )
