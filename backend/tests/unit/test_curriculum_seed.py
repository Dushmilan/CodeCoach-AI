"""Validate the curriculum seed JSON files against the Pydantic schemas.

These tests are pure-data (no DB): they ensure the hand-authored curriculum
under backend/data/courses/ stays valid and that every exercise lesson links
to a question that actually exists in the sample question bank.
"""

import json
from collections import defaultdict
from pathlib import Path

import pytest

from app.models.course_schemas import Course, Lesson, Module

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CURRICULUM_DIR = BASE_DIR / "data" / "courses"
QUESTIONS_PATH = BASE_DIR / "questions" / "sample_questions.json"


def _items(data):
    if isinstance(data, dict):
        items = data.get("items", [data])
        return items if isinstance(items, list) else [items]
    return data


def _course_dirs():
    dirs = []
    if not CURRICULUM_DIR.exists():
        return dirs
    for lang_dir in sorted(CURRICULUM_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue
        for course_dir in sorted(lang_dir.iterdir()):
            if course_dir.is_dir() and (course_dir / "course.json").exists():
                dirs.append(course_dir)
    return dirs


def _module_lesson_ids(entry):
    module_ids = [m["id"] for m in entry["modules"]]
    return {
        m_id: [
            lesson["id"] for lesson in entry["lessons"] if lesson["module_id"] == m_id
        ]
        for m_id in module_ids
    }


@pytest.fixture(scope="module")
def seed_content():
    courses = []
    for d in _course_dirs():
        courses.append(
            {
                "dir": d,
                "course": json.loads((d / "course.json").read_text(encoding="utf-8")),
                "modules": _items(
                    json.loads((d / "modules.json").read_text(encoding="utf-8"))
                ),
                "lessons": _items(
                    json.loads((d / "lessons.json").read_text(encoding="utf-8"))
                ),
            }
        )
    return courses


@pytest.fixture(scope="module")
def bank_ids():
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    questions = data.get("questions", data) if isinstance(data, dict) else data
    return {q["id"] for q in questions}


class TestCurriculumSeedSchema:
    def test_at_least_one_course(self, seed_content):
        assert len(seed_content) >= 1

    def test_course_valid(self, seed_content):
        for entry in seed_content:
            modules = [
                Module(**m, lessons=_module_lesson_ids(entry)[m["id"]])
                for m in entry["modules"]
            ]
            course = Course(**entry["course"], modules=[m.id for m in modules])
            assert course.id
            assert course.language in {
                "python",
                "c",
                "java",
                "javascript",
                "bash",
                "r",
            }

    def test_modules_valid(self, seed_content):
        for entry in seed_content:
            cid = entry["course"]["id"]
            modules = [
                Module(**m, lessons=_module_lesson_ids(entry)[m["id"]])
                for m in entry["modules"]
            ]
            assert len(modules) >= 1
            assert all(m.course_id == cid for m in modules)

    def test_lessons_valid(self, seed_content):
        for entry in seed_content:
            cid = entry["course"]["id"]
            lessons = [Lesson(**item) for item in entry["lessons"]]
            assert len(lessons) >= 1
            assert all(lesson.course_id == cid for lesson in lessons)

    def test_unique_ids_across_curriculum(self, seed_content):
        assert len({e["course"]["id"] for e in seed_content}) == len(seed_content)
        all_module_ids = [m["id"] for e in seed_content for m in e["modules"]]
        assert len(all_module_ids) == len(set(all_module_ids))
        all_lesson_ids = [l_id["id"] for e in seed_content for l_id in e["lessons"]]
        assert len(all_lesson_ids) == len(set(all_lesson_ids))

    def test_lesson_modules_belong_to_course(self, seed_content):
        for entry in seed_content:
            module_ids = {m["id"] for m in entry["modules"]}
            for lesson in entry["lessons"]:
                assert lesson["module_id"] in module_ids

    def test_lesson_orders_unique_and_sorted_per_module(self, seed_content):
        for entry in seed_content:
            by_module = defaultdict(list)
            for lesson in entry["lessons"]:
                by_module[lesson["module_id"]].append(lesson["order"])
            for module_id, orders in by_module.items():
                assert len(set(orders)) == len(orders), (
                    f"duplicate lesson orders in {module_id}"
                )
                assert orders == sorted(orders), (
                    f"lesson orders not sequential in {module_id}"
                )

    def test_each_module_has_lessons(self, seed_content):
        for entry in seed_content:
            module_ids = {m["id"] for m in entry["modules"]}
            used_module_ids = {lesson["module_id"] for lesson in entry["lessons"]}
            assert module_ids == used_module_ids

    def test_exercise_lessons_link_to_existing_questions(self, seed_content, bank_ids):
        for entry in seed_content:
            for lesson in entry["lessons"]:
                if lesson["type"] == "exercise":
                    if lesson.get("question_id"):
                        assert lesson["question_id"] in bank_ids, (
                            f"exercise '{lesson['id']}' links unknown question "
                            f"'{lesson['question_id']}'"
                        )

    def test_exercises_are_question_linked_or_embedded(self, seed_content):
        """Every exercise must link to a bank question OR carry embedded
        starter_code + test_cases — never neither, never both.

        Practice lessons (type='practice') are open-ended design/build work
        with no automated grader, so they are exempt from this invariant.
        """
        for entry in seed_content:
            for lesson in entry["lessons"]:
                if lesson["type"] == "exercise":
                    has_question = bool(lesson.get("question_id"))
                    has_embedded = bool(
                        lesson.get("starter_code") or lesson.get("test_cases")
                    )
                    assert has_question != has_embedded, (
                        f"exercise '{lesson['id']}' must link a question OR embed "
                        f"starter_code/test_cases, not neither/both"
                    )
                    if has_embedded:
                        assert lesson.get("starter_code"), (
                            f"exercise '{lesson['id']}' is missing starter_code"
                        )
                        assert lesson.get("test_cases"), (
                            f"exercise '{lesson['id']}' is missing test_cases"
                        )

    def test_practice_lessons_are_open_ended(self, seed_content):
        """Practice lessons must not carry automated grading artifacts."""
        for entry in seed_content:
            for lesson in entry["lessons"]:
                if lesson["type"] == "practice":
                    assert not lesson.get("question_id"), (
                        f"practice lesson '{lesson['id']}' should not link a question"
                    )
                    assert not lesson.get("starter_code"), (
                        f"practice lesson '{lesson['id']}' should not embed starter_code"
                    )
                    assert not lesson.get("test_cases"), (
                        f"practice lesson '{lesson['id']}' should not embed test_cases"
                    )
