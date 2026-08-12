"""Tests for the curriculum verifier (backend/scripts/verify_curriculum.py).

These are pure-data tests exercising the integrity gate on the checked-in
curriculum repository plus synthetic failure cases.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from verify_curriculum import (
    CurriculumError,
    _course_dirs,
    _items,
    verify,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CURRICULUM_DIR = BASE_DIR / "data" / "courses"
QUESTIONS_PATH = BASE_DIR / "questions" / "sample_questions.json"


@pytest.fixture(scope="module")
def bank_ids():
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    questions = data.get("questions", data) if isinstance(data, dict) else data
    return {q["id"] for q in questions}


class TestCurriculumVerifier:
    def test_real_curriculum_passes(self, bank_ids):
        report = verify(CURRICULUM_DIR, QUESTIONS_PATH)
        assert report["courses"] >= 1
        assert report["modules"] >= 1
        assert report["lessons"] >= 1

    def test_course_dirs_discovered(self):
        dirs = _course_dirs(CURRICULUM_DIR)
        assert len(dirs) >= 1
        assert all((d / "course.json").exists() for d in dirs)

    def test_items_normalization(self):
        assert _items({"items": [1, 2, 3]}) == [1, 2, 3]
        assert _items({"a": 1}) == [{"a": 1}]
        assert _items([1, 2]) == [1, 2]
        assert _items(None) == []

    def test_missing_curriculum_dir_raises(self, tmp_path):
        with pytest.raises(CurriculumError):
            _course_dirs(tmp_path / "nope")

    def test_invalid_json_raises(self, tmp_path):
        d = tmp_path / "lang" / "course"
        d.mkdir(parents=True)
        (d / "course.json").write_text("{not json", encoding="utf-8")
        (d / "modules.json").write_text("[]", encoding="utf-8")
        (d / "lessons.json").write_text("[]", encoding="utf-8")
        with pytest.raises(CurriculumError):
            verify(tmp_path, QUESTIONS_PATH)

    def test_duplicate_lesson_ids_raise(self, tmp_path, bank_ids):
        course_dir = tmp_path / "lang" / "dup"
        course_dir.mkdir(parents=True)
        (course_dir / "course.json").write_text(
            json.dumps(
                {
                    "id": "dup-course",
                    "title": "Dup",
                    "description": "d",
                    "language": "python",
                    "order": 1,
                    "version": 1,
                }
            ),
            encoding="utf-8",
        )
        (course_dir / "modules.json").write_text(
            json.dumps(
                [
                    {
                        "id": "m1",
                        "course_id": "dup-course",
                        "title": "M",
                        "description": "d",
                        "order": 1,
                        "version": 1,
                    }
                ]
            ),
            encoding="utf-8",
        )
        (course_dir / "lessons.json").write_text(
            json.dumps(
                [
                    {
                        "id": "l1",
                        "course_id": "dup-course",
                        "module_id": "m1",
                        "title": "A",
                        "type": "theory",
                        "content": "c",
                        "order": 1,
                        "language": "python",
                    },
                    {
                        "id": "l1",
                        "course_id": "dup-course",
                        "module_id": "m1",
                        "title": "B",
                        "type": "theory",
                        "content": "c",
                        "order": 2,
                        "language": "python",
                    },
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(CurriculumError, match="duplicate lesson"):
            verify(tmp_path, QUESTIONS_PATH)

    def test_orphan_module_reference_raises(self, tmp_path, bank_ids):
        course_dir = tmp_path / "lang" / "orphan"
        course_dir.mkdir(parents=True)
        (course_dir / "course.json").write_text(
            json.dumps(
                {
                    "id": "orphan-course",
                    "title": "Orphan",
                    "description": "d",
                    "language": "python",
                    "order": 1,
                }
            ),
            encoding="utf-8",
        )
        (course_dir / "modules.json").write_text(
            json.dumps(
                [
                    {
                        "id": "m1",
                        "course_id": "orphan-course",
                        "title": "M",
                        "description": "d",
                        "order": 1,
                    }
                ]
            ),
            encoding="utf-8",
        )
        (course_dir / "lessons.json").write_text(
            json.dumps(
                [
                    {
                        "id": "l1",
                        "course_id": "orphan-course",
                        "module_id": "UNKNOWN_MODULE",
                        "title": "A",
                        "type": "theory",
                        "content": "c",
                        "order": 1,
                        "language": "python",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(CurriculumError, match="unknown module"):
            verify(tmp_path, QUESTIONS_PATH)

    def test_exercise_unknown_question_raises(self, tmp_path):
        course_dir = tmp_path / "lang" / "badq"
        course_dir.mkdir(parents=True)
        (course_dir / "course.json").write_text(
            json.dumps(
                {
                    "id": "badq-course",
                    "title": "BadQ",
                    "description": "d",
                    "language": "python",
                    "order": 1,
                }
            ),
            encoding="utf-8",
        )
        (course_dir / "modules.json").write_text(
            json.dumps(
                [
                    {
                        "id": "m1",
                        "course_id": "badq-course",
                        "title": "M",
                        "description": "d",
                        "order": 1,
                    }
                ]
            ),
            encoding="utf-8",
        )
        (course_dir / "lessons.json").write_text(
            json.dumps(
                [
                    {
                        "id": "l1",
                        "course_id": "badq-course",
                        "module_id": "m1",
                        "title": "A",
                        "type": "exercise",
                        "content": "c",
                        "order": 1,
                        "language": "python",
                        "question_id": "does-not-exist",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(CurriculumError, match="unknown question"):
            verify(tmp_path, QUESTIONS_PATH)
