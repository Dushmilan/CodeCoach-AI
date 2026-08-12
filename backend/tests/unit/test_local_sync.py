"""Tests for the idempotent local->DB sync service.

The sync service upserts the checked-in question bank + curriculum JSON into
the database: it inserts missing rows, updates rows that already exist, and
never deletes unrelated database data. These tests run against the isolated
``codecoach_test`` schema using synthetic fixture content (no real data files).
"""

import json

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.models.orm import CourseORM, LessonORM, ModuleORM, QuestionORM
from app.services.local_sync import (
    LocalSyncError,
    load_curriculum,
    load_questions,
    sync,
)

BANK_FILE = "sample_questions.json"


def _write_bank(path, questions):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(questions), encoding="utf-8")


def _write_curriculum(courses_dir, bundles):
    for bundle in bundles:
        lang_dir = courses_dir / bundle["language"]
        course_dir = lang_dir / bundle["course"]["id"]
        course_dir.mkdir(parents=True, exist_ok=True)
        (course_dir / "course.json").write_text(
            json.dumps(bundle["course"]), encoding="utf-8"
        )
        (course_dir / "modules.json").write_text(
            json.dumps(bundle["modules"]), encoding="utf-8"
        )
        (course_dir / "lessons.json").write_text(
            json.dumps(bundle["lessons"]), encoding="utf-8"
        )


@pytest.fixture
def bank_data():
    return [
        {
            "id": "q-1",
            "title": "Two Sum",
            "difficulty": "easy",
            "category": "arrays",
            "company_tags": ["Google"],
            "description": "Find the pair that sums to the target.",
            "starter": {
                "python": "def two_sum(nums, target):\n    pass",
                "javascript": "function twoSum(nums, target) {}",
                "java": "class Solution { public int[] twoSum(int[] nums, int target) {} }",
            },
            "examples": [
                {"input": "[2,7,11,15],9", "output": "[0,1]", "explanation": "Basic"}
            ],
            "test_cases": [
                {"input": "[2,7,11,15]\n9", "expected_output": "[0,1]", "hidden": False}
            ],
            "hints": ["Use a hash map."],
            "solution": "def two_sum(nums, target):\n    seen = {}\n",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "constraints": ["2 <= nums.length <= 10^4"],
            "is_interactive": False,
        }
    ]


@pytest.fixture
def curriculum_bundles():
    course = {
        "id": "course-1",
        "title": "C Fundamentals",
        "description": "Foundations of C.",
        "language": "c",
        "icon": "code",
        "order": 1,
        "version": 1,
    }
    module = {
        "id": "mod-1",
        "course_id": "course-1",
        "title": "Basics",
        "description": "First module.",
        "order": 1,
        "version": 1,
    }
    lesson_theory = {
        "id": "lesson-1",
        "course_id": "course-1",
        "module_id": "mod-1",
        "title": "Intro to C",
        "type": "theory",
        "content": "# Intro",
        "order": 1,
        "version": 1,
        "language": "c",
    }
    lesson_exercise = {
        "id": "lesson-2",
        "course_id": "course-1",
        "module_id": "mod-1",
        "title": "Two Sum",
        "type": "exercise",
        "content": "Solve it",
        "order": 2,
        "version": 1,
        "language": "c",
        "question_id": "q-1",
    }
    return [
        {
            "language": "c",
            "course": course,
            "modules": [module],
            "lessons": [lesson_theory, lesson_exercise],
        }
    ]


class TestLoaders:
    def test_load_questions_parses_bank(self, tmp_path):
        bank = tmp_path / BANK_FILE
        _write_bank(bank, [{"id": "x", "title": "X", "difficulty": "hard"}])
        with pytest.raises(LocalSyncError):
            load_questions(bank)

    def test_load_questions_missing_file_returns_empty(self, tmp_path):
        assert load_questions(tmp_path / "nope.json") == []

    def test_load_curriculum_missing_dir_returns_empty(self, tmp_path):
        assert load_curriculum(tmp_path / "nope") == []

    def test_load_curriculum_parses_bundles(self, tmp_path, curriculum_bundles):
        courses_dir = tmp_path / "courses"
        _write_curriculum(courses_dir, curriculum_bundles)
        bundles = load_curriculum(courses_dir)
        assert len(bundles) == 1
        assert bundles[0]["course"].id == "course-1"
        assert [m.id for m in bundles[0]["modules"]] == ["mod-1"]
        assert [ls.id for ls in bundles[0]["lessons"]] == ["lesson-1", "lesson-2"]

    def test_load_curriculum_invalid_course_raises(self, tmp_path):
        courses_dir = tmp_path / "courses"
        bundle = {
            "language": "c",
            "course": {"id": "bad", "title": "X"},
            "modules": [],
            "lessons": [],
        }
        _write_curriculum(courses_dir, [bundle])
        with pytest.raises(LocalSyncError):
            load_curriculum(courses_dir)


