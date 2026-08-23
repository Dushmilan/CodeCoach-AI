"""Unit tests for SqlRescueRepository - durable rescue re-surface queue.

Persistence half of the "never-alone" rescue contract (Ideas #4): every
abandoned problem resurfaces tomorrow as a tiny re-entry step. Rows live in
the ``rescue_queue`` table; "due" is derived (status='abandoned' AND
due_at <= now) so no scheduled job is needed to flip states.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)
DUE_TOMORROW = datetime(2026, 8, 24, 9, 0, 0, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_rescue_repository import SqlRescueRepository

    return SqlRescueRepository(test_db)


async def _make_user(test_db, uid=None):
    """Create a user row (FK target) and return its id."""
    from app.models.auth_schemas import UserInDB
    from app.repositories.sql_user_repository import SqlUserRepository

    uid = uid or str(uuid.uuid4())
    await SqlUserRepository(test_db).add(
        UserInDB(
            id=uid,
            username=f"rescueuser{uid[:8]}",
            email=f"rescue{uid[:8]}@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
    )
    await test_db.commit()
    return uid


async def _make_question(test_db, qid):
    """Create a question row (FK target) and return its id."""
    from sqlalchemy import text

    await test_db.execute(
        text(
            "INSERT INTO questions "
            "(id, title, difficulty, category, company_tags, description, "
            " starter_code, examples, test_cases, constraints, hints, is_interactive) "
            "VALUES (:id, 'Rescue Q', 'easy', 'arrays', '[]', 'desc', '{}', '[]', "
            "'[]', '[]', '[]', 0)"
        ),
        {"id": qid},
    )
    await test_db.commit()
    return qid


@pytest_asyncio.fixture
async def user_id(test_db):
    return await _make_user(test_db)


@pytest_asyncio.fixture
async def question_id(test_db):
    return await _make_question(test_db, f"q-rescue-{uuid.uuid4().hex[:8]}")


class TestCreateAbandoned:
    async def test_creates_open_row_with_due_date(self, repo, user_id, question_id):
        item = await repo.create_abandoned(
            user_id=user_id,
            question_id=question_id,
            due_at=DUE_TOMORROW,
            now=NOW,
        )

        assert item.user_id == user_id
        assert item.question_id == question_id
        assert item.status == "abandoned"
        assert item.due_at == DUE_TOMORROW
        assert item.first_abandoned_at == NOW
        assert item.resurface_count == 0
        assert item.created_at == NOW
        assert item.id

    async def test_only_one_open_row_per_user_question(
        self, repo, test_db, user_id, question_id
    ):
        await repo.create_abandoned(
            user_id=user_id,
            question_id=question_id,
            due_at=DUE_TOMORROW,
            now=NOW,
        )

        # A second open row for the same (user, question) must be rejected by
        # the partial unique index - re-abandonment goes through reschedule().
        with pytest.raises(IntegrityError):
            await repo.create_abandoned(
                user_id=user_id,
                question_id=question_id,
                due_at=DUE_TOMORROW,
                now=NOW,
            )
        await test_db.rollback()


class TestListDue:
    async def test_returns_only_matured_rows_ordered_by_due_at(
        self, repo, test_db, user_id
    ):
        q_late = await _make_question(test_db, f"q-rescue-late-{uuid.uuid4().hex[:6]}")
        q_earlier = await _make_question(
            test_db, f"q-rescue-early-{uuid.uuid4().hex[:6]}"
        )
        q_future = await _make_question(
            test_db, f"q-rescue-future-{uuid.uuid4().hex[:6]}"
        )

        await repo.create_abandoned(
            user_id=user_id,
            question_id=q_future,
            due_at=NOW + timedelta(days=5),
            now=NOW,
        )
        await repo.create_abandoned(
            user_id=user_id,
            question_id=q_late,
            due_at=NOW - timedelta(hours=1),
            now=NOW,
        )
        await repo.create_abandoned(
            user_id=user_id,
            question_id=q_earlier,
            due_at=NOW - timedelta(days=2),
            now=NOW,
        )

        due = await repo.list_due(user_id=user_id, now=NOW)

        assert [i.question_id for i in due] == [q_earlier, q_late]

    async def test_excludes_other_users_rows(self, repo, test_db, user_id):
        other = await _make_user(test_db)
        q_mine = await _make_question(test_db, f"q-rescue-mine-{uuid.uuid4().hex[:6]}")
        q_theirs = await _make_question(
            test_db, f"q-rescue-theirs-{uuid.uuid4().hex[:6]}"
        )

        await repo.create_abandoned(
            user_id=user_id,
            question_id=q_mine,
            due_at=NOW - timedelta(hours=1),
            now=NOW,
        )
        await repo.create_abandoned(
            user_id=other,
            question_id=q_theirs,
            due_at=NOW - timedelta(hours=1),
            now=NOW,
        )

        due = await repo.list_due(user_id=user_id, now=NOW)

        assert [i.question_id for i in due] == [q_mine]

    @pytest.mark.parametrize("closed_status", ["completed", "dismissed"])
    async def test_closed_rows_never_surface_as_due(
        self, repo, user_id, question_id, closed_status
    ):
        await repo.create_abandoned(
            user_id=user_id,
            question_id=question_id,
            due_at=NOW - timedelta(hours=1),
            now=NOW,
        )
        await repo.close(
            user_id=user_id, question_id=question_id, status=closed_status, now=NOW
        )

        due = await repo.list_due(user_id=user_id, now=NOW)

        assert all(i.question_id != question_id for i in due)


class TestClose:
    async def test_close_transitions_open_row(self, repo, user_id, question_id):
        await repo.create_abandoned(
            user_id=user_id, question_id=question_id, due_at=DUE_TOMORROW, now=NOW
        )

        closed = await repo.close(
            user_id=user_id,
            question_id=question_id,
            status="completed",
            now=NOW + timedelta(hours=2),
        )

        assert closed is not None
        assert closed.status == "completed"

    async def test_close_without_open_row_returns_none(
        self, repo, user_id, question_id
    ):
        result = await repo.close(
            user_id=user_id, question_id=question_id, status="dismissed", now=NOW
        )

        assert result is None


class TestReschedule:
    async def test_bumps_resurface_count_and_moves_due_date(
        self, repo, user_id, question_id
    ):
        await repo.create_abandoned(
            user_id=user_id, question_id=question_id, due_at=DUE_TOMORROW, now=NOW
        )

        pushed = await repo.reschedule(
            user_id=user_id,
            question_id=question_id,
            due_at=DUE_TOMORROW + timedelta(days=1),
            now=NOW + timedelta(hours=1),
        )

        assert pushed.status == "abandoned"
        assert pushed.due_at == DUE_TOMORROW + timedelta(days=1)
        assert pushed.resurface_count == 1


class TestGet:
    async def test_get_returns_open_row(self, repo, user_id, question_id):
        assert await repo.get(user_id=user_id, question_id=question_id) is None

        await repo.create_abandoned(
            user_id=user_id, question_id=question_id, due_at=DUE_TOMORROW, now=NOW
        )

        found = await repo.get(user_id=user_id, question_id=question_id)
        assert found is not None
        assert found.status == "abandoned"


class TestLatest:
    async def test_returns_open_row_when_present(self, repo, user_id, question_id):
        await repo.create_abandoned(
            user_id=user_id, question_id=question_id, due_at=DUE_TOMORROW, now=NOW
        )

        found = await repo.latest(user_id=user_id, question_id=question_id)

        assert found is not None and found.status == "abandoned"

    async def test_returns_closed_row_when_nothing_open(
        self, repo, user_id, question_id
    ):
        await repo.create_abandoned(
            user_id=user_id, question_id=question_id, due_at=DUE_TOMORROW, now=NOW
        )
        await repo.close(
            user_id=user_id, question_id=question_id, status="dismissed", now=NOW
        )

        found = await repo.latest(user_id=user_id, question_id=question_id)

        assert found is not None and found.status == "dismissed"

    async def test_returns_none_without_any_row(self, repo, user_id, question_id):
        assert await repo.latest(user_id=user_id, question_id=question_id) is None
