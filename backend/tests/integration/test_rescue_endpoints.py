"""Integration tests for the durable rescue re-surface queue endpoints.

The "never-alone" contract's persistence half: abandoning a problem must
schedule a tomorrow-morning resurface that survives reloads and restarts.
Action endpoints answer uniformly with {"item": RescueItem | null} - a null
item is a normal outcome (nothing was open / dismissal is permanent), never
an error.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.main import app

QUESTION = "rescue-question"


@contextmanager
def mock_auth():
    """Override auth dependency for testing (user id must exist in the DB)."""
    from app.api.auth_deps import get_current_user
    from app.models.auth_schemas import UserResponse

    async def override_get_current_user():
        return UserResponse(
            id="test-id",
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
            plan="free",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def _seed_user_and_question(test_db):
    """Create the FK targets (user + question) in the test schema."""
    await test_db.execute(
        text(
            "INSERT INTO users "
            "(id, username, email, hashed_password, created_at, is_active, "
            " plan, role) "
            "VALUES ('test-id', 'testuser', 'test@example.com', 'x', :ts, 1, "
            " 'free', 'user') ON CONFLICT (id) DO NOTHING"
        ),
        {"ts": datetime.now(timezone.utc)},
    )
    await test_db.execute(
        text(
            "INSERT INTO questions "
            "(id, title, difficulty, category, company_tags, description, "
            " starter_code, examples, test_cases, constraints, hints, is_interactive) "
            f"VALUES ('{QUESTION}', 'Rescue Q', 'easy', 'arrays', '[]', 'desc', "
            "'{}', '[]', '[]', '[]', '[]', 0)"
        )
    )
    await test_db.commit()


async def _mature_row(test_db):
    """Time-travel the queue row into maturity (due in the past)."""
    await test_db.execute(
        text(
            "UPDATE rescue_queue SET due_at = now() - interval '1 hour' "
            f"WHERE user_id = 'test-id' AND question_id = '{QUESTION}'"
        )
    )
    await test_db.commit()


class TestAbandonEndpoint:
    @pytest.mark.asyncio
    async def test_abandon_persists_row_due_tomorrow(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            resp = await async_client.post(f"/api/rescue/{QUESTION}/abandon")

        assert resp.status_code == 200, resp.text
        item = resp.json()["item"]
        assert item["question_id"] == QUESTION
        assert item["status"] == "abandoned"

        due_at = datetime.fromisoformat(item["due_at"])
        now = datetime.now(timezone.utc)
        assert now < due_at < now + timedelta(days=2)

    @pytest.mark.asyncio
    async def test_re_abandon_is_idempotent_single_open_row(
        self, async_client, test_db
    ):
        await _seed_user_and_question(test_db)
        with mock_auth():
            first = await async_client.post(f"/api/rescue/{QUESTION}/abandon")
            second = await async_client.post(f"/api/rescue/{QUESTION}/abandon")

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()["item"]["resurface_count"] == 1

    @pytest.mark.asyncio
    async def test_abandon_requires_auth(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        resp = await async_client.post(f"/api/rescue/{QUESTION}/abandon")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_abandon_unknown_question_404(self, async_client, test_db):
        await test_db.execute(
            text(
                "INSERT INTO users "
                "(id, username, email, hashed_password, created_at, is_active, "
                " plan, role) "
                "VALUES ('test-id', 'testuser', 'test@example.com', 'x', :ts, 1, "
                " 'free', 'user') ON CONFLICT (id) DO NOTHING"
            ),
            {"ts": datetime.now(timezone.utc)},
        )
        await test_db.commit()

        with mock_auth():
            resp = await async_client.post("/api/rescue/no-such-q/abandon")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_dismissed_question_never_reopens(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            await async_client.post(f"/api/rescue/{QUESTION}/abandon")
            await async_client.post(f"/api/rescue/{QUESTION}/dismiss")
            resp = await async_client.post(f"/api/rescue/{QUESTION}/abandon")

        assert resp.status_code == 200
        assert resp.json()["item"] is None


class TestDueEndpoint:
    @pytest.mark.asyncio
    async def test_due_returns_matured_items_only(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            await async_client.post(f"/api/rescue/{QUESTION}/abandon")

            early = await async_client.get("/api/rescue/due")
            assert early.status_code == 200
            assert early.json()["items"] == []

        await _mature_row(test_db)

        with mock_auth():
            late = await async_client.get("/api/rescue/due")

        assert late.status_code == 200
        items = late.json()["items"]
        assert [i["question_id"] for i in items] == [QUESTION]
        assert late.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_due_requires_auth(self, async_client):
        resp = await async_client.get("/api/rescue/due")
        assert resp.status_code in (401, 403)


class TestCompleteDismissEndpoints:
    @pytest.mark.asyncio
    async def test_complete_closes_row(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            await async_client.post(f"/api/rescue/{QUESTION}/abandon")
            resp = await async_client.post(f"/api/rescue/{QUESTION}/complete")

        assert resp.status_code == 200
        assert resp.json()["item"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_complete_without_row_returns_null_item(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            resp = await async_client.post(f"/api/rescue/{QUESTION}/complete")

        assert resp.status_code == 200
        assert resp.json()["item"] is None

    @pytest.mark.asyncio
    async def test_dismiss_closes_row(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            await async_client.post(f"/api/rescue/{QUESTION}/abandon")
            resp = await async_client.post(f"/api/rescue/{QUESTION}/dismiss")

        assert resp.status_code == 200
        assert resp.json()["item"]["status"] == "dismissed"


class TestAbandonRaceHandling:
    """A concurrent duplicate abandon must NOT surface as a bogus 404."""

    @staticmethod
    def _fake_service_raising(sqlstate):
        from app.services.rescue_service import RescueService

        class _FakePgOrig(Exception):
            pass

        _FakePgOrig.sqlstate = sqlstate

        class _FakeService(RescueService):
            def __init__(self):  # bypass repo wiring - behaviour is faked
                super().__init__(repo=None)

            async def abandon(self, *, user_id, question_id, now, tz_offset_minutes=0):
                raise IntegrityError(
                    "INSERT INTO rescue_queue ...",  # statement
                    {},  # params
                    _FakePgOrig("concurrent abandon"),  # driver exception
                )

            async def open_item(self, user_id, question_id):
                return None  # race lost; nothing durable to return

        return _FakeService()

    @pytest.mark.asyncio
    async def test_unique_violation_is_idempotent_not_404(
        self, async_client, monkeypatch
    ):
        from app.api.dependencies import get_rescue_service

        fake = self._fake_service_raising("23505")
        app.dependency_overrides[get_rescue_service] = lambda: fake
        try:
            with mock_auth():
                resp = await async_client.post("/api/rescue/any-q/abandon")
        finally:
            app.dependency_overrides.pop(get_rescue_service, None)

        assert resp.status_code == 200
        assert resp.json()["item"] is None

    @pytest.mark.asyncio
    async def test_fk_violation_maps_to_404(self, async_client):
        from app.api.dependencies import get_rescue_service

        fake = self._fake_service_raising("23503")
        app.dependency_overrides[get_rescue_service] = lambda: fake
        try:
            with mock_auth():
                resp = await async_client.post("/api/rescue/any-q/abandon")
        finally:
            app.dependency_overrides.pop(get_rescue_service, None)

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Question not found"
