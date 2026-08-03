"""Tests for safe entity-ID validation (path-traversal guard).

Entity IDs are validated by the Pydantic admin models before any storage use.
"""

import pytest

from app.utils.ids import validate_entity_id


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
