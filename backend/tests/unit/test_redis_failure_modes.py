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


@needs_redis
@pytest.mark.asyncio
async def test_client_is_shared_across_ops():
    """One client per cache — no per-op construct/aclose churn."""
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    try:
        assert await cache._client() is await cache._client()
    finally:
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_pool_has_socket_timeouts():
    """Pool must fail fast (2s) instead of hanging on a black-holed Redis."""
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    try:
        kwargs = cache._pool.connection_kwargs
        assert kwargs.get("socket_timeout") == 2.0
        assert kwargs.get("socket_connect_timeout") == 2.0
    finally:
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_ping_true_on_live_redis():
    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    try:
        assert await cache.ping() is True
        assert cache._enabled is True
    finally:
        await cache.close()


@pytest.mark.asyncio
async def test_ping_false_on_dead_redis_disables():
    """Unreachable Redis: ping is False and the breaker trips — no raise."""
    from app.services.redis_service import RedisCache

    cache = RedisCache("redis://127.0.0.1:1/0", socket_timeout=0.2)
    try:
        assert await cache.ping() is False
        assert cache._enabled is False
    finally:
        await cache.close()


@needs_redis
@pytest.mark.asyncio
async def test_half_open_recovers_without_restart():
    """A disabled cache re-probes after the backoff and serves again."""
    import time

    from app.services.redis_service import RedisCache

    cache = RedisCache(REDIS_URL)
    key = f"codecoach:test:{os.getpid()}:recover"
    try:
        cache.disable()
        assert await cache.get(key) is None  # fail fast, stays disabled
        assert cache._enabled is False
        cache._disabled_at = time.monotonic() - 31  # backoff elapsed
        await cache.set(key, {"v": 1}, ttl=60)
        assert await cache.get(key) == {"v": 1}
        assert cache._enabled is True
    finally:
        cache._enabled = True
        cache._disabled_at = None
        await cache.delete(key)
        await cache.close()


def _dead_cache():
    """Real RedisCache pointed at a closed port: every op fails fast."""
    from app.services.redis_service import RedisCache

    return RedisCache("redis://127.0.0.1:1/0", socket_timeout=0.2)


@pytest.mark.asyncio
async def test_question_bank_serves_from_db_when_cache_dead():
    """Issue #210: dead cache degrades to the repository, never raises."""
    from unittest.mock import AsyncMock, MagicMock

    from app.models.schemas import (
        Difficulty,
        Example,
        Question,
        StarterCode,
        TestCase,
    )
    from app.services.question_bank import QuestionBank

    question = Question(
        id="two-sum",
        title="Two Sum",
        difficulty=Difficulty.EASY,
        category="arrays",
        description="desc",
        starter=StarterCode(python="def f(): pass"),
        examples=[Example(input="1", output="1")],
        test_cases=[TestCase(input="1", expected_output="1")],
    )
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=question)
    cache = _dead_cache()
    try:
        bank = QuestionBank(repository=repo, cache=cache)
        assert await bank.get("two-sum") == question
    finally:
        await cache.close()


@pytest.mark.asyncio
async def test_piston_execute_ignores_dead_cache():
    """Issue #210: execution still runs via Piston when caching is down."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services.piston_service import PistonService

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_client.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "run": {"stdout": "Hi\n", "stderr": "", "code": 0},
            "language": "python",
            "version": "3.10.0",
        }
        mock_instance.post.return_value = mock_response

        cache = _dead_cache()
        try:
            service = PistonService(cache=cache)
            result = await service.execute("python", "print('Hi')")
            assert result.stdout == "Hi\n"
        finally:
            await cache.close()
