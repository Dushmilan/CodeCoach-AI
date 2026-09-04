"""Integration tests: learner progress flows (/api/progress).

End-to-end through admin-seeded curriculum content: mark lessons
complete, read back progress, track lesson access, and verify auth +
validation boundaries.
"""

import uuid

from fastapi.testclient import TestClient

from tests.db_helpers import truncate_course_tables_sync
from tests.fixtures.auth_helpers import admin_headers, register_headers


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _seed_curriculum(test_client: TestClient):
    """Create one course + module + lesson via admin; return ids."""
    headers = admin_headers(test_client, "progressadmin")
    course_id = _uid("prog-course")
    module_id = _uid("prog-mod")
    lesson_id = _uid("prog-lesson")
    assert (
        test_client.post(
            "/api/admin/courses",
            json={
                "id": course_id,
                "title": "Progress Course",
                "description": "progress probe",
                "language": "python",
                "order": 1,
            },
            headers=headers,
        ).status_code
        == 200
    )
    assert (
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
        ).status_code
        == 200
    )
    assert (
        test_client.post(
            "/api/admin/lessons",
            json={
                "id": lesson_id,
                "course_id": course_id,
                "module_id": module_id,
                "title": "L1",
                "type": "theory",
                "content": "# hi",
                "order": 1,
                "language": "python",
            },
            headers=headers,
        ).status_code
        == 200
    )
    return course_id, lesson_id


def teardown_module():
    truncate_course_tables_sync()


class TestProgressFlows:
    def test_mark_complete_then_read_progress(self, test_client: TestClient):
        course_id, lesson_id = _seed_curriculum(test_client)
        headers = register_headers(test_client, f"learner-{uuid.uuid4().hex[:8]}")
        try:
            done = test_client.post(
                f"/api/progress/{lesson_id}/complete?course_id={course_id}",
                headers=headers,
            )
            assert done.status_code == 200

            progress = test_client.get(f"/api/progress/{course_id}", headers=headers)
            assert progress.status_code == 200
            data = progress.json()
            assert lesson_id in data["completed_lessons"]

            all_progress = test_client.get("/api/progress/", headers=headers)
            assert all_progress.status_code == 200
            entries = all_progress.json()["progress"]
            assert any(
                e["course_id"] == course_id and lesson_id in e["completed_lessons"]
                for e in entries
            )
        finally:
            admin = admin_headers(test_client, "progressadmin")
            test_client.delete(f"/api/admin/courses/{course_id}", headers=admin)
            truncate_course_tables_sync()

    def test_progress_empty_for_new_learner(self, test_client: TestClient):
        course_id, _ = _seed_curriculum(test_client)
        headers = register_headers(test_client, f"fresh-{uuid.uuid4().hex[:8]}")
        try:
            res = test_client.get(f"/api/progress/{course_id}", headers=headers)
            assert res.status_code == 200
            assert res.json() == {"completed_lessons": [], "progress": 0.0}
        finally:
            admin = admin_headers(test_client, "progressadmin")
            test_client.delete(f"/api/admin/courses/{course_id}", headers=admin)
            truncate_course_tables_sync()

    def test_track_access_returns_last_accessed(self, test_client: TestClient):
        course_id, lesson_id = _seed_curriculum(test_client)
        headers = register_headers(test_client, f"access-{uuid.uuid4().hex[:8]}")
        try:
            res = test_client.post(
                f"/api/progress/{lesson_id}/access?course_id={course_id}",
                headers=headers,
            )
            assert res.status_code == 200
            assert res.json()["last_accessed_lesson_id"] == lesson_id
        finally:
            admin = admin_headers(test_client, "progressadmin")
            test_client.delete(f"/api/admin/courses/{course_id}", headers=admin)
            truncate_course_tables_sync()

    def test_complete_lesson_wrong_course_rejected(self, test_client: TestClient):
        course_id, lesson_id = _seed_curriculum(test_client)
        headers = register_headers(test_client, f"mismatch-{uuid.uuid4().hex[:8]}")
        try:
            res = test_client.post(
                f"/api/progress/{lesson_id}/complete?course_id=other-course",
                headers=headers,
            )
            assert res.status_code == 400
        finally:
            admin = admin_headers(test_client, "progressadmin")
            test_client.delete(f"/api/admin/courses/{course_id}", headers=admin)
            truncate_course_tables_sync()

    def test_progress_isolated_per_learner(self, test_client: TestClient):
        course_id, lesson_id = _seed_curriculum(test_client)
        headers_a = register_headers(test_client, f"usera-{uuid.uuid4().hex[:8]}")
        headers_b = register_headers(test_client, f"userb-{uuid.uuid4().hex[:8]}")
        try:
            test_client.post(
                f"/api/progress/{lesson_id}/complete?course_id={course_id}",
                headers=headers_a,
            )
            res = test_client.get(f"/api/progress/{course_id}", headers=headers_b)
            assert res.status_code == 200
            assert res.json() == {"completed_lessons": [], "progress": 0.0}
        finally:
            admin = admin_headers(test_client, "progressadmin")
            test_client.delete(f"/api/admin/courses/{course_id}", headers=admin)
            truncate_course_tables_sync()
