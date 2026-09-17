"""Issue #159 Task 5: live instructor classroom endpoints (classroom scope).

TDD RED: these tests assert the Task 5 routes
(`GET /api/instructor/classrooms` and `GET /api/instructor/classrooms/{id}`)
backed by the real ClassroomRepository + ClassAnalyticsService. They FAIL
while the routes are missing (FastAPI returns 404 for unknown paths).

Classrooms are ALWAYS resolved by invite_code (CS101-A-2026 / CS201-B-2026)
— uuid ids differ per fresh schema and are never hardcoded.
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text

from app.main import app
from app.api.auth_deps import get_current_user
from app.models.auth_schemas import UserResponse
from app.models.orm import (
    ClassroomORM,
    CourseORM,
    CourseProgressORM,
    UserORM,
)
from app.repositories.sql_classroom_repository import SqlClassroomRepository

CS101_INVITE = "CS101-A-2026"
CS201_INVITE = "CS201-B-2026"

ADA = ("t5-ada", "professor.ada", "professor")
GRACE = ("t5-grace", "professor.grace", "professor")
TURING = ("t5-turing", "demonstrator.turing", "ta")

CS101_STUDENTS = ("t5-mia", "t5-leo", "t5-ava", "t5-noah", "t5-zoe")
CS201_STUDENTS = ("t5-eli", "t5-ivy", "t5-max")

# Deterministic completed-lesson counts for the CS101 roster (total_lessons=10).
CS101_COMPLETED = {
    "t5-mia": 6,
    "t5-leo": 4,
    "t5-ava": 2,
    "t5-noah": 0,
    "t5-zoe": 8,
}


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


async def _seed_hierarchy(test_db) -> dict[str, str]:
    """Seed professors, TA, students, courses, rooms, enrollments, progress.

    Returns invite_code -> classroom id, resolved via a select on invite_code
    (never hardcoded). Uses keyword-only repo calls per the Task 3 handoff.
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
        for uid, name, role in (ADA, GRACE, TURING)
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
                id="t5-py",
                title="Python Fundamentals",
                description="D",
                language="python",
                order=1,
                owner_id="t5-ada",
            ),
            CourseORM(
                id="t5-ds",
                title="Data Structures",
                description="D",
                language="python",
                order=2,
                owner_id="t5-grace",
            ),
        ]
    )
    await test_db.commit()

    repo = SqlClassroomRepository(test_db)
    await repo.create_classroom(
        course_id="t5-py",
        owner_id="t5-ada",
        name="CS101 · Section A",
        invite_code=CS101_INVITE,
        term="Fall 2026",
        schedule="Mon/Wed 10:00",
    )
    await repo.create_classroom(
        course_id="t5-ds",
        owner_id="t5-grace",
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
            classroom_id=by_invite[invite], user_id="t5-turing", role="ta"
        )

    for uid, count in CS101_COMPLETED.items():
        if count == 0:
            continue  # noah: no progress row -> 0 completed lessons
        test_db.add(
            CourseProgressORM(
                id=f"t5-prog-{uid}",
                user_id=uid,
                course_id="t5-py",
                completed_lessons=[
                    f"t5-py-lesson-{i:03d}" for i in range(1, count + 1)
                ],
            )
        )
    test_db.add(
        CourseProgressORM(
            id="t5-prog-t5-eli",
            user_id="t5-eli",
            course_id="t5-ds",
            completed_lessons=["t5-ds-lesson-001"],
        )
    )
    # Submissions need a question row (FK); mia: 2 attempted, 1 solved.
    await test_db.execute(
        text(
            "INSERT INTO questions (id, title, difficulty, category, company_tags, "
            "description, starter_code, examples, test_cases, constraints, hints, "
            "is_interactive) VALUES ('two-sum', 'T', 'easy', 'arrays', '[]', 'd', "
            "'{}', '[]', '[]', '[]', '[]', 0) ON CONFLICT DO NOTHING"
        )
    )
    await test_db.execute(
        text(
            "INSERT INTO submissions (id, user_id, question_id, code, language, "
            "passed, attempt_index, created_at) VALUES "
            "('t5-s1', 't5-mia', 'two-sum', 'c', 'python', true, 0, :ts), "
            "('t5-s2', 't5-mia', 'two-sum', 'c', 'python', false, 1, :ts)"
        ),
        {"ts": now},
    )
    await test_db.commit()
    return by_invite


