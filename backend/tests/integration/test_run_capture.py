"""Integration tests: free runs are Redis-only (#264) and never touch
Postgres — no attempt history, no review cards, on any surface.

The learn surface is accepted for API symmetry; the learn/problem
persistence boundary lives on /api/submit/.
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from app.main import app

USER = "test-id"
QUESTION = "test-question"


@contextmanager
def mock_auth():
    from app.api.auth_deps import get_current_user
    from app.models.auth_schemas import UserResponse

    async def override_get_current_user():
        return UserResponse(
            id=USER,
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def _seed_user_and_question(test_db):
    await test_db.execute(
        text(
            "INSERT INTO users "
            "(id, username, email, hashed_password, created_at, is_active, "
            " role) "
            "VALUES (:u, 'testuser', 'test@example.com', 'x', :ts, 1, "
            " 'user') ON CONFLICT (id) DO NOTHING"
        ),
        {"u": USER, "ts": datetime.now(timezone.utc)},
    )
    await test_db.execute(
        text(
            "INSERT INTO questions "
            "(id, title, difficulty, category, company_tags, description, "
            " starter_code, examples, test_cases, constraints, hints, is_interactive) "
            f"VALUES ('{QUESTION}', 'Run Capture Q', 'easy', 'arrays', '[]', 'desc', "
            "'{}', '[]', '[]', '[]', '[]', 0)"
        )
    )
    await test_db.commit()


@pytest.fixture
def crashing_executor():
    from app.ports.code_executor import ExecutionResult

    class MockExec:
        async def execute(self, language, code, stdin="", version=None):
            return ExecutionResult(
                stdout="",
                stderr="ZeroDivisionError: division by zero",
                exit_code=1,
            )

    return MockExec()


@pytest.fixture
def healthy_executor():
    from app.ports.code_executor import ExecutionResult

    class MockExec:
        async def execute(self, language, code, stdin="", version=None):
            return ExecutionResult(stdout="ok", stderr="", exit_code=0)

    return MockExec()


def _override_executor(mock_exec):
    from app.api.dependencies import get_executor

    app.dependency_overrides[get_executor] = lambda: mock_exec


def _clear_executor():
    from app.api.dependencies import get_executor

    app.dependency_overrides.pop(get_executor, None)


def _run_body(question_id=None):
    body = {"language": "python", "code": "1/0", "stdin": ""}
    if question_id is not None:
        body["question_id"] = question_id
    return body


@pytest.mark.asyncio
async def test_crashed_run_with_question_persists_nothing_redis_only(
    async_client, test_db, crashing_executor
):
    """Free runs never touch Postgres (#264), even with question context."""
    await _seed_user_and_question(test_db)
    _override_executor(crashing_executor)
    try:
        with mock_auth():
            resp = await async_client.post("/api/run/", json=_run_body(QUESTION))
    finally:
        _clear_executor()

    assert resp.status_code == 200
    assert resp.json()["exit_code"] == 1

    subs = (
        await test_db.execute(text("SELECT COUNT(*) FROM submissions"))
    ).scalar_one()
    cards = (
        await test_db.execute(text("SELECT COUNT(*) FROM review_cards"))
    ).scalar_one()
    assert subs == 0 and cards == 0


@pytest.mark.asyncio
async def test_crashed_run_learn_surface_captures_nothing(
    async_client, test_db, crashing_executor
):
    """Learn surface runs persist nothing (free runs are Redis-only)."""
    await _seed_user_and_question(test_db)
    _override_executor(crashing_executor)
    try:
        with mock_auth():
            resp = await async_client.post(
                "/api/run/",
                json={**_run_body(QUESTION), "surface": "learn"},
            )
    finally:
        _clear_executor()

    assert resp.status_code == 200
    subs = (
        await test_db.execute(text("SELECT COUNT(*) FROM submissions"))
    ).scalar_one()
    cards = (
        await test_db.execute(text("SELECT COUNT(*) FROM review_cards"))
    ).scalar_one()
    assert subs == 0 and cards == 0


@pytest.mark.asyncio
async def test_successful_run_captures_nothing(async_client, test_db, healthy_executor):
    await _seed_user_and_question(test_db)
    _override_executor(healthy_executor)
    try:
        with mock_auth():
            resp = await async_client.post("/api/run/", json=_run_body(QUESTION))
    finally:
        _clear_executor()

    assert resp.status_code == 200
    subs = (
        await test_db.execute(text("SELECT COUNT(*) FROM submissions"))
    ).scalar_one()
    cards = (
        await test_db.execute(text("SELECT COUNT(*) FROM review_cards"))
    ).scalar_one()
    assert subs == 0 and cards == 0


@pytest.mark.asyncio
async def test_crashed_run_without_question_context_captures_nothing(
    async_client, test_db, crashing_executor
):
    await _seed_user_and_question(test_db)
    _override_executor(crashing_executor)
    try:
        with mock_auth():
            resp = await async_client.post("/api/run/", json=_run_body(None))
    finally:
        _clear_executor()

    assert resp.status_code == 200
    subs = (
        await test_db.execute(text("SELECT COUNT(*) FROM submissions"))
    ).scalar_one()
    assert subs == 0


@pytest.mark.asyncio
async def test_run_requires_auth(async_client):
    resp = await async_client.post("/api/run/", json=_run_body())
    assert resp.status_code in (401, 403)
