#!/usr/bin/env python3
"""Shared helpers for building curriculum JSON from Python content modules.

Each course content module in this package defines COURSE, MODULES and LESSONS.
This module validates them with the app's Pydantic schemas and writes the
course.json / modules.json / lessons.json files expected by seed_curriculum.py.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.course_schemas import Course, Lesson, Module

DATA_COURSES = Path(__file__).parent.parent.parent / "data" / "courses"


def _items(data: Any) -> List[Any]:
    if isinstance(data, dict):
        items = data.get("items", [data])
        if isinstance(items, dict):
            return [items]
        return items
    if isinstance(data, list):
        return data
    return []


def _dump_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_course(
    language: str,
    course: Dict[str, Any],
    modules: List[Dict[str, Any]],
    lessons: List[Dict[str, Any]],
) -> Path:
    """Validate and write one course subtree. Returns the course directory."""
    lesson_models = [Lesson(**lesson) for lesson in lessons]
    module_lesson_ids: Dict[str, List[str]] = {}
    for lesson in lesson_models:
        module_lesson_ids.setdefault(lesson.module_id, []).append(lesson.id)
    module_models = [
        Module(**m, lessons=module_lesson_ids.get(m["id"], [])) for m in modules
    ]
    Course(**course, modules=[m.id for m in module_models])

    for module in module_models:
        if module.course_id != course["id"]:
            raise ValueError(
                f"module {module.id} course_id {module.course_id} != {course['id']}"
            )
    for lesson in lesson_models:
        if lesson.course_id != course["id"]:
            raise ValueError(
                f"lesson {lesson.id} course_id {lesson.course_id} != {course['id']}"
            )
        if lesson.module_id not in {m.id for m in module_models}:
            raise ValueError(
                f"lesson {lesson.id} references unknown module {lesson.module_id}"
            )

    ids = [lesson.id for lesson in lesson_models]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate lesson ids in course {course['id']}")

    course_dir = DATA_COURSES / language / course["id"]
    _dump_json(course_dir / "course.json", course)
    _dump_json(course_dir / "modules.json", {"items": modules})
    _dump_json(course_dir / "lessons.json", {"items": lessons})
    return course_dir


def load_course_dir(course_dir: Path) -> Dict[str, Any]:
    """Re-load a written course subtree (mirrors seed_curriculum)."""
    with open(course_dir / "course.json", "r", encoding="utf-8") as f:
        course_data = json.load(f)
    raw_modules = _items(json.load(open(course_dir / "modules.json", encoding="utf-8")))
    lessons = [
        Lesson(**item)
        for item in _items(
            json.load(open(course_dir / "lessons.json", encoding="utf-8"))
        )
    ]
    module_lesson_ids: dict = {}
    for lesson in lessons:
        module_lesson_ids.setdefault(lesson.module_id, []).append(lesson.id)
    modules = [
        Module(**m, lessons=module_lesson_ids.get(m["id"], [])) for m in raw_modules
    ]
    course = Course(**course_data, modules=[m.id for m in modules])
    return {"course": course, "modules": modules, "lessons": lessons}
