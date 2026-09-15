"""Issue #159 Task 3: ClassroomRepository port + SQL implementation.

Covers the port contract (one test per method) plus the Task 2
ORM persistence test, which must stay green.
"""

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.models.orm import (
    Base,
    ClassroomEnrollmentORM,
    ClassroomORM,
    CourseORM,
    UserORM,
)
from app.ports.classroom_repository import ClassroomRepository
from app.repositories.sql_classroom_repository import (
    DuplicateInviteCodeError,
    SqlClassroomRepository,
)


def _test_db_url() -> str:
    db_url = os.environ["DATABASE_URL"]
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return db_url


@pytest_asyncio.fixture
async def db_session():
    """Function-scoped async session against the isolated test schema."""
    engine = create_async_engine(
        _test_db_url(),
        poolclass=NullPool,
        connect_args={
            "server_settings": {
                "search_path": os.environ.get("DATABASE_SEARCH_PATH", "codecoach_test")
            },
            "statement_cache_size": 0,
        },
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session
        # Roll back any failed-test transaction so teardown never masks it.
        await session.rollback()
        # New tables are wiped whole (no other writers); shared tables
        # (courses/users) are cleaned by id only.
        await session.execute(delete(ClassroomEnrollmentORM))
        await session.execute(delete(ClassroomORM))
        for cid in ("c-1", "c-2"):
            await session.execute(delete(CourseORM).where(CourseORM.id == cid))
        for uid in ("u-prof", "u-other", "u-ta", "u-student"):
            await session.execute(delete(UserORM).where(UserORM.id == uid))
        await session.commit()
    await engine.dispose()


async def _seed_professor_course(db_session, user_id="u-prof", course_id="c-1"):
    """Seed one professor user + one owned course; returns (user, course)."""
    prof = UserORM(
        id=user_id,
        username=f"user-{user_id}",
        email=f"{user_id}@e.edu",
        hashed_password="x",
        role="professor",
    )
    db_session.add(prof)
    course = CourseORM(
        id=course_id,
        title="T",
        description="D",
        language="python",
        order=1,
        owner_id=user_id,
    )
    db_session.add(course)
    await db_session.commit()
    return prof, course


def _repo(db_session) -> ClassroomRepository:
    return SqlClassroomRepository(db_session)


async def test_models_persist(db_session):
    prof = UserORM(
        id="u-prof",
        username="p",
        email="p@e.edu",
        hashed_password="x",
        role="professor",
    )
    db_session.add(prof)
    course = CourseORM(
        id="c-1",
        title="T",
        description="D",
        language="python",
        order=1,
        owner_id="u-prof",
    )
    db_session.add(course)
    room = ClassroomORM(
        id="r-1",
        course_id="c-1",
        owner_id="u-prof",
        name="CS101",
        invite_code="INV-1",
        term="Fall 2026",
        schedule="Mon",
    )
    db_session.add(room)
    await db_session.commit()
    assert (await db_session.get(ClassroomORM, "r-1")).invite_code == "INV-1"


async def test_create_classroom_persists(db_session):
    await _seed_professor_course(db_session)
    room = await _repo(db_session).create_classroom(
        course_id="c-1",
        owner_id="u-prof",
        name="CS101-A",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        term="Fall 2026",
        schedule="Mon 10:00",
    )
    assert room.id
    assert room.course_id == "c-1"
    assert room.owner_id == "u-prof"
    assert room.name == "CS101-A"
    persisted = await db_session.get(ClassroomORM, room.id)
    assert persisted is not None
    assert persisted.invite_code == room.invite_code


async def test_create_classroom_duplicate_invite_code_raises(db_session):
    await _seed_professor_course(db_session)
    repo = _repo(db_session)
    await repo.create_classroom(
        course_id="c-1",
        owner_id="u-prof",
        name="CS101-A",
        invite_code="INV-DUP-1",
        term="Fall 2026",
        schedule="Mon",
    )
    with pytest.raises(DuplicateInviteCodeError):
        await repo.create_classroom(
            course_id="c-1",
            owner_id="u-prof",
            name="CS101-B",
            invite_code="INV-DUP-1",
            term="Fall 2026",
            schedule="Tue",
        )


async def test_list_owned_by_professor_excludes_others_rooms(db_session):
    await _seed_professor_course(db_session, user_id="u-prof", course_id="c-1")
    await _seed_professor_course(db_session, user_id="u-other", course_id="c-2")
    repo = _repo(db_session)
    await repo.create_classroom(
        course_id="c-1",
        owner_id="u-prof",
        name="Mine",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        term="Fall 2026",
        schedule="Mon",
    )
    await repo.create_classroom(
        course_id="c-2",
        owner_id="u-other",
        name="Theirs",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        term="Fall 2026",
        schedule="Tue",
    )
    mine = await repo.list_owned_by_professor("u-prof")
    assert [r.name for r in mine] == ["Mine"]
    assert all(r.owner_id == "u-prof" for r in mine)


async def test_list_for_ta_returns_only_assigned_rooms(db_session):
    await _seed_professor_course(db_session)
    ta = UserORM(
        id="u-ta",
        username="user-u-ta",
        email="u-ta@e.edu",
        hashed_password="x",
        role="user",
    )
    db_session.add(ta)
    await db_session.commit()
    repo = _repo(db_session)
    assigned = await repo.create_classroom(
        course_id="c-1",
        owner_id="u-prof",
        name="Assigned",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        term="Fall 2026",
        schedule="Mon",
    )
    await repo.create_classroom(
        course_id="c-1",
        owner_id="u-prof",
        name="Unassigned",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        term="Fall 2026",
        schedule="Tue",
    )
    await repo.enroll(classroom_id=assigned.id, user_id="u-ta", role="ta")
    rooms = await repo.list_for_ta("u-ta")
    assert [r.id for r in rooms] == [assigned.id]


async def test_enroll_upserts_role_without_duplicating(db_session):
    await _seed_professor_course(db_session)
    student = UserORM(
        id="u-student",
        username="user-u-student",
        email="u-student@e.edu",
        hashed_password="x",
        role="user",
    )
    db_session.add(student)
    await db_session.commit()
    repo = _repo(db_session)
    room = await repo.create_classroom(
        course_id="c-1",
        owner_id="u-prof",
        name="CS101",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        term="Fall 2026",
        schedule="Mon",
    )
    first = await repo.enroll(classroom_id=room.id, user_id="u-student", role="student")
    assert first.role == "student"
    second = await repo.enroll(classroom_id=room.id, user_id="u-student", role="ta")
    assert second.role == "ta"
    assert second.id == first.id


async def test_enroll_rejects_invalid_role(db_session):
    await _seed_professor_course(db_session)
    repo = _repo(db_session)
    room = await repo.create_classroom(
        course_id="c-1",
        owner_id="u-prof",
        name="CS101",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        term="Fall 2026",
        schedule="Mon",
    )
    with pytest.raises(ValueError):
        await repo.enroll(classroom_id=room.id, user_id="u-prof", role="admin")


async def test_set_course_owner_persists(db_session):
    await _seed_professor_course(db_session, user_id="u-prof", course_id="c-1")
    other = UserORM(
        id="u-other",
        username="user-u-other",
        email="u-other@e.edu",
        hashed_password="x",
        role="professor",
    )
    db_session.add(other)
    await db_session.commit()
    await _repo(db_session).set_course_owner("c-1", "u-other")
    db_session.expire_all()
    assert (await db_session.get(CourseORM, "c-1")).owner_id == "u-other"


async def test_create_classroom_non_unique_error_is_not_mapped_to_duplicate(
    db_session,
):
    """A NOT NULL IntegrityError must re-raise, not map to Duplicate (409)."""
    await _seed_professor_course(db_session)
    with pytest.raises(IntegrityError) as exc_info:
        await _repo(db_session).create_classroom(
            course_id="c-1",
            owner_id="u-prof",
            name="CS101",
            invite_code=None,
            term="Fall 2026",
            schedule="Mon",
        )
    assert not isinstance(exc_info.value, DuplicateInviteCodeError)


async def test_enroll_fk_violation_surfaces_instead_of_no_result(db_session):
    """A bad classroom_id must raise IntegrityError, never NoResultFound."""
    await _seed_professor_course(db_session)
    student = UserORM(
        id="u-student",
        username="user-u-student",
        email="u-student@e.edu",
        hashed_password="x",
        role="user",
    )
    db_session.add(student)
    await db_session.commit()
    with pytest.raises(IntegrityError):
        await _repo(db_session).enroll(
            classroom_id="no-such-room", user_id="u-student", role="student"
        )
