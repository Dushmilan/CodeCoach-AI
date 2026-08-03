"""Integration tests for the curriculum seed script against MySQL.

Runs seed_curriculum.py against the codecoach_test database and verifies
idempotency (re-running does not duplicate rows) and that exercise lessons
keep their question links.
"""

import json
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.models.orm import CourseORM, LessonORM, ModuleORM, QuestionORM

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CURRICULUM_DIR = BASE_DIR / "data" / "courses"

sys.path.insert(0, str(BASE_DIR / "scripts"))
import seed_curriculum  # noqa: E402


def _items(data):
    if isinstance(data, dict):
        items = data.get("items", [data])
        return items if isinstance(items, list) else [items]
    return data


def _referenced_question_ids() -> set:
    ids = set()
    for lang_dir in CURRICULUM_DIR.iterdir():
        if not lang_dir.is_dir():
            continue
        for course_dir in lang_dir.iterdir():
            lessons_path = course_dir / "lessons.json"
            if not lessons_path.exists():
                continue
            lessons = _items(json.loads(lessons_path.read_text(encoding="utf-8")))
            for lesson in lessons:
                if lesson.get("question_id"):
                    ids.add(lesson["question_id"])
    return ids


def _expected_counts() -> dict:
    courses = modules = lessons = 0
    for lang_dir in CURRICULUM_DIR.iterdir():
        if not lang_dir.is_dir():
            continue
        for course_dir in lang_dir.iterdir():
            if not (course_dir / "course.json").exists():
                continue
            courses += 1
            modules += len(
                _items(json.loads((course_dir / "modules.json").read_text("utf-8")))
            )
            lessons += len(
                _items(json.loads((course_dir / "lessons.json").read_text("utf-8")))
            )
    return {"courses": courses, "modules": modules, "lessons": lessons}


@pytest_asyncio.fixture
async def seeded_curriculum(test_db):
    """Insert question stubs, run seed_curriculum, then clean up the tables
    so the test_db teardown can re-seed the full question bank."""
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        for qid in _referenced_question_ids():
            session.add(
                QuestionORM(
                    id=qid,
                    title="seed-ref",
                    difficulty="easy",
                    category="strings",
                    description="minimal seed reference row",
                )
            )
        await session.commit()

    await seed_curriculum.seed()

    yield async_session

    async with async_session() as session:
        await session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        await session.execute(LessonORM.__table__.delete())
        await session.execute(ModuleORM.__table__.delete())
        await session.execute(CourseORM.__table__.delete())
        await session.execute(
            QuestionORM.__table__.delete().where(QuestionORM.title == "seed-ref")
        )
        await session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        await session.commit()

    await engine.dispose()


class TestCurriculumSeed:
    @pytest.mark.asyncio
    async def test_seed_inserts_expected_rows(self, seeded_curriculum):
        async with seeded_curriculum() as session:
            expected = _expected_counts()
            course_count = (
                await session.execute(select(func.count()).select_from(CourseORM))
            ).scalar()
            module_count = (
                await session.execute(select(func.count()).select_from(ModuleORM))
            ).scalar()
            lesson_count = (
                await session.execute(select(func.count()).select_from(LessonORM))
            ).scalar()
            assert course_count == expected["courses"]
            assert module_count == expected["modules"]
            assert lesson_count == expected["lessons"]

    @pytest.mark.asyncio
    async def test_seed_is_idempotent(self, seeded_curriculum):
        await seed_curriculum.seed()

        async with seeded_curriculum() as session:
            expected = _expected_counts()
            for model in (CourseORM, ModuleORM, LessonORM):
                total = (
                    await session.execute(select(func.count()).select_from(model))
                ).scalar()
                distinct = (
                    await session.execute(select(func.count(func.distinct(model.id))))
                ).scalar()
                assert total == distinct, f"duplicate rows in {model.__tablename__}"
            course_count = (
                await session.execute(select(func.count()).select_from(CourseORM))
            ).scalar()
            assert course_count == expected["courses"]

    @pytest.mark.asyncio
    async def test_exercise_lessons_keep_question_links(self, seeded_curriculum):
        async with seeded_curriculum() as session:
            result = await session.execute(
                select(LessonORM).where(LessonORM.type == "exercise")
            )
            lessons = result.scalars().all()
            assert lessons, "no exercise lessons seeded"
            for lesson in lessons:
                has_question = bool(lesson.question_id)
                has_embedded = bool(lesson.starter_code or lesson.test_cases)
                assert has_question != has_embedded, (
                    f"exercise lesson '{lesson.id}' must link a question OR embed "
                    f"starter_code/test_cases, not neither/both"
                )
