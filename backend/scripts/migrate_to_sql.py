#!/usr/bin/env python3
"""Migrate JSON data files to SQL database.

Usage:
    python scripts/migrate_to_sql.py [--url DATABASE_URL]

Defaults to DATABASE_URL from .env or sqlite+aiosqlite:///./codecoach.db
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.inspection import inspect

from app.models.orm import Base, UserORM, QuestionORM, CourseORM, ModuleORM, LessonORM, CourseProgressORM
from app.models.schemas import Question


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        url = "sqlite+aiosqlite:///./codecoach.db"
    return url


def _load_json(path: Path) -> Any:
    if not path.exists():
        print(f"  SKIP: {path} not found")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _col_keys(model) -> set:
    return {c.key for c in inspect(model).columns}


_ORM_COLUMNS = {
    CourseORM: _col_keys(CourseORM),
    ModuleORM: _col_keys(ModuleORM),
    LessonORM: _col_keys(LessonORM),
}


async def migrate_users(session: AsyncSession, base_dir: Path) -> int:
    path = base_dir / "data" / "users.json"
    data = _load_json(path)
    if not data:
        return 0

    count = 0
    for item in data:
        try:
            item["created_at"] = datetime.fromisoformat(item["created_at"])
            session.add(UserORM(**item))
            count += 1
        except Exception as e:
            print(f"  ERROR migrating user {item.get('username', '?')}: {e}")
    return count


async def migrate_questions(session: AsyncSession, base_dir: Path) -> int:
    path = base_dir / "questions" / "sample_questions.json"
    data = _load_json(path)
    if not data:
        return 0

    questions = data.get("questions", data) if isinstance(data, dict) else data
    count = 0
    for item in questions:
        try:
            question = Question(**item)
            session.add(QuestionORM(
                id=question.id,
                title=question.title,
                difficulty=question.difficulty.value,
                category=question.category,
                company_tags=question.company_tags,
                description=question.description,
                starter_code=question.starter.model_dump()
                if hasattr(question.starter, "model_dump")
                else question.starter,
                examples=[e.model_dump() if hasattr(e, "model_dump") else e for e in question.examples],
                test_cases=[tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in question.test_cases],
                hints=question.hints,
                solution=question.solution,
                time_complexity=question.time_complexity,
                space_complexity=question.space_complexity,
                constraints=question.constraints,
                is_interactive=1 if question.is_interactive else 0,
            ))
            count += 1
        except Exception as e:
            title = item.get("title", "?")
            print(f"  ERROR migrating question '{title}': {e}")
    return count


async def migrate_courses(session: AsyncSession, base_dir: Path) -> Dict[str, int]:
    counts = {"courses": 0, "modules": 0, "lessons": 0}
    courses_dir = base_dir / "data" / "courses"

    if not courses_dir.exists():
        return counts

    for lang_dir in courses_dir.iterdir():
        if not lang_dir.is_dir():
            continue
        for course_dir in lang_dir.iterdir():
            if not course_dir.is_dir():
                continue

            cols = _ORM_COLUMNS[CourseORM]
            course_data = _load_json(course_dir / "course.json")
            if course_data:
                try:
                    session.add(CourseORM(**{k: v for k, v in course_data.items() if k in cols}))
                    counts["courses"] += 1
                except Exception as e:
                    print(f"  ERROR migrating course {course_dir.name}: {e}")

            cols = _ORM_COLUMNS[ModuleORM]
            modules_data = _load_json(course_dir / "modules.json")
            if modules_data:
                items = modules_data.get("items", [modules_data]) if isinstance(modules_data, dict) else modules_data
                if isinstance(items, dict):
                    items = [items]
                for m in items:
                    try:
                        session.add(ModuleORM(**{k: v for k, v in m.items() if k in cols}))
                        counts["modules"] += 1
                    except Exception as e:
                        print(f"  ERROR migrating module {m.get('id', '?')}: {e}")

            cols = _ORM_COLUMNS[LessonORM]
            lessons_data = _load_json(course_dir / "lessons.json")
            if lessons_data:
                items = lessons_data.get("items", [lessons_data]) if isinstance(lessons_data, dict) else lessons_data
                if isinstance(items, dict):
                    items = [items]
                for l in items:
                    try:
                        ldata = {k: v for k, v in l.items() if k in cols}
                        if ldata.get("test_cases") and isinstance(ldata["test_cases"], list):
                            ldata["test_cases"] = [
                                tc.model_dump() if hasattr(tc, "model_dump") else tc
                                for tc in ldata["test_cases"]
                            ]
                        session.add(LessonORM(**ldata))
                        counts["lessons"] += 1
                    except Exception as e:
                        print(f"  ERROR migrating lesson {l.get('id', '?')}: {e}")

    return counts


async def migrate_progress(session: AsyncSession, base_dir: Path) -> int:
    path = base_dir / "data" / "user_progress.json"
    data = _load_json(path)
    if not data:
        return 0

    items = data.get("items", data) if isinstance(data, dict) else data
    if isinstance(items, dict):
        items = [items]

    count = 0
    for item in items:
        try:
            if "started_at" in item and isinstance(item["started_at"], str):
                item["started_at"] = datetime.fromisoformat(item["started_at"])
            if "last_accessed_at" in item and isinstance(item["last_accessed_at"], str):
                item["last_accessed_at"] = datetime.fromisoformat(item["last_accessed_at"])
            item["id"] = f"{item['user_id']}:{item['course_id']}"
            session.add(CourseProgressORM(**item))
            count += 1
        except Exception as e:
            print(f"  ERROR migrating progress: {e}")
    return count


async def migrate():
    database_url = _get_database_url()
    base_dir = Path(__file__).parent.parent

    print(f"Migrating data to: {database_url}")
    print(f"Base directory: {base_dir}")
    print()

    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created/verified.")
    print()

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        users = await migrate_users(session, base_dir)
        print(f"  Users: {users}")

        questions = await migrate_questions(session, base_dir)
        print(f"  Questions: {questions}")

        course_counts = await migrate_courses(session, base_dir)
        print(f"  Courses: {course_counts['courses']}")
        print(f"  Modules: {course_counts['modules']}")
        print(f"  Lessons: {course_counts['lessons']}")

        progress = await migrate_progress(session, base_dir)
        print(f"  Progress records: {progress}")

        print()
        print("Committing...")
        await session.commit()
        print("Done!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
