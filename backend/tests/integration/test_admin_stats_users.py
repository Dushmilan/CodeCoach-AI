"""Integration tests for admin stats/user-management surfaces (Issue #202, A1).

Covers GET /stats, /stats/users, /users (+search/pagination), /users/{id},
PATCH /users/{id} (super-admin gate, role validation, persistence),
GET /check-id, and GET /groq/status. Auth paths use real registered users;
privileged paths stub only the identity dependency so writes hit the real DB.
"""

from types import SimpleNamespace

import pytest

from app.main import app
from app.api.auth_deps import (
    get_current_user,
    require_admin,
    require_course_editor,
    require_super_admin,
)
from tests.fixtures.auth_helpers import aregister_headers


def _stub_admin():
    return SimpleNamespace(id="admin-stub", username="stub_admin", role="admin")


def _stub_super_admin():
    return SimpleNamespace(id="super-stub", username="stub_super", role="super_admin")


def _stub_professor():
    return SimpleNamespace(id="prof-stub", username="stub_prof", role="professor")


class TestAdminStats:
    @pytest.mark.asyncio
    async def test_stats_shape(self, async_client):
        app.dependency_overrides[require_admin] = _stub_admin
        try:
            res = await async_client.get("/api/admin/stats")
            assert res.status_code == 200, res.text
            data = res.json()
            for key in ("users", "questions", "courses", "system", "generation"):
                assert key in data, f"missing stats section: {key}"
            assert data["users"]["total"] >= 0
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_user_stats_counts_consistent(self, async_client):
        await aregister_headers(async_client, "a1stat_alpha")
        await aregister_headers(async_client, "a1stat_beta")
        app.dependency_overrides[require_admin] = _stub_admin
        try:
            res = await async_client.get("/api/admin/stats/users")
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["total"] >= 2
            assert data["total"] == data["active"] + data["inactive"]
            assert data["admin"] >= 0
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_stats_forbidden_for_student(self, async_client):
        _, headers = await aregister_headers(async_client, "a1stat_student")
        res = await async_client.get("/api/admin/stats", headers=headers)
        assert res.status_code == 403, res.text


class TestAdminUserManagement:
    @pytest.mark.asyncio
    async def test_list_users_search_and_pagination(self, async_client):
        await aregister_headers(async_client, "a1list_zedone")
        await aregister_headers(async_client, "a1list_zedtwo")
        app.dependency_overrides[require_admin] = _stub_admin
        try:
            res = await async_client.get("/api/admin/users?search=a1list_zed")
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["total"] >= 2
            assert all("a1list_zed" in u["username"] for u in data["users"]), data[
                "users"
            ]
            assert data["page"] == 1
            assert data["pages"] >= 1

            res = await async_client.get("/api/admin/users?page=1&per_page=1")
            assert res.status_code == 200, res.text
            assert len(res.json()["users"]) == 1
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_user_detail_and_404(self, async_client):
        user_id, _ = await aregister_headers(async_client, "a1detail_who")
        app.dependency_overrides[require_admin] = _stub_admin
        try:
            res = await async_client.get(f"/api/admin/users/{user_id}")
            assert res.status_code == 200, res.text
            assert res.json()["username"] == "a1detail_who"

            res = await async_client.get("/api/admin/users/does-not-exist")
            assert res.status_code == 404, res.text
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_patch_role_persists(self, async_client):
        user_id, _ = await aregister_headers(async_client, "a1patch_target")
        app.dependency_overrides[require_super_admin] = _stub_super_admin
        app.dependency_overrides[require_admin] = _stub_admin
        try:
            res = await async_client.patch(
                f"/api/admin/users/{user_id}", json={"role": "professor"}
            )
            assert res.status_code == 200, res.text

            res = await async_client.get(f"/api/admin/users/{user_id}")
            assert res.status_code == 200, res.text
            assert res.json()["role"] == "professor"
        finally:
            app.dependency_overrides.pop(require_super_admin, None)
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_patch_invalid_role_400(self, async_client):
        user_id, _ = await aregister_headers(async_client, "a1patch_badrole")
        app.dependency_overrides[require_super_admin] = _stub_super_admin
        try:
            res = await async_client.patch(
                f"/api/admin/users/{user_id}", json={"role": "wizard"}
            )
            assert res.status_code == 400, res.text
        finally:
            app.dependency_overrides.pop(require_super_admin, None)

    @pytest.mark.asyncio
    async def test_patch_unknown_user_404(self, async_client):
        app.dependency_overrides[require_super_admin] = _stub_super_admin
        try:
            res = await async_client.patch(
                "/api/admin/users/does-not-exist", json={"role": "ta"}
            )
            assert res.status_code == 404, res.text
        finally:
            app.dependency_overrides.pop(require_super_admin, None)

    @pytest.mark.asyncio
    async def test_patch_forbidden_for_admin_and_student(self, async_client):
        user_id, _ = await aregister_headers(async_client, "a1patch_victim")
        _, student_headers = await aregister_headers(async_client, "a1patch_plain")
        # Real student token: must be 403 (super-admin only).
        res = await async_client.patch(
            f"/api/admin/users/{user_id}", json={"role": "ta"}, headers=student_headers
        )
        assert res.status_code == 403, res.text
        # Real admin identity (non-super) must also be 403: stub only the
        # inner get_current_user so the real require_super_admin guard runs.
        app.dependency_overrides[get_current_user] = _stub_admin
        try:
            res = await async_client.patch(
                f"/api/admin/users/{user_id}", json={"role": "ta"}
            )
            assert res.status_code == 403, res.text
        finally:
            app.dependency_overrides.pop(get_current_user, None)


class TestAdminCheckId:
    @pytest.mark.asyncio
    async def test_unknown_id_reports_missing(self, async_client):
        app.dependency_overrides[require_course_editor] = _stub_professor
        try:
            res = await async_client.get(
                "/api/admin/check-id?entity_type=course&entity_id=no-such-course"
            )
            assert res.status_code == 200, res.text
            assert res.json() == {"exists": False}
        finally:
            app.dependency_overrides.pop(require_course_editor, None)

    @pytest.mark.asyncio
    async def test_student_denied(self, async_client):
        _, headers = await aregister_headers(async_client, "a1check_student")
        res = await async_client.get(
            "/api/admin/check-id?entity_type=course&entity_id=x", headers=headers
        )
        assert res.status_code == 403, res.text


class TestAdminGroqStatus:
    @pytest.mark.asyncio
    async def test_status_diagnostic_shape(self, async_client):
        app.dependency_overrides[require_admin] = _stub_admin
        try:
            res = await async_client.get("/api/admin/groq/status")
            assert res.status_code == 200, res.text
            data = res.json()
            for key in ("valid", "models", "model_count", "error"):
                assert key in data, f"missing groq status key: {key}"
            assert isinstance(data["models"], list)
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_status_forbidden_for_student(self, async_client):
        _, headers = await aregister_headers(async_client, "a1groq_student")
        res = await async_client.get("/api/admin/groq/status", headers=headers)
        assert res.status_code == 403, res.text
