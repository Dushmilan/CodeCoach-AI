"""Unit tests for SqlUsageRepository — MySQL-backed usage persistence."""

from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
import uuid


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_usage_repository import SqlUsageRepository

    return SqlUsageRepository(test_db)


async def _make_user(test_db, uid=None):
    """Create a user row (FK target) and return its id."""
    from app.models.auth_schemas import UserInDB
    from app.repositories.sql_user_repository import SqlUserRepository

    uid = uid or str(uuid.uuid4())
    await SqlUserRepository(test_db).add(
        UserInDB(
            id=uid,
            username=f"usageuser{uid[:8]}",
            email=f"usage{uid[:8]}@example.com",
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


class TestSqlUsageRepository:
    @pytest.mark.asyncio
    async def test_increment_daily_creates_row(self, repo, user_id):
        today = date.today()
        await repo.increment_daily(
            user_id=user_id, usage_date=today, input_tokens=10, output_tokens=20
        )
        daily = await repo.get_daily(user_id, today)
        assert daily is not None
        assert daily.input_tokens == 10
        assert daily.output_tokens == 20

    @pytest.mark.asyncio
    async def test_increment_daily_accumulates(self, repo, user_id):
        today = date.today()
        await repo.increment_daily(
            user_id=user_id, usage_date=today, input_tokens=10, output_tokens=20
        )
        await repo.increment_daily(
            user_id=user_id, usage_date=today, input_tokens=5, output_tokens=7
        )
        daily = await repo.get_daily(user_id, today)
        assert daily.input_tokens == 15
        assert daily.output_tokens == 27

    @pytest.mark.asyncio
    async def test_increment_daily_isolated_by_date(self, repo, user_id):
        today = date.today()
        yesterday = date(2000, 1, 1)
        await repo.increment_daily(
            user_id=user_id, usage_date=today, input_tokens=10, output_tokens=10
        )
        await repo.increment_daily(
            user_id=user_id, usage_date=yesterday, input_tokens=99, output_tokens=99
        )
        daily = await repo.get_daily(user_id, today)
        assert daily.input_tokens == 10
        assert daily.output_tokens == 10

    @pytest.mark.asyncio
    async def test_increment_daily_isolated_by_user(self, repo, test_db, user_id):
        today = date.today()
        other_user = await _make_user(test_db)
        await repo.increment_daily(
            user_id=user_id, usage_date=today, input_tokens=10, output_tokens=10
        )
        await repo.increment_daily(
            user_id=other_user, usage_date=today, input_tokens=99, output_tokens=99
        )
        daily = await repo.get_daily(user_id, today)
        assert daily.input_tokens == 10
        assert daily.output_tokens == 10

    @pytest.mark.asyncio
    async def test_get_daily_missing_returns_none(self, repo, user_id):
        daily = await repo.get_daily(user_id, date.today())
        assert daily is None

    @pytest.mark.asyncio
    async def test_add_event_inserts_row(self, repo, user_id):
        await repo.add_event(
            user_id=user_id,
            provider="groq",
            model="llama-3.3-70b-versatile",
            endpoint="coach",
            input_tokens=12,
            output_tokens=34,
        )
        events = await repo.recent_events(user_id, limit=10)
        assert len(events) == 1
        event = events[0]
        assert event.provider == "groq"
        assert event.model == "llama-3.3-70b-versatile"
        assert event.endpoint == "coach"
        assert event.input_tokens == 12
        assert event.output_tokens == 34
        assert event.user_id == user_id

    @pytest.mark.asyncio
    async def test_user_totals_aggregates_over_period(self, repo, user_id):
        await repo.add_event(
            user_id=user_id,
            provider="groq",
            model="m1",
            endpoint="coach",
            input_tokens=10,
            output_tokens=20,
        )
        await repo.add_event(
            user_id=user_id,
            provider="groq",
            model="m2",
            endpoint="coach_stream",
            input_tokens=5,
            output_tokens=7,
        )
        totals = await repo.user_totals(
            user_id, since=datetime(2000, 1, 1, tzinfo=timezone.utc)
        )
        assert totals.input_tokens == 15
        assert totals.output_tokens == 27

    @pytest.mark.asyncio
    async def test_all_user_totals_groups_by_user(self, repo, test_db, user_id):
        other_user = await _make_user(test_db)
        await repo.add_event(
            user_id=user_id,
            provider="groq",
            model="m",
            endpoint="coach",
            input_tokens=10,
            output_tokens=10,
        )
        await repo.add_event(
            user_id=other_user,
            provider="groq",
            model="m",
            endpoint="coach",
            input_tokens=50,
            output_tokens=50,
        )
        rows = await repo.all_user_totals(
            since=datetime(2000, 1, 1, tzinfo=timezone.utc)
        )
        by_user = {r.user_id: r for r in rows}
        assert by_user[user_id].input_tokens == 10
        assert by_user[other_user].input_tokens == 50

    @pytest.mark.asyncio
    async def test_concurrent_increments_accumulate(self, test_db, user_id):
        import asyncio
        import os

        from app.repositories.sql_usage_repository import SqlUsageRepository
        from sqlalchemy.ext.asyncio import (
            AsyncSession,
            async_sessionmaker,
            create_async_engine,
        )
        from sqlalchemy.pool import NullPool

        today = date.today()
        engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async def bump(n):
            async with async_session() as session:
                repo = SqlUsageRepository(session)
                for _ in range(n):
                    await repo.increment_daily(
                        user_id=user_id,
                        usage_date=today,
                        input_tokens=2,
                        output_tokens=1,
                    )

        await asyncio.gather(bump(5), bump(5))
        await engine.dispose()

        repo = SqlUsageRepository(test_db)
        daily = await repo.get_daily(user_id, today)
        assert daily.input_tokens == 20
        assert daily.output_tokens == 10
