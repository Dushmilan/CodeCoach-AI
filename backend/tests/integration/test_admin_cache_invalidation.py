"""Integration tests: admin writes must invalidate read caches.

Learners must see admin-published content immediately:
- anonymous course list (in-memory TTL cache) reflects created courses
- course detail (Redis cache) reflects lesson updates
- question detail (Redis cache) reflects question updates
"""

import asyncio
import os
import uuid
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_redis_cache
from app.main import app
from app.services.redis_service import RedisCache
from tests.db_helpers import promote_to_admin, truncate_course_tables_sync

_TEST_REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")


def _redis_available() -> bool:
    import socket
    from urllib.parse import urlparse

    parts = urlparse(_TEST_REDIS_URL)
    try:
        with socket.create_connection((parts.hostname, parts.port or 6379), timeout=2):
            return True
    except OSError:
        return False


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _admin_headers(test_client: TestClient) -> dict:
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": "cacheadmin",
            "email": "cacheadmin@test.com",
            "password": "testpass123",
        },
    )
    if res.status_code != 201:
        res = test_client.post(
            "/api/auth/login",
            json={"username": "cacheadmin", "password": "testpass123"},
        )
    token = res.json()["access_token"]
    asyncio.run(promote_to_admin("cacheadmin"))
    return {"Authorization": f"Bearer {token}"}


@contextmanager
def live_redis_cache():
    cache = RedisCache(_TEST_REDIS_URL)
    app.dependency_overrides[get_redis_cache] = lambda: cache
    try:
        yield cache
    finally:
        app.dependency_overrides.pop(get_redis_cache, None)


def _clear_course_list_cache() -> None:
    from app.services.course_service import _course_list_cache

    _course_list_cache.clear()


def teardown_module():
    truncate_course_tables_sync()
    _clear_course_list_cache()


class TestCourseListInvalidation:
    def test_created_course_visible_immediately(self, test_client: TestClient):
        """Prime the anonymous list cache, create a course, re-list."""
        course_id = _uid("cache-course")
        try:
            # Prime the in-memory anonymous course-list cache.
            first = test_client.get("/api/courses/")
            assert first.status_code == 200

            headers = _admin_headers(test_client)
            created = test_client.post(
                "/api/admin/courses",
                json={
                    "id": course_id,
                    "title": "Cache Test Course",
                    "description": "staleness probe",
                    "language": "python",
                    "order": 1,
                },
                headers=headers,
            )
            assert created.status_code == 200

            second = test_client.get("/api/courses/")
            assert second.status_code == 200
            ids = [c["id"] for c in second.json()["courses"]]
            assert course_id in ids
        finally:
            headers = _admin_headers(test_client)
            test_client.delete(f"/api/admin/courses/{course_id}", headers=headers)
            truncate_course_tables_sync()
            _clear_course_list_cache()

    def test_deleted_course_disappears_immediately(self, test_client: TestClient):
        course_id = _uid("cache-course")
        headers = _admin_headers(test_client)
        try:
            test_client.post(
                "/api/admin/courses",
                json={
                    "id": course_id,
                    "title": "Cache Test Course",
                    "description": "staleness probe",
                    "language": "python",
                    "order": 1,
                },
                headers=headers,
            )
            # Prime cache with the course present.
            primed = test_client.get("/api/courses/")
            assert course_id in [c["id"] for c in primed.json()["courses"]]

            deleted = test_client.delete(
                f"/api/admin/courses/{course_id}", headers=headers
            )
            assert deleted.status_code == 200

            second = test_client.get("/api/courses/")
            ids = [c["id"] for c in second.json()["courses"]]
            assert course_id not in ids
        finally:
            test_client.delete(f"/api/admin/courses/{course_id}", headers=headers)
            truncate_course_tables_sync()
            _clear_course_list_cache()


@pytest.mark.skipif(not _redis_available(), reason="Redis unavailable")
class TestCourseDetailInvalidation:
    def test_lesson_update_visible_in_course_detail(self, test_client: TestClient):
        course_id = _uid("cache-course")
        module_id = _uid("cache-mod")
        lesson_id = _uid("cache-lesson")
        headers = _admin_headers(test_client)
        try:
            with live_redis_cache():
                test_client.post(
                    "/api/admin/courses",
                    json={
                        "id": course_id,
                        "title": "Cache Detail Course",
                        "description": "detail probe",
                        "language": "python",
                        "order": 1,
                    },
                    headers=headers,
                )
                test_client.post(
                    "/api/admin/modules",
                    json={
                        "id": module_id,
                        "course_id": course_id,
                        "title": "M",
                        "description": "m",
                        "order": 1,
                    },
                    headers=headers,
                )
                test_client.post(
                    "/api/admin/lessons",
                    json={
                        "id": lesson_id,
                        "course_id": course_id,
                        "module_id": module_id,
                        "title": "Original Lesson",
                        "type": "theory",
                        "content": "# v1",
                        "order": 1,
                        "language": "python",
                    },
                    headers=headers,
                )
                # Prime the Redis course-detail cache.
                primed = test_client.get(f"/api/courses/{course_id}")
                assert primed.status_code == 200

                updated = test_client.put(
                    f"/api/admin/lessons/{lesson_id}",
                    json={"title": "Updated Lesson"},
                    headers=headers,
                )
                assert updated.status_code == 200

                second = test_client.get(f"/api/courses/{course_id}")
                assert second.status_code == 200
                lessons = second.json()["modules"][0]["lessons"]
                assert lessons[0]["title"] == "Updated Lesson"
        finally:
            test_client.delete(f"/api/admin/courses/{course_id}", headers=headers)
            truncate_course_tables_sync()
            _clear_course_list_cache()


@pytest.mark.skipif(not _redis_available(), reason="Redis unavailable")
class TestQuestionDetailInvalidation:
    def test_question_update_visible_in_detail(self, test_client: TestClient):
        question_id = _uid("cache-q")
        headers = _admin_headers(test_client)
        try:
            with live_redis_cache():
                created = test_client.post(
                    "/api/admin/questions",
                    json={
                        "id": question_id,
                        "title": "Original Title",
                        "difficulty": "easy",
                        "category": "arrays",
                        "description": "probe",
                    },
                    headers=headers,
                )
                assert created.status_code == 200

                # Prime the Redis question-detail cache.
                primed = test_client.get(f"/api/questions/{question_id}")
                assert primed.status_code == 200
                assert primed.json()["title"] == "Original Title"

                updated = test_client.put(
                    f"/api/admin/questions/{question_id}",
                    json={"title": "Updated Title"},
                    headers=headers,
                )
                assert updated.status_code == 200

                second = test_client.get(f"/api/questions/{question_id}")
                assert second.status_code == 200
                assert second.json()["title"] == "Updated Title"
        finally:
            test_client.delete(f"/api/admin/questions/{question_id}", headers=headers)