class TestLocalSync:
    @pytest_asyncio.fixture
    async def seeded(self, test_db, tmp_path, bank_data, curriculum_bundles):
        bank = tmp_path / BANK_FILE
        courses_dir = tmp_path / "data" / "courses"
        _write_bank(bank, bank_data)
        _write_curriculum(courses_dir, curriculum_bundles)
        report = await sync(test_db, bank, courses_dir)
        await test_db.commit()
        return test_db, report

    @pytest.mark.asyncio
    async def test_sync_inserts_all_content(self, seeded):
        db, report = seeded
        assert report.questions_inserted == 1
        assert report.courses_inserted == 1
        assert report.modules_inserted == 1
        assert report.lessons_inserted == 2
        assert report.lessons_linked == 1

        q = await db.get(QuestionORM, "q-1")
        assert q is not None
        assert q.title == "Two Sum"

        course = await db.get(CourseORM, "course-1")
        assert course is not None
        module = await db.get(ModuleORM, "mod-1")
        assert module is not None
        assert module.course_id == "course-1"

        lesson = await db.get(LessonORM, "lesson-2")
        assert lesson is not None
        assert lesson.type == "exercise"
        assert lesson.question_id == "q-1"

    @pytest.mark.asyncio
    async def test_sync_is_idempotent(
        self, test_db, tmp_path, bank_data, curriculum_bundles
    ):
        bank = tmp_path / BANK_FILE
        courses_dir = tmp_path / "data" / "courses"
        _write_bank(bank, bank_data)
        _write_curriculum(courses_dir, curriculum_bundles)

        first = await sync(test_db, bank, courses_dir)
        await test_db.commit()
        second = await sync(test_db, bank, courses_dir)
        await test_db.commit()

        assert first.questions_inserted == 1
        assert second.questions_inserted == 0
        assert second.questions_updated == 1
        assert second.courses_inserted == 0
        assert second.courses_updated == 1
        assert second.modules_inserted == 0
        assert second.lessons_inserted == 0

        total = (
            await test_db.execute(select(func.count()).select_from(QuestionORM))
        ).scalar()
        assert total == 1

    @pytest.mark.asyncio
    async def test_sync_updates_existing_matching_id(
        self, test_db, tmp_path, bank_data, curriculum_bundles
    ):
        test_db.add(
            QuestionORM(
                id="q-1",
                title="Old Title",
                difficulty="easy",
                category="arrays",
                description="old",
            )
        )
        await test_db.commit()

        bank = tmp_path / BANK_FILE
        courses_dir = tmp_path / "data" / "courses"
        _write_bank(bank, bank_data)
        _write_curriculum(courses_dir, curriculum_bundles)

        report = await sync(test_db, bank, courses_dir)
        await test_db.commit()

        assert report.questions_updated == 1
        q = await test_db.get(QuestionORM, "q-1")
        assert q.title == "Two Sum"

    @pytest.mark.asyncio
    async def test_sync_preserves_existing_unrelated_rows(
        self, test_db, tmp_path, bank_data, curriculum_bundles
    ):
        test_db.add(
            QuestionORM(
                id="q-keep",
                title="Keep Me",
                difficulty="medium",
                category="strings",
                description="untouched",
            )
        )
        await test_db.commit()

        bank = tmp_path / BANK_FILE
        courses_dir = tmp_path / "data" / "courses"
        _write_bank(bank, bank_data)
        _write_curriculum(courses_dir, curriculum_bundles)

        await sync(test_db, bank, courses_dir)
        await test_db.commit()

        keep = await test_db.get(QuestionORM, "q-keep")
        assert keep is not None
        assert keep.title == "Keep Me"

    @pytest.mark.asyncio
    async def test_sync_unlinks_lesson_with_unknown_question(
        self, test_db, tmp_path, bank_data, curriculum_bundles
    ):
        curriculum_bundles[0]["lessons"].append(
            {
                "id": "lesson-3",
                "course_id": "course-1",
                "module_id": "mod-1",
                "title": "Orphan",
                "type": "exercise",
                "content": "solve",
                "order": 3,
                "version": 1,
                "language": "c",
                "question_id": "q-missing",
            }
        )
        bank = tmp_path / BANK_FILE
        courses_dir = tmp_path / "data" / "courses"
        _write_bank(bank, bank_data)
        _write_curriculum(courses_dir, curriculum_bundles)

        report = await sync(test_db, bank, courses_dir)
        await test_db.commit()

        assert report.lessons_unlinked == 1
        lesson = await test_db.get(LessonORM, "lesson-3")
        assert lesson.question_id is None
