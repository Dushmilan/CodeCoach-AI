"""Issue #176: professor analytics access — legacy class-analytics ownership scoping.

TDD RED: legacy GET /api/instructor/class-analytics currently trusts an
arbitrary user_ids CSV with no ownership check. These tests assert the
ownership chain (nav -> guard -> require_instructor -> ownership):

- professor requesting owned student ids -> 200
- professor requesting non-owned student ids -> 403
- TA requesting assigned students -> 200, unassigned -> 403
- student role -> 403 (require_instructor guard)
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.main import app
from app.api.auth_deps import get_current_user
from app.models.auth_schemas import UserResponse
from app.models.orm import ClassroomORM, CourseORM, UserORM
from app.repositories.sql_classroom_repository import SqlClassroomRepository

CS101_INVITE = "A176-CS101"
CS201_INVITE = "A176-CS201"

ADA = ("a176-ada", "a176.professor.ada", "professor")
GRACE = ("a176-grace", "a176.professor.grace", "professor")
TURING = ("a176-turing", "a176.demonstrator.turing", "ta")

CS101_STUDENTS = ("a176-mia", "a176-leo")
CS201_STUDENTS = ("a176-eli", "a176-ivy")


@contextmanager
def _auth_as(user_id: str, username: str, role: str):
    async def _ov():
        return UserResponse(
            id=user_id,
            username=username,
            email=f"{username}@university.example",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            role=role,
            plan="free",
        )

    app.dependency_overrides[get_current_user] = _ov
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def _seed_176(test_db) -> None:
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
                id="a176-py",
                title="Python Fundamentals",
                description="D",
                language="python",
                order=1,
                owner_id="a176-ada",
            ),
            CourseORM(
                id="a176-ds",
                title="Data Structures",
                description="D",
                language="python",
                order=2,
                owner_id="a176-grace",
            ),
        ]
    )
    await test_db.commit()

    repo = SqlClassroomRepository(test_db)
    await repo.create_classroom(
        course_id="a176-py",
        owner_id="a176-ada",
        name="A176 CS101",
        invite_code=CS101_INVITE,
        term="Fall 2026",
        schedule="Mon/Wed 10:00",
    )
    await repo.create_classroom(
        course_id="a176-ds",
        owner_id="a176-grace",
        name="A176 CS201",
        invite_code=CS201_INVITE,
        term="Fall 2026",
        schedule="Tue/Thu 14:00",
    )
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
    # TA assigned ONLY to CS101 — CS201 is out of scope for the TA.
    await repo.enroll(
        classroom_id=by_invite[CS101_INVITE], user_id="a176-turing", role="ta"
    )
    await test_db.commit()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_professor_owned_roster_returns_200(async_client, test_db):
    await _seed_176(test_db)
    roster = ",".join(CS101_STUDENTS)
    with _auth_as(*ADA):
        resp = await async_client.get(
            "/api/instructor/class-analytics", params={"user_ids": roster}
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_students"] == 2
    assert {s["user_id"] for s in body["students"]} == set(CS101_STUDENTS)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_professor_non_owned_roster_is_forbidden(async_client, test_db):
    await _seed_176(test_db)
    roster = ",".join(CS201_STUDENTS)
    with _auth_as(*ADA):
        resp = await async_client.get(
            "/api/instructor/class-analytics", params={"user_ids": roster}
        )
    assert resp.status_code == 403, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_professor_mixed_roster_is_forbidden(async_client, test_db):
    await _seed_176(test_db)
    roster = f"{CS101_STUDENTS[0]},{CS201_STUDENTS[0]}"
    with _auth_as(*ADA):
        resp = await async_client.get(
            "/api/instructor/class-analytics", params={"user_ids": roster}
        )
    assert resp.status_code == 403, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ta_assigned_roster_returns_200(async_client, test_db):
    await _seed_176(test_db)
    roster = ",".join(CS101_STUDENTS)
    with _auth_as(*TURING):
        resp = await async_client.get(
            "/api/instructor/class-analytics", params={"user_ids": roster}
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["total_students"] == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ta_unassigned_roster_is_forbidden(async_client, test_db):
    await _seed_176(test_db)
    roster = ",".join(CS201_STUDENTS)
    with _auth_as(*TURING):
        resp = await async_client.get(
            "/api/instructor/class-analytics", params={"user_ids": roster}
        )
    assert resp.status_code == 403, resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_empty_roster_returns_200_empty_body(async_client, test_db):
    """Empty CSV roster is not a scoping violation: 200 with zero students."""
    await _seed_176(test_db)
    with _auth_as(*ADA):
        resp = await async_client.get(
            "/api/instructor/class-analytics", params={"user_ids": ""}
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_students"] == 0
    assert body["students"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_student_role_cannot_use_class_analytics(async_client, test_db):
    await _seed_176(test_db)
    roster = ",".join(CS101_STUDENTS)
    with _auth_as("a176-mia", "a176-mia", "user"):
        resp = await async_client.get(
            "/api/instructor/class-analytics", params={"user_ids": roster}
        )
    assert resp.status_code == 403, resp.text
