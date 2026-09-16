"""Issue #159 Task 5: instructor classroom endpoint response contracts.

Shape-only tests with stubbed dependencies (no DB): the list/detail payloads
must carry exactly the documented keys, and ClassAnalyticsResponse must stay
byte-identical (total_students, avg_completion, avg_solved, students).
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.auth_deps import get_current_user
from app.api.dependencies import (
    get_class_analytics_service,
    get_classroom_repository,
)
from app.models.analytics_schemas import ClassAnalyticsResponse, ClassStudentSummary
from app.models.auth_schemas import UserResponse
from app.services.class_analytics_service import ClassroomNotFoundError

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
            username="ada.student",
            completed_lessons=6,
            completion_pct=60.0,
            attempted=2,
            solved=1,
        )
    ],
)

ROOM_KEYS = {"id", "course_id", "owner_id", "name", "invite_code", "term", "schedule"}
ANALYTICS_KEYS = {"total_students", "avg_completion", "avg_solved", "students"}
STUDENT_KEYS = {
    "user_id",
    "username",
    "completed_lessons",
    "completion_pct",
    "attempted",
    "solved",
}

# Issue #176: legacy class-analytics roster scoping. Only "s1" belongs to
# prof-ada's room; "outsider" belongs to nobody in scope.
OWNED_STUDENT_IDS = ["s1"]


class _FakeClassrooms:
    async def list_owned_by_professor(self, owner_id: str):
        return [ROOM] if owner_id == ROOM.owner_id else []

    async def list_for_ta(self, user_id: str):
        return [ROOM] if user_id == "ta-turing" else []

    async def list_classroom_student_ids(self, classroom_id: str):
        return list(OWNED_STUDENT_IDS) if classroom_id == ROOM.id else []


class _FakeAnalytics:
    async def get_classroom(self, classroom_id, *, classrooms=None):
        return ROOM if classroom_id == ROOM.id else None

    async def classroom_overview(
        self, classroom_id, *, total_lessons=10, classrooms=None
    ):
        if classroom_id != ROOM.id:
            raise ClassroomNotFoundError(classroom_id)
        return ROOM, OVERVIEW

    async def class_overview(self, roster, *, total_lessons=10):
        return OVERVIEW


def _professor():
    async def _ov():
        return UserResponse(
            id="prof-ada",
            username="professor.ada",
            email="ada@university.example",
            created_at="2025-01-01T00:00:00Z",
            is_active=True,
            role="professor",
            plan="free",
        )

    return _ov


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _professor()
    app.dependency_overrides[get_classroom_repository] = lambda: _FakeClassrooms()
    app.dependency_overrides[get_class_analytics_service] = lambda: _FakeAnalytics()
    try:
        with TestClient(app) as c:
            yield c
    finally:
        for dep in (
            get_current_user,
            get_classroom_repository,
            get_class_analytics_service,
        ):
            app.dependency_overrides.pop(dep, None)


class TestInstructorClassroomContract:
    def test_list_shape(self, client):
        resp = client.get("/api/instructor/classrooms")
        assert resp.status_code == 200, resp.text
        rooms = resp.json()
        assert len(rooms) == 1
        assert set(rooms[0]) == ROOM_KEYS
        assert rooms[0]["invite_code"] == "CS101-A-2026"

    def test_detail_shape(self, client):
        resp = client.get(f"/api/instructor/classrooms/{ROOM.id}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert set(body) == {"classroom", "analytics"}
        assert set(body["classroom"]) == ROOM_KEYS
        assert set(body["analytics"]) == ANALYTICS_KEYS
        assert set(body["analytics"]["students"][0]) == STUDENT_KEYS

    def test_detail_unknown_id_is_404(self, client):
        resp = client.get("/api/instructor/classrooms/no-such-room")
        assert resp.status_code == 404, resp.text


class TestLegacyClassAnalyticsScoping:
    """Issue #176: legacy CSV roster must be ownership-scoped (shape + guard)."""

    def test_owned_roster_returns_200_with_contract_shape(self, client):
        resp = client.get("/api/instructor/class-analytics", params={"user_ids": "s1"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert set(body) == ANALYTICS_KEYS
        assert set(body["students"][0]) == STUDENT_KEYS

    def test_non_owned_roster_is_forbidden(self, client):
        resp = client.get(
            "/api/instructor/class-analytics", params={"user_ids": "outsider"}
        )
        assert resp.status_code == 403, resp.text

    def test_non_owner_professor_is_forbidden(self):
        async def _other():
            return UserResponse(
                id="prof-mallory",
                username="professor.mallory",
                email="mallory@university.example",
                created_at="2025-01-01T00:00:00Z",
                is_active=True,
                role="professor",
                plan="free",
            )

        app.dependency_overrides[get_current_user] = _other
        app.dependency_overrides[get_classroom_repository] = lambda: _FakeClassrooms()
        app.dependency_overrides[get_class_analytics_service] = lambda: _FakeAnalytics()
        try:
            with TestClient(app) as c:
                resp = c.get(
                    "/api/instructor/class-analytics", params={"user_ids": "s1"}
                )
        finally:
            for dep in (
                get_current_user,
                get_classroom_repository,
                get_class_analytics_service,
            ):
                app.dependency_overrides.pop(dep, None)
        assert resp.status_code == 403, resp.text

    def test_empty_roster_returns_200_empty_body(self, client):
        resp = client.get("/api/instructor/class-analytics", params={"user_ids": ""})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_students"] == 0
        assert body["students"] == []
