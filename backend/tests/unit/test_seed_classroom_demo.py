"""Issue #159 Task 4: demo classroom seed — professors, course owners, temp students.

Runs against an in-memory FakeSession (no database). The seed must:
- refuse to run unless explicitly allowed (SystemExit),
- upsert 2 professors + TA + 8 temp students,
- assign every course to professor.ada except data-structures → professor.grace,
- create 2 classrooms, 10 enrollments (8 student + 2 TA), 8 progress rows,
- be idempotent (second run changes nothing) and return an exact report dict.
"""

import sys
from pathlib import Path

import pytest
from sqlalchemy import Select, Update

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))


DEMO_COUNTS = {
    "mia": 30,
    "leo": 22,
    "ava": 18,
    "noah": 9,
    "zoe": 5,
    "eli": 21,
    "ivy": 12,
    "max": 4,
}
CS101_STUDENTS = ("mia", "leo", "ava", "noah", "zoe")
CS201_STUDENTS = ("eli", "ivy", "max")
EXPECTED_REPORT_KEYS = {
    "professors",
    "courses_assigned",
    "students",
    "enrollments",
    "progress",
}


class _FakeResult:
    def __init__(self, single=None, many=None):
        self._single = single
        self._many = many if many is not None else []

    def scalar_one_or_none(self):
        return self._single

    def scalars(self):
        return self

    def all(self):
        return list(self._many)


class FakeSession:
    """Minimal in-memory stand-in for AsyncSession (select-then-insert/update)."""

    def __init__(self):
        from app.models.orm import CourseORM

        self.users = {}
        self.courses = {}
        self.classrooms = {}
        self.enrollments = {}
        self.progress = {}
        self.added = []
        self.commits = 0
        # One pre-existing non-demo course + the data-structures course so the
        # assignment rule (data-structures → grace, rest → ada) is exercised.
        for cid, title in (
            ("python-advanced", "Python Advanced"),
            ("data-structures", "Data Structures"),
        ):
            self.courses[cid] = CourseORM(
                id=cid,
                title=title,
                description="pre-existing",
                language="python",
                order=9,
            )

    def _user_ids(self):
        return {u.id for u in self.users.values() if getattr(u, "id", None)}

    async def execute(self, stmt):
        from app.models.orm import (
            ClassroomEnrollmentORM,
            ClassroomORM,
            CourseORM,
            CourseProgressORM,
            UserORM,
        )

        if isinstance(stmt, Update):
            values = list(stmt.compile().params.values())
            course_id = next((v for v in values if v in self.courses), None)
            owner_id = next(
                (v for v in values if isinstance(v, str) and v in self._user_ids()),
                None,
            )
            if course_id is not None:
                self.courses[course_id].owner_id = owner_id
            return _FakeResult()
        assert isinstance(stmt, Select)
        entity = stmt.column_descriptions[0].get("entity")
        params = [v for v in stmt.compile().params.values() if isinstance(v, str)]
        if entity is UserORM:
            return _FakeResult(single=self.users.get(params[0]))
        if entity is CourseORM:
            if params:
                return _FakeResult(single=self.courses.get(params[0]))
            return _FakeResult(many=sorted(self.courses.values(), key=lambda c: c.id))
        if entity is ClassroomORM:
            return _FakeResult(single=self.classrooms.get(params[0]))
        if entity is ClassroomEnrollmentORM:
            key = (params[0], params[1])
            alt = (params[1], params[0])
            return _FakeResult(
                single=self.enrollments.get(key) or self.enrollments.get(alt)
            )
        if entity is CourseProgressORM:
            key = (params[0], params[1])
            alt = (params[1], params[0])
            return _FakeResult(single=self.progress.get(key) or self.progress.get(alt))
        raise AssertionError(f"unexpected entity {entity}")

    def add(self, obj):
        from app.models.orm import (
            ClassroomEnrollmentORM,
            ClassroomORM,
            CourseORM,
            CourseProgressORM,
            UserORM,
        )

        self.added.append(obj)
        if isinstance(obj, UserORM):
            self.users[obj.username] = obj
        elif isinstance(obj, CourseORM):
            self.courses[obj.id] = obj
        elif isinstance(obj, ClassroomORM):
            self.classrooms[obj.invite_code] = obj
        elif isinstance(obj, ClassroomEnrollmentORM):
            self.enrollments[(obj.classroom_id, obj.user_id)] = obj
        elif isinstance(obj, CourseProgressORM):
            self.progress[(obj.user_id, obj.course_id)] = obj
        else:
            raise AssertionError(f"unexpected add {type(obj)}")

    async def commit(self):
        self.commits += 1


async def _seed(session):
    import seed_classroom_demo

    return await seed_classroom_demo.seed_demo(session, allow=True)


