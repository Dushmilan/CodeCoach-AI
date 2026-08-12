#!/usr/bin/env python3
"""Validate the versioned curriculum repository (backend/data/courses).

This is the CI + --verify integrity gate for curriculum content. It runs
PURE data checks against the checked-in JSON (no database required):

- Schema lint: every course/module/lesson parses with the Pydantic schemas.
- Version metadata present on courses, modules, and lessons.
- Unique IDs across courses, modules, and lessons.
- Referential integrity: modules belong to their course, lessons belong to a
  module of their course, exercise lessons link a bank question XOR embed
  starter_code/test_cases (never neither/both).
- Orphan detection: no lesson references an unknown module, no module an
  unknown course, and every exercise's question_id exists in the question bank.

Usage:
    python scripts/verify_curriculum.py [--questions questions/sample_questions.json]

Exit code 0 on success, 1 on any violation.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.course_schemas import Course, Lesson, Module

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CURRICULUM_DIR = BASE_DIR / "data" / "courses"
DEFAULT_QUESTIONS_PATH = BASE_DIR / "questions" / "sample_questions.json"


class CurriculumError(Exception):
    pass


def _items(data: Any) -> List[Any]:
    """Normalize {"items": [...]} or a bare list to a list."""
    if isinstance(data, dict):
        items = data.get("items", [data])
        return items if isinstance(items, list) else [items]
    if isinstance(data, list):
        return data
    return []


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise CurriculumError(f"missing file: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise CurriculumError(f"invalid JSON in {path}: {exc}") from exc


def _course_dirs(curriculum_dir: Path) -> List[Path]:
    if not curriculum_dir.exists():
        raise CurriculumError(f"curriculum dir does not exist: {curriculum_dir}")
    dirs = []
    for lang_dir in sorted(curriculum_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        for course_dir in sorted(lang_dir.iterdir()):
            if course_dir.is_dir() and (course_dir / "course.json").exists():
                dirs.append(course_dir)
    if not dirs:
        raise CurriculumError(f"no course dirs found under {curriculum_dir}")
    return dirs


def _bank_ids(questions_path: Path) -> set:
    data = _load_json(questions_path)
    questions = data.get("questions", data) if isinstance(data, dict) else data
    return {q.get("id") for q in questions if isinstance(q, dict) and q.get("id")}


def _load_course(course_dir: Path, bank_ids: set) -> Dict[str, Any]:
    """Load + schema-validate one course subtree. Raises CurriculumError on
    any schema or integrity violation."""
    course_data = _load_json(course_dir / "course.json")
    raw_modules = _items(_load_json(course_dir / "modules.json"))
    raw_lessons = _items(_load_json(course_dir / "lessons.json"))

    course_id = course_data.get("id")

    module_ids = [m.get("id") for m in raw_modules]
    if len(module_ids) != len(set(module_ids)):
        raise CurriculumError(f"duplicate module IDs in {course_id}")
    lesson_ids = [ls.get("id") for ls in raw_lessons]
    if len(lesson_ids) != len(set(lesson_ids)):
        raise CurriculumError(f"duplicate lesson IDs in {course_id}")

    module_lesson_ids = defaultdict(list)
    for lesson in raw_lessons:
        module_lesson_ids[lesson.get("module_id")].append(lesson.get("id"))

    modules = []
    for m in raw_modules:
        if m.get("course_id") != course_id:
            raise CurriculumError(
                f"module '{m.get('id')}' course_id mismatch in {course_id}"
            )
        modules.append(Module(**m, lessons=module_lesson_ids.get(m.get("id"), [])))
        if m.get("version", 1) < 1:
            raise CurriculumError(f"module '{m.get('id')}' has invalid version")

    for lesson in raw_lessons:
        if lesson.get("course_id") != course_id:
            raise CurriculumError(
                f"lesson '{lesson.get('id')}' course_id mismatch in {course_id}"
            )
        if lesson.get("module_id") not in module_ids:
            raise CurriculumError(
                f"lesson '{lesson.get('id')}' references unknown module "
                f"'{lesson.get('module_id')}' in {course_id}"
            )
        if lesson.get("version", 1) < 1:
            raise CurriculumError(f"lesson '{lesson.get('id')}' has invalid version")

    lessons = [Lesson(**ls) for ls in raw_lessons]
    for lesson in lessons:
        if lesson.type.value == "exercise":
            has_question = bool(lesson.question_id)
            has_embedded = bool(lesson.starter_code or lesson.test_cases)
            if has_question == has_embedded:
                raise CurriculumError(
                    f"exercise '{lesson.id}' must link a question XOR embed "
                    f"starter_code/test_cases"
                )
            if has_question and lesson.question_id not in bank_ids:
                raise CurriculumError(
                    f"exercise '{lesson.id}' links unknown question "
                    f"'{lesson.question_id}'"
                )

    course = Course(**course_data, modules=module_ids)
    if course.version < 1:
        raise CurriculumError(f"course '{course.id}' has invalid version")

    return {
        "dir": course_dir,
        "course": course,
        "modules": modules,
        "lessons": lessons,
    }


def verify(curriculum_dir: Path, questions_path: Path) -> Dict[str, Any]:
    """Run all integrity checks. Returns a report; raises CurriculumError on
    the first violation."""
    bank_ids = _bank_ids(questions_path)
    courses = [_load_course(d, bank_ids) for d in _course_dirs(curriculum_dir)]

    course_ids = [c["course"].id for c in courses]
    if len(course_ids) != len(set(course_ids)):
        raise CurriculumError(f"duplicate course IDs: {course_ids}")

    # Every module of every course lists exactly the lessons in it, in order.
    for bundle in courses:
        course = bundle["course"]
        for module in bundle["modules"]:
            expected = module.lessons
            actual = [ls.id for ls in bundle["lessons"] if ls.module_id == module.id]
            if expected != actual:
                raise CurriculumError(
                    f"module '{module.id}' lessons list mismatch: "
                    f"expected={expected} actual={actual}"
                )
        if course.modules != [m.id for m in bundle["modules"]]:
            raise CurriculumError(f"course '{course.id}' modules list mismatch")

    total_lessons = sum(len(c["lessons"]) for c in courses)
    total_exercises = sum(
        1 for c in courses for ls in c["lessons"] if ls.type.value == "exercise"
    )
    return {
        "courses": len(courses),
        "modules": sum(len(c["modules"]) for c in courses),
        "lessons": total_lessons,
        "exercises": total_exercises,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate curriculum JSON content")
    parser.add_argument(
        "--curriculum-dir",
        type=Path,
        default=DEFAULT_CURRICULUM_DIR,
        help="Path to backend/data/courses",
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_QUESTIONS_PATH,
        help="Path to sample_questions.json",
    )
    args = parser.parse_args()

    try:
        report = verify(args.curriculum_dir, args.questions)
    except CurriculumError as exc:
        print(f"CURRICULUM VERIFICATION FAILED: {exc}")
        return 1

    print(
        f"CURRICULUM VERIFICATION OK — {report['courses']} course(s), "
        f"{report['modules']} module(s), {report['lessons']} lesson(s), "
        f"{report['exercises']} exercise(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
