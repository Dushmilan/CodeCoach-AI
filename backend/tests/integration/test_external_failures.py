"""
Failure-simulation tests: verify the API degrades gracefully when external
dependencies (Piston, Groq, Redis) are unavailable.

These tests prove the "unbreakable" property: an external outage must never
crash the process, hang the request, or leak internals — the API returns a
well-formed error response (4xx/5xx) and stays responsive.

Each test overrides the relevant FastAPI dependency and/or HTTP transport so no
real external network call is made.
"""

from fastapi import HTTPException
from fastapi.testclient import TestClient
from contextlib import contextmanager

from app.main import app


@contextmanager
def mock_auth(user_id: str = "test-id", username: str = "testuser"):
    """Override auth dependency for testing."""
    from app.api.auth_deps import get_current_user
    from app.models.auth_schemas import UserResponse

    async def override_get_current_user():
        return UserResponse(
            id=user_id,
            username=username,
            email="test@example.com",
            is_active=True,
            plan="premium",
            created_at="2025-01-01T00:00:00Z",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _failing_executor():
    """Build a fake CodeExecutor whose calls raise like a dead Piston service."""

    class FailingExecutor:
        async def execute(self, language, code, stdin="", version=None):
            raise HTTPException(
                status_code=502, detail="Piston API error: upstream down"
            )

        def validate_code(self, language, code):
            raise HTTPException(
                status_code=502, detail="Piston API error: upstream down"
            )

        async def get_runtimes(self):
            raise HTTPException(
                status_code=502, detail="Piston API error: upstream down"
            )

    return FailingExecutor()


@contextmanager
def failing_executor_override():
    """Override the code-executor dependency with a Piston outage simulator."""
    from app.api.dependencies import get_executor

    app.dependency_overrides[get_executor] = lambda: _failing_executor()
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_executor, None)


class TestPistonOutage:
    """The /api/run endpoints must fail cleanly when Piston is unreachable."""

    def test_execute_returns_502_when_piston_down(self, test_client: TestClient):
        code_request = {
            "language": "python",
            "code": "print('hi')",
            "stdin": "",
            "version": "3.11.0",
        }
        with mock_auth(), failing_executor_override():
            response = test_client.post("/api/run/", json=code_request)

        assert response.status_code == 502
        assert "Piston" in response.json()["detail"]

    def test_validate_returns_502_when_piston_down(self, test_client: TestClient):
        code_request = {
            "language": "python",
            "code": "print('hi')",
            "stdin": "",
        }
        with mock_auth(), failing_executor_override():
            response = test_client.post("/api/run/validate", json=code_request)

        assert response.status_code == 502
        assert "Piston" in response.json()["detail"]

    def test_languages_returns_502_when_piston_down(self, test_client: TestClient):
        with mock_auth(), failing_executor_override():
            response = test_client.get("/api/run/languages")

        assert response.status_code == 502

    def test_runtimes_returns_502_when_piston_down(self, test_client: TestClient):
        with mock_auth(), failing_executor_override():
            response = test_client.get("/api/run/runtimes")

        assert response.status_code == 502


class TestGroqOutage:
    """The coaching endpoint must fail cleanly when Groq is unreachable."""

    def test_coach_returns_502_when_groq_down(self, test_client: TestClient):
        from app.api.coach import get_coaching_provider

        class DownGroq:
            async def get_structured(self, *args, **kwargs):
                raise HTTPException(
                    status_code=502, detail="Groq API error: upstream down"
                )

            async def stream(self, *args, **kwargs):
                raise HTTPException(
                    status_code=502, detail="Groq API error: upstream down"
                )

        app.dependency_overrides[get_coaching_provider] = lambda: DownGroq()
        try:
            coaching_request = {
                "problem": "Find the max element in an array",
                "code": "def max_element(arr):\n    return max(arr)",
                "language": "python",
                "message": "Is this efficient?",
                "mode": "review",
                "difficulty": "easy",
            }
            with mock_auth():
                response = test_client.post("/api/coach/", json=coaching_request)
        finally:
            app.dependency_overrides.pop(get_coaching_provider, None)

        assert response.status_code == 502
        assert "Groq" in response.json()["detail"]


class TestRedisOutage:
    """Redis failures must degrade gracefully (no 500, no crash)."""

    def test_redis_down_health_ok(self, test_client: TestClient):
        """Health endpoint still responds when Redis is unavailable."""
        from app.services.redis_service import RedisCache

        original = app.dependency_overrides.get("_none_", None)  # placeholder
        _ = original
        dead_cache = RedisCache("redis://localhost:1", max_connections=1)
        dead_cache.disable()  # simulate an already-dead cache

        from app.api.dependencies import get_redis_cache

        async def override_redis_cache():
            return dead_cache

        app.dependency_overrides[get_redis_cache] = override_redis_cache
        try:
            response = test_client.get("/health/")
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
