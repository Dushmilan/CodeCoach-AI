"""Issue #185: professor curriculum endpoint response contracts.

Shape/guard tests with stubbed dependencies (no DB): the owned-tree payload
carries the documented keys (incl. owner_id), professor creates stamp the
caller, cross-owner writes are 403 / unknown ids 404, deletes are admin-only
(403), and non-professor roles get 403 from require_professor.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.auth_deps import get_current_user
from app.api.dependencies import get_course_admin_repo
from app.models.auth_schemas import UserResponse

TREE = {
    "courses": [
        {
            "id": "prof-course-1",
            "title": "Prof Course",
            "description": "owned",
            "language": "python",
            "icon": "code",
            "order": 1,
            "owner_id": "prof-ada",
        }
    ],
    "modules": [],
    "lessons": [],
}

COURSE_KEYS = {
    "id",
    "title",
    "description",
    "language",
    "icon",
    "order",
    "owner_id",
}


class _FakeCourseAdmin:
    async def exists(self, entity_type, entity_id):
        return entity_id in ("prof-course-1", "mod-1", "les-1")

    async def get_course_tree(self, owner_id=None):
        assert owner_id == "prof-ada"
        return TREE

    async def get_course_owner(self, course_id):
        return "prof-ada" if course_id == "prof-course-1" else None

    async def get_module_course(self, module_id):
        return "prof-course-1" if module_id == "mod-1" else None

    async def get_lesson_course(self, lesson_id):
        return "prof-course-1" if lesson_id == "les-1" else None

    async def create_course(self, data):
        assert data["owner_id"] == "prof-ada"
        return {**data}

    async def update_course(self, course_id, data):
        return True

    async def create_module(self, data):
        return {**data}

    async def update_module(self, module_id, data):
        return True

    async def create_lesson(self, data):
        return {**data}

    async def update_lesson(self, lesson_id, data):
        return True

    async def delete_course(self, course_id):  # pragma: no cover
        raise AssertionError("professor must never reach delete")

    async def delete_module(self, module_id):  # pragma: no cover
        raise AssertionError("professor must never reach delete")

    async def delete_lesson(self, lesson_id):  # pragma: no cover
        raise AssertionError("professor must never reach delete")


def _user(role: str, user_id: str = "prof-ada"):
    async def _ov():
        return UserResponse(
            id=user_id,
            username=f"{role}.ada",
            email="ada@university.example",
            created_at="2025-01-01T00:00:00Z",
            is_active=True,
            role=role,
            plan="free",
        )

    return _ov


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _user("professor")
    app.dependency_overrides[get_course_admin_repo] = lambda: _FakeCourseAdmin()
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_course_admin_repo, None)


class TestProfessorContract:
    def test_tree_shape_includes_owner(self, client):
        resp = client.get("/api/professor/courses/tree")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert set(body) == {"courses", "modules", "lessons"}
        assert set(body["courses"][0]) == COURSE_KEYS

    def test_create_stamps_owner(self, client):
        resp = client.post(
            "/api/professor/courses",
            json={
                "id": "new-course",
                "title": "New",
                "description": "",
                "language": "python",
                "order": 1,
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["owner_id"] == "prof-ada"

    def test_update_unknown_course_404(self, client):
        resp = client.put("/api/professor/courses/no-such-course", json={"title": "x"})
        assert resp.status_code == 404, resp.text

    def test_update_unknown_module_404(self, client):
        resp = client.put("/api/professor/modules/no-such-mod", json={"title": "x"})
        assert resp.status_code == 404, resp.text

    def test_update_unknown_lesson_404(self, client):
        resp = client.put("/api/professor/lessons/no-such-les", json={"title": "x"})
        assert resp.status_code == 404, resp.text

    def test_deletes_are_admin_only(self, client):
        for url in (
            "/api/professor/courses/prof-course-1",
            "/api/professor/modules/mod-1",
            "/api/professor/lessons/les-1",
        ):
            resp = client.delete(url)
            assert resp.status_code == 403, url

    def test_student_forbidden(self, client):
        app.dependency_overrides[get_current_user] = _user("user", "stu-1")
        try:
            resp = client.get("/api/professor/courses/tree")
            assert resp.status_code == 403, resp.text
        finally:
            app.dependency_overrides[get_current_user] = _user("professor")

    def test_ta_forbidden(self, client):
        app.dependency_overrides[get_current_user] = _user("ta", "ta-1")
        try:
            resp = client.get("/api/professor/courses/tree")
            assert resp.status_code == 403, resp.text
        finally:
            app.dependency_overrides[get_current_user] = _user("professor")
