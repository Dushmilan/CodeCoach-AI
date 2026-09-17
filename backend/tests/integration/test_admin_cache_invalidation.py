"""Integration: admin catalog writes invalidate Redis caches.

Proves the Redis-backed anonymous course list never serves stale data after
create/update/delete of courses, and that question detail entries are
dropped on question delete (override is scoped to this module and removed
afterwards so the session app stays untouched for other tests).
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_redis_cache
from app.main import app
from app.services.redis_service import RedisCache
from tests.db_helpers import truncate_course_tables_sync
from tests.fixtures.auth_helpers import admin_headers

pytestmark = pytest.mark.integration


def _admin_headers(test_client: TestClient) -> dict:
    return admin_headers(test_client, "cacheinvalidation", "cacheinvalidation@test.com")


@pytest.fixture
def redis_override():
    """Route get_redis_cache at a real Redis for one test, then restore."""
    app.dependency_overrides[get_redis_cache] = lambda: RedisCache(
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    )
    yield
    app.dependency_overrides.pop(get_redis_cache, None)


def _course_ids(test_client: TestClient) -> list:
    res = test_client.get("/api/courses/")
    assert res.status_code == 200
    return [c["id"] for c in res.json()["courses"]]


class TestAdminCacheInvalidation:
    def test_create_then_delete_refreshes_anonymous_list(
        self, test_client: TestClient, redis_override
    ):
        truncate_course_tables_sync()
        headers = _admin_headers(test_client)
        try:
            assert "cache-bust-course" not in _course_ids(test_client)

            create = test_client.post(
                "/api/admin/courses",
                json={
                    "id": "cache-bust-course",
                    "title": "Cache Bust",
                    "description": "invalidation probe",
                    "language": "python",
                    "order": 99,
                },
                headers=headers,
            )
            assert create.status_code == 200
            assert "cache-bust-course" in _course_ids(test_client)

            delete = test_client.delete(
                "/api/admin/courses/cache-bust-course", headers=headers
            )
            assert delete.status_code == 200
            assert "cache-bust-course" not in _course_ids(test_client)
        finally:
            truncate_course_tables_sync()

    def test_update_lesson_refreshes_lesson_detail_cache(
        self, test_client: TestClient, redis_override
    ):
        truncate_course_tables_sync()
        headers = _admin_headers(test_client)
        lesson_id = "cache-lesson-1"
        try:
            course = test_client.post(
                "/api/admin/courses",
                json={
                    "id": "cache-lesson-course",
                    "title": "Cache Lesson Course",
                    "description": "lesson invalidation probe",
                    "language": "python",
                    "order": 98,
                },
                headers=headers,
            )
            assert course.status_code == 200

            module = test_client.post(
                "/api/admin/modules",
                json={
                    "id": "cache-lesson-module",
                    "course_id": "cache-lesson-course",
                    "title": "Cache Lesson Module",
                    "description": "lesson invalidation probe",
                    "order": 1,
                },
                headers=headers,
            )
            assert module.status_code == 200

            lesson = test_client.post(
                "/api/admin/lessons",
                json={
                    "id": lesson_id,
                    "course_id": "cache-lesson-course",
                    "module_id": "cache-lesson-module",
                    "title": "Cache Lesson",
                    "type": "theory",
                    "content": "version one",
                    "order": 1,
                    "language": "python",
                },
                headers=headers,
            )
            assert lesson.status_code == 200

            first = test_client.get(f"/api/courses/lessons/{lesson_id}")
            assert first.status_code == 200
            assert first.json()["content"] == "version one"

            update = test_client.put(
                f"/api/admin/lessons/{lesson_id}",
                json={"content": "version two"},
                headers=headers,
            )
            assert update.status_code == 200

            second = test_client.get(f"/api/courses/lessons/{lesson_id}")
            assert second.status_code == 200
            assert second.json()["content"] == "version two"
        finally:
            test_client.delete(f"/api/admin/lessons/{lesson_id}", headers=headers)
            truncate_course_tables_sync()

    def test_delete_question_drops_detail_cache(
        self, test_client: TestClient, redis_override
    ):
        headers = _admin_headers(test_client)
        qid = "cache-bust-question"
        test_client.delete(f"/api/admin/questions/{qid}", headers=headers)
        try:
            create = test_client.post(
                "/api/admin/questions",
                json={
                    "id": qid,
                    "title": "Cache Bust Question",
                    "difficulty": "easy",
                    "category": "arrays",
                    "description": "Reverse a string.",
                },
                headers=headers,
            )
            assert create.status_code == 200

            first = test_client.get(f"/api/questions/{qid}")
            assert first.status_code == 200

            delete = test_client.delete(f"/api/admin/questions/{qid}", headers=headers)
            assert delete.status_code == 200
            assert test_client.get(f"/api/questions/{qid}").status_code == 404
        finally:
            test_client.delete(f"/api/admin/questions/{qid}", headers=headers)
