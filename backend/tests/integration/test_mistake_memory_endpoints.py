"""Integration tests for mistake-memory phase 2 (Ideas #1).

Covers the two new surfaces:
  * GET  /api/mistakes/graph        - per-user error graph over submissions
  * GET  /api/reviews/due           - SM-2 cards due for review
  * POST /api/reviews/{id}/grade    - grade a review card
and the observe hook wired into POST /api/submit.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.main import app

NOW = datetime.now(timezone.utc)
USER = "test-id"
QUESTION = "test-question"


@contextmanager
def mock_auth():
    """Override auth dependency for testing (user id must exist in the DB)."""
    from app.api.auth_deps import get_current_user
    from app.models.auth_schemas import UserResponse

    async def override_get_current_user():
        return UserResponse(
            id=USER,
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
    await test_db.execute(
        text(
            "INSERT INTO users "
            "(id, username, email, hashed_password, created_at, is_active, "
            " plan, role) "
            "VALUES (:u, 'testuser', 'test@example.com', 'x', :ts, 1, "
            " 'free', 'user') ON CONFLICT (id) DO NOTHING"
        ),
        {"u": USER, "ts": NOW},
    )
    await test_db.execute(
        text(
            "INSERT INTO questions "
            "(id, title, difficulty, category, company_tags, description, "
            " starter_code, examples, test_cases, constraints, hints, is_interactive) "
            f"VALUES ('{QUESTION}', 'Mistake Q', 'easy', 'arrays', '[]', 'desc', "
            "'{}', '[]', '[]', '[]', '[]', 0)"
        )
    )
    await test_db.commit()


async def _seed_submission(
    test_db,
    *,
    sub_id: str,
    passed: bool,
    signature: str | None,
    hours_ago: int = 0,
) -> None:
    await test_db.execute(
        text(
            "INSERT INTO submissions "
            "(id, user_id, question_id, code, language, passed, error_signature,"
            " attempt_index, created_at) "
            "VALUES (:id, :u, :q, 'code', 'python', :passed, :sig, 0,"
            " :created)"
        ),
        {
            "id": sub_id,
            "u": USER,
            "q": QUESTION,
            "passed": passed,
            "sig": signature,
            "created": NOW - timedelta(hours=hours_ago),
        },
    )


async def _seed_card(
    test_db,
    *,
    card_id: str,
    state: str,
    due_in_hours: int,
    signature: str = "expected True, got False",
) -> None:
    """Insert a review card due ``due_in_hours`` from now.

    Signature defaults to a stable value; tests seeding several cards for
    the same question must pass distinct signatures (natural unique key).
    """
    await test_db.execute(
        text(
            "INSERT INTO review_cards "
            "(id, user_id, question_id, error_signature, state, ease,"
            " interval_days, repetitions, lapses, due_at, last_reviewed_at,"
            " created_at, updated_at) "
            "VALUES (:id, :u, :q, :sig, :state, 2.5, 1,"
            " 1, 0, :due, NULL, :ts, :ts)"
        ),
        {
            "id": card_id,
            "u": USER,
            "q": QUESTION,
            "sig": signature,
            "state": state,
            "due": NOW + timedelta(hours=due_in_hours),
            "ts": NOW,
        },
    )
    await test_db.commit()


def _submit_request(code: str) -> dict:
    return {
        "question_id": QUESTION,
        "code": code,
        "language": "python",
        "version": "3.10.0",
    }


@pytest.fixture
def mock_question_repo():
    class MockRepo:
        async def get_by_id(self, question_id):
            if question_id == QUESTION:
                from app.models.schemas import (
                    Difficulty,
                    Example,
                    Question,
                    StarterCode,
                    TestCase,
                )

                return Question(
                    id=QUESTION,
                    title="Mistake Q",
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
    from app.ports.code_executor import ExecutionResult, TestCaseResult

    class MockExec:
        async def execute(self, language, code, stdin="", version=None):
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
                results.append(
                    TestCaseResult(
                        index=i + 1,
                        passed=actual == expected and result.exit_code == 0,
                        input=tc["input"],
                        expected=tc["expected_output"],
                        actual=actual,
                        hidden=tc.get("hidden", False),
                    )
                )
            return results

    return MockExec()


class TestMistakesGraph:
    @pytest.mark.asyncio
    async def test_groups_failures_by_signature_with_resolution(
        self, async_client, test_db
    ):
        await _seed_user_and_question(test_db)
        # Two failures with the same signature, then a later pass on the
        # same question -> one resolved node with occurrences=2.
        await _seed_submission(
            test_db, sub_id="s1", passed=False, signature="expected True", hours_ago=3
        )
        await _seed_submission(
            test_db, sub_id="s2", passed=False, signature="expected True", hours_ago=2
        )
        await _seed_submission(
            test_db, sub_id="s3", passed=True, signature=None, hours_ago=1
        )
        await test_db.commit()

        with mock_auth():
            resp = await async_client.get("/api/mistakes/graph")

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total_signatures"] == 1
        node = data["signatures"][0]
        assert node["signature"] == "expected True"
        assert node["occurrences"] == 2
        assert node["questions"] == [QUESTION]
        assert node["resolved"] is True

    @pytest.mark.asyncio
    async def test_empty_history_returns_empty_graph(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            resp = await async_client.get("/api/mistakes/graph")

        assert resp.status_code == 200
        data = resp.json()
        assert data["signatures"] == []
        assert data["total_signatures"] == 0

    @pytest.mark.asyncio
    async def test_requires_auth(self, async_client):
        resp = await async_client.get("/api/mistakes/graph")
        assert resp.status_code in (401, 403)


class TestReviewsDue:
    @pytest.mark.asyncio
    async def test_lists_only_due_scheduled_cards(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        await _seed_card(
            test_db,
            card_id="card-due",
            state="scheduled",
            due_in_hours=-1,
            signature="sig-due",
        )
        await _seed_card(
            test_db,
            card_id="card-future",
            state="scheduled",
            due_in_hours=5,
            signature="sig-future",
        )
        await _seed_card(
            test_db,
            card_id="card-active",
            state="active",
            due_in_hours=-1,
            signature="sig-active",
        )

        with mock_auth():
            resp = await async_client.get("/api/reviews/due")

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert [c["id"] for c in data["cards"]] == ["card-due"]
        assert data["total"] == 1
        assert data["cards"][0]["error_signature"] == "sig-due"

    @pytest.mark.asyncio
    async def test_requires_auth(self, async_client):
        resp = await async_client.get("/api/reviews/due")
        assert resp.status_code in (401, 403)


class TestGradeEndpoint:
    @pytest.mark.asyncio
    async def test_grade_grows_interval_per_sm2(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        await _seed_card(
            test_db, card_id="card-grade", state="scheduled", due_in_hours=-1
        )

        with mock_auth():
            resp = await async_client.post(
                "/api/reviews/card-grade/grade", json={"quality": 4}
            )

        assert resp.status_code == 200, resp.text
        card = resp.json()["card"]
        assert card["repetitions"] == 2
        assert card["interval_days"] == 6
        assert card["state"] == "scheduled"

    @pytest.mark.asyncio
    async def test_grade_unknown_card_is_404(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        with mock_auth():
            resp = await async_client.post(
                "/api/reviews/nope/grade", json={"quality": 4}
            )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_grade_rejects_out_of_range_quality(self, async_client, test_db):
        await _seed_user_and_question(test_db)
        await _seed_card(test_db, card_id="card-q", state="scheduled", due_in_hours=-1)

        with mock_auth():
            resp = await async_client.post(
                "/api/reviews/card-q/grade", json={"quality": 9}
            )
        assert resp.status_code == 422


class TestSubmitObserveHook:
    @pytest.mark.asyncio
    async def test_failed_submit_opens_active_review_card(
        self, async_client, test_db, mock_question_repo, mock_executor
    ):
        from app.api.dependencies import get_executor, get_question_repo

        await _seed_user_and_question(test_db)
        app.dependency_overrides[get_question_repo] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            with mock_auth():
                resp = await async_client.post(
                    "/api/submit/", json=_submit_request("wrong")
                )
        finally:
            app.dependency_overrides.pop(get_question_repo, None)
            app.dependency_overrides.pop(get_executor, None)

        assert resp.status_code == 200
        assert resp.json()["passed"] is False

        rows = (
            await test_db.execute(text("SELECT state FROM review_cards"))
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "active"

    @pytest.mark.asyncio
    async def test_passing_submit_schedules_active_cards(
        self, async_client, test_db, mock_question_repo, mock_executor
    ):
        from app.api.dependencies import get_executor, get_question_repo

        await _seed_user_and_question(test_db)
        await _seed_card(test_db, card_id="card-open", state="active", due_in_hours=0)

        app.dependency_overrides[get_question_repo] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            with mock_auth():
                resp = await async_client.post(
                    "/api/submit/", json=_submit_request("ok")
                )
        finally:
            app.dependency_overrides.pop(get_question_repo, None)
            app.dependency_overrides.pop(get_executor, None)

        assert resp.status_code == 200
        assert resp.json()["passed"] is True

        row = (
            await test_db.execute(
                text(
                    "SELECT state, repetitions FROM review_cards WHERE id = 'card-open'"
                )
            )
        ).fetchone()
        assert row is not None
        assert row[0] == "scheduled"
        assert row[1] == 1
