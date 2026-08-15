"""Integration tests for submission persistence (attempt history).

A graded submit must persist a row the user can later read back via
GET /api/submissions/me — the seed of the mistake-memory data layer.
"""

import pytest

from app.main import app
from contextlib import contextmanager


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
    from datetime import datetime, timezone

    from sqlalchemy import text

    now = datetime.now(timezone.utc)
    await test_db.execute(
        text(
            "INSERT INTO users "
            "(id, username, email, hashed_password, created_at, is_active, "
            " plan, role) "
            "VALUES ('test-id', 'testuser', 'test@example.com', 'x', :ts, 1, "
            " 'free', 'user')"
        ),
        {"ts": now},
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


def _submit_request(code: str) -> dict:
    return {
        "question_id": "test-question",
        "code": code,
        "language": "python",
        "version": "3.10.0",
    }


@pytest.fixture
def mock_question_repo():
    class MockRepo:
        async def get_by_id(self, question_id):
            if question_id == "test-question":
                from app.models.schemas import (
                    Question,
                    Difficulty,
                    StarterCode,
                    TestCase,
                    Example,
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
                    test_cases=[
                        TestCase(input="1", expected_output="1", hidden=False),
                        TestCase(input="2", expected_output="2", hidden=False),
                    ],
                )
            return None

    return MockRepo()


@pytest.fixture
def mock_executor():
    from app.ports.code_executor import TestCaseResult

    class MockExec:
        async def execute(self, language, code, stdin="", version=None):
            from app.ports.code_executor import ExecutionResult

            if "wrong" in code.lower():
                return ExecutionResult(stdout="wrong\n", exit_code=0)
            return ExecutionResult(stdout=stdin + "\n", exit_code=0)

        async def evaluate_suite(self, language, code, test_cases):
            results = []
            for i, tc in enumerate(test_cases):
                result = await self.execute(
                    language=language, code=code, stdin=tc["input"]
                )
                actual = result.stdout.rstrip("\n")
                expected = tc["expected_output"].rstrip("\n")
                passed = actual == expected and result.exit_code == 0
                results.append(
                    TestCaseResult(
                        index=i + 1,
                        passed=passed,
                        input=tc["input"],
                        expected=tc["expected_output"],
                        actual=actual,
                        hidden=tc.get("hidden", False),
                    )
                )
            return results

    return MockExec()


@pytest.mark.asyncio
async def test_submit_persists_history_and_attempt_index(
    async_client, test_db, mock_question_repo, mock_executor
):
    from app.api.dependencies import (
        get_question_repo,
        get_executor,
    )

    await _seed_user_and_question(test_db)

    app.dependency_overrides[get_question_repo] = lambda: mock_question_repo
    app.dependency_overrides[get_executor] = lambda: mock_executor
    try:
        with mock_auth():
            first = await async_client.post("/api/submit/", json=_submit_request("1"))
            second = await async_client.post(
                "/api/submit/", json=_submit_request("wrong")
            )
            history = await async_client.get("/api/submissions/me")
    finally:
        app.dependency_overrides.pop(get_question_repo, None)
        app.dependency_overrides.pop(get_executor, None)

    assert first.status_code == 200
    assert first.json()["passed"] is True
    assert second.status_code == 200
    assert second.json()["passed"] is False

    assert history.status_code == 200
    data = history.json()
    assert data["total"] == 2
    # Newest first: the failing attempt came last.
    assert data["submissions"][0]["passed"] is False
    assert data["submissions"][0]["attempt_index"] == 1
    assert data["submissions"][1]["passed"] is True
    assert data["submissions"][1]["attempt_index"] == 0
    assert data["submissions"][0]["question_id"] == "test-question"
    assert data["submissions"][0]["error_signature"] is not None


@pytest.mark.asyncio
async def test_submissions_me_requires_auth(async_client, test_db):
    response = await async_client.get("/api/submissions/me")
    assert response.status_code in (401, 403)
