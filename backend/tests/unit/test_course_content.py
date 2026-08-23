"""Content guard for the committed curricula (F5).

Validates every course subtree in ``backend/data/courses`` against the
same schema pipeline the DB sync uses, and pins the C / Java language
courses to the F5 definition of done (>= 15 lessons each, mixed theory +
exercises, every exercise carrying starter code and test cases).
"""

from pathlib import Path

import pytest

from app.services.local_sync import load_curriculum

COURSES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "courses"


@pytest.fixture(scope="module")
def bundles():
    return load_curriculum(COURSES_DIR)


def _find(bundles, course_id):
    return next(b for b in bundles if b["course"].id == course_id)


class TestCurricula:
    def test_all_bundles_schema_valid(self, bundles):
        ids = [b["course"].id for b in bundles]
        assert {"c-programming", "java-programming"} <= set(ids), (
            f"committed curricula drifted: {sorted(ids)}"
        )

    def test_c_programming_meets_f5_targets(self, bundles):
        bundle = _find(bundles, "c-programming")
        assert len(bundle["modules"]) >= 2
        assert len(bundle["lessons"]) >= 15
        types = {ls.type for ls in bundle["lessons"]}
        assert {"theory", "exercise"} <= types

    def test_java_programming_meets_f5_targets(self, bundles):
        bundle = _find(bundles, "java-programming")
        assert len(bundle["modules"]) >= 2
        assert len(bundle["lessons"]) >= 15
        types = {ls.type for ls in bundle["lessons"]}
        assert {"theory", "exercise"} <= types

    @pytest.mark.parametrize("course_id", ["c-programming", "java-programming"])
    def test_every_exercise_is_runnable(self, bundles, course_id):
        bundle = _find(bundles, course_id)
        exercises = [ls for ls in bundle["lessons"] if ls.type == "exercise"]
        assert exercises, f"{course_id} has no exercises"
        for ex in exercises:
            assert ex.starter_code, f"{ex['id']} missing starter_code"
            assert ex.test_cases, f"{ex['id']} missing test_cases"
            assert ex.language == ("c" if course_id == "c-programming" else "java"), (
                f"{ex['id']} wrong language"
            )

    @pytest.mark.parametrize(
        "course_id",
        ["c-programming", "java-programming"],
    )
    def test_lesson_orders_unique_per_module(self, bundles, course_id):
        bundle = _find(bundles, course_id)
        by_module = {}
        for lesson in bundle["lessons"]:
            by_module.setdefault(lesson.module_id, []).append(lesson.order)
        for module_id, orders in by_module.items():
            assert len(orders) == len(set(orders)), (
                f"{course_id}/{module_id} has duplicate lesson order values"
            )
