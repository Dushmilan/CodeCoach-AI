import os
import urllib.parse
from urllib.parse import urlparse

import pymysql
from fastapi.testclient import TestClient


def _truncate_course_tables():
    """Remove courses/modules/lessons created by these tests so other tests
    see a clean course tree (mirrors the old file-based teardown_module)."""
    parsed = urlparse(
        os.environ["DATABASE_URL"].replace("mysql+aiomysql://", "mysql://")
    )
    conn = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=urllib.parse.unquote(parsed.username or ""),
        password=urllib.parse.unquote(parsed.password or ""),
        database=os.environ["DATABASE_URL"].rsplit("/", 1)[-1],
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            cur.execute("TRUNCATE TABLE course_progress")
            cur.execute("TRUNCATE TABLE lessons")
            cur.execute("TRUNCATE TABLE modules")
            cur.execute("TRUNCATE TABLE courses")
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    finally:
        conn.close()


def teardown_module():
    _truncate_course_tables()


def _admin_headers(test_client: TestClient) -> dict:
    """Register a user and promote to admin by updating the users table."""
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": "admincurriculum",
            "email": "admincurriculum@test.com",
            "password": "testpass123",
        },
    )
    if res.status_code != 201:
        res = test_client.post(
            "/api/auth/login",
            json={
                "username": "admincurriculum",
                "password": "testpass123",
            },
        )
    token = res.json()["access_token"]

    parsed = urlparse(
        os.environ["DATABASE_URL"].replace("mysql+aiomysql://", "mysql://")
    )
    conn = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=urllib.parse.unquote(parsed.username or ""),
        password=urllib.parse.unquote(parsed.password or ""),
        database=os.environ["DATABASE_URL"].rsplit("/", 1)[-1],
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET role='admin' WHERE username=%s",
                ("admincurriculum",),
            )
        conn.commit()
    finally:
        conn.close()

    return {"Authorization": f"Bearer {token}"}


class TestAdminCurriculumCRUD:
    """Integration tests for admin curriculum CRUD endpoints."""

    def test_create_course(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.post(
            "/api/admin/courses",
            json={
                "id": "test-python",
                "title": "Test Python Course",
                "description": "A test course",
                "language": "python",
                "order": 1,
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "test-python"
        assert data["title"] == "Test Python Course"

    def test_create_course_duplicate(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        test_client.post(
            "/api/admin/courses",
            json={
                "id": "dup-course",
                "title": "Duplicate",
                "description": "",
                "language": "python",
                "order": 1,
            },
            headers=headers,
        )
        res = test_client.post(
            "/api/admin/courses",
            json={
                "id": "dup-course",
                "title": "Duplicate",
                "description": "",
                "language": "python",
                "order": 2,
            },
            headers=headers,
        )
        assert res.status_code == 409

    def test_update_course(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        test_client.post(
            "/api/admin/courses",
            json={
                "id": "update-course",
                "title": "Original Title",
                "description": "Original",
                "language": "java",
                "order": 1,
            },
            headers=headers,
        )
        res = test_client.put(
            "/api/admin/courses/update-course",
            json={"title": "Updated Title", "description": "Updated desc"},
            headers=headers,
        )
        assert res.status_code == 200

        tree_res = test_client.get("/api/admin/courses/tree", headers=headers)
        courses = tree_res.json().get("courses", [])
        match = [c for c in courses if c["id"] == "update-course"]
        assert len(match) == 1
        assert match[0]["title"] == "Updated Title"

    def test_update_course_not_found(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.put(
            "/api/admin/courses/nonexistent",
            json={"title": "Nope"},
            headers=headers,
        )
        assert res.status_code == 404

    def test_create_module(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        test_client.post(
            "/api/admin/courses",
            json={
                "id": "course-for-modules",
                "title": "Course for Modules",
                "description": "",
                "language": "python",
                "order": 1,
            },
            headers=headers,
        )
        res = test_client.post(
            "/api/admin/modules",
            json={
                "id": "mod-1",
                "course_id": "course-for-modules",
                "title": "Getting Started",
                "description": "First module",
                "order": 1,
            },
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["id"] == "mod-1"

    def test_create_module_missing_course(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.post(
            "/api/admin/modules",
            json={
                "id": "orphan-mod",
                "course_id": "nonexistent-course",
                "title": "Orphan",
                "description": "",
                "order": 1,
            },
            headers=headers,
        )
        assert res.status_code == 404

    def test_update_module(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        test_client.post(
            "/api/admin/courses",
            json={
                "id": "course-mod-update",
                "title": "Module Update Course",
                "description": "",
                "language": "c",
                "order": 1,
            },
            headers=headers,
        )
        test_client.post(
            "/api/admin/modules",
            json={
                "id": "mod-to-update",
                "course_id": "course-mod-update",
                "title": "Old Module",
                "description": "Old desc",
                "order": 1,
            },
            headers=headers,
        )
        res = test_client.put(
            "/api/admin/modules/mod-to-update",
            json={"title": "Updated Module", "description": "New desc"},
            headers=headers,
        )
        assert res.status_code == 200

    def test_create_lesson(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        test_client.post(
            "/api/admin/courses",
            json={
                "id": "course-for-lessons",
                "title": "Lesson Course",
                "description": "",
                "language": "python",
                "order": 1,
            },
            headers=headers,
        )
        test_client.post(
            "/api/admin/modules",
            json={
                "id": "lesson-mod",
                "course_id": "course-for-lessons",
                "title": "Lesson Module",
                "description": "",
                "order": 1,
            },
            headers=headers,
        )
        res = test_client.post(
            "/api/admin/lessons",
            json={
                "id": "hello-world",
                "title": "Hello, World!",
                "type": "theory",
                "content": "# Hello\nWorld!",
                "order": 1,
                "language": "python",
                "module_id": "lesson-mod",
                "course_id": "course-for-lessons",
            },
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["id"] == "hello-world"

    def test_update_lesson(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.put(
            "/api/admin/lessons/hello-world",
            json={"title": "Hello Updated!", "content": "# Updated\nContent"},
            headers=headers,
        )
        assert res.status_code == 200

    def test_delete_lesson(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.delete(
            "/api/admin/lessons/hello-world",
            headers=headers,
        )
        assert res.status_code == 200

    def test_delete_module(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.delete(
            "/api/admin/modules/lesson-mod",
            headers=headers,
        )
        assert res.status_code == 200

    def test_delete_course(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.delete(
            "/api/admin/courses/test-python",
            headers=headers,
        )
        assert res.status_code == 200

    def test_delete_not_found(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.delete("/api/admin/courses/nonexistent", headers=headers)
        assert res.status_code == 404

    def test_create_question(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.post(
            "/api/admin/questions",
            json={
                "id": "admin-create-question-1",
                "title": "Admin Create Test Question",
                "difficulty": "easy",
                "category": "strings",
                "description": "Write a function to reverse a string.",
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "admin-create-question-1"

    def test_get_course_tree(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.get("/api/admin/courses/tree", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "courses" in data
        assert "modules" in data
        assert "lessons" in data