async def test_refuses_without_allow_flag():
    import seed_classroom_demo

    with pytest.raises(SystemExit):
        await seed_classroom_demo.seed_demo(FakeSession(), allow=False)


async def test_seed_demo_gate_requires_both_env_vars(monkeypatch):
    import seed_classroom_demo

    monkeypatch.delenv("ALLOW_DEMO_SEED", raising=False)
    monkeypatch.delenv("DATABASE_SEARCH_PATH", raising=False)
    assert seed_classroom_demo._demo_seed_allowed() is False
    monkeypatch.setenv("ALLOW_DEMO_SEED", "1")
    assert seed_classroom_demo._demo_seed_allowed() is False
    monkeypatch.setenv("DATABASE_SEARCH_PATH", "codecoach_test")
    assert seed_classroom_demo._demo_seed_allowed() is True


async def test_grace_seed_entry_matches_admin_conventions():
    import seed_admin

    by_username = {u["username"]: u for u in seed_admin.INSTRUCTOR_SEED_USERS}
    grace = by_username["professor.grace"]
    assert grace["role"] == "professor"
    assert grace["email"] == "grace@university.edu"
    assert grace["password"], "seed professor.grace needs a dev password"
    assert len({u["username"] for u in seed_admin.INSTRUCTOR_SEED_USERS}) == len(
        seed_admin.INSTRUCTOR_SEED_USERS
    )
    assert len({u["email"] for u in seed_admin.INSTRUCTOR_SEED_USERS}) == len(
        seed_admin.INSTRUCTOR_SEED_USERS
    )


async def test_returns_exact_report_dict():
    report = await _seed(FakeSession())
    assert set(report) == EXPECTED_REPORT_KEYS
    assert report == {
        "professors": 2,
        "courses_assigned": 3,
        "students": 8,
        "enrollments": 10,
        "progress": 8,
    }


async def test_assigns_data_structures_to_grace_rest_to_ada():
    session = FakeSession()
    await _seed(session)
    ada_id = session.users["professor.ada"].id
    grace_id = session.users["professor.grace"].id
    assert session.users["professor.ada"].role == "professor"
    assert session.users["professor.grace"].role == "professor"
    assert session.courses["data-structures"].owner_id == grace_id
    assert session.courses["python-advanced"].owner_id == ada_id
    assert session.courses["python-fundamentals"].owner_id == ada_id


async def test_enrollments_use_explicit_roles_and_demo_split():
    from app.models.orm import ClassroomEnrollmentORM

    session = FakeSession()
    await _seed(session)
    enrolls = [o for o in session.added if isinstance(o, ClassroomEnrollmentORM)]
    assert len(enrolls) == 10
    cs101 = session.classrooms["CS101-A-2026"]
    cs201 = session.classrooms["CS201-B-2026"]
    assert {e.role for e in enrolls} == {"student", "ta"}
    by_user = {}
    for e in enrolls:
        by_user.setdefault(e.user_id, []).append(e)
    for u in CS101_STUDENTS:
        mine = by_user[session.users[u].id]
        assert len(mine) == 1
        assert mine[0].role == "student"
        assert mine[0].classroom_id == cs101.id
    for u in CS201_STUDENTS:
        mine = by_user[session.users[u].id]
        assert len(mine) == 1
        assert mine[0].role == "student"
        assert mine[0].classroom_id == cs201.id
    ta_id = session.users["demonstrator.turing"].id
    ta_mine = by_user[ta_id]
    assert len(ta_mine) == 2
    assert all(e.role == "ta" for e in ta_mine)
    assert {e.classroom_id for e in ta_mine} == {cs101.id, cs201.id}


async def test_temp_students_and_progress_mirror_demo_counts():
    from app.models.orm import CourseProgressORM

    session = FakeSession()
    await _seed(session)
    for username in DEMO_COUNTS:
        user = session.users[username]
        assert user.email == f"{username}@university.example"
    rows = [o for o in session.added if isinstance(o, CourseProgressORM)]
    assert len(rows) == 8
    cs101_course = session.classrooms["CS101-A-2026"].course_id
    cs201_course = session.classrooms["CS201-B-2026"].course_id
    for row in rows:
        username = next(u for u, obj in session.users.items() if obj.id == row.user_id)
        assert len(row.completed_lessons) == DEMO_COUNTS[username]
        expected_course = cs201_course if username in CS201_STUDENTS else cs101_course
        assert row.course_id == expected_course


async def test_second_run_changes_nothing():
    first = FakeSession()
    report_one = await _seed(first)
    added_once = len(first.added)
    report_two = await _seed(first)
    assert report_two == report_one
    assert len(first.added) == added_once
