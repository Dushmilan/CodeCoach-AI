import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.main import app
from app.api.auth_deps import get_current_user
from app.models.auth_schemas import UserResponse

NOW = datetime.now(timezone.utc)
USER = "test-id"


def mock_auth():
    async def _ov():
        return UserResponse(
            id=USER,
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
            plan="free",
        )

    app.dependency_overrides[get_current_user] = _ov
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def _seed_user_q(test_db):
    await test_db.execute(
        text(
            "INSERT INTO users (id, username, email, hashed_password, created_at, is_active, plan, role) "
            "VALUES (:u, 'testuser', 'test@example.com', 'x', :ts, 1, 'free', 'user') ON CONFLICT DO NOTHING"
        ),
        {"u": USER, "ts": NOW},
    )
    await test_db.execute(
        text(
            "INSERT INTO questions (id, title, difficulty, category, company_tags, description, starter_code, examples, test_cases, constraints, hints, is_interactive) "
            "VALUES ('invert-binary-tree', 'T', 'easy', 'trees', '[]', 'desc', '{}', '[]', '[]', '[]', '[]', 0) ON CONFLICT DO NOTHING"
        )
    )
    await test_db.commit()


class TestAnalyticsSignals:
    @pytest.mark.asyncio
    async def test_requires_auth(self, async_client):
        assert (await async_client.get("/api/analytics/signals")).status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_empty_returns_empty(self, async_client, test_db):
        await _seed_user_q(test_db)
        from contextlib import contextmanager

        with contextmanager(mock_auth)():
            resp = await async_client.get("/api/analytics/signals")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_plateau_detected(self, async_client, test_db):
        await _seed_user_q(test_db)
        for i in range(3):
            await test_db.execute(
                text(
                    "INSERT INTO submissions (id, user_id, question_id, code, language, passed, error_signature, attempt_index, created_at) "
                    "VALUES (:id, :u, 'invert-binary-tree', 'c', 'python', false, 'sig A', :i, :ts)"
                ),
                {"id": f"s{i}", "u": USER, "i": i, "ts": NOW - timedelta(days=i)},
            )
        await test_db.commit()
        from contextlib import contextmanager

        with contextmanager(mock_auth)():
            resp = await async_client.get("/api/analytics/signals")
        assert resp.status_code == 200
        assert any(s["skill"] == "recursion" for s in resp.json()["signals"])
