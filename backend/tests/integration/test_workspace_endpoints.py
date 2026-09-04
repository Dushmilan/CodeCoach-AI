"""Integration tests for workspace persistence endpoints (/api/workspace).

Covers the Redis-backed draft-code / last-visited / chat-history API:
auth gating, save/fetch/delete round-trips, per-user isolation, empty
states, validation boundaries, and graceful degradation when Redis is
unavailable.
"""

import os
import uuid
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_redis_cache
from app.main import app
from app.models.auth_schemas import UserResponse
from app.services.redis_service import RedisCache

_TEST_REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")


def _redis_available() -> bool:
    import socket
    from urllib.parse import urlparse

    parts = urlparse(_TEST_REDIS_URL)
    try:
        with socket.create_connection((parts.hostname, parts.port or 6379), timeout=2):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _redis_available(), reason="Redis unavailable — skipping workspace API tests"
)


def _user(user_id: str, username: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        username=username,
        email=f"{username}@test.com",
        is_active=True,
        created_at="2025-01-01T00:00:00Z",
    )


@contextmanager
def mock_auth(user_id: str = "ws-user-1", username: str = "wsuser1"):
    """Override auth dependency for testing."""

    async def override_get_current_user():
        return _user(user_id, username)

    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@contextmanager
def live_redis_cache():
    """Wire the workspace service to a real Redis (test instance)."""
    cache = RedisCache(_TEST_REDIS_URL)
    app.dependency_overrides[get_redis_cache] = lambda: cache
    try:
        yield cache
    finally:
        app.dependency_overrides.pop(get_redis_cache, None)


def _qid() -> str:
    return f"ws-q-{uuid.uuid4().hex[:12]}"


class TestWorkspaceAuth:
    def test_put_code_requires_auth(self, test_client: TestClient):
        res = test_client.put(
            "/api/workspace/code/some-q",
            json={"language": "python", "code": "print(1)"},
        )
        assert res.status_code in (401, 403)

    def test_get_code_requires_auth(self, test_client: TestClient):
        res = test_client.get("/api/workspace/code/some-q?language=python")
        assert res.status_code in (401, 403)

    def test_last_visited_requires_auth(self, test_client: TestClient):
        res = test_client.get("/api/workspace/last-visited")
        assert res.status_code in (401, 403)


class TestWorkspaceCodeRoundTrip:
    def test_get_code_empty_before_put(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            res = test_client.get(f"/api/workspace/code/{qid}?language=python")
        assert res.status_code == 200
        data = res.json()
        assert data["code"] == ""
        assert data["question_id"] == qid
        assert data["updated_at"] is None

    def test_put_and_get_code(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            put = test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "def solve():\n    return 42"},
            )
            assert put.status_code == 204
            res = test_client.get(f"/api/workspace/code/{qid}?language=python")
        assert res.status_code == 200
        data = res.json()
        assert data["code"] == "def solve():\n    return 42"
        assert data["language"] == "python"
        assert data["question_id"] == qid
        assert data["updated_at"]

    def test_put_overwrites_previous_code(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "v1"},
            )
            test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "v2"},
            )
            res = test_client.get(f"/api/workspace/code/{qid}?language=python")
        assert res.json()["code"] == "v2"

    def test_delete_code(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "temp"},
            )
            delete = test_client.delete(f"/api/workspace/code/{qid}?language=python")
            assert delete.status_code == 204
            res = test_client.get(f"/api/workspace/code/{qid}?language=python")
        assert res.json()["code"] == ""

    def test_code_isolated_per_user(self, test_client: TestClient):
        qid = _qid()
        with mock_auth("ws-user-1", "wsuser1"), live_redis_cache():
            test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "user1-secret"},
            )
        with mock_auth("ws-user-2", "wsuser2"), live_redis_cache():
            res = test_client.get(f"/api/workspace/code/{qid}?language=python")
        assert res.status_code == 200
        assert res.json()["code"] == ""

    def test_code_isolated_per_language(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "py-code"},
            )
            res = test_client.get(f"/api/workspace/code/{qid}?language=javascript")
        assert res.json()["code"] == ""


class TestWorkspaceValidation:
    def test_put_code_too_large_rejected(self, test_client: TestClient):
        with mock_auth(), live_redis_cache():
            res = test_client.put(
                "/api/workspace/code/big-q",
                json={"language": "python", "code": "x" * 51201},
            )
        assert res.status_code == 422

    def test_put_code_at_max_size_accepted(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            res = test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "x" * 51200},
            )
        assert res.status_code == 204

    def test_get_code_missing_language_rejected(self, test_client: TestClient):
        with mock_auth(), live_redis_cache():
            res = test_client.get("/api/workspace/code/some-q")
        assert res.status_code == 422

    def test_put_code_missing_fields_rejected(self, test_client: TestClient):
        with mock_auth(), live_redis_cache():
            res = test_client.put(
                "/api/workspace/code/some-q", json={"language": "python"}
            )
        assert res.status_code == 422


class TestWorkspaceLastVisited:
    def test_last_visited_empty_initially(self, test_client: TestClient):
        with (
            mock_auth(f"ws-fresh-{uuid.uuid4().hex[:8]}", "wsfresh"),
            live_redis_cache(),
        ):
            res = test_client.get("/api/workspace/last-visited")
        assert res.status_code == 200
        assert res.json() is None

    def test_get_code_records_last_visited(self, test_client: TestClient):
        user = f"ws-lv-{uuid.uuid4().hex[:8]}"
        qid = _qid()
        with mock_auth(user, user), live_redis_cache():
            test_client.put(
                f"/api/workspace/code/{qid}",
                json={"language": "python", "code": "x = 1"},
            )
            test_client.get(f"/api/workspace/code/{qid}?language=python")
            res = test_client.get("/api/workspace/last-visited")
        assert res.status_code == 200
        data = res.json()
        assert data["question_id"] == qid


class TestWorkspaceChat:
    def test_get_chat_empty_initially(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            res = test_client.get(f"/api/workspace/chat/{qid}")
        assert res.status_code == 200
        assert res.json()["messages"] == []
        assert res.json()["question_id"] == qid

    def test_delete_chat_returns_204(self, test_client: TestClient):
        qid = _qid()
        with mock_auth(), live_redis_cache():
            res = test_client.delete(f"/api/workspace/chat/{qid}")
        assert res.status_code == 204


class TestWorkspaceDegraded:
    def test_put_code_without_redis_still_204(self, test_client: TestClient):
        """Without Redis the API degrades to a no-op instead of 5xx."""

        async def _no_cache():
            return None

        app.dependency_overrides[get_redis_cache] = _no_cache
        try:
            with mock_auth():
                res = test_client.put(
                    "/api/workspace/code/any-q",
                    json={"language": "python", "code": "x = 1"},
                )
            assert res.status_code == 204
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)

    def test_get_code_without_redis_returns_empty(self, test_client: TestClient):
        async def _no_cache():
            return None

        app.dependency_overrides[get_redis_cache] = _no_cache
        try:
            with mock_auth():
                res = test_client.get("/api/workspace/code/any-q?language=python")
            assert res.status_code == 200
            assert res.json()["code"] == ""
        finally:
            app.dependency_overrides.pop(get_redis_cache, None)
