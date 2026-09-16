"""Issue #179: SQL batch equality + O(1) query budget + owned-rooms contract.

RED first: batch ports, window cap identical to list_by_user, batch grouping,
service figures identical on SQL, perf <= 5 queries, and the new
GET /classrooms-analytics own-rooms-only contract.
"""

import os
import uuid
from datetime import datetime, timezone

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_class_analytics_service, get_classroom_repository
from app.main import app
from app.models.auth_schemas import UserResponse
from app.models.orm import (
    Base,
    ClassroomEnrollmentORM,
    ClassroomORM,
    CourseORM,
    CourseProgressORM,
    SubmissionORM,
    UserORM,
)
from app.repositories.sql_classroom_repository import SqlClassroomRepository
from app.repositories.sql_progress_repository import SqlProgressRepository
from app.repositories.sql_submission_repository import SqlSubmissionRepository
from app.services.class_analytics_service import ClassAnalyticsService


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
        for model in (
            ClassroomEnrollmentORM,
            ClassroomORM,
            CourseProgressORM,
            SubmissionORM,
            UserORM,
            CourseORM,
        ):
            await session.execute(delete(model))
        await session.commit()
    await engine.dispose()


async def _seed_users_course(db_session, uids, course_id="c-179"):
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
    db_session.add(
        CourseORM(
            id=course_id,
            title="T",
            description="D",
            language="python",
            order=1,
            owner_id="u-prof-179",
        )
    )
    prof = UserORM(
        id="u-prof-179",
        username="prof-179",
        email="prof179@e.edu",
        hashed_password="x",
        role="professor",
    )
    db_session.add(prof)
    await db_session.commit()


async def _seed_submissions(db_session, user_id, n, passed_every=2):
    for i in range(n):
        db_session.add(
            SubmissionORM(
                id=f"{user_id}-sub-{i}-{uuid.uuid4().hex[:6]}",
                user_id=user_id,
                question_id="two-sum",
                code="c",
                language="python",
                passed=(i % passed_every == 0),
                attempt_index=i,
                status="graded",
                created_at=datetime.now(timezone.utc),
            )
        )
    await db_session.commit()


async def test_sql_list_by_users_matches_list_by_user_with_cap(db_session):
    await _seed_users_course(db_session, ["u-a", "u-b"])
    await _seed_submissions(db_session, "u-a", 8)
    await _seed_submissions(db_session, "u-b", 3)
    repo = SqlSubmissionRepository(db_session)
    for limit in (3, 1000):
        batch = await repo.list_by_users(["u-a", "u-b"], limit=limit)
        assert set(batch) == {"u-a", "u-b"}
        for uid in ("u-a", "u-b"):
            single = await repo.list_by_user(uid, limit=limit)
            assert [s.id for s in batch[uid]] == [s.id for s in single]
            assert len(batch[uid]) <= limit
    # Unknown users map to empty, order newest-first like the single path.
    batch = await repo.list_by_users(["u-a", "no-such"], limit=5)
    assert batch["no-such"] == []
    created = [s.created_at for s in batch["u-a"]]
    assert created == sorted(created, reverse=True)


async def test_sql_progress_and_classroom_batch_grouping(db_session):
    await _seed_users_course(db_session, ["u-a", "u-b"])
    db_session.add(
        CourseProgressORM(
            id="u-a:c-179",
            user_id="u-a",
            course_id="c-179",
            completed_lessons=["l1", "l2"],
        )
    )
    db_session.add(
        CourseProgressORM(
            id="u-b:c-179",
            user_id="u-b",
            course_id="c-179",
            completed_lessons=["l9"],
        )
    )
    await db_session.commit()
    progress = SqlProgressRepository(db_session)
    grouped = await progress.get_all_progress_for_users(["u-a", "u-b", "ghost"])
    assert set(grouped) == {"u-a", "u-b", "ghost"}
    assert grouped["ghost"] == []
    assert grouped["u-a"][0].completed_lessons == ["l1", "l2"]

    rooms = SqlClassroomRepository(db_session)
    r1 = await rooms.create_classroom(
        course_id="c-179",
        owner_id="u-prof-179",
        name="R1",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
    )
    r2 = await rooms.create_classroom(
        course_id="c-179",
        owner_id="u-prof-179",
        name="R2",
        invite_code=f"INV-{uuid.uuid4().hex[:8]}",
    )
    await rooms.enroll(classroom_id=r1.id, user_id="u-a", role="student")
    await rooms.enroll(classroom_id=r2.id, user_id="u-b", role="student")
    by_room = await rooms.list_classroom_student_ids_by_room([r1.id, r2.id, "ghost"])
    assert by_room[r1.id] == ["u-a"]
    assert by_room[r2.id] == ["u-b"]
    assert by_room["ghost"] == []


