import os

import pymysql
from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
COURSES_DIR = os.path.join(DATA_DIR, "courses")


def _cleanup_test_dirs():
    """Remove leftover test course directories after tests."""
    test_dirs = [
        "test-python",
        "dup-course",
        "update-course",
        "course-for-modules",
        "course-mod-update",
        "course-for-lessons",
    ]
    for d in test_dirs:
        path = os.path.join(COURSES_DIR, d)
        if os.path.isdir(path):
            import shutil

            shutil.rmtree(path, ignore_errors=True)


def _cleanup_test_data():
    """Remove test courses from MySQL between tests."""
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="#Dush@17897@$#",
        db="codecoach",
        charset="utf8mb4",
    )
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM lessons WHERE course_id IN ('test-python','dup-course','update-course','course-for-modules','course-mod-update','course-for-lessons')"
        )
        cur.execute(
            "DELETE FROM modules WHERE course_id IN ('test-python','dup-course','update-course','course-for-modules','course-mod-update','course-for-lessons')"
        )
        cur.execute(
            "DELETE FROM courses WHERE id IN ('test-python','dup-course','update-course','course-for-modules','course-mod-update','course-for-lessons')"
        )
        cur.execute("DELETE FROM questions WHERE id IN ('test-q-1')")
        conn.commit()
    conn.close()


def _admin_headers(test_client: TestClient) -> dict:
    """Register a user and promote to admin via MySQL."""
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

    # Promote to admin directly in MySQL
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="#Dush@17897@$#",
        db="codecoach",
        charset="utf8mb4",
    )
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET role = 'admin' WHERE username = %s", ("admincurriculum",)
        )
        conn.commit()
    conn.close()

    return {"Authorization": f"Bearer {token}"}


def teardown_module():
    _cleanup_test_dirs()


class TestAdminCurriculumCRUD:
    """Integration tests for admin curriculum CRUD endpoints.
    Tests run sequentially; each builds on state created by previous tests."""

    @classmethod
    def setup_class(cls):
        _cleanup_test_data()

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
                "id": "test-q-1",
                "title": "Reverse a String",
                "difficulty": "easy",
                "category": "strings",
                "description": "Write a function to reverse a string.",
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "test-q-1"

    def test_get_course_tree(self, test_client: TestClient):
        headers = _admin_headers(test_client)
        res = test_client.get("/api/admin/courses/tree", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "courses" in data
        assert "modules" in data
        assert "lessons" in data
