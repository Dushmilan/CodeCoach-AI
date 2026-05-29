import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def mock_question_repo():
    class MockRepo:
        async def get_by_id(self, question_id):
            if question_id == "test-question":
                from app.models.schemas import Question, Difficulty, StarterCode, TestCase, Example
                return Question(
                    id="test-question",
                    title="Test",
                    difficulty=Difficulty.EASY,
                    category="arrays",
                    description="Test",
                    starter=StarterCode(python="def solve():\n    pass", javascript="function solve() {}", java="class Solution { public static void solve() {} }"),
                    examples=[Example(input="1", output="1")],
                    test_cases=[
                        TestCase(input="1", expected_output="1", hidden=False),
                        TestCase(input="2", expected_output="2", hidden=False),
                        TestCase(input="3", expected_output="3", hidden=True),
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
            if "error" in code.lower():
                return ExecutionResult(stderr="SyntaxError", exit_code=1)
            if "wrong" in code.lower():
                return ExecutionResult(stdout="wrong\n", exit_code=0)
            return ExecutionResult(stdout=stdin + "\n", exit_code=0)

        async def evaluate_suite(self, language, code, test_cases):
            results = []
            for i, tc in enumerate(test_cases):
                result = await self.execute(language=language, code=code, stdin=tc["input"])
                actual = result.stdout.rstrip("\n")
                expected = tc["expected_output"].rstrip("\n")
                passed = actual == expected and result.exit_code == 0
                hidden = tc.get("hidden", False)
                results.append(TestCaseResult(
                    index=i + 1,
                    passed=passed,
                    input="" if hidden else tc["input"],
                    expected="" if hidden else tc["expected_output"],
                    actual="" if hidden else actual,
                    hidden=hidden,
                ))
            return results

    return MockExec()


class TestSubmitEndpoint:
    def test_submit_all_pass(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor

        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question",
                "language": "python",
                "code": "print(input())",
            })

            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is True
            assert data["total"] == 3
            assert data["passed_count"] == 3
            assert len(data["results"]) == 3

            for r in data["results"]:
                assert r["passed"] is True

            assert data["results"][0]["hidden"] is False
            assert data["results"][0]["input"] == "1"
            assert data["results"][2]["hidden"] is True
            assert data["results"][2]["input"] == ""
        finally:
            app.dependency_overrides.clear()

    def test_submit_partial_pass(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor

        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question",
                "language": "python",
                "code": "print('wrong')",
            })

            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is False
            assert data["total"] == 3
            assert data["passed_count"] == 0
        finally:
            app.dependency_overrides.clear()

    def test_submit_question_not_found(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor

        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "nonexistent",
                "language": "python",
                "code": "print('hi')",
            })

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_submit_code_error_handling(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor

        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question",
                "language": "python",
                "code": "print('error')",
            })

            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is False
            for r in data["results"]:
                assert r["passed"] is False
        finally:
            app.dependency_overrides.clear()

    # ── Validation & Error paths ────────────────────────────────────────

    @pytest.fixture
    def mock_question_repo_single(self):
        class MockRepo:
            async def get_by_id(self, question_id):
                if question_id == "single-tc":
                    from app.models.schemas import Question, Difficulty, StarterCode, TestCase, Example
                    return Question(
                        id="single-tc", title="Single", difficulty=Difficulty.EASY,
                        category="arrays", description="Test",
                        starter=StarterCode(python="def solve():\n    pass"),
                        examples=[Example(input="1", output="1")],
                        test_cases=[TestCase(input="1", expected_output="1", hidden=False)],
                    )
                return None
        return MockRepo()

    @pytest.fixture
    def mock_question_repo_empty(self):
        class MockRepo:
            async def get_by_id(self, question_id):
                if question_id == "empty-tc":
                    from app.models.schemas import Question, Difficulty, StarterCode, Example
                    return Question(
                        id="empty-tc", title="Empty", difficulty=Difficulty.EASY,
                        category="arrays", description="Test",
                        starter=StarterCode(python="def solve():\n    pass"),
                        examples=[Example(input="1", output="1")],
                        test_cases=[],
                    )
                return None
        return MockRepo()

    # ── 422 Validation tests ────────────────────────────────────────────

    def test_submit_invalid_json_body(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", data="not json")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_submit_missing_question_id(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={"language": "python", "code": "x"})
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_submit_missing_code(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={"question_id": "test-question", "language": "python"})
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_submit_invalid_language_enum(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "brainfuck", "code": "x",
            })
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    # ── Executor exception handling ─────────────────────────────────────

    def test_submit_executor_generic_exception(self, test_client, mock_question_repo):
        from app.api.submit import get_repository, get_executor
        class FailingExec:
            async def evaluate_suite(self, language, code, test_cases):
                raise RuntimeError("Piston unreachable")
            async def execute(self, language, code, stdin="", version=None):
                raise RuntimeError("fail")
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: FailingExec()
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "python", "code": "x",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is False
            assert data["total"] == 0
            assert data["results"] == []
        finally:
            app.dependency_overrides.clear()

    def test_submit_executor_http_exception(self, test_client, mock_question_repo):
        from app.api.submit import get_repository, get_executor
        from fastapi import HTTPException
        class FailingExec:
            async def evaluate_suite(self, language, code, test_cases):
                raise HTTPException(status_code=502, detail="Bad Gateway")
            async def execute(self, language, code, stdin="", version=None):
                raise HTTPException(502, "Bad Gateway")
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: FailingExec()
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "python", "code": "x",
            })
            assert response.status_code == 502
        finally:
            app.dependency_overrides.clear()

    # ── Response shape tests ────────────────────────────────────────────

    def test_submit_response_all_fields_present(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "python", "code": "pass",
            })
            assert response.status_code == 200
            data = response.json()
            assert "passed" in data
            assert "total" in data
            assert "passed_count" in data
            assert "results" in data
            for r in data["results"]:
                assert "index" in r
                assert "passed" in r
                assert "input" in r
                assert "expected" in r
                assert "actual" in r
                assert "hidden" in r
        finally:
            app.dependency_overrides.clear()

    def test_submit_response_content_type(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "python", "code": "pass",
            })
            assert response.headers["content-type"] == "application/json"
        finally:
            app.dependency_overrides.clear()

    # ── Multi-language tests ────────────────────────────────────────────

    def test_submit_javascript(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "javascript", "code": "function solve() { return 1; }",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is True
        finally:
            app.dependency_overrides.clear()

    def test_submit_java(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "java", "code": "class S { public static void solve() {} }",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is True
        finally:
            app.dependency_overrides.clear()

    # ── Empty and single test case ──────────────────────────────────────

    def test_submit_empty_test_cases(self, test_client, mock_question_repo_empty, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo_empty
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "empty-tc", "language": "python", "code": "pass",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["passed"] is False
            assert data["results"] == []
        finally:
            app.dependency_overrides.clear()

    def test_submit_single_test_case(self, test_client, mock_question_repo_single, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo_single
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "single-tc", "language": "python", "code": "x",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["passed_count"] == 1
        finally:
            app.dependency_overrides.clear()

    # ── Edge cases ──────────────────────────────────────────────────────

    def test_submit_wrong_http_methods(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            assert test_client.get("/api/submit/").status_code == 405
            assert test_client.put("/api/submit/", json={}).status_code == 405
            assert test_client.delete("/api/submit/").status_code == 405
        finally:
            app.dependency_overrides.clear()

    def test_submit_empty_code_string(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "python", "code": "",
            })
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_submit_unicode_in_code(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "python",
                "code": "# ©ñßência\nprint('héllo')",
            })
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_submit_very_long_code(self, test_client, mock_question_repo, mock_executor):
        from app.api.submit import get_repository, get_executor
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            long_code = "def f():\n    return " + "x" * 10_000
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question", "language": "python", "code": long_code,
            })
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
