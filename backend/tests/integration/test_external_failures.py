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


@contextmanager
def dead_postgres_override():
    """Override the DB session dependency with a Postgres outage simulator."""
    from app.core.database import get_db
    from sqlalchemy.exc import OperationalError

    async def _dead_db():
        raise OperationalError("SELECT 1", None, ConnectionError("connection refused"))

    app.dependency_overrides[get_db] = _dead_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


def _assert_sanitized_500(response) -> None:
    """A DB outage must surface as JSON 500 with no driver internals."""
    assert response.status_code == 500
    body = response.text
    for marker in ("asyncpg", "sqlalchemy", "Traceback", "connection refused"):
        assert marker.lower() not in body.lower(), f"leaked {marker!r}: {body[:200]}"


class TestPostgresOutage:
    """Hot paths must fail closed with sanitized 500s when Postgres is down."""

    def test_public_catalog_returns_sanitized_500_when_postgres_down(
        self, test_client: TestClient
    ):
        # Unhandled DB errors escape the route: read the true client-visible
        # 500 instead of re-raising in-process.
        with TestClient(app, raise_server_exceptions=False) as raw_client:
            with dead_postgres_override():
                response = raw_client.get("/api/courses/")

        _assert_sanitized_500(response)

    def test_login_returns_sanitized_500_when_postgres_down(
        self, test_client: TestClient
    ):
        with TestClient(app, raise_server_exceptions=False) as raw_client:
            with dead_postgres_override():
                response = raw_client.post(
                    "/api/auth/login",
                    json={"username": "nobody", "password": "wrong"},
                )

        # Fail closed: a DB outage must never read as 401 "bad credentials".
        _assert_sanitized_500(response)


def _raw_client() -> TestClient:
    """Non-following client: surfaces 307s instead of chasing them."""
    return TestClient(app, raise_server_exceptions=False, follow_redirects=False)


class TestNoSlashRootParity:
    """Same-origin rewrites may strip trailing slashes (observed: the
    Next /api rewrite forwards ``/api/run/`` as ``/api/run``). Root
    routes must answer with and without the slash — never 307 to an
    absolute backend URL (browsers follow it cross-origin and CSP
    ``connect-src 'self'`` kills the request: "Failed to fetch").

    questions/courses/progress already carry dual ``""``/``"/"`` routes;
    run/submit/coach/health must match that convention.
    """

    def test_run_no_slash_routes(self):
        with _raw_client() as client:
            response = client.post(
                "/api/run",
                json={"language": "python", "code": "print(1)"},
            )
        assert response.status_code != 307, response.headers.get("location")
        assert response.status_code == 401

    def test_submit_no_slash_routes(self):
        with _raw_client() as client:
            response = client.post(
                "/api/submit",
                json={"question_id": "two-sum", "language": "python", "code": "x"},
            )
        assert response.status_code != 307, response.headers.get("location")
        assert response.status_code == 401

    def test_coach_no_slash_routes(self):
        with _raw_client() as client:
            response = client.post(
                "/api/coach",
                json={"problem": "x", "code": "y", "language": "python"},
            )
        assert response.status_code != 307, response.headers.get("location")
        assert response.status_code in (401, 422)

    def test_health_no_slash(self):
        with _raw_client() as client:
            response = client.get("/health")
        assert response.status_code != 307, response.headers.get("location")
        assert response.status_code == 200
