"""Tests for the 3 backend bug fixes:
1. Cache invalidation (FileCourseRepository.reload)
2. Parent ID lists maintained on create
3. Delete cleans parent references
"""

import json
import tempfile
import pytest
from pathlib import Path

from app.repositories.file_course_repository import FileCourseRepository
from app.repositories.file_admin_repository import FileAdminRepository


@pytest.fixture
def tmp_courses_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def admin_repo(tmp_courses_dir):
    return FileAdminRepository(courses_dir=tmp_courses_dir)


@pytest.fixture
def course_repo(tmp_courses_dir):
    return FileCourseRepository(courses_dir=tmp_courses_dir)


# ── Bug 1: Cache invalidation ──────────────────────────


class TestCacheInvalidation:
    @pytest.mark.asyncio
    async def test_reload_picks_up_new_courses(self, tmp_courses_dir):
        repo = FileCourseRepository(courses_dir=tmp_courses_dir)
        courses = await repo.get_all_courses()
        assert len(courses) == 0

        # Create a course directly on disk
        course_dir = Path(tmp_courses_dir) / "new-course"
        course_dir.mkdir()
        with open(course_dir / "course.json", "w") as f:
            json.dump(
                {
                    "id": "new-course",
                    "title": "New",
                    "description": "",
                    "language": "python",
                    "order": 1,
                    "modules": [],
                },
                f,
            )

        # Without reload, still empty
        courses = await repo.get_all_courses()
        assert len(courses) == 0

        # After reload, visible
        repo.reload()
        courses = await repo.get_all_courses()
        assert len(courses) == 1
        assert courses[0].id == "new-course"

    @pytest.mark.asyncio
    async def test_reload_picks_up_new_modules(self, tmp_courses_dir):
        course_dir = Path(tmp_courses_dir) / "my-course"
        course_dir.mkdir()
        with open(course_dir / "course.json", "w") as f:
            json.dump(
                {
                    "id": "my-course",
                    "title": "My Course",
                    "description": "",
                    "language": "python",
                    "order": 1,
                    "modules": [],
                },
                f,
            )
        with open(course_dir / "modules.json", "w") as f:
            json.dump({"items": []}, f)

        repo = FileCourseRepository(courses_dir=tmp_courses_dir)
        modules = await repo.get_modules_by_course("my-course")
        assert len(modules) == 0

        # Add module on disk
        with open(course_dir / "modules.json", "w") as f:
            json.dump(
                {
                    "items": [
                        {
                            "id": "mod-1",
                            "course_id": "my-course",
                            "title": "Module 1",
                            "description": "",
                            "order": 1,
                            "lessons": [],
                        }
                    ]
                },
                f,
            )
        # Also add module ID to course's modules list
        with open(course_dir / "course.json", "w") as f:
            json.dump(
                {
                    "id": "my-course",
                    "title": "My Course",
                    "description": "",
                    "language": "python",
                    "order": 1,
                    "modules": ["mod-1"],
                },
                f,
            )

        repo.reload()
        modules = await repo.get_modules_by_course("my-course")
        assert len(modules) == 1
        assert modules[0].id == "mod-1"

    @pytest.mark.asyncio
    async def test_reload_clears_deleted_data(self, tmp_courses_dir):
        course_dir = Path(tmp_courses_dir) / "del-course"
        course_dir.mkdir()
        with open(course_dir / "course.json", "w") as f:
            json.dump(
                {
                    "id": "del-course",
                    "title": "Delete Me",
                    "description": "",
                    "language": "python",
                    "order": 1,
                    "modules": [],
                },
                f,
            )

        repo = FileCourseRepository(courses_dir=tmp_courses_dir)
        courses = await repo.get_all_courses()
        assert len(courses) == 1

        # Delete on disk
        import shutil

        shutil.rmtree(course_dir)

        repo.reload()
        courses = await repo.get_all_courses()
        assert len(courses) == 0


# ── Bug 2: Parent ID lists on create ───────────────────


