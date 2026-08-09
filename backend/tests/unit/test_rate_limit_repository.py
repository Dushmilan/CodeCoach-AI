"""Unit tests for rate-limit event persistence (denials + abuse flags)."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
import uuid


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_usage_repository import SqlUsageRepository

    return SqlUsageRepository(test_db)


async def _make_user(test_db, uid=None):
    from app.models.auth_schemas import UserInDB
    from app.repositories.sql_user_repository import SqlUserRepository

    uid = uid or str(uuid.uuid4())
    await SqlUserRepository(test_db).add(
        UserInDB(
            id=uid,
            username=f"rle{uid[:8]}",
            email=f"rle{uid[:8]}@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
    )
    await test_db.commit()
    return uid


@pytest_asyncio.fixture
async def user_id(test_db):
    return await _make_user(test_db)


class TestRateLimitRepository:
    @pytest.mark.asyncio
    async def test_add_rate_limit_event_inserts_row(self, repo, user_id):
        await repo.add_rate_limit_event(
            user_id=user_id,
            ip="203.0.113.10",
            reason="daily_cap",
            endpoint="/api/coach/",
        )
        events = await repo.recent_rate_limit_events(limit=10)
        assert len(events) == 1
        event = events[0]
        assert event.user_id == user_id
        assert event.ip == "203.0.113.10"
        assert event.reason == "daily_cap"
        assert event.endpoint == "/api/coach/"

    @pytest.mark.asyncio
    async def test_add_rate_limit_event_allows_null_user(self, repo):
        await repo.add_rate_limit_event(
            user_id=None,
            ip="198.51.100.7",
            reason="burst_velocity",
            endpoint="/api/coach/",
        )
        events = await repo.recent_rate_limit_events(limit=10)
        assert len(events) == 1
        assert events[0].user_id is None
        assert events[0].ip == "198.51.100.7"

    @pytest.mark.asyncio
    async def test_recent_rate_limit_events_orders_desc(self, repo, user_id):
        import time

        await repo.add_rate_limit_event(
            user_id=user_id, ip="ip-a", reason="daily_cap", endpoint="/api/coach/"
        )
        time.sleep(1.1)
        await repo.add_rate_limit_event(
            user_id=user_id, ip="ip-b", reason="daily_cap", endpoint="/api/coach/stream"
        )
        events = await repo.recent_rate_limit_events(limit=10)
        assert len(events) == 2
        assert events[0].endpoint == "/api/coach/stream"
        assert events[1].endpoint == "/api/coach/"

    @pytest.mark.asyncio
    async def test_count_rate_limit_events_since(self, repo, user_id):
        await repo.add_rate_limit_event(
            user_id=user_id, ip="ip", reason="daily_cap", endpoint="/api/coach/"
        )
        await repo.add_rate_limit_event(
            user_id=user_id, ip="ip", reason="abuse", endpoint="/api/coach/"
        )
        since = datetime.now(timezone.utc) - timedelta(minutes=5)
        count = await repo.count_rate_limit_events(since)
        assert count == 2
        old = since - timedelta(days=30)
        count_old = await repo.count_rate_limit_events(old)
        assert count_old == 2
