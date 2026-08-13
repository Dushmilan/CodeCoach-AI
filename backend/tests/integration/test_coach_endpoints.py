"""
Integration tests for coach endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from contextlib import contextmanager

from app.main import app
from app.api.coach import get_coaching_provider
from tests.fixtures.mock_coaching_provider import MockCoachingProvider


@contextmanager
def mock_auth(
    user_id: str = "test-id",
    username: str = "testuser",
    plan: str = "premium",
):
    """Override auth dependency for testing."""
    from app.api.auth_deps import get_current_user

    async def override_get_current_user():
        from app.models.auth_schemas import UserResponse

        return UserResponse(
            id=user_id,
            username=username,
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
            plan=plan,
        )

    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def _override_coaching_provider():
    """Auto-override coaching provider for all coach tests."""
    app.dependency_overrides[get_coaching_provider] = MockCoachingProvider
    yield
    app.dependency_overrides.pop(get_coaching_provider, None)


@pytest.mark.usefixtures("test_env_vars")
class TestCoachEndpoints:
    """Test cases for coach endpoints."""

    def test_get_coaching_basic(self, test_client: TestClient, test_env_vars):
        """Test basic coaching endpoint."""
        coaching_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this the most efficient solution?",
            "mode": "review",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert data["mode"] == "review"
        assert data["language"] == "python"
        assert len(data["response"]) > 0

    @pytest.mark.usefixtures("test_env_vars")
    def test_get_coaching_with_lesson_context(
        self, test_client: TestClient, test_env_vars
    ):
        """Coaching endpoint accepts optional lesson_context field."""
        coaching_request = {
            "problem": "Write a for loop that prints 1 to 5",
            "code": "for i in range(5):\n    print(i)",
            "language": "python",
            "message": "How can I modify this to only print even numbers?",
            "mode": "hint",
            "difficulty": "easy",
            "lesson_context": "Python Lesson 4: For Loops",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["mode"] == "hint"

    def test_get_coaching_streaming(self, test_client: TestClient):
        """Test streaming coaching endpoint."""
        coaching_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this the most efficient solution?",
            "mode": "review",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/stream", json=coaching_request)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Check for SSE format
        content = response.text
        assert "data:" in content
        assert "done" in content

    @pytest.mark.usefixtures("test_env_vars")
    def test_get_coaching_streaming_with_lesson_context(
        self, test_client: TestClient, test_env_vars
    ):
        """Streaming coaching endpoint accepts optional lesson_context."""
        coaching_request = {
            "problem": "Print numbers 1 to 10",
            "code": "for i in range(10):\n    print(i)",
            "language": "python",
            "message": "How do I print only odd numbers?",
            "mode": "hint",
            "difficulty": "easy",
            "lesson_context": "Python Lesson 4: For Loops",
        }

        with mock_auth():
            response = test_client.post("/api/coach/stream", json=coaching_request)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        content = response.text
        assert "data:" in content
        assert "done" in content

    def test_get_coaching_modes(self, test_client: TestClient):
        """Test getting available coaching modes."""
        with mock_auth():
            response = test_client.get("/api/coach/modes")

        assert response.status_code == 200
        data = response.json()

        assert "modes" in data
        assert "descriptions" in data

        expected_modes = ["hint", "review", "explain", "debug", "freeform"]
        assert set(data["modes"]) == set(expected_modes)

        # Check descriptions
        descriptions = data["descriptions"]
        assert "hint" in descriptions
        assert "review" in descriptions
        assert "explain" in descriptions
        assert "debug" in descriptions

    def test_get_supported_languages(self, test_client: TestClient):
        """Test getting supported programming languages."""
        with mock_auth():
            response = test_client.get("/api/coach/languages")

        assert response.status_code == 200
        data = response.json()

        assert "languages" in data
        assert "descriptions" in data

        expected_languages = ["python"]
        assert set(data["languages"]) >= set(expected_languages)

    def test_coaching_invalid_language(self, test_client: TestClient):
        """Test coaching with invalid language."""
        coaching_request = {
            "problem": "Test problem",
            "code": "test code",
            "language": "invalid_language",
            "message": "test message",
            "mode": "hint",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)

        assert response.status_code == 422  # Validation error

    def test_coaching_invalid_mode(self, test_client: TestClient):
        """Test coaching with invalid mode."""
        coaching_request = {
            "problem": "Test problem",
            "code": "test code",
            "language": "python",
            "message": "test message",
            "mode": "invalid_mode",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)

        assert response.status_code == 422  # Validation error

    def test_coaching_missing_required_fields(self, test_client: TestClient):
        """Test coaching with missing required fields."""
        # Missing problem
        coaching_request = {
            "code": "test code",
            "language": "python",
            "message": "test message",
            "mode": "hint",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 422

        # Missing code
        coaching_request = {
            "problem": "Test problem",
            "language": "python",
            "message": "test message",
            "mode": "hint",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 422

    def test_coaching_all_modes(self, test_client: TestClient):
        """Test coaching with all available modes."""
        base_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Please provide guidance",
            "difficulty": "easy",
        }

        modes = ["hint", "review", "explain", "debug"]

        for mode in modes:
            request = {**base_request, "mode": mode}
            with mock_auth():
                response = test_client.post("/api/coach/", json=request)

            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == mode
            assert len(data["response"]) > 0

    def test_coaching_python(self, test_client: TestClient):
        """Test coaching with Python."""
        base_request = {
            "problem": "Find the maximum element in an array",
            "message": "Please provide guidance",
            "mode": "hint",
            "difficulty": "easy",
        }

        code = "def solution(arr):\n    return max(arr)"

        request = {**base_request, "language": "python", "code": code}

        with mock_auth():
            response = test_client.post("/api/coach/", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "python"
        assert len(data["response"]) > 0

    def test_coaching_boundary_conditions(self, test_client: TestClient):
        """Test coaching with boundary conditions."""
        # Very long problem description
        long_problem = "x" * 1000
        coaching_request = {
            "problem": long_problem,
            "code": "def test(): pass",
            "language": "python",
            "message": "short",
            "mode": "hint",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 200

        # Very long code
        long_code = "x" * 2000
        coaching_request = {
            "problem": "Test problem",
            "code": long_code,
            "language": "python",
            "message": "short",
            "mode": "hint",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 200

    def test_coaching_empty_strings(self, test_client: TestClient):
        """Test coaching with empty strings."""
        coaching_request = {
            "problem": "",
            "code": "",
            "language": "python",
            "message": "",
            "mode": "hint",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 200  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_coaching_async(self, async_client):
        """Test coaching with async client."""
        coaching_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this the most efficient solution?",
            "mode": "review",
            "difficulty": "easy",
        }

        from app.api.auth_deps import require_premium, get_current_user
        from app.models.auth_schemas import UserResponse

        async def override_auth_user():
            return UserResponse(
                id="test-id",
                username="testuser",
                email="test@example.com",
                is_active=True,
                created_at="2025-01-01T00:00:00Z",
                plan="premium",
            )

        app.dependency_overrides[get_current_user] = override_auth_user
        app.dependency_overrides[require_premium] = override_auth_user
        try:
            response = await async_client.post("/api/coach/", json=coaching_request)
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(require_premium, None)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["mode"] == "review"

    def test_coaching_response_format(self, test_client: TestClient):
        """Test coaching response format consistency."""
        coaching_request = {
            "problem": "Test problem",
            "code": "def test(): pass",
            "language": "python",
            "message": "Test message",
            "mode": "hint",
            "difficulty": "easy",
        }

        with mock_auth():
            response = test_client.post("/api/coach/", json=coaching_request)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        required_fields = ["response", "mode", "language"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_coaching_error_handling(self, test_client: TestClient):
        """Test coaching error handling."""
        # Test invalid JSON
        with mock_auth():
            response = test_client.post("/api/coach/", data="invalid json")
        assert response.status_code in [401, 422]

        # Test with wrong HTTP method
        response = test_client.get("/api/coach/")
        assert response.status_code == 405

        response = test_client.put("/api/coach/")
        assert response.status_code == 405

        response = test_client.delete("/api/coach/")
        assert response.status_code == 405


@pytest.mark.usefixtures("test_env_vars")
class TestAnimateEndpoint:
    """The /api/coach/animate endpoint returns a visual animation only.

    This is the dedicated endpoint behind the standalone Animate viewer: it
    must return a validated animation script and never a chat/coaching text
    response.
    """

    def _animate_request(self) -> dict:
        return {
            "problem": "Find the target value in an array using linear search",
            "code": "def search(arr, target):\n    for i, v in enumerate(arr):\n        if v == target:\n            return i\n    return -1",
            "language": "python",
            "difficulty": "easy",
            "initial_code": "def search(arr, target):\n    pass",
        }

    def test_animate_returns_valid_animation(
        self, test_client: TestClient, test_env_vars
    ):
        with mock_auth():
            response = test_client.post(
                "/api/coach/animate", json=self._animate_request()
            )

        assert response.status_code == 200
        data = response.json()

        assert "animation" in data
        animation = data["animation"]
        assert "title" in animation
        assert "steps" in animation and len(animation["steps"]) > 0
        assert "shapes" in animation["steps"][0]
        assert "motion" in animation["steps"][0]
        # Never a chat response
        assert "response" not in data
        assert "summary" not in data

    def test_animate_rejects_missing_animation(
        self, test_client: TestClient, test_env_vars, monkeypatch
    ):
        from tests.fixtures.mock_coaching_provider import MockCoachingProvider

        class NoAnimationProvider(MockCoachingProvider):
            async def get_animation_script(self, *args, **kwargs):
                return None

        from app.api.coach import get_coaching_provider

        app.dependency_overrides[get_coaching_provider] = NoAnimationProvider
        try:
            with mock_auth():
                response = test_client.post(
                    "/api/coach/animate", json=self._animate_request()
                )
        finally:
            app.dependency_overrides.pop(get_coaching_provider, None)

        assert response.status_code == 502

    def test_animate_invalid_language_422(self, test_client: TestClient, test_env_vars):
        request = self._animate_request()
        request["language"] = "invalid_language"
        with mock_auth():
            response = test_client.post("/api/coach/animate", json=request)
        assert response.status_code == 422

    def test_animate_missing_required_fields_422(
        self, test_client: TestClient, test_env_vars
    ):
        with mock_auth():
            response = test_client.post(
                "/api/coach/animate", json={"problem": "x", "language": "python"}
            )
        assert response.status_code == 422

    def test_animate_free_user_gets_403(self, test_client: TestClient, test_env_vars):
        with mock_auth(plan="free"):
            response = test_client.post(
                "/api/coach/animate", json=self._animate_request()
            )
        assert response.status_code == 403

    def test_animate_usage_headers_set(self, test_client: TestClient, test_env_vars):
        with mock_auth():
            response = test_client.post(
                "/api/coach/animate", json=self._animate_request()
            )
        assert response.status_code == 200
        assert response.headers.get("x-usage-remaining-input") is not None


@pytest.mark.usefixtures("test_env_vars")
class TestCoachPremiumGating:
    """Premium gate on coach endpoints: free users are rejected, premium pass."""

    def _coaching_request(self) -> dict:
        return {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this efficient?",
            "mode": "review",
            "difficulty": "easy",
        }

    def test_free_user_gets_403_on_coach(self, test_client: TestClient, test_env_vars):
        with mock_auth(plan="free"):
            response = test_client.post("/api/coach/", json=self._coaching_request())

        assert response.status_code == 403
        assert "premium" in response.json()["detail"].lower()

    def test_premium_user_gets_200_on_coach(
        self, test_client: TestClient, test_env_vars
    ):
        with mock_auth(plan="premium"):
            response = test_client.post("/api/coach/", json=self._coaching_request())

        assert response.status_code == 200
        assert "response" in response.json()

    def test_free_user_gets_403_on_stream(self, test_client: TestClient, test_env_vars):
        with mock_auth(plan="free"):
            response = test_client.post(
                "/api/coach/stream", json=self._coaching_request()
            )

        assert response.status_code == 403

    def test_free_user_gets_403_on_modes(self, test_client: TestClient, test_env_vars):
        with mock_auth(plan="free"):
            response = test_client.get("/api/coach/modes")

        assert response.status_code == 403

    def test_free_user_gets_403_on_languages(
        self, test_client: TestClient, test_env_vars
    ):
        with mock_auth(plan="free"):
            response = test_client.get("/api/coach/languages")

        assert response.status_code == 403
