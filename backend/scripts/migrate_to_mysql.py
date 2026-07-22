"""Migrate JSON file data to MySQL.

Loads data from:
  - backend/data/users.json
  - backend/questions/sample_questions.json
  - backend/data/courses/ (course.json, modules.json, lessons.json per course)
  - backend/data/user_progress.json

And inserts into MySQL via SQLAlchemy ORM.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_maker, init_db
from app.models.orm import (
    UserORM,
    QuestionORM,
    CourseORM,
    ModuleORM,
    LessonORM,
    CourseProgressORM,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
QUESTIONS_DIR = BASE_DIR / "questions"
COURSES_DIR = DATA_DIR / "courses"


async def migrate_users():
    path = DATA_DIR / "users.json"
    if not path.exists():
        logger.info("No users.json found, skipping")
        return 0
    with open(path) as f:
        users = json.load(f)
    async with async_session_maker() as session:
        for u in users:
            exists = await session.execute(select(UserORM).where(UserORM.id == u["id"]))
            if exists.scalar():
                continue
            session.add(UserORM(**u))
        await session.commit()
    logger.info("Migrated %d users", len(users))
    return len(users)


async def migrate_questions():
    path = QUESTIONS_DIR / "sample_questions.json"
    if not path.exists():
        logger.info("No sample_questions.json found, skipping")
        return 0
    with open(path, encoding="utf-8") as f:
        questions = json.load(f)
    FIELD_MAP = {
        "starter": "starter_code",
    }
    async with async_session_maker() as session:
        for q in questions:
            exists = await session.execute(
                select(QuestionORM).where(QuestionORM.id == q["id"])
            )
            if exists.scalar():
                continue
            mapped = {}
            for k, v in q.items():
                orm_key = FIELD_MAP.get(k, k)
                mapped[orm_key] = v
            if "is_interactive" not in mapped:
                mapped["is_interactive"] = 0
            if mapped.get("starter_code") is None:
                mapped["starter_code"] = {}
            session.add(QuestionORM(**mapped))
        await session.commit()
    logger.info("Migrated %d questions", len(questions))
    return len(questions)


async def migrate_courses():
    if not COURSES_DIR.exists():
        logger.info("No courses directory found, skipping")
        return 0, 0, 0
    course_count = module_count = lesson_count = 0
    async with async_session_maker() as session:
        for course_dir in sorted(COURSES_DIR.iterdir()):
            if not course_dir.is_dir():
                continue
            course_file = course_dir / "course.json"
            modules_file = course_dir / "modules.json"
            lessons_file = course_dir / "lessons.json"

            if course_file.exists():
                with open(course_file) as f:
                    course_data = json.load(f)
                course_data.pop("modules", None)
                exists = await session.execute(
                    select(CourseORM).where(CourseORM.id == course_data["id"])
                )
                if not exists.scalar():
                    session.add(CourseORM(**course_data))
                    course_count += 1

            if modules_file.exists():
                with open(modules_file) as f:
                    modules = json.load(f)
                items = (
                    modules.get("items", modules)
                    if isinstance(modules, dict)
                    else modules
                )
                for m in items:
                    m.pop("lessons", None)
                    exists = await session.execute(
                        select(ModuleORM).where(ModuleORM.id == m["id"])
                    )
                    if not exists.scalar():
                        session.add(ModuleORM(**m))
                        module_count += 1

            if lessons_file.exists():
                with open(lessons_file) as f:
                    lessons = json.load(f)
                items = (
                    lessons.get("items", lessons)
                    if isinstance(lessons, dict)
                    else lessons
                )
                for le in items:
                    if not le.get("language"):
                        le["language"] = "python"
                    if not le.get("question_id"):
                        le["question_id"] = None
                    exists = await session.execute(
                        select(LessonORM).where(LessonORM.id == le["id"])
                    )
                    if not exists.scalar():
                        session.add(LessonORM(**le))
                        lesson_count += 1

        await session.commit()
    logger.info(
        "Migrated %d courses, %d modules, %d lessons",
        course_count,
        module_count,
        lesson_count,
    )
    return course_count, module_count, lesson_count


async def migrate_progress():
    path = DATA_DIR / "user_progress.json"
    if not path.exists():
        logger.info("No user_progress.json found, skipping")
        return 0
    with open(path) as f:
        data = json.load(f)
    items = data.get("items", data) if isinstance(data, dict) else data
    if isinstance(items, dict):
        items = [items]
    from datetime import datetime

    async with async_session_maker() as session:
        for p in items:
            if "id" not in p or not p["id"]:
                p["id"] = f"{p['user_id'][:8]}-{p['course_id']}"
            for key in ("started_at", "last_accessed_at"):
                if isinstance(p.get(key), str):
                    p[key] = datetime.fromisoformat(p[key].replace("Z", "+00:00"))
            with session.no_autoflush:
                user = await session.execute(
                    select(UserORM).where(UserORM.id == p["user_id"])
                )
                course = await session.execute(
                    select(CourseORM).where(CourseORM.id == p["course_id"])
                )
                if not user.scalar() or not course.scalar():
                    logger.warning(
                        "Skipping progress: missing user %s or course %s",
                        p["user_id"],
                        p["course_id"],
                    )
                    continue
                exists = await session.execute(
                    select(CourseProgressORM).where(
                        CourseProgressORM.user_id == p["user_id"],
                        CourseProgressORM.course_id == p["course_id"],
                    )
                )
                if exists.scalar():
                    continue
                session.add(CourseProgressORM(**p))
        await session.commit()
    logger.info("Migrated %d progress entries", len(items))
    return len(items)


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    logger.info("Creating database tables...")
    await init_db()

    logger.info("Migrating users...")
    u = await migrate_users()

    logger.info("Migrating questions...")
    q = await migrate_questions()

    logger.info("Migrating courses...")
    c, m, le = await migrate_courses()

    logger.info("Migrating progress...")
    p = await migrate_progress()

    logger.info(
        "Migration complete: %d users, %d questions, %d courses, %d modules, %d lessons, %d progress entries",
        u,
        q,
        c,
        m,
        le,
        p,
    )


if __name__ == "__main__":
    asyncio.run(main())