class TestParentIdListsOnCreate:
    @pytest.mark.asyncio
    async def test_create_module_adds_id_to_course(self, admin_repo, course_repo):
        await admin_repo.create_course(
            {
                "id": "c1",
                "title": "Course 1",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        await admin_repo.create_module(
            {
                "id": "m1",
                "course_id": "c1",
                "title": "Module 1",
                "description": "",
                "order": 1,
            }
        )

        course_repo.reload()
        course = await course_repo.get_course_by_id("c1")
        assert course is not None
        assert "m1" in course.modules

    @pytest.mark.asyncio
    async def test_create_lesson_adds_id_to_module(self, admin_repo, course_repo):
        await admin_repo.create_course(
            {
                "id": "c2",
                "title": "Course 2",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        await admin_repo.create_module(
            {
                "id": "m2",
                "course_id": "c2",
                "title": "Module 2",
                "description": "",
                "order": 1,
            }
        )
        await admin_repo.create_lesson(
            {
                "id": "l1",
                "course_id": "c2",
                "module_id": "m2",
                "title": "Lesson 1",
                "type": "theory",
                "content": "# Hello",
                "order": 1,
                "language": "python",
            }
        )

        course_repo.reload()
        module = await course_repo.get_module_by_id("m2")
        assert module is not None
        assert "l1" in module.lessons

    @pytest.mark.asyncio
    async def test_multiple_modules_all_appear_in_course(self, admin_repo, course_repo):
        await admin_repo.create_course(
            {
                "id": "c3",
                "title": "Course 3",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        for i in range(3):
            await admin_repo.create_module(
                {
                    "id": f"m{i}",
                    "course_id": "c3",
                    "title": f"Module {i}",
                    "description": "",
                    "order": i + 1,
                }
            )

        course_repo.reload()
        course = await course_repo.get_course_by_id("c3")
        assert len(course.modules) == 3
        assert set(course.modules) == {"m0", "m1", "m2"}


# ── Bug 3: Delete cleans parent references ─────────────


class TestDeleteCleansParentReferences:
    @pytest.mark.asyncio
    async def test_delete_module_removes_from_course(self, admin_repo, course_repo):
        await admin_repo.create_course(
            {
                "id": "c4",
                "title": "Course 4",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        await admin_repo.create_module(
            {
                "id": "m4",
                "course_id": "c4",
                "title": "Module 4",
                "description": "",
                "order": 1,
            }
        )

        course_repo.reload()
        course = await course_repo.get_course_by_id("c4")
        assert "m4" in course.modules

        await admin_repo.delete_module("m4")

        course_repo.reload()
        course = await course_repo.get_course_by_id("c4")
        assert "m4" not in course.modules

    @pytest.mark.asyncio
    async def test_delete_lesson_removes_from_module(self, admin_repo, course_repo):
        await admin_repo.create_course(
            {
                "id": "c5",
                "title": "Course 5",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        await admin_repo.create_module(
            {
                "id": "m5",
                "course_id": "c5",
                "title": "Module 5",
                "description": "",
                "order": 1,
            }
        )
        await admin_repo.create_lesson(
            {
                "id": "l5",
                "course_id": "c5",
                "module_id": "m5",
                "title": "Lesson 5",
                "type": "theory",
                "content": "# Hello",
                "order": 1,
                "language": "python",
            }
        )

        course_repo.reload()
        module = await course_repo.get_module_by_id("m5")
        assert "l5" in module.lessons

        await admin_repo.delete_lesson("l5")

        course_repo.reload()
        module = await course_repo.get_module_by_id("m5")
        assert "l5" not in module.lessons

    @pytest.mark.asyncio
    async def test_delete_module_cascades_lessons_from_parent(
        self, admin_repo, course_repo
    ):
        await admin_repo.create_course(
            {
                "id": "c6",
                "title": "Course 6",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        await admin_repo.create_module(
            {
                "id": "m6",
                "course_id": "c6",
                "title": "Module 6",
                "description": "",
                "order": 1,
            }
        )
        await admin_repo.create_lesson(
            {
                "id": "l6a",
                "course_id": "c6",
                "module_id": "m6",
                "title": "Lesson 6a",
                "type": "theory",
                "content": "# A",
                "order": 1,
                "language": "python",
            }
        )
        await admin_repo.create_lesson(
            {
                "id": "l6b",
                "course_id": "c6",
                "module_id": "m6",
                "title": "Lesson 6b",
                "type": "exercise",
                "content": "# B",
                "order": 2,
                "language": "python",
            }
        )

        # Delete module should also remove lessons and clean course.modules
        await admin_repo.delete_module("m6")

        course_repo.reload()
        course = await course_repo.get_course_by_id("c6")
        assert "m6" not in course.modules

        module = await course_repo.get_module_by_id("m6")
        assert module is None

        lesson_a = await course_repo.get_lesson_by_id("l6a")
        assert lesson_a is None
        lesson_b = await course_repo.get_lesson_by_id("l6b")
        assert lesson_b is None


# ── Integration: full create/read/delete cycle ─────────


class TestFullCycle:
    @pytest.mark.asyncio
    async def test_create_module_lesson_appears_in_course_tree(
        self, admin_repo, course_repo
    ):
        """End-to-end: create course -> module -> lesson, verify nested data."""
        await admin_repo.create_course(
            {
                "id": "e2e-course",
                "title": "E2E Course",
                "description": "End to end",
                "language": "python",
                "order": 1,
            }
        )
        await admin_repo.create_module(
            {
                "id": "e2e-mod",
                "course_id": "e2e-course",
                "title": "E2E Module",
                "description": "",
                "order": 1,
            }
        )
        await admin_repo.create_lesson(
            {
                "id": "e2e-lesson",
                "course_id": "e2e-course",
                "module_id": "e2e-mod",
                "title": "E2E Lesson",
                "type": "theory",
                "content": "# E2E Content",
                "order": 1,
                "language": "python",
            }
        )

        course_repo.reload()
        course = await course_repo.get_course_by_id("e2e-course")
        assert course is not None
        assert "e2e-mod" in course.modules

        modules = await course_repo.get_modules_by_course("e2e-course")
        assert len(modules) == 1
        assert modules[0].id == "e2e-mod"
        assert "e2e-lesson" in modules[0].lessons

        lessons = await course_repo.get_lessons_by_module("e2e-mod")
        assert len(lessons) == 1
        assert lessons[0].id == "e2e-lesson"

    @pytest.mark.asyncio
    async def test_full_delete_cycle(self, admin_repo, course_repo):
        """End-to-end: create everything, delete module, verify clean state."""
        await admin_repo.create_course(
            {
                "id": "del-course",
                "title": "Delete Course",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        await admin_repo.create_module(
            {
                "id": "del-mod",
                "course_id": "del-course",
                "title": "Delete Module",
                "description": "",
                "order": 1,
            }
        )
        await admin_repo.create_lesson(
            {
                "id": "del-lesson",
                "course_id": "del-course",
                "module_id": "del-mod",
                "title": "Delete Lesson",
                "type": "theory",
                "content": "# Delete",
                "order": 1,
                "language": "python",
            }
        )

        # Delete the module
        await admin_repo.delete_module("del-mod")

        course_repo.reload()
        course = await course_repo.get_course_by_id("del-course")
        assert "del-mod" not in course.modules

        # Delete the course
        await admin_repo.delete_course("del-course")

        course_repo.reload()
        course = await course_repo.get_course_by_id("del-course")
        assert course is None
