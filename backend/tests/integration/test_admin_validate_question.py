"""Tests for the admin question-validation endpoint (was a stub).

Verifies the endpoint now runs the real validation pipeline and returns
honest results instead of always claiming "All test cases passed".
"""

from app.main import app
from app.api.dependencies import get_question_admin_repo, get_executor


class _StubNotFound:
    async def get_question_by_id(self, question_id):
        return None


class _StubQuestion:
    async def get_question_by_id(self, question_id):
        return {
            "id": question_id,
            "title": "Two Sum",
            "difficulty": "easy",
            "category": "arrays",
            "company_tags": [],
            "description": "Find two numbers that sum to target.",
            "starter_code": {"python": "def two_sum(nums, target):\n    pass"},
            "examples": [
                {"input": "[2, 7, 11, 15], 9", "output": "[0, 1]", "explanation": ""}
            ],
            "test_cases": [
                {
                    "input": "[2, 7, 11, 15], 9",
                    "expected_output": "[0, 1]",
                    "hidden": False,
                }
            ],
            "hints": [],
            "solution": None,
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "constraints": ["2 <= nums.length <= 10^4"],
        }


class TestAdminQuestionValidation:
    def test_validate_question_not_found(self, test_client, admin_headers):
        app.dependency_overrides[get_question_admin_repo] = lambda: _StubNotFound()
        try:
            res = test_client.post(
                "/api/admin/questions/validate/nonexistent", headers=admin_headers
            )
            assert res.status_code == 404
        finally:
            app.dependency_overrides.pop(get_question_admin_repo, None)

    def test_validate_question_runs_real_pipeline(
        self, test_client, admin_headers, mock_piston_service
    ):
        app.dependency_overrides[get_question_admin_repo] = lambda: _StubQuestion()
        app.dependency_overrides[get_executor] = lambda: mock_piston_service()
        try:
            res = test_client.post(
                "/api/admin/questions/validate/test-q", headers=admin_headers
            )
            assert res.status_code == 200
            data = res.json()
            assert data["question_id"] == "test-q"
            assert "valid" in data
            assert "total_issues" in data
            assert "results" in data
        finally:
            app.dependency_overrides.pop(get_question_admin_repo, None)
            app.dependency_overrides.pop(get_executor, None)
