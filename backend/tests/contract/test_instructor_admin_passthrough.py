"""Issue #178: admin passthrough on instructor classroom detail.

Admins sit above professors in the hierarchy — an admin must be able to open
any classroom detail (room + analytics) without owning the room. Regression:
``classroom_detail`` currently treats admin like a professor and 403s when
``room.owner_id != admin.id``.
"""

from fastapi.testclient import TestClient

from app.api.auth_deps import get_current_user
from app.api.dependencies import (
    get_class_analytics_service,
    get_classroom_repository,
)
from app.main import app
from app.models.analytics_schemas import ClassAnalyticsResponse, ClassStudentSummary
from app.models.auth_schemas import UserResponse
from types import SimpleNamespace


ROOM = SimpleNamespace(
    id="room-1",
    course_id="python-fundamentals",
    owner_id="prof-ada",
    name="CS101 · Section A",
    invite_code="CS101-A-2026",
    term="Fall 2026",
    schedule="Mon/Wed 10:00",
)

OVERVIEW = ClassAnalyticsResponse(
    total_students=1,
    avg_completion=60.0,
    avg_solved=1.0,
    students=[
        ClassStudentSummary(
            user_id="s1",
            completed_lessons=6,
            completion_pct=60.0,
            attempted=2,
            solved=1,
        )
    ],
)


class _FakeClassrooms:
    async def get_classroom(self, classroom_id, *, classrooms=None):  # noqa: ARG002
        return None

    async def list_owned_by_professor(self, owner_id: str):
        return [ROOM] if owner_id == ROOM.owner_id else []

    async def list_for_ta(self, user_id: str):  # noqa: ARG002
        return []


class _FakeAnalytics:
    async def course_lesson_counts(self, course_ids, courses=None):  # noqa: ARG002
        return {}

    async def get_classroom(self, classroom_id, *, classrooms=None):  # noqa: ARG002
        return ROOM if classroom_id == ROOM.id else None

    async def classroom_overview(
        self,
        classroom_id,
        *,
        total_lessons=10,
        classrooms=None,  # noqa: ARG002
    ):
        return ROOM, OVERVIEW


def _admin():
    async def _ov():
        return UserResponse(
            id="admin-1",
            username="admin",
            email="admin@university.example",
            created_at="2025-01-01T00:00:00Z",
            is_active=True,
            role="admin",
            plan="free",
        )

    return _ov


def test_admin_can_open_unowned_classroom_detail():
    app.dependency_overrides[get_current_user] = _admin()
    app.dependency_overrides[get_classroom_repository] = lambda: _FakeClassrooms()
    app.dependency_overrides[get_class_analytics_service] = lambda: _FakeAnalytics()
    try:
        with TestClient(app) as c:
            resp = c.get(f"/api/instructor/classrooms/{ROOM.id}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["classroom"]["id"] == ROOM.id
        assert body["classroom"]["invite_code"] == "CS101-A-2026"
    finally:
        for dep in (
            get_current_user,
            get_classroom_repository,
            get_class_analytics_service,
        ):
            app.dependency_overrides.pop(dep, None)
