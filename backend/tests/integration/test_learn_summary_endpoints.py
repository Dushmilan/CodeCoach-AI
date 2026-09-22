"""Integration: single-fetch learn summary `GET /api/courses/?view=learn`
(issue #268).

Proves the minimal shape, the untouched default shape, strict view
validation, and end-to-end freshness: completing a lesson invalidates the
cached entry so the next learn fetch shows the new percentage despite the
hour-long TTL.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_redis_cache
from app.main import app
from app.services.redis_service import RedisCache
from tests.db_helpers import truncate_course_tables_sync
from tests.fixtures.auth_helpers import admin_headers, register_headers

pytestmark = pytest.mark.integration

_LEARN_KEYS = {
    "id",
    "title",
    "description",
    "language",
    "progress",
    "completed_lessons_count",
    "last_accessed_lesson_id",
}


@pytest.fixture
def redis_override():
    """Route get_redis_cache at a real Redis for one test, then restore."""
    app.dependency_overrides[get_redis_cache] = lambda: RedisCache(
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    )
    yield
    app.dependency_overrides.pop(get_redis_cache, None)


def _seed_course_with_lesson(test_client: TestClient, headers: dict) -> None:
    course = test_client.post(
        "/api/admin/courses",
        json={
            "id": "learn268-course",
            "title": "Learn268 Course",
            "description": "learn summary probe",
            "language": "python",
            "order": 97,
        },
        headers=headers,
    )
    assert course.status_code == 200
    module = test_client.post(
        "/api/admin/modules",
        json={
            "id": "learn268-module",
            "course_id": "learn268-course",
            "title": "Learn268 Module",
            "description": "learn summary probe",
            "order": 1,
        },
        headers=headers,
    )
    assert module.status_code == 200
    lesson = test_client.post(
        "/api/admin/lessons",
        json={
            "id": "learn268-lesson",
            "course_id": "learn268-course",
            "module_id": "learn268-module",
            "title": "Learn268 Lesson",
            "type": "theory",
            "content": "hello",
            "order": 1,
            "language": "python",
        },
        headers=headers,
    )
    assert lesson.status_code == 200


class TestLearnView:
    def test_learn_view_returns_minimal_shape(self, test_client: TestClient):
        truncate_course_tables_sync()
        admin = admin_headers(test_client, "learn268admin", "learn268admin@test.com")
        user = register_headers(test_client, "learn268user", "learn268user@test.com")
        try:
            _seed_course_with_lesson(test_client, admin)

            res = test_client.get("/api/courses/?view=learn", headers=user)

            assert res.status_code == 200
            rows = res.json()["courses"]
            assert len(rows) == 1
            assert set(rows[0]) == _LEARN_KEYS
            assert rows[0]["id"] == "learn268-course"
            assert rows[0]["progress"] == 0.0
        finally:
            truncate_course_tables_sync()

    def test_default_view_shape_unchanged(self, test_client: TestClient):
        truncate_course_tables_sync()
        admin = admin_headers(test_client, "learn268admin", "learn268admin@test.com")
        user = register_headers(test_client, "learn268user", "learn268user@test.com")
        try:
            _seed_course_with_lesson(test_client, admin)

            res = test_client.get("/api/courses/", headers=user)

            assert res.status_code == 200
            rows = res.json()["courses"]
            assert len(rows) == 1
            assert "description" in rows[0]
            assert "order" in rows[0]
        finally:
            truncate_course_tables_sync()

    def test_learn_view_rejects_unknown_view(self, test_client: TestClient):
        user = register_headers(test_client, "learn268user", "learn268user@test.com")
        res = test_client.get("/api/courses/?view=full", headers=user)
        assert res.status_code == 422

    def test_complete_lesson_refreshes_learn_summary(
        self, test_client: TestClient, redis_override
    ):
        truncate_course_tables_sync()
        admin = admin_headers(test_client, "learn268admin", "learn268admin@test.com")
        user = register_headers(test_client, "learn268user", "learn268user@test.com")
        try:
            _seed_course_with_lesson(test_client, admin)

            first = test_client.get("/api/courses/?view=learn", headers=user)
            assert first.status_code == 200
            assert first.json()["courses"][0]["progress"] == 0.0

            complete = test_client.post(
                "/api/progress/learn268-lesson/complete?course_id=learn268-course",
                headers=user,
            )
            assert complete.status_code == 200

            second = test_client.get("/api/courses/?view=learn", headers=user)
            assert second.status_code == 200
            row = second.json()["courses"][0]
            assert row["progress"] == 100.0
            assert row["completed_lessons_count"] == 1
            assert row["last_accessed_lesson_id"] == "learn268-lesson"
        finally:
            truncate_course_tables_sync()
