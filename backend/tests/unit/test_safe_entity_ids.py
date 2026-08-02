"""Tests for safe entity-ID validation (path-traversal guard).

Entity IDs (course/module/lesson) are used as filesystem paths by the file
admin repository, so unsafe IDs must be rejected before any filesystem use.
"""

import tempfile
import pytest
from pathlib import Path

from app.utils.ids import validate_entity_id
from app.repositories.file_course_admin_repository import FileCourseAdminRepository


# ── validate_entity_id unit tests ───────────────────────


class TestValidateEntityId:
    @pytest.mark.parametrize(
        "entity_id",
        [
            "python-fundamentals",
            "c-programming",
            "module_01",
            "lesson-2",
            "a",
            "A1_b-c",
        ],
    )
    def test_accepts_valid_slugs(self, entity_id):
        assert validate_entity_id(entity_id) == entity_id

    @pytest.mark.parametrize(
        "entity_id",
        [
            "",
            "../etc",
            "..",
            "a/b",
            "a\\b",
            "has space",
            ".hidden",
            "-leading-dash",
            "/absolute",
            "a" * 101,
            None,
            123,
        ],
    )
    def test_rejects_unsafe_ids(self, entity_id):
        with pytest.raises(ValueError):
            validate_entity_id(entity_id)


# ── FileCourseAdminRepository path-traversal guard ──────


class TestCourseAdminRepositorySafePaths:
    @pytest.fixture
    def repo_and_tmp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            courses_dir = Path(tmpdir) / "courses"
            courses_dir.mkdir()
            repo = FileCourseAdminRepository(courses_dir=str(courses_dir))
            yield repo, Path(tmpdir)

    @pytest.mark.asyncio
    async def test_create_course_rejects_traversal(self, repo_and_tmp):
        repo, tmpdir = repo_and_tmp
        with pytest.raises(ValueError):
            await repo.create_course({"id": "../../escaped", "title": "Bad"})
        # No directory created outside the courses dir
        assert not (tmpdir / "escaped").exists()
        assert not (tmpdir / "courses" / "escaped").exists()

    @pytest.mark.asyncio
    async def test_delete_course_rejects_traversal(self, repo_and_tmp):
        repo, tmpdir = repo_and_tmp
        # Sentinel outside the courses dir must survive an attempted delete
        sentinel = tmpdir / "sentinel.txt"
        sentinel.write_text("keep me")
        with pytest.raises(ValueError):
            await repo.delete_course("../../sentinel.txt")
        assert sentinel.exists()
        assert sentinel.read_text() == "keep me"

    @pytest.mark.asyncio
    async def test_course_dir_rejects_unsafe_id(self, repo_and_tmp):
        repo, _ = repo_and_tmp
        for bad in ("../x", "a/b", "a\\b", "..", "has space"):
            with pytest.raises(ValueError):
                repo._course_dir(bad)

    @pytest.mark.asyncio
    async def test_valid_course_still_round_trips(self, repo_and_tmp):
        repo, _ = repo_and_tmp
        created = await repo.create_course(
            {
                "id": "valid-course",
                "title": "OK",
                "description": "",
                "language": "python",
                "order": 1,
            }
        )
        assert created["id"] == "valid-course"
        assert await repo.delete_course("valid-course") is True


# ── Admin API rejects unsafe IDs (Pydantic layer) ───────


class TestAdminApiSafeIds:
    @pytest.mark.parametrize(
        "bad_id",
        ["../../etc", "a/b", "a\\b", "has space", "..", ""],
    )
    def test_create_course_with_bad_id_returns_422(
        self, test_client, admin_headers, bad_id
    ):
        res = test_client.post(
            "/api/admin/courses",
            json={
                "id": bad_id,
                "title": "Bad",
                "description": "x",
                "language": "python",
                "order": 1,
            },
            headers=admin_headers,
        )
        assert res.status_code == 422

    def test_create_module_with_bad_ids_returns_422(self, test_client, admin_headers):
        res = test_client.post(
            "/api/admin/modules",
            json={
                "id": "../../mod",
                "course_id": "ok-course",
                "title": "M",
                "description": "x",
                "order": 1,
            },
            headers=admin_headers,
        )
        assert res.status_code == 422

    def test_create_lesson_with_bad_ids_returns_422(self, test_client, admin_headers):
        res = test_client.post(
            "/api/admin/lessons",
            json={
                "id": "ok-lesson",
                "course_id": "../../etc",
                "module_id": "ok-module",
                "title": "L",
                "type": "theory",
                "content": "x",
                "order": 1,
                "language": "python",
            },
            headers=admin_headers,
        )
        assert res.status_code == 422
