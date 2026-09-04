from fastapi.testclient import TestClient

from tests.fixtures.auth_helpers import register_headers


class TestCoursesEndpoints:
    def test_list_courses_empty(self, test_client: TestClient):
        """With no seed data, courses list returns empty array."""
        response = test_client.get("/api/courses/")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert data["courses"] == []

    def test_get_course_not_found(self, test_client: TestClient):
        """Non-existent course returns 404."""
        response = test_client.get("/api/courses/nonexistent-course")
        assert response.status_code == 404

    def test_get_lesson_not_found(self, test_client: TestClient):
        """Non-existent lesson returns 404."""
        response = test_client.get("/api/courses/lessons/nonexistent-lesson")
        assert response.status_code == 404

    def test_get_adjacent_not_found(self, test_client: TestClient):
        """Non-existent lesson returns 404 for adjacent endpoint."""
        response = test_client.get("/api/courses/lessons/nonexistent/adjacent")
        assert response.status_code == 404

    def test_mark_complete_unauthenticated(self, test_client: TestClient):
        """Unauthenticated requests to progress endpoints return 401."""
        response = test_client.post(
            "/api/progress/nonexistent-lesson/complete?course_id=nonexistent"
        )
        assert response.status_code == 401

    def test_track_access_unauthenticated(self, test_client: TestClient):
        response = test_client.post(
            "/api/progress/nonexistent-lesson/access?course_id=nonexistent"
        )
        assert response.status_code == 401

    def test_get_progress_unauthenticated(self, test_client: TestClient):
        response = test_client.get("/api/progress/")
        assert response.status_code == 401

    def test_get_course_progress_unauthenticated(self, test_client: TestClient):
        response = test_client.get("/api/progress/nonexistent")
        assert response.status_code == 401


class TestCoursesEndpointsAuthenticated:
    def _get_auth_headers(self, test_client: TestClient):
        return register_headers(test_client, "coursetestuser", "coursetest@example.com")

    def test_list_courses_authenticated_empty(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.get("/api/courses/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert data["courses"] == []

    def test_mark_complete_nonexistent_lesson(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.post(
            "/api/progress/nonexistent/complete?course_id=nonexistent",
            headers=headers,
        )
        assert response.status_code == 404

    def test_get_progress_empty(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.get("/api/progress/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "progress" in data

    def test_track_access_nonexistent(self, test_client: TestClient):
        headers = self._get_auth_headers(test_client)
        response = test_client.post(
            "/api/progress/nonexistent/access?course_id=nonexistent",
            headers=headers,
        )
        assert response.status_code == 404
