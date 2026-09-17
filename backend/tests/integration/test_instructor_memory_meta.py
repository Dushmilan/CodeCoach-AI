"""Integration tests for instructor/memory/workspace-meta surfaces (Issue #202).

A2: GET /api/instructor/class-analytics — instructor gate, empty roster,
    out-of-scope roster denied, student denied.
A3: GET /api/memory/graph — shape for a fresh user, auth required.
A4: GET /api/workspace/meta/{id} — defaults, save_code round-trip via
    PUT /code/{id}, per-user isolation. (Needs Redis; skipped otherwise.)
"""

import os
import uuid
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.main import app
from app.api.auth_deps import get_current_user
from app.api.dependencies import get_redis_cache
from app.models.auth_schemas import UserResponse
from app.services.redis_service import RedisCache
from tests.fixtures.auth_helpers import aregister_headers


def _identity(user_id: str, role: str):
    return SimpleNamespace(id=user_id, username=f"stub_{role}", role=role)


@contextmanager
def _stub_identity(user_id: str, role: str):
    async def _override():
        return _identity(user_id, role)

    app.dependency_overrides[get_current_user] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _user_response(user_id: str, username: str, role: str = "user") -> UserResponse:
    return UserResponse(
        id=user_id,
        username=username,
        email=f"{username}@test.com",
        role=role,
        is_active=True,
        created_at="2025-01-01T00:00:00Z",
    )


class TestClassAnalytics:
    @pytest.mark.asyncio
    async def test_empty_roster_returns_zeros(self, async_client):
        with _stub_identity("prof-a2", "professor"):
            res = await async_client.get("/api/instructor/class-analytics")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["total_students"] == 0
        assert data["students"] == []

    @pytest.mark.asyncio
    async def test_out_of_scope_roster_denied(self, async_client):
        # Professor owns no rooms here, so any roster id is out of scope.
        with _stub_identity("prof-a2", "professor"):
            res = await async_client.get(
                "/api/instructor/class-analytics?user_ids=foreign-student-1"
            )
        assert res.status_code == 403, res.text
        assert "authorized" in res.text.lower()

    @pytest.mark.asyncio
    async def test_student_denied(self, async_client):
        _, headers = await aregister_headers(async_client, "a2_student_plain")
        res = await async_client.get("/api/instructor/class-analytics", headers=headers)
        assert res.status_code == 403, res.text

    @pytest.mark.asyncio
    async def test_ta_identity_allowed_empty(self, async_client):
        with _stub_identity("ta-a2", "ta"):
            res = await async_client.get("/api/instructor/class-analytics")
        assert res.status_code == 200, res.text

    @pytest.mark.asyncio
    async def test_anonymous_denied(self, async_client):
        res = await async_client.get("/api/instructor/class-analytics")
        assert res.status_code in (401, 403), res.text


class TestMemoryGraph:
    @pytest.mark.asyncio
    async def test_fresh_user_empty_graph(self, async_client):
        user_id, _ = await aregister_headers(async_client, "a3_memory_fresh")

        async def _override():
            return _user_response(user_id, "a3_memory_fresh")

        app.dependency_overrides[get_current_user] = _override
        try:
            res = await async_client.get("/api/memory/graph")
        finally:
            app.dependency_overrides.pop(get_current_user, None)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["topics"] == []
        assert data["totalDue"] == 0
        assert data["totalCards"] == 0

    @pytest.mark.asyncio
    async def test_requires_auth(self, async_client):
        res = await async_client.get("/api/memory/graph")
        assert res.status_code in (401, 403), res.text


def _redis_available() -> bool:
    import socket
    from urllib.parse import urlparse

    url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    parts = urlparse(url)
    try:
        with socket.create_connection((parts.hostname, parts.port or 6379), timeout=2):
            return True
    except OSError:
        return False


@contextmanager
def _live_redis_cache():
    """Wire the workspace service to a real Redis (test instance)."""
    cache = RedisCache(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
    app.dependency_overrides[get_redis_cache] = lambda: cache
    try:
        yield cache
    finally:
        app.dependency_overrides.pop(get_redis_cache, None)


def _qid() -> str:
    return f"a4meta-q-{uuid.uuid4().hex[:10]}"


@pytest.mark.skipif(not _redis_available(), reason="Redis unavailable")
class TestWorkspaceMeta:
    @pytest.mark.asyncio
    async def test_unknown_question_returns_defaults(self, async_client):
        user_id, _ = await aregister_headers(async_client, "a4meta_fresh")

        async def _override():
            return _user_response(user_id, "a4meta_fresh")

        app.dependency_overrides[get_current_user] = _override
        try:
            res = await async_client.get("/api/workspace/meta/q-never-touched")
        finally:
            app.dependency_overrides.pop(get_current_user, None)
        assert res.status_code == 200, res.text
        assert res.json() == {
            "question_id": "q-never-touched",
            "language": None,
            "last_opened_at": None,
        }

    @pytest.mark.asyncio
    async def test_save_code_round_trips_meta(self, async_client):
        user_id, _ = await aregister_headers(async_client, "a4meta_roundtrip")
        qid = _qid()

        async def _override():
            return _user_response(user_id, "a4meta_roundtrip")

        app.dependency_overrides[get_current_user] = _override
        try:
            with _live_redis_cache():
                res = await async_client.put(
                    f"/api/workspace/code/{qid}",
                    json={"language": "python", "code": "print('hi')"},
                )
                assert res.status_code == 204, res.text
                res = await async_client.get(f"/api/workspace/meta/{qid}")
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["question_id"] == qid
            assert data["language"] == "python"
            assert data["last_opened_at"]
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_meta_isolated_per_user(self, async_client):
        user_a, _ = await aregister_headers(async_client, "a4meta_user_a")
        user_b, _ = await aregister_headers(async_client, "a4meta_user_b")
        qid = _qid()

        async def _override_a():
            return _user_response(user_a, "a4meta_user_a")

        async def _override_b():
            return _user_response(user_b, "a4meta_user_b")

        app.dependency_overrides[get_current_user] = _override_a
        try:
            with _live_redis_cache():
                res = await async_client.put(
                    f"/api/workspace/code/{qid}",
                    json={"language": "java", "code": "class A {}"},
                )
                assert res.status_code == 204, res.text
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        app.dependency_overrides[get_current_user] = _override_b
        try:
            with _live_redis_cache():
                res = await async_client.get(f"/api/workspace/meta/{qid}")
        finally:
            app.dependency_overrides.pop(get_current_user, None)
        assert res.status_code == 200, res.text
        assert res.json()["language"] is None

    @pytest.mark.asyncio
    async def test_requires_auth(self, async_client):
        res = await async_client.get("/api/workspace/meta/anything")
        assert res.status_code in (401, 403), res.text
