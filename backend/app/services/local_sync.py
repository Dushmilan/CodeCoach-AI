"""Idempotent, non-destructive sync of local seed content into the database.

Reads the checked-in question bank and curriculum JSON and upserts it into the
connected database: rows that are missing are inserted, rows that already exist
are updated in place, and unrelated database data is never deleted.

The database is the source of truth; the local files are a one-time bootstrap
that can be removed once the sync has run. Re-running this sync is safe.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_schemas import Course, Lesson, Module
from app.models.orm import CourseORM, LessonORM, ModuleORM, QuestionORM
from app.models.schemas import Question

logger = logging.getLogger(__name__)


class LocalSyncError(Exception):
    """Raised when local content cannot be loaded or schema-validated."""


@dataclass
class SyncReport:
    questions_inserted: int = 0
    questions_updated: int = 0
    courses_inserted: int = 0
    courses_updated: int = 0
    modules_inserted: int = 0
    modules_updated: int = 0
    lessons_inserted: int = 0
    lessons_updated: int = 0
    lessons_linked: int = 0
    lessons_unlinked: int = 0

    def summary(self) -> str:
        return (
            f"questions: {self.questions_inserted} inserted, "
            f"{self.questions_updated} updated; "
            f"courses: {self.courses_inserted} inserted, {self.courses_updated} updated; "
            f"modules: {self.modules_inserted} inserted, {self.modules_updated} updated; "
            f"lessons: {self.lessons_inserted} inserted, {self.lessons_updated} updated, "
            f"{self.lessons_linked} linked, {self.lessons_unlinked} unlinked"
        )


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise LocalSyncError(f"invalid JSON in {path}: {exc}") from exc


def _items(data: Any) -> List[Any]:
    """Normalize {"items": [...]} or a bare list to a list."""
    if isinstance(data, dict):
        items = data.get("items", [data])
        return items if isinstance(items, list) else [items]
    if isinstance(data, list):
        return data
    return []


def load_questions(path: Path) -> List[Question]:
    """Load and schema-validate the question bank. Empty when the file is absent."""
    data = _load_json(path)
    if not data:
        logger.info("No question bank found at %s — nothing to sync.", path)
        return []
    questions = data.get("questions", data) if isinstance(data, dict) else data
    parsed = []
    for item in questions:
        try:
            parsed.append(Question(**item))
        except Exception as exc:  # noqa: BLE001 - surface the offending item
            title = item.get("title", "?") if isinstance(item, dict) else "?"
            raise LocalSyncError(f"invalid question '{title}': {exc}") from exc
    return parsed


def load_curriculum(courses_dir: Path) -> List[Dict[str, Any]]:
    """Load and schema-validate every course subtree under ``courses_dir``."""
    if not courses_dir.exists():
        logger.info("No curriculum dir at %s — nothing to sync.", courses_dir)
        return []

    bundles = []
    for lang_dir in sorted(courses_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        for course_dir in sorted(lang_dir.iterdir()):
            if not course_dir.is_dir():
                continue
            course_data = _load_json(course_dir / "course.json")
            if not course_data:
                continue
            try:
                raw_modules = _items(_load_json(course_dir / "modules.json"))
                raw_lessons = _items(_load_json(course_dir / "lessons.json"))
                module_lesson_ids: Dict[str, List[str]] = {}
                for ls in raw_lessons:
                    module_lesson_ids.setdefault(ls["module_id"], []).append(ls["id"])
                modules = [
                    Module(**m, lessons=module_lesson_ids.get(m["id"], []))
                    for m in raw_modules
                ]
                lessons = [Lesson(**ls) for ls in raw_lessons]
                course = Course(**course_data, modules=[m.id for m in modules])
            except Exception as exc:  # noqa: BLE001 - surface the offending dir
                raise LocalSyncError(
                    f"invalid curriculum under {course_dir}: {exc}"
                ) from exc
            bundles.append({"course": course, "modules": modules, "lessons": lessons})
    return bundles


def _question_to_orm(q: Question) -> QuestionORM:
    return QuestionORM(
        id=q.id,
        title=q.title,
        difficulty=q.difficulty.value,
        category=q.category,
        company_tags=q.company_tags,
        description=q.description,
        starter_code=q.starter.model_dump()
        if hasattr(q.starter, "model_dump")
        else q.starter,
        examples=[
            e.model_dump() if hasattr(e, "model_dump") else e for e in q.examples
        ],
        test_cases=[
            tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in q.test_cases
        ],
        hints=q.hints,
        solution=q.solution,
        time_complexity=q.time_complexity,
        space_complexity=q.space_complexity,
        constraints=q.constraints,
        is_interactive=1 if q.is_interactive else 0,
    )


async def _upsert(session: AsyncSession, model, obj) -> str:
    """Insert ``obj`` or update the row with the same primary key. Returns
    ``"insert"`` or ``"update"``."""
    existing = await session.get(model, obj.id)
    if existing is None:
        session.add(obj)
        return "insert"
    for key, value in obj.__dict__.items():
        if key == "_sa_instance_state":
            continue
        setattr(existing, key, value)
    return "update"


async def _existing_ids(session: AsyncSession, model) -> set:
    result = await session.execute(select(model.id))
    return {row[0] for row in result.all()}


async def sync(
    session: AsyncSession,
    questions_path: Path,
    courses_dir: Path,
) -> SyncReport:
    """Upsert local question + curriculum content into ``session``.

    Never deletes existing database rows. Callers are responsible for
    committing (and rolling back on error).
    """
    report = SyncReport()

    questions = load_questions(questions_path)
    for q in questions:
        outcome = await _upsert(session, QuestionORM, _question_to_orm(q))
        if outcome == "insert":
            report.questions_inserted += 1
        else:
            report.questions_updated += 1
    await session.flush()

    known_questions = await _existing_ids(session, QuestionORM)

    for bundle in load_curriculum(courses_dir):
        course = bundle["course"]
        outcome = await _upsert(
            session,
            CourseORM,
            CourseORM(
                id=course.id,
                title=course.title,
                description=course.description,
                language=course.language,
                icon=course.icon,
                order=course.order,
            ),
        )
        if outcome == "insert":
            report.courses_inserted += 1
        else:
            report.courses_updated += 1

        for module in bundle["modules"]:
            outcome = await _upsert(
                session,
                ModuleORM,
                ModuleORM(
                    id=module.id,
                    course_id=module.course_id,
                    title=module.title,
                    description=module.description,
                    order=module.order,
                ),
            )
            if outcome == "insert":
                report.modules_inserted += 1
            else:
                report.modules_updated += 1

        for lesson in bundle["lessons"]:
            question_id = lesson.question_id
            if question_id and question_id not in known_questions:
                logger.warning(
                    "Lesson '%s' links unknown question '%s' — inserting unlinked.",
                    lesson.id,
                    question_id,
                )
                question_id = None
                report.lessons_unlinked += 1
            elif question_id:
                report.lessons_linked += 1

            outcome = await _upsert(
                session,
                LessonORM,
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
                    question_id=question_id,
                    language=lesson.language,
                ),
            )
            if outcome == "insert":
                report.lessons_inserted += 1
            else:
                report.lessons_updated += 1

    return report
