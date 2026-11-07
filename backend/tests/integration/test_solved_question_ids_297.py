"""SQL solved-id lookup backing the whats-next exclusion (Issue #297).

``list_solved_question_ids`` must be DISTINCT and passed-only (many failed
attempts must not evict an older pass), scoped to one user, and complete —
no recent-submissions window like ``list_by_user`` has.
"""

import os
import uuid
from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models.orm import Base, SubmissionORM, UserORM
from app.repositories.sql_submission_repository import SqlSubmissionRepository


def _test_db_url() -> str:
    db_url = os.environ["DATABASE_URL"]
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return db_url


@pytest_asyncio.fixture
async def db_session():
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
        await session.rollback()
        for model in (SubmissionORM, UserORM):
            await session.execute(delete(model))
        await session.commit()


async def _seed_users(db_session, uids):
    for uid in uids:
        db_session.add(
            UserORM(
                id=uid,
                username=f"user-{uid}",
                email=f"{uid}@e.edu",
                hashed_password="x",
                role="user",
            )
        )
    # Commit users first: without an ORM relationship between UserORM and
    # SubmissionORM the flush order is not FK-safe on its own.
    await db_session.commit()


def _submission(user_id: str, question_id: str, passed: bool, attempt: int):
    return SubmissionORM(
        id=f"{user_id}-{question_id}-{attempt}-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        question_id=question_id,
        code="c",
        language="python",
        passed=passed,
        attempt_index=attempt,
        status="graded",
        created_at=datetime.now(timezone.utc),
    )


async def test_solved_ids_are_distinct_passed_only_user_scoped_and_complete(
    db_session,
):
    await _seed_users(db_session, ["u-297-a", "u-297-b"])
    # Two passes on two-sum (DISTINCT collapses them) + one other pass.
    db_session.add(_submission("u-297-a", "two-sum", True, 0))
    db_session.add(_submission("u-297-a", "two-sum", True, 1))
    db_session.add(_submission("u-297-a", "valid-anagram", True, 0))
    # A failed-only question must never count as solved.
    db_session.add(_submission("u-297-a", "contains-duplicate", False, 0))
    # Another user's pass must not leak into this user's set.
    db_session.add(_submission("u-297-b", "contains-duplicate", True, 0))
    # Flood 60 newer failed attempts: a recent-submissions window (like
    # list_by_user's limit) would evict the oldest passes; the DISTINCT
    # query must keep them.
    for i in range(60):
        db_session.add(_submission("u-297-a", "contains-duplicate", False, i + 1))
    await db_session.commit()

    repo = SqlSubmissionRepository(db_session)
    solved = await repo.list_solved_question_ids("u-297-a")

    assert solved == {"two-sum", "valid-anagram"}


async def test_solved_ids_empty_for_user_with_no_passes(db_session):
    await _seed_users(db_session, ["u-297-c"])
    db_session.add(_submission("u-297-c", "two-sum", False, 0))
    await db_session.commit()

    repo = SqlSubmissionRepository(db_session)
    assert await repo.list_solved_question_ids("u-297-c") == set()
