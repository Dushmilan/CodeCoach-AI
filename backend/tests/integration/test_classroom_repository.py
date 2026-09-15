"""Issue #159 Task 2: ORM persistence for course ownership/classrooms.

Task 3 owns this file's evolution (repository tests); Task 2 lands the
first test only to drive the models red -> green.
"""

import os

import pytest_asyncio
from sqlalchemy import delete
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
        # (courses/users) are cleaned by id only. Task 3 extends this
        # as it adds tests to this file.
        await session.execute(delete(ClassroomEnrollmentORM))
        await session.execute(delete(ClassroomORM).where(ClassroomORM.id == "r-1"))
        await session.execute(delete(CourseORM).where(CourseORM.id == "c-1"))
        await session.execute(delete(UserORM).where(UserORM.id == "u-prof"))
        await session.commit()
    await engine.dispose()


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