async def test_service_figures_identical_on_sql_and_query_budget(db_session):
    await _seed_users_course(db_session, ["u-a", "u-b", "u-c"])
    for uid in ("u-a", "u-b", "u-c"):
        await _seed_submissions(db_session, uid, 4)
    db_session.add(
        CourseProgressORM(
            id="u-a:c-179",
            user_id="u-a",
            course_id="c-179",
            completed_lessons=["l1", "l2", "l3"],
        )
    )
    await db_session.commit()
    svc = ClassAnalyticsService(
        submissions=SqlSubmissionRepository(db_session),
        progress=SqlProgressRepository(db_session),
    )
    single = await svc.class_overview(["u-a", "u-b", "u-c"], total_lessons=10)
    multi = await svc.class_overviews(
        {"room-1": ["u-a", "u-b"], "room-2": ["u-c"]}, total_lessons=10
    )
    assert [s.model_dump() for s in multi["room-1"].students] == [
        s.model_dump() for s in single.students[:2]
    ]

    # Perf: 2 rooms x 3 students must stay within 5 SQL statements.
    queries: list[str] = []

    def _before(conn, clause, *a, **k):
        queries.append(str(clause)[:80])

    event.listen(db_session.bind.sync_engine, "before_cursor_execute", _before)
    try:
        rooms = SqlClassroomRepository(db_session)
        r1 = await rooms.create_classroom(
            course_id="c-179",
            owner_id="u-prof-179",
            name="P1",
            invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        )
        r2 = await rooms.create_classroom(
            course_id="c-179",
            owner_id="u-prof-179",
            name="P2",
            invite_code=f"INV-{uuid.uuid4().hex[:8]}",
        )
        await rooms.enroll(classroom_id=r1.id, user_id="u-a", role="student")
        await rooms.enroll(classroom_id=r2.id, user_id="u-b", role="student")
        queries.clear()
        by_room = await rooms.list_classroom_student_ids_by_room([r1.id, r2.id])
        overviews = await svc.class_overviews(by_room, total_lessons=10)
        assert set(overviews) == {r1.id, r2.id}
    finally:
        event.remove(db_session.bind.sync_engine, "before_cursor_execute", _before)
    assert len(queries) <= 5, f"expected <=5 queries, got {len(queries)}"


def _user(username, uid, role):
    async def _ov():
        return UserResponse(
            id=uid,
            username=username,
            email=f"{username}@e.mail",
            created_at="2025-01-01T00:00:00Z",
            is_active=True,
            role=role,
            plan="free",
        )

    return _ov


def test_classrooms_analytics_endpoint_own_rooms_only_and_contract():
    from types import SimpleNamespace

    room_a = SimpleNamespace(
        id="room-a",
        course_id="c",
        owner_id="prof-1",
        name="A",
        invite_code="A-1",
        term=None,
        schedule=None,
    )
    room_b = SimpleNamespace(
        id="room-b",
        course_id="c",
        owner_id="other",
        name="B",
        invite_code="B-1",
        term=None,
        schedule=None,
    )

    class _Rooms:
        async def list_owned_by_professor(self, owner_id):
            return [room_a] if owner_id == "prof-1" else []

        async def list_for_ta(self, user_id):
            return [room_b] if user_id == "ta-1" else []

        async def get_classroom_by_id(self, cid):
            return {"room-a": room_a, "room-b": room_b}.get(cid)

        async def list_classroom_student_ids(self, cid):
            return []

        async def list_classroom_student_ids_by_room(self, cids):
            return {c: [] for c in cids}

    class _Svc:
        async def class_overviews(self, rosters, total_lessons=10):
            from app.models.analytics_schemas import ClassAnalyticsResponse

            return {r: ClassAnalyticsResponse() for r in rosters}

    app.dependency_overrides[get_current_user] = _user("prof", "prof-1", "professor")
    app.dependency_overrides[get_classroom_repository] = lambda: _Rooms()
    app.dependency_overrides[get_class_analytics_service] = lambda: _Svc()
    try:
        with TestClient(app) as c:
            resp = c.get("/api/instructor/classrooms-analytics")
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert isinstance(body, list) and len(body) == 1
            assert set(body[0]) == {"classroom", "analytics"}
            assert body[0]["classroom"]["id"] == "room-a"
            assert set(body[0]["analytics"]) == {
                "total_students",
                "avg_completion",
                "avg_solved",
                "students",
            }
    finally:
        for dep in (
            get_current_user,
            get_classroom_repository,
            get_class_analytics_service,
        ):
            app.dependency_overrides.pop(dep, None)

    # TA sees only assigned rooms; students get 403.
    app.dependency_overrides[get_current_user] = _user("ta", "ta-1", "ta")
    app.dependency_overrides[get_classroom_repository] = lambda: _Rooms()
    app.dependency_overrides[get_class_analytics_service] = lambda: _Svc()
    try:
        with TestClient(app) as c:
            body = c.get("/api/instructor/classrooms-analytics").json()
            assert [r["classroom"]["id"] for r in body] == ["room-b"]
    finally:
        for dep in (
            get_current_user,
            get_classroom_repository,
            get_class_analytics_service,
        ):
            app.dependency_overrides.pop(dep, None)

    app.dependency_overrides[get_current_user] = _user("stu", "s-1", "user")
    try:
        with TestClient(app) as c:
            assert c.get("/api/instructor/classrooms-analytics").status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