@pytest.mark.integration
@pytest.mark.asyncio
async def test_professor_sees_only_owned_rooms(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as(*ADA):
        resp = await async_client.get("/api/instructor/classrooms")
    assert resp.status_code == 200, resp.text
    rooms = resp.json()
    assert [r["invite_code"] for r in rooms] == [CS101_INVITE]
    assert all(r["owner_id"] == "t5-ada" for r in rooms)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ta_sees_only_assigned_rooms(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as(*TURING):
        resp = await async_client.get("/api/instructor/classrooms")
    assert resp.status_code == 200, resp.text
    assert sorted(r["invite_code"] for r in resp.json()) == [CS101_INVITE, CS201_INVITE]
    with _auth_as(*TURING):
        detail = await async_client.get(
            f"/api/instructor/classrooms/{(await _invite_map(test_db))[CS101_INVITE]}"
        )
    assert detail.status_code == 200, detail.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_professor_detail_is_forbidden(async_client, test_db):
    by_invite = await _seed_hierarchy(test_db)
    with _auth_as(*GRACE):
        resp = await async_client.get(
            f"/api/instructor/classrooms/{by_invite[CS101_INVITE]}"
        )
    assert resp.status_code == 403, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unknown_classroom_id_is_not_found(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as(*ADA):
        resp = await async_client.get(
            "/api/instructor/classrooms/00000000-0000-0000-0000-000000000000"
        )
    assert resp.status_code == 404, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_analytics_match_seeded_progress(async_client, test_db):
    by_invite = await _seed_hierarchy(test_db)
    with _auth_as(*ADA):
        resp = await async_client.get(
            f"/api/instructor/classrooms/{by_invite[CS101_INVITE]}"
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["classroom"]["invite_code"] == CS101_INVITE
    analytics = body["analytics"]
    # TA + other-room students are excluded: exactly the 5 CS101 students.
    assert analytics["total_students"] == 5
    by_user = {s["user_id"]: s for s in analytics["students"]}
    assert set(by_user) == set(CS101_STUDENTS)
    for uid, count in CS101_COMPLETED.items():
        assert by_user[uid]["completed_lessons"] == count
        assert by_user[uid]["completion_pct"] == round(count / 10 * 100, 1)
    assert by_user["t5-mia"]["attempted"] == 2
    assert by_user["t5-mia"]["solved"] == 1
    expected_avg = round(
        sum(round(c / 10 * 100, 1) for c in CS101_COMPLETED.values()) / 5, 1
    )
    assert analytics["avg_completion"] == expected_avg
    assert analytics["avg_solved"] == round(1 / 5, 2)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_student_role_cannot_list_classrooms(async_client, test_db):
    await _seed_hierarchy(test_db)
    with _auth_as("t5-mia", "t5-mia", "user"):
        resp = await async_client.get("/api/instructor/classrooms")
    assert resp.status_code == 403, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_instructor_and_hierarchy_agree_on_avg_completion(async_client, test_db):
    """Consistency: the instructor batch view (no explicit total_lessons) and
    the admin hierarchy tree must report the same avg_completion for the same
    room — the server resolves the room's real course denominator, falling
    back to the shared default when the course has no lessons yet.

    Fixture courses carry no lessons, so both views must use the default
    (10): (60 + 40 + 20 + 0 + 80) / 5 == 40.0.
    """
    await _seed_hierarchy(test_db)
    with _auth_as(*ADA):
        batch = await async_client.get("/api/instructor/classrooms-analytics")
    assert batch.status_code == 200, batch.text
    instructor_avg = {
        r["classroom"]["invite_code"]: r["analytics"]["avg_completion"]
        for r in batch.json()
    }[CS101_INVITE]
    with _auth_as("t5-root", "root", "super_admin"):
        tree = await async_client.get("/api/admin/hierarchy")
    assert tree.status_code == 200, tree.text
    ada = next(p for p in tree.json()["professors"] if p["username"] == "professor.ada")
    cs101 = next(r for r in ada["classrooms"] if r["invite_code"] == CS101_INVITE)
    assert cs101["students"] == 5
    assert cs101["avg_completion"] == instructor_avg == 40.0


async def _invite_map(test_db) -> dict[str, str]:
    result = await test_db.execute(
        select(ClassroomORM).where(
            ClassroomORM.invite_code.in_([CS101_INVITE, CS201_INVITE])
        )
    )
    return {room.invite_code: room.id for room in result.scalars().all()}
