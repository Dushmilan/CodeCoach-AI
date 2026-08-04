from fastapi.testclient import TestClient


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
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "coursetestuser",
                "email": "coursetest@example.com",
                "password": "testpass123",
            },
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

    def test_list_courses_domain_filter(self, test_client: TestClient):
        import os
        import urllib.parse
        from urllib.parse import urlparse

        import pymysql

        headers = self._get_auth_headers(test_client)

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
                    ("coursetestuser",),
                )
            conn.commit()
        finally:
            conn.close()

        test_client.post(
            "/api/admin/courses",
            json={
                "id": "filter-ml",
                "title": "Intro to ML",
                "description": "ML course",
                "language": "python",
                "domain": "ml",
                "order": 1,
            },
            headers=headers,
        )
        test_client.post(
            "/api/admin/courses",
            json={
                "id": "filter-se",
                "title": "C Programming",
                "description": "SE course",
                "language": "c",
                "domain": "se",
                "order": 2,
            },
            headers=headers,
        )

        response = test_client.get("/api/courses/?domain=ml", headers=headers)
        assert response.status_code == 200
        courses = response.json()["courses"]
        assert len(courses) == 1
        assert courses[0]["id"] == "filter-ml"
        assert courses[0]["domain"] == "ml"

        test_client.delete("/api/admin/courses/filter-ml", headers=headers)
        test_client.delete("/api/admin/courses/filter-se", headers=headers)
