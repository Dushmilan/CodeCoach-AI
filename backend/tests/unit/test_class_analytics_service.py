"""Read-only class analytics over existing data (Issue #159, phase 2).

No new tracking tables for MVP: aggregates submissions + course progress
that already exist per student.
"""

import asyncio
from datetime import datetime, timezone

from app.models.course_schemas import CourseProgress
from app.models.orm import ClassroomORM
from app.ports.classroom_repository import ClassroomRepository
from app.services.class_analytics_service import (
    ClassAnalyticsService,
    ClassroomNotFoundError,
)


class FakeSubmissions:
    def __init__(self, by_user):
        self._by_user = by_user

    async def list_by_user(self, user_id, limit=1000):
        return self._by_user.get(user_id, [])[:limit]


class FakeProgress:
    def __init__(self, by_user):
        self._by_user = by_user

    async def get_all_progress(self, user_id):
        completed = self._by_user.get(user_id, [])
        if not completed:
            return []
        return [
            CourseProgress(
                user_id=user_id,
                course_id="course-1",
                completed_lessons=completed,
            )
        ]


def _sub(passed):
    from app.models.submission_schemas import Submission

    return Submission(
        id=f"s-{passed}-{id(object())}",
        user_id="u",
        question_id="two-sum",
        code="c",
        language="python",
        passed=passed,
        attempt_index=0,
        created_at=datetime.now(timezone.utc),
    )


def test_class_overview_aggregates_per_student():
    subs = FakeSubmissions(
        {
            "s1": [_sub(True), _sub(False)],
            "s2": [_sub(False)],
        }
    )
    progress = FakeProgress(
        {
            "s1": ["l1", "l2", "l3", "l4", "l5", "l6"],
            "s2": ["l1", "l2"],
        }
    )
    svc = ClassAnalyticsService(submissions=subs, progress=progress)
    resp = asyncio.run(svc.class_overview(["s1", "s2"], total_lessons=10))
    assert resp.total_students == 2
    assert len(resp.students) == 2
    by_id = {s.user_id: s for s in resp.students}
    assert by_id["s1"].solved == 1
    assert by_id["s1"].attempted == 2
    assert by_id["s1"].completion_pct == 60.0
    assert resp.avg_completion == 40.0
    assert resp.avg_solved == 0.5


def test_empty_roster_returns_zeroes():
    svc = ClassAnalyticsService(
        submissions=FakeSubmissions({}), progress=FakeProgress({})
    )
    resp = asyncio.run(svc.class_overview([]))
    assert resp.total_students == 0
    assert resp.students == []
    assert resp.avg_completion == 0.0


class StubClassrooms(ClassroomRepository):
    """Port-only double: deliberately exposes no `session` attribute, so any
    service reach-through to the SQL implementation fails loudly."""

    def __init__(self, rooms, students_by_room):
        assert not hasattr(self, "session")
        self._rooms = rooms
        self._students = students_by_room

    async def create_classroom(self, **kwargs):
        raise NotImplementedError

    async def list_owned_by_professor(self, owner_id: str):
        raise NotImplementedError

    async def list_for_ta(self, user_id: str):
        raise NotImplementedError

    async def enroll(self, **kwargs):
        raise NotImplementedError

    async def set_course_owner(self, course_id: str, owner_id: str) -> None:
        raise NotImplementedError

    async def get_classroom_by_id(self, classroom_id: str):
        return self._rooms.get(classroom_id)

    async def list_classroom_student_ids(self, classroom_id: str):
        return list(self._students.get(classroom_id, []))

    async def list_classroom_ta_ids(self, classroom_id: str):
        return []


def _stub_service():
    rooms = {
        "room-1": ClassroomORM(
            id="room-1",
            course_id="course-1",
            owner_id="prof-1",
            name="CS101",
            invite_code="CS101-A-2026",
        )
    }
    subs = FakeSubmissions({"s1": [_sub(True), _sub(False)], "s2": [_sub(False)]})
    progress = FakeProgress({"s1": ["l1", "l2", "l3", "l4", "l5", "l6"], "s2": ["l1"]})
    classrooms = StubClassrooms(rooms, {"room-1": ["s1", "s2"]})
    svc = ClassAnalyticsService(
        submissions=subs, progress=progress, classrooms=classrooms
    )
    return svc, classrooms


def test_classroom_overview_uses_port_only():
    svc, classrooms = _stub_service()
    assert not hasattr(classrooms, "session")
    room, resp = asyncio.run(svc.classroom_overview("room-1"))
    assert room.id == "room-1"
    assert room.invite_code == "CS101-A-2026"
    assert resp.total_students == 2
    assert {s.user_id for s in resp.students} == {"s1", "s2"}
    assert resp.students[0].attempted == 2
    assert asyncio.run(svc.get_classroom("no-such-room")) is None


def test_classroom_overview_unknown_id_raises_not_found():
    svc, _ = _stub_service()
    try:
        asyncio.run(svc.classroom_overview("no-such-room"))
    except ClassroomNotFoundError:
        pass
    else:
        raise AssertionError("expected ClassroomNotFoundError")
