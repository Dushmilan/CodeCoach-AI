"""Integration tests for adapter-state audit endpoints.

Covers GET /api/coach/interactions, GET /api/run/jobs and
GET /api/submissions/{id} — the read side of sent/submitted/failed
persistence. All routes require auth and are scoped to the caller.
"""

from contextlib import contextmanager

import pytest

from app.main import app


@contextmanager
def mock_auth(user_id="test-id"):
    from app.api.auth_deps import get_current_user
    from app.models.auth_schemas import UserResponse

    async def override_get_current_user():
        return UserResponse(
            id=user_id,
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


async def _seed_user_and_question(test_db, user_id="test-id"):
    from datetime import datetime, timezone

    from sqlalchemy import text

    now = datetime.now(timezone.utc)
    await test_db.execute(
        text(
            "INSERT INTO users "
            "(id, username, email, hashed_password, created_at, is_active, "
            " plan, role) "
            "VALUES (:uid, 'testuser', 'test@example.com', 'x', :ts, 1, "
            " 'free', 'user')"
        ),
        {"uid": user_id, "ts": now},
    )
    await test_db.execute(
        text(
            "INSERT INTO questions "
            "(id, title, difficulty, category, company_tags, description, "
            " starter_code, examples, test_cases, constraints, hints, is_interactive) "
            "VALUES ('test-question', 'Test', 'easy', 'arrays', '[]', 'desc', "
            " '{}', '[]', '[]', '[]', '[]', 0)"
        )
    )
    await test_db.commit()


@pytest.fixture
def mock_provider():
    from tests.fixtures.mock_coaching_provider import MockCoachingProvider

    return MockCoachingProvider()


@pytest.mark.asyncio
async def test_coach_interactions_audit_lists_own_rows(
    async_client, test_db, mock_provider
):
    import uuid

    from app.api.coach import get_coaching_provider
    from app.repositories.sql_coaching_interaction_repository import (
        SqlCoachingInteractionRepository,
    )

    await _seed_user_and_question(test_db)
    repo = SqlCoachingInteractionRepository(test_db)
    row = await repo.create_sent(
        user_id="test-id",
        question_id="test-question",
        mode="hint",
        language="python",
        problem_hash="ph",
        code_hash="ch",
        idempotency_key=f"idem-{uuid.uuid4().hex}",
        request_payload={"mode": "hint"},
    )
    assert row.status == "sent"

    app.dependency_overrides[get_coaching_provider] = lambda: mock_provider
    try:
        with mock_auth():
            response = await async_client.get("/api/coach/interactions?limit=10")
    finally:
        app.dependency_overrides.pop(get_coaching_provider, None)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(i["id"] == row.id for i in data["interactions"])
    assert all(i["user_id"] == "test-id" for i in data["interactions"])


@pytest.mark.asyncio
async def test_run_jobs_audit_and_submission_status(
    async_client, test_db, mock_provider
):
    import uuid

    from app.api.coach import get_coaching_provider
    from app.api.dependencies import get_question_repo
    from app.repositories.sql_execution_job_repository import (
        SqlExecutionJobRepository,
    )

    await _seed_user_and_question(test_db)

    class MockRepo:
        async def get_by_id(self, question_id):
            if question_id == "test-question":
                from app.models.schemas import (
                    Difficulty,
                    Example,
                    Question,
                    StarterCode,
                    TestCase,
                )

                return Question(
                    id="test-question",
                    title="Test",
                    difficulty=Difficulty.EASY,
                    category="arrays",
                    description="Test",
                    starter=StarterCode(
                        python="def solve():\n    pass",
                        javascript="function solve() {}",
                        java="class Solution { public static void solve() {} }",
                    ),
                    examples=[Example(input="1", output="1")],
                    test_cases=[TestCase(input="1", expected_output="1", hidden=False)],
                )
            return None

    class MockExec:
        async def execute(self, language, code, stdin="", version=None):
            from app.ports.code_executor import ExecutionResult

            return ExecutionResult(stdout="ok\n", exit_code=0)

        async def evaluate_suite(self, language, code, test_cases):
            from app.ports.code_executor import TestCaseResult

            return [
                TestCaseResult(
                    index=1,
                    passed=True,
                    input="1",
                    expected="1",
                    actual="1",
                    hidden=False,
                )
            ]

        async def get_runtimes(self):
            return []

    from app.api.dependencies import get_executor

    app.dependency_overrides[get_question_repo] = lambda: MockRepo()
    app.dependency_overrides[get_executor] = lambda: MockExec()
    app.dependency_overrides[get_coaching_provider] = lambda: mock_provider
    try:
        with mock_auth():
            # Generate one coaching row + one graded submission via the API.
            coach = await async_client.post(
                "/api/coach/",
                json={
                    "problem": "Add one",
                    "code": "def solve():\n    pass",
                    "language": "python",
                    "message": "hint?",
                    "mode": "hint",
                    "difficulty": "easy",
                },
            )
            assert coach.status_code == 200
            submit = await async_client.post(
                "/api/submit/",
                json={
                    "question_id": "test-question",
                    "code": "x",
                    "language": "python",
                },
            )
            assert submit.status_code == 200
            # Seed one execution job directly (run uses live Piston here).
            jobs = SqlExecutionJobRepository(test_db)
            job = await jobs.create_sent(
                user_id="test-id",
                question_id="test-question",
                language="python",
                code_hash="ch",
                idempotency_key=f"idem-{uuid.uuid4().hex}",
                request_payload={},
            )
            got_jobs = await async_client.get("/api/run/jobs?limit=10")
            history = await async_client.get("/api/submissions/me?limit=10")
    finally:
        app.dependency_overrides.pop(get_question_repo, None)
        app.dependency_overrides.pop(get_executor, None)
        app.dependency_overrides.pop(get_coaching_provider, None)

    assert got_jobs.status_code == 200
    assert any(j["id"] == job.id for j in got_jobs.json()["jobs"])
    assert history.status_code == 200
    sub_id = history.json()["submissions"][0]["id"]
    with mock_auth():
        one = await async_client.get(f"/api/submissions/{sub_id}")
    assert one.status_code == 200
    assert one.json()["status"] == "graded"


@pytest.mark.asyncio
async def test_audit_endpoints_require_auth(async_client, test_db):
    for path in (
        "/api/coach/interactions",
        "/api/run/jobs",
        "/api/submissions/me",
    ):
        response = await async_client.get(path)
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_submission_status_missing_returns_404(async_client, test_db):
    await _seed_user_and_question(test_db)
    with mock_auth():
        response = await async_client.get("/api/submissions/does-not-exist")
    assert response.status_code == 404
