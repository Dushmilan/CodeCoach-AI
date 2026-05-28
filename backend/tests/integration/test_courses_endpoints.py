import pytest
from fastapi.testclient import TestClient


class TestCoursesEndpoints:
    def test_list_courses_unauthenticated(self, test_client: TestClient):
        response = test_client.get("/api/courses/")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data

    def test_get_course_detail(self, test_client: TestClient):
        response = test_client.get("/api/courses/python-fundamentals")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "python-fundamentals"
        assert "modules" in data

    def test_get_course_not_found(self, test_client: TestClient):
        response = test_client.get("/api/courses/nonexistent-course")
        assert response.status_code == 404

    def test_get_lesson(self, test_client: TestClient):
        response = test_client.get("/api/courses/lessons/py-hello-world")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "py-hello-world"
        assert "content" in data

    def test_get_lesson_not_found(self, test_client: TestClient):
        response = test_client.get("/api/courses/lessons/nonexistent-lesson")
        assert response.status_code == 404

    def test_mark_complete_unauthenticated(self, test_client: TestClient):
        response = test_client.post("/api/progress/py-hello-world/complete?course_id=python-fundamentals")
        assert response.status_code == 401

    def test_track_access_unauthenticated(self, test_client: TestClient):
        response = test_client.post("/api/progress/py-hello-world/access?course_id=python-fundamentals")
        assert response.status_code == 401


class TestCoursesEndpointsAuthenticated:
    def _get_auth_headers(self, test_client: TestClient):
        response = test_client.post(
            "/api/auth/register",
            json={"username": "coursetestuser", "email": "coursetest@example.com", "password": "testpass123"},
        )
        if response.status_code == 201:
            token = response.json()["access_token"]
        else:
            response = test_client.post(
                "/api/auth/login",
                json={"username": "coursetestuser", "password": "testpass123"},
            )
            token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_list_courses_authenticated(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.get("/api/courses/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data

    def test_mark_complete_authenticated(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.post(
            "/api/progress/py-hello-world/complete?course_id=python-fundamentals",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "completed_lessons" in data
        assert "py-hello-world" in data["completed_lessons"]

    def test_track_access_authenticated(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.post(
            "/api/progress/py-hello-world/access?course_id=python-fundamentals",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["last_accessed_lesson_id"] == "py-hello-world"

    def test_get_progress(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.get("/api/progress/python-fundamentals", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "completed_lessons" in data

    def test_get_all_progress(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.get("/api/progress/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "progress" in data

    def test_mark_complete_wrong_course(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.post(
            "/api/progress/py-hello-world/complete?course_id=wrong-course",
            headers=headers,
        )
        assert response.status_code == 400

    def test_mark_complete_nonexistent_lesson(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.post(
            "/api/progress/nonexistent/complete?course_id=python-fundamentals",
            headers=headers,
        )
        assert response.status_code == 404
