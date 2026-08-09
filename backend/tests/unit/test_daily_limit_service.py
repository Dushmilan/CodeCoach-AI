"""Unit tests for DailyLimitService — Redis-backed daily request counter
with graceful DB fallback."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
import uuid


class FakeRedisCache:
    """In-memory stand-in for RedisCache.incr/get/decr.

    `fail` toggles Redis-down behavior (methods return None).
    """

    def __init__(self):
        self.data = {}
        self.fail = False

    async def get(self, key):
        if self.fail:
            return None
        return self.data.get(key)

    async def incr(self, key, ttl=60):
        if self.fail:
            return None
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]

    async def decr(self, key):
        if self.fail:
            return None
        self.data[key] = self.data.get(key, 1) - 1
        return self.data[key]


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_usage_repository import SqlUsageRepository

    return SqlUsageRepository(test_db)


async def _make_user(test_db):
    from datetime import datetime as dt

    from app.models.auth_schemas import UserInDB
    from app.repositories.sql_user_repository import SqlUserRepository

    uid = str(uuid.uuid4())
    await SqlUserRepository(test_db).add(
        UserInDB(
            id=uid,
            username=f"dl{uid[:8]}",
            email=f"dl{uid[:8]}@example.com",
            hashed_password="hash",
            created_at=dt.now(timezone.utc),
            is_active=True,
        )
    )
    await test_db.commit()
    return uid


def _now():
    return datetime(2026, 8, 6, 12, 0, 0, tzinfo=timezone.utc)


class TestDailyLimitServiceTtl:
    @pytest.mark.asyncio
    async def test_ttl_to_midnight_near_midnight(self):
        from app.services.daily_limit_service import DailyLimitService

        now = datetime(2026, 8, 6, 23, 59, 59, tzinfo=timezone.utc)
        ttl = DailyLimitService.ttl_to_midnight(now)
        assert ttl == 1

    @pytest.mark.asyncio
    async def test_ttl_to_midnight_at_midnight(self):
        from app.services.daily_limit_service import DailyLimitService

        now = datetime(2026, 8, 7, 0, 0, 0, tzinfo=timezone.utc)
        ttl = DailyLimitService.ttl_to_midnight(now)
        assert ttl == 86400

    @pytest.mark.asyncio
    async def test_ttl_to_midnight_noon(self):
        from app.services.daily_limit_service import DailyLimitService

        now = datetime(2026, 8, 6, 12, 0, 0, tzinfo=timezone.utc)
        ttl = DailyLimitService.ttl_to_midnight(now)
        assert ttl == 12 * 3600


class TestDailyLimitServiceConsume:
    @pytest.mark.asyncio
    async def test_consume_allows_within_cap(self, repo, test_db):
        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        cache = FakeRedisCache()
        service = DailyLimitService(cache=cache, repo=repo)
        for _ in range(5):
            allowed, remaining = await service.consume(user_id, cap=20, now=_now())
            assert allowed is True
        assert remaining == 15

    @pytest.mark.asyncio
    async def test_consume_blocks_at_cap(self, repo, test_db):
        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        cache = FakeRedisCache()
        service = DailyLimitService(cache=cache, repo=repo)
        for _ in range(2):
            allowed, _ = await service.consume(user_id, cap=2, now=_now())
            assert allowed is True
        allowed, remaining = await service.consume(user_id, cap=2, now=_now())
        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_denied_attempt_does_not_burn_slot(self, repo, test_db):
        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        cache = FakeRedisCache()
        service = DailyLimitService(cache=cache, repo=repo)
        for _ in range(2):
            await service.consume(user_id, cap=2, now=_now())
        _, _ = await service.consume(user_id, cap=2, now=_now())
        # Denial refunded the slot: counter back at cap (2), not higher.
        key = service._key(user_id, _now().date())
        assert cache.data[key] == 2

    @pytest.mark.asyncio
    async def test_consume_concurrent_no_overshoot(self, repo, test_db):
        import asyncio

        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        cache = FakeRedisCache()
        service = DailyLimitService(cache=cache, repo=repo)

        async def attempt(_):
            return await service.consume(user_id, cap=3, now=_now())

        results = await asyncio.gather(*[attempt(i) for i in range(6)])
        allowed = [r for r in results if r[0]]
        assert len(allowed) == 3


class TestDailyLimitServiceFallback:
    @pytest.mark.asyncio
    async def test_remaining_reads_db_when_redis_down(self, repo, test_db):
        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        from datetime import date

        await repo.increment_daily(
            user_id=user_id,
            usage_date=date(2026, 8, 6),
            input_tokens=0,
            output_tokens=0,
            request_count=5,
        )
        cache = FakeRedisCache()
        cache.fail = True
        service = DailyLimitService(cache=cache, repo=repo)
        remaining = await service.remaining(user_id, cap=20, now=_now())
        assert remaining == 15

    @pytest.mark.asyncio
    async def test_remaining_reads_db_when_redis_miss(self, repo, test_db):
        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        from datetime import date

        await repo.increment_daily(
            user_id=user_id,
            usage_date=date(2026, 8, 6),
            input_tokens=0,
            output_tokens=0,
            request_count=7,
        )
        service = DailyLimitService(cache=FakeRedisCache(), repo=repo)
        remaining = await service.remaining(user_id, cap=20, now=_now())
        assert remaining == 13

    @pytest.mark.asyncio
    async def test_consume_blocks_when_db_at_cap(self, repo, test_db):
        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        from datetime import date

        await repo.increment_daily(
            user_id=user_id,
            usage_date=date(2026, 8, 6),
            input_tokens=0,
            output_tokens=0,
            request_count=20,
        )
        cache = FakeRedisCache()
        cache.fail = True
        service = DailyLimitService(cache=cache, repo=repo)
        allowed, remaining = await service.consume(user_id, cap=20, now=_now())
        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_consume_uses_db_when_redis_down(self, repo, test_db):
        from app.services.daily_limit_service import DailyLimitService

        user_id = await _make_user(test_db)
        cache = FakeRedisCache()
        cache.fail = True
        service = DailyLimitService(cache=cache, repo=repo)
        allowed, _ = await service.consume(user_id, cap=20, now=_now())
        assert allowed is True
