#!/usr/bin/env python3
"""Seed demo school data (Issue #159 Task 4, extended by Issue #166).

Upserts admins + professor.grace + professor.ada + 2 TAs, assigns every
course to an owner (course id/title containing ``data-structures`` →
professor.grace, everything else → professor.ada), creates the 2 demo
classrooms, enrolls the 15 temp students + both TAs (TA in both rooms), and
mirrors deterministic ``completedLessons`` counts into ``course_progress``.

Every write is select-then-insert/update, so re-runs change nothing.

Seed passwords resolve from the environment (``backend/.env.seed``,
gitignored; see ``backend/.env.seed.example``) with dev defaults.

SAFETY: refuses to run unless ``ALLOW_DEMO_SEED=1`` AND the target schema is
the isolated test schema (``DATABASE_SEARCH_PATH=codecoach_test``) — or, for
the explicitly authorized live run, the production schema
(``DATABASE_SEARCH_PATH=public``) PLUS ``SEED_LIVE_CONFIRM=YES-I-AM-SURE``.
Supabase/PostgreSQL is the only database — no local fallback.

Usage:
    ALLOW_DEMO_SEED=1 DATABASE_SEARCH_PATH=codecoach_test \
    DATABASE_URL=postgresql://... python backend/scripts/seed_classroom_demo.py
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import seed_admin
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.models.orm import (
    Base,
    ClassroomORM,
    CourseORM,
    CourseProgressORM,
    UserORM,
)
from app.repositories.sql_classroom_repository import SqlClassroomRepository

# Usernames match frontend/src/data/instructor-demo.json; temp students use
# @university.example emails so they can never collide with real accounts.
TEMP_STUDENTS = [
    {"username": "mia", "password": "student123", "role": "user"},
    {"username": "leo", "password": "student123", "role": "user"},
    {"username": "ava", "password": "student123", "role": "user"},
    {"username": "noah", "password": "student123", "role": "user"},
    {"username": "zoe", "password": "student123", "role": "user"},
    {"username": "lucas", "password": "student123", "role": "user"},
    {"username": "emma", "password": "student123", "role": "user"},
    {"username": "olivia", "password": "student123", "role": "user"},
    {"username": "eli", "password": "student123", "role": "user"},
    {"username": "ivy", "password": "student123", "role": "user"},
    {"username": "max", "password": "student123", "role": "user"},
    {"username": "liam", "password": "student123", "role": "user"},
    {"username": "sophia", "password": "student123", "role": "user"},
    {"username": "ethan", "password": "student123", "role": "user"},
    {"username": "ruby", "password": "student123", "role": "user"},
]

# completedLessons counts from frontend/src/data/instructor-demo.json
# ("progress" section) for the original 8, deterministic variety for the
# Issue #166 additions. Stored as deterministic synthetic lesson ids
# (completed_lessons is schemaless JSONB with no FK — length is what matters).
DEMO_COMPLETED_COUNT = {
    "mia": 30,
    "leo": 22,
    "ava": 18,
    "noah": 9,
    "zoe": 5,
    "lucas": 17,
    "emma": 11,
    "olivia": 7,
    "eli": 21,
    "ivy": 12,
    "max": 4,
    "liam": 14,
    "sophia": 19,
    "ethan": 6,
    "ruby": 3,
}

CS101_STUDENTS = ("mia", "leo", "ava", "noah", "zoe", "lucas", "emma", "olivia")
CS201_STUDENTS = ("eli", "ivy", "max", "liam", "sophia", "ethan", "ruby")

TA_USERNAMES = ("demonstrator.turing", "demonstrator.curie")

# Demo courses from instructor-demo.json. Ensured (not blindly inserted) so the
# two classrooms always have a valid course_id FK, even on an empty schema.
DEMO_COURSES = [
    {
        "id": "python-fundamentals",
        "title": "Python Fundamentals",
        "description": "Created by Prof. Ada Lovelace.",
        "language": "python",
        "icon": "code",
        "order": 1,
    },
    {
        "id": "data-structures",
        "title": "Data Structures",
        "description": "Created by Prof. Grace Hopper.",
        "language": "python",
        "icon": "database",
        "order": 2,
    },
]

CLASSROOMS = [
    {
        "name": "CS101 · Section A",
        "course_id": "python-fundamentals",
        "owner_username": "professor.ada",
        "invite_code": "CS101-A-2026",
        "term": "Fall 2026",
        "schedule": "Mon/Wed 10:00",
    },
    {
        "name": "CS201 · Section B",
        "course_id": "data-structures",
        "owner_username": "professor.grace",
        "invite_code": "CS201-B-2026",
        "term": "Fall 2026",
        "schedule": "Tue/Thu 14:00",
    },
]


def _demo_seed_allowed() -> bool:
    """True for the isolated test schema, or for production only with an
    explicit live-confirm secret (Issue #166 live run)."""
    if os.getenv("ALLOW_DEMO_SEED") != "1":
        return False
    search_path = os.getenv("DATABASE_SEARCH_PATH")
    if search_path == "codecoach_test":
        return True
    return search_path == "public" and os.getenv("SEED_LIVE_CONFIRM") == "YES-I-AM-SURE"


def _owner_username_for_course(course_id: str, title: str | None) -> str:
    """Deterministic owner rule for ANY course catalog size.

    Course id/title containing ``data-structures`` → professor.grace,
    everything else → professor.ada.
    """
    haystack = f"{course_id} {title or ''}".lower()
    if "data-structures" in haystack:
        return "professor.grace"
    return "professor.ada"


async def _upsert_user(session: AsyncSession, entry: dict) -> UserORM:
    result = await session.execute(
        select(UserORM).where(UserORM.username == entry["username"])
    )
    user = result.scalar_one_or_none()
    if user is not None:
        user.role = entry["role"]
        return user
    user = UserORM(
        id=str(uuid.uuid4()),
        username=entry["username"],
        email=entry["email"],
        hashed_password=seed_admin.hash_password(
            seed_admin.seed_password(
                entry.get("password_env", "SEED_STUDENT_PASSWORD"),
                entry["password"],
            )
        ),
        created_at=datetime.now(timezone.utc),
        is_active=1,
        role=entry["role"],
    )
    session.add(user)
    return user


async def _ensure_course(session: AsyncSession, spec: dict) -> CourseORM:
    result = await session.execute(select(CourseORM).where(CourseORM.id == spec["id"]))
    course = result.scalar_one_or_none()
    if course is not None:
        return course
    course = CourseORM(**spec)
    session.add(course)
    return course


async def _ensure_classroom(
    repo: SqlClassroomRepository, session: AsyncSession, spec: dict, owner_id: str
) -> ClassroomORM:
    result = await session.execute(
        select(ClassroomORM).where(ClassroomORM.invite_code == spec["invite_code"])
    )
    room = result.scalar_one_or_none()
    if room is not None:
        return room
    return await repo.create_classroom(
        course_id=spec["course_id"],
        owner_id=owner_id,
        name=spec["name"],
        invite_code=spec["invite_code"],
        term=spec["term"],
        schedule=spec["schedule"],
    )


async def seed_demo(session: AsyncSession, *, allow: bool) -> dict[str, int]:
    """Seed demo data; return the exact report dict. Refuses unless allowed."""
    if not allow:
        raise SystemExit(
            "ERROR: demo seed refused — set ALLOW_DEMO_SEED=1 and "
            "DATABASE_SEARCH_PATH=codecoach_test (test schema), or "
            "DATABASE_SEARCH_PATH=public plus SEED_LIVE_CONFIRM=YES-I-AM-SURE "
            "for the authorized live run."
        )
    repo = SqlClassroomRepository(session)

    users: dict[str, UserORM] = {}
    admin_count = 0
    for entry in seed_admin.ADMIN_USERS:
        users[entry["username"]] = await _upsert_user(session, entry)
        admin_count += 1
    professor_count = 0
    ta_count = 0
    for entry in seed_admin.INSTRUCTOR_SEED_USERS:
        users[entry["username"]] = await _upsert_user(session, entry)
        if entry["role"] == "professor":
            professor_count += 1
        elif entry["role"] == "ta":
            ta_count += 1
    for spec in TEMP_STUDENTS:
        entry = {
            "username": spec["username"],
            "email": f"{spec['username']}@university.example",
            "password": spec["password"],
            "role": spec["role"],
        }
        users[entry["username"]] = await _upsert_user(session, entry)
    await session.commit()

    for spec in DEMO_COURSES:
        await _ensure_course(session, spec)
    await session.commit()

    # Assignment runs over EVERY course so set_course_owner() silent no-ops
    # (unknown ids) cannot hide: the reported count is the rows we just read.
    result = await session.execute(select(CourseORM).order_by(CourseORM.id))
    courses = list(result.scalars().all())
    for course in courses:
        owner = users[_owner_username_for_course(course.id, course.title)]
        await repo.set_course_owner(course.id, owner.id)
        print(f"  Course '{course.id}' → owner '{owner.username}'")

    rooms: dict[str, ClassroomORM] = {}
    for spec in CLASSROOMS:
        rooms[spec["invite_code"]] = await _ensure_classroom(
            repo, session, spec, owner_id=users[spec["owner_username"]].id
        )
        print(f"  Classroom '{spec['invite_code']}' ensured")

    enrollments = 0
    for username in CS101_STUDENTS:
        await repo.enroll(
            classroom_id=rooms["CS101-A-2026"].id,
            user_id=users[username].id,
            role="student",
        )
        enrollments += 1
    for username in CS201_STUDENTS:
        await repo.enroll(
            classroom_id=rooms["CS201-B-2026"].id,
            user_id=users[username].id,
            role="student",
        )
        enrollments += 1
    ta_ids = [users[username].id for username in TA_USERNAMES]
    for invite_code in ("CS101-A-2026", "CS201-B-2026"):
        for ta_id in ta_ids:
            await repo.enroll(
                classroom_id=rooms[invite_code].id, user_id=ta_id, role="ta"
            )
            enrollments += 1

    progress = 0
    for username, count in DEMO_COMPLETED_COUNT.items():
        if username in CS201_STUDENTS:
            course_id = rooms["CS201-B-2026"].course_id
        else:
            course_id = rooms["CS101-A-2026"].course_id
        completed = [f"{course_id}-lesson-{i:03d}" for i in range(1, count + 1)]
        result = await session.execute(
            select(CourseProgressORM).where(
                CourseProgressORM.user_id == users[username].id,
                CourseProgressORM.course_id == course_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            row.completed_lessons = completed
        else:
            session.add(
                CourseProgressORM(
                    id=uuid.uuid4().hex,
                    user_id=users[username].id,
                    course_id=course_id,
                    completed_lessons=completed,
                )
            )
        progress += 1
    await session.commit()

    return {
        "admins": admin_count,
        "professors": professor_count,
        "tas": ta_count,
        "courses_assigned": len(courses),
        "students": len(TEMP_STUDENTS),
        "enrollments": enrollments,
        "progress": progress,
    }


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit(
            "ERROR: DATABASE_URL is required (Supabase/PostgreSQL connection "
            "string); no local fallback is allowed."
        )
    # Drop Supabase pooler params (?pgbouncer=true) — asyncpg rejects them as
    # unknown connection kwargs.
    parts = urlsplit(url)
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def _main() -> None:
    if not _demo_seed_allowed():
        print(
            "ERROR: refusing to seed demo data — requires ALLOW_DEMO_SEED=1 and "
            "DATABASE_SEARCH_PATH=codecoach_test (isolated test schema), or "
            "DATABASE_SEARCH_PATH=public plus SEED_LIVE_CONFIRM=YES-I-AM-SURE "
            "for the authorized live run.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    search_path = os.getenv("DATABASE_SEARCH_PATH", "codecoach_test")
    engine = create_async_engine(
        _database_url(),
        poolclass=NullPool,
        connect_args={
            "server_settings": {"search_path": search_path},
            "statement_cache_size": 0,
        },
    )
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )() as session:
            report = await seed_demo(session, allow=True)
    finally:
        await engine.dispose()
    print(f"Done. Demo seed report: {report}")


if __name__ == "__main__":
    asyncio.run(_main())
