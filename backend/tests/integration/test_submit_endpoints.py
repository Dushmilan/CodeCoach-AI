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
    class MockExec:
        async def execute(self, language, code, stdin="", version=None):
            from app.ports.code_executor import ExecutionResult
            if "error" in code.lower():
                return ExecutionResult(stderr="SyntaxError", exit_code=1)
            if "wrong" in code.lower():
                return ExecutionResult(stdout="wrong\n", exit_code=0)
            return ExecutionResult(stdout=stdin + "\n", exit_code=0)

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
