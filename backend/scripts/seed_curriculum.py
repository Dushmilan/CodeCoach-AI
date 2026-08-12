#!/usr/bin/env python3
"""Seed curriculum (courses/modules/lessons) from JSON files into the DB.

Reads the layout expected by the app and used by migrate_to_sql.py:

    data/courses/<language>/<course-slug>/course.json
    data/courses/<language>/<course-slug>/modules.json
    data/courses/<language>/<course-slug>/lessons.json

Idempotent by default: any course/module/lesson whose id already exists is
skipped, so re-running the script is safe. Use --force to delete the course
subtree (course + modules + lessons) and insert it again.

--verify runs the pure-data integrity gate (schema lint + orphan checks) and,
when a database is reachable, compares DB row counts against the repository.

Usage:
    python scripts/seed_curriculum.py [--force] [--verify] [--url DATABASE_URL]
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from app.models.course_schemas import Course, Lesson, Module
from app.models.orm import CourseORM, LessonORM, ModuleORM, QuestionORM

from scripts.verify_curriculum import verify as verify_curriculum


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        url = "postgresql://codecoach:codecoach@host.docker.internal:5432/codecoach"
    # SQLAlchemy maps bare `postgresql://` to the sync psycopg2 driver; the
    # script is async, so force asyncpg for Postgres URLs.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _items(data: Any) -> List[Any]:
    """Normalize {"items": [...]} or a bare list to a list."""
    if isinstance(data, dict):
        items = data.get("items", [data])
        if isinstance(items, dict):
            return [items]
        return items
    if isinstance(data, list):
        return data
    return []


def _load_course_dir(course_dir: Path) -> Optional[dict]:
    """Load and validate the course subtree in a course directory."""
    course_data = _load_json(course_dir / "course.json")
    if not course_data:
        return None

    raw_modules = _items(_load_json(course_dir / "modules.json"))
    lessons = [
        Lesson(**item) for item in _items(_load_json(course_dir / "lessons.json"))
    ]

    module_lesson_ids: dict = {}
    for lesson in lessons:
        module_lesson_ids.setdefault(lesson.module_id, []).append(lesson.id)

    modules = [
        Module(**m, lessons=module_lesson_ids.get(m["id"], [])) for m in raw_modules
    ]
    course = Course(**course_data, modules=[m.id for m in modules])
    return {"course": course, "modules": modules, "lessons": lessons}


async def _question_ids(session: AsyncSession) -> set:
    result = await session.execute(select(QuestionORM.id))
    return set(result.scalars().all())


async def _db_counts(session: AsyncSession) -> dict:
    from sqlalchemy import func

    async def _count(model) -> int:
        result = await session.execute(select(func.count()).select_from(model))
        return result.scalar_one()

    return {
        "courses": await _count(CourseORM),
        "modules": await _count(ModuleORM),
        "lessons": await _count(LessonORM),
    }


async def verify(database_url: Optional[str] = None) -> int:
    """Run the pure-data integrity gate, then compare DB counts if reachable.

    Returns 0 on success, 1 on any failure. DB comparison is best-effort:
    if the database is unreachable we still pass on the pure-data checks.
    """
    base_dir = Path(__file__).parent.parent
    report = verify_curriculum(
        base_dir / "data" / "courses", base_dir / "questions" / "sample_questions.json"
    )
    print(
        f"Repo content OK: {report['courses']} course(s), {report['modules']} "
        f"module(s), {report['lessons']} lesson(s), {report['exercises']} exercise(s)."
    )

    if not database_url:
        print("No database URL — skipped DB count comparison (pure-data verify only).")
        return 0

    engine_kwargs = {}
    search_path = os.getenv("DATABASE_SEARCH_PATH")
    if search_path:
        engine_kwargs["connect_args"] = {
            "server_settings": {"search_path": search_path}
        }
    engine = create_async_engine(database_url, echo=False, **engine_kwargs)
    try:
        async with async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )() as session:
            db = await _db_counts(session)
    except Exception as exc:  # noqa: BLE001 - DB may be down during pure verify
        print(f"WARNING: database unreachable, skipping count comparison: {exc}")
        return 0
    finally:
        await engine.dispose()

    mismatches = []
    for key in ("courses", "modules", "lessons"):
        if report[key] != db[key]:
            mismatches.append(f"{key}: repo={report[key]} db={db[key]}")
    if mismatches:
        print(f"DB INTEGRITY MISMATCH — {', '.join(mismatches)}")
        return 1
    print("DB integrity OK: repo counts match database counts.")
    return 0


async def _course_exists(session: AsyncSession, course_id: str) -> bool:
    result = await session.execute(
        select(CourseORM.id).where(CourseORM.id == course_id).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _delete_course_subtree(session: AsyncSession, course_id: str):
    await session.execute(
        LessonORM.__table__.delete().where(LessonORM.course_id == course_id)
    )
    await session.execute(
        ModuleORM.__table__.delete().where(ModuleORM.course_id == course_id)
    )
    await session.execute(CourseORM.__table__.delete().where(CourseORM.id == course_id))


async def _seed_course(
    session: AsyncSession, bundle: dict, known_questions: set
) -> int:
    """Insert one course subtree. Returns number of lessons linked to questions."""
    course: Course = bundle["course"]

    if await _course_exists(session, course.id):
        print(f"  SKIP: course '{course.id}' already exists (use --force to re-seed)")
        return 0

    session.add(
        CourseORM(
            id=course.id,
            title=course.title,
            description=course.description,
            language=course.language,
            icon=course.icon,
            order=course.order,
        )
    )
    print(f"  Course: {course.id}")

    for module in bundle["modules"]:
        if module.course_id != course.id:
            print(f"  SKIP: module '{module.id}' course mismatch, skipping")
            continue
        session.add(
            ModuleORM(
                id=module.id,
                course_id=module.course_id,
                title=module.title,
                description=module.description,
                order=module.order,
            )
        )
        print(f"    Module: {module.id}")

    linked = 0
    for lesson in bundle["lessons"]:
        if lesson.course_id != course.id:
            print(f"  SKIP: lesson '{lesson.id}' course mismatch, skipping")
            continue
        if lesson.question_id:
            if lesson.question_id not in known_questions:
                print(
                    f"  WARN: lesson '{lesson.id}' links unknown question "
                    f"'{lesson.question_id}' — inserting without question link"
                )
                lesson.question_id = None
            else:
                linked += 1
        session.add(
            LessonORM(
                id=lesson.id,
                course_id=lesson.course_id,
                module_id=lesson.module_id,
                title=lesson.title,
                type=lesson.type.value,
                content=lesson.content,
                order=lesson.order,
                starter_code=lesson.starter_code,
                test_cases=(
                    [tc.model_dump() for tc in lesson.test_cases]
                    if lesson.test_cases
                    else None
                ),
                question_id=lesson.question_id,
                language=lesson.language,
            )
        )
        print(f"      Lesson: {lesson.id}")

    return linked


async def seed(force: bool = False):
    database_url = _get_database_url()
    base_dir = Path(__file__).parent.parent
    courses_dir = base_dir / "data" / "courses"

    print(f"Seeding curriculum into: {database_url}")
    print(f"Looking for curriculum under: {courses_dir}")
    print()

    if not courses_dir.exists():
        raise FileNotFoundError(f"{courses_dir} does not exist — nothing to seed")

    bundles = []
    for lang_dir in sorted(courses_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        for course_dir in sorted(lang_dir.iterdir()):
            if not course_dir.is_dir():
                continue
            bundle = _load_course_dir(course_dir)
            if bundle:
                bundles.append(bundle)

    if not bundles:
        print("No curriculum JSON found to seed.")
        return

    engine_kwargs = {}
    search_path = os.getenv("DATABASE_SEARCH_PATH")
    if search_path:
        engine_kwargs["connect_args"] = {
            "server_settings": {"search_path": search_path}
        }
    engine = create_async_engine(database_url, echo=False, **engine_kwargs)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        known_questions = await _question_ids(session)
        if force:
            for bundle in bundles:
                await _delete_course_subtree(session, bundle["course"].id)
            print("Cleared existing course subtrees (--force).")
            print()

        total_linked = 0
        for bundle in bundles:
            total_linked += await _seed_course(session, bundle, known_questions)

        await session.commit()
        print()
        print(
            f"Done! {len(bundles)} course(s) processed, {total_linked} exercise "
            f"lesson(s) linked to questions."
        )
        print(f"Questions available in bank: {len(known_questions)}")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed curriculum JSON into the database"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing course subtrees before seeding",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Validate repo content (and DB counts if reachable), then exit",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Database URL (overrides DATABASE_URL env var)",
    )
    args = parser.parse_args()

    if args.url:
        os.environ["DATABASE_URL"] = args.url

    if args.verify:
        sys.exit(asyncio.run(verify(database_url=_get_database_url())))

    asyncio.run(seed(force=args.force))
