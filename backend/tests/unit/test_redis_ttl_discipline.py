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

    async def eval(self, script, numkeys, key, ttl):
        """Emulate the INCR+EXPIRE Lua script: one atomic round trip."""
        if self.fail:
            raise ConnectionError("boom")
        self._counter += 1
        if self._counter == 1:
            await self.expire(key, ttl)
        return self._counter

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
async def test_incr_is_single_atomic_round_trip(fake_cache):
    """Issue #210: INCR+EXPIRE runs as one Lua EVAL — no crash window.

    Replaces the old two-round-trip pin: a single client call per incr,
    with EXPIRE applied server-side only when the counter is new.
    """
    cache, fake = fake_cache
    calls = []
    orig_eval = fake.eval

    async def _eval(script, numkeys, key, ttl):
        calls.append("eval")
        assert "EXPIRE" in script  # TTL rides along in the same script
        return await orig_eval(script, numkeys, key, ttl)

    fake.eval = _eval
    assert await cache.incr("ctr2", ttl=60) == 1
    assert await cache.incr("ctr2", ttl=60) == 2
    assert calls == ["eval", "eval"]
    assert fake.expire_calls == [("ctr2", 60)]


def test_key_namespacing():
    assert (
        RedisCache.key("workspace", "meta", "u", "q") == "codecoach:workspace:meta:u:q"
    )
