"""Issue #159 Task 6: admin hierarchy endpoint (admin tree scope).

TDD RED: these tests assert the Task 6 route
(`GET /api/admin/hierarchy`, admin/super_admin only) backed by the real
port stack (UserAdminRepository + ClassroomRepository + CourseRepository +
ClassAnalyticsService). They FAIL while the route is missing (FastAPI
returns 404 for unknown paths).

Classrooms are ALWAYS resolved by invite_code (CS101-A-2026 / CS201-B-2026)
— uuid ids differ per fresh schema and are never hardcoded. Tree shape is
EXACTLY the Task 6 brief contract::

    {"professors": [{"id", "username",
                     "courses": [{"id", "title", "lessons"}],
                     "classrooms": [{"id", "name", "invite_code",
                                     "tas", "students", "avg_completion"}]}]}
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.main import app
from app.api.auth_deps import get_current_user
from app.models.auth_schemas import UserResponse
from app.models.orm import (
    ClassroomORM,
    CourseORM,
    CourseProgressORM,
    LessonORM,
    ModuleORM,
    UserORM,
)
from app.repositories.sql_classroom_repository import SqlClassroomRepository

CS101_INVITE = "CS101-A-2026"
CS201_INVITE = "CS201-B-2026"

ADA = ("t6-ada", "professor.ada", "professor")
GRACE = ("t6-grace", "professor.grace", "professor")
TURING = ("t6-turing", "demonstrator.turing", "ta")
ADMIN = ("t6-admin", "admin", "admin")
SUPER_ADMIN = ("t6-root", "root", "super_admin")

CS101_STUDENTS = ("t6-mia", "t6-leo", "t6-ava", "t6-noah", "t6-zoe")
CS201_STUDENTS = ("t6-eli", "t6-ivy", "t6-max")

# Deterministic completed-lesson counts for the CS101 roster (t6-py holds
# 3 real lessons, so the average uses denominator 3 with per-student clamp:
# 6 -> 200 -> 100; 4 -> 133.3 -> 100; 2 -> 66.7; 0; 8 -> 266.7 -> 100).
CS101_COMPLETED = {
    "t6-mia": 6,
    "t6-leo": 4,
    "t6-ava": 2,
    "t6-noah": 0,
    "t6-zoe": 8,
}
# (100 + 100 + 66.7 + 0 + 100) / 5 = 73.3
CS101_AVG = 73.3


@contextmanager
def _auth_as(user_id: str, username: str, role: str):
    """Override auth with a fixed role-bearing user for one test."""

    async def _ov():
        return UserResponse(
            id=user_id,
            username=username,
            email=f"{username}@university.example",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            role=role,
        )

    app.dependency_overrides[get_current_user] = _ov
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def _seed_hierarchy(test_db) -> None:
    """Seed professors, TA, admin, students, courses (+1 module/3 lessons),
    rooms, enrollments, and progress. Uses keyword-only repo calls per the
    Task 3 handoff; ids resolve by invite_code, never hardcoded.
    """
    now = datetime.now(timezone.utc)
    users = [
        UserORM(
            id=uid,
            username=name,
            email=f"{name}@university.example",
            hashed_password="x",
            created_at=now,
            is_active=1,
            role=role,
        )
        for uid, name, role in (ADA, GRACE, TURING, ADMIN, SUPER_ADMIN)
    ]
    for uid in CS101_STUDENTS + CS201_STUDENTS:
        users.append(
            UserORM(
                id=uid,
                username=uid,
                email=f"{uid}@university.example",
                hashed_password="x",
                created_at=now,
                is_active=1,
                role="user",
            )
        )
    test_db.add_all(users)
    test_db.add_all(
        [
            CourseORM(
                id="t6-py",
                title="Python Fundamentals",
                description="D",
                language="python",
                order=1,
                owner_id="t6-ada",
            ),
            CourseORM(
                id="t6-ds",
                title="Data Structures",
                description="D",
                language="python",
                order=2,
                owner_id="t6-grace",
            ),
        ]
    )
    # One module with 3 lessons on ada's course pins the lessons counter.
    test_db.add(
        ModuleORM(
            id="t6-m1",
            course_id="t6-py",
            title="Basics",
            description="D",
            order=1,
        )
    )
    for i in range(1, 4):
        test_db.add(
            LessonORM(
                id=f"t6-l{i}",
                course_id="t6-py",
                module_id="t6-m1",
                title=f"Lesson {i}",
                type="theory",
                content="C",
                order=i,
                language="python",
            )
        )
    await test_db.commit()

    repo = SqlClassroomRepository(test_db)
    await repo.create_classroom(
        course_id="t6-py",
        owner_id="t6-ada",
        name="CS101 · Section A",
        invite_code=CS101_INVITE,
        term="Fall 2026",
        schedule="Mon/Wed 10:00",
    )
    await repo.create_classroom(
        course_id="t6-ds",
        owner_id="t6-grace",
        name="CS201 · Section B",
        invite_code=CS201_INVITE,
        term="Fall 2026",
        schedule="Tue/Thu 14:00",
    )

    # Resolve ids by invite_code — never hardcode classroom uuids.
    result = await test_db.execute(
        select(ClassroomORM).where(
            ClassroomORM.invite_code.in_([CS101_INVITE, CS201_INVITE])
        )
    )
    by_invite = {room.invite_code: room.id for room in result.scalars().all()}
    assert set(by_invite) == {CS101_INVITE, CS201_INVITE}

    for uid in CS101_STUDENTS:
        await repo.enroll(
            classroom_id=by_invite[CS101_INVITE], user_id=uid, role="student"
        )
    for uid in CS201_STUDENTS:
        await repo.enroll(
            classroom_id=by_invite[CS201_INVITE], user_id=uid, role="student"
        )
    for invite in (CS101_INVITE, CS201_INVITE):
        await repo.enroll(
            classroom_id=by_invite[invite], user_id="t6-turing", role="ta"
        )

    for uid, count in CS101_COMPLETED.items():
        if count == 0:
            continue  # noah: no progress row -> 0 completed lessons
        test_db.add(
            CourseProgressORM(
                id=f"t6-prog-{uid}",
                user_id=uid,
                course_id="t6-py",
                completed_lessons=[
                    f"t6-py-lesson-{i:03d}" for i in range(1, count + 1)
                ],
            )
        )
    await test_db.commit()


def _professors_by_username(body: dict) -> dict:
    assert set(body.keys()) == {"professors"}
    return {p["username"]: p for p in body["professors"]}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_avg_completion_capped_when_completed_exceeds_lessons(
    async_client, test_db
):
    """Regression: completed lessons above the real course lesson count must
    not push avg_completion past 100 — the average uses the room's real
    per-course denominator (3 lessons here), clamped per student at 100.

    mia at 10 completed: 333.3 → 100; leo 4 → 133.3 → 100; ava 2 → 66.7;
    noah 0; zoe 8 → 266.7 → 100. avg = (100 + 100 + 66.7 + 0 + 100) / 5.
    """
    await _seed_hierarchy(test_db)
    result = await test_db.execute(
        select(CourseProgressORM).where(CourseProgressORM.id == "t6-prog-t6-mia")
    )
    row = result.scalar_one()
    row.completed_lessons = [f"t6-py-lesson-{i:03d}" for i in range(1, 11)]
    await test_db.commit()
    with _auth_as(*ADMIN):
        resp = await async_client.get("/api/admin/hierarchy")
    assert resp.status_code == 200, resp.text
    by_name = _professors_by_username(resp.json())
    ada = by_name["professor.ada"]
    cs101 = next(r for r in ada["classrooms"] if r["invite_code"] == CS101_INVITE)
    assert cs101["avg_completion"] <= 100
    assert cs101["avg_completion"] == 73.3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_admin_sees_exact_tree_for_ada(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as(*ADMIN):
        resp = await async_client.get("/api/admin/hierarchy")
    assert resp.status_code == 200, resp.text
    by_name = _professors_by_username(resp.json())

    ada = by_name["professor.ada"]
    assert set(ada.keys()) == {"id", "username", "courses", "classrooms"}
    assert ada["id"] == "t6-ada"
    # Course count follows real DB content (>=1); ada's course is exact.
    assert len(ada["courses"]) >= 1
    py = next(c for c in ada["courses"] if c["id"] == "t6-py")
    assert set(py.keys()) == {"id", "title", "lessons"}
    assert py["title"] == "Python Fundamentals"
    assert py["lessons"] == 3

    rooms = {r["invite_code"]: r for r in ada["classrooms"]}
    assert set(rooms) == {CS101_INVITE}
    cs101 = rooms[CS101_INVITE]
    assert set(cs101.keys()) == {
        "id",
        "name",
        "invite_code",
        "tas",
        "students",
        "avg_completion",
    }
    assert cs101["name"] == "CS101 · Section A"
    assert cs101["tas"] == ["demonstrator.turing"]
    assert cs101["students"] == 5
    assert cs101["avg_completion"] == CS101_AVG


@pytest.mark.integration
@pytest.mark.asyncio
async def test_admin_sees_grace_room_with_three_students(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as(*ADMIN):
        resp = await async_client.get("/api/admin/hierarchy")
    assert resp.status_code == 200, resp.text
    by_name = _professors_by_username(resp.json())

    grace = by_name["professor.grace"]
    rooms = {r["invite_code"]: r for r in grace["classrooms"]}
    assert set(rooms) == {CS201_INVITE}
    assert rooms[CS201_INVITE]["students"] == 3
    assert rooms[CS201_INVITE]["tas"] == ["demonstrator.turing"]
    # Non-professors never appear as tree roots.
    assert "demonstrator.turing" not in by_name
    assert "admin" not in by_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_super_admin_is_allowed(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as(*SUPER_ADMIN):
        resp = await async_client.get("/api/admin/hierarchy")
    assert resp.status_code == 200, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_professor_token_is_forbidden(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as(*ADA):
        resp = await async_client.get("/api/admin/hierarchy")
    assert resp.status_code == 403, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_student_token_is_forbidden(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as("t6-mia", "t6-mia", "user"):
        resp = await async_client.get("/api/admin/hierarchy")
    assert resp.status_code == 403, resp.text
