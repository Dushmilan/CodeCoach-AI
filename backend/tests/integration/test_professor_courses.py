"""Professor course authority (Issue #175).

Professors create/own courses via the admin curriculum endpoints
(paths unchanged); ownership gates scope every mutation to the owning
professor while admins bypass. Professors list only owned courses;
admins list all.
"""

import asyncio
import uuid

from fastapi.testclient import TestClient

from tests.db_helpers import truncate_course_tables_sync, update_user


def teardown_module():
    truncate_course_tables_sync()


def _professor_headers(test_client: TestClient, tag: str):
    """Register a user, promote to professor, return (user_id, headers)."""
    username = f"prof175_{tag}_{uuid.uuid4().hex[:8]}"
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "testpass123",
        },
    )
    assert res.status_code == 201, res.text
    user_id = res.json()["user"]["id"]
    token = res.json()["access_token"]
    asyncio.run(update_user("role='professor'", {}, username))
    return user_id, {"Authorization": f"Bearer {token}"}


def _user_headers(test_client: TestClient, tag: str, role: str):
    username = f"{tag}_{uuid.uuid4().hex[:8]}"
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "testpass123",
        },
    )
    assert res.status_code == 201, res.text
    asyncio.run(update_user(f"role='{role}'", {}, username))
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _admin_headers(test_client: TestClient, tag: str):
    return _user_headers(test_client, f"admin175_{tag}", "admin")


def _course_payload(slug: str) -> dict:
    return {
        "id": slug,
        "title": f"Course {slug}",
        "description": "professor owned course",
        "language": "python",
        "order": 1,
    }


def _create_course(test_client: TestClient, headers: dict, slug: str):
    res = test_client.post(
        "/api/admin/courses", json=_course_payload(slug), headers=headers
    )
    assert res.status_code == 200, res.text
    return res.json()


class TestProfessorCourseOwnership:
    def test_professor_create_course_sets_owner(self, test_client: TestClient):
        prof_id, headers = _professor_headers(test_client, "create")
        slug = f"prof-owned-{uuid.uuid4().hex[:8]}"
        data = _create_course(test_client, headers, slug)
        assert data["id"] == slug

        tree = test_client.get("/api/admin/courses/tree", headers=headers)
        assert tree.status_code == 200
        match = [c for c in tree.json()["courses"] if c["id"] == slug]
        assert len(match) == 1
        assert match[0]["owner_id"] == prof_id

    def test_professor_update_owned_course(self, test_client: TestClient):
        _, headers = _professor_headers(test_client, "update")
        slug = f"prof-update-{uuid.uuid4().hex[:8]}"
        _create_course(test_client, headers, slug)
        res = test_client.put(
            f"/api/admin/courses/{slug}",
            json={"title": "Updated by owner"},
            headers=headers,
        )
        assert res.status_code == 200, res.text

    def test_professor_cannot_update_non_owned_course(self, test_client: TestClient):
        _, headers_a = _professor_headers(test_client, "ownera")
        _, headers_b = _professor_headers(test_client, "ownerb")
        slug = f"prof-guarded-{uuid.uuid4().hex[:8]}"
        _create_course(test_client, headers_a, slug)
        res = test_client.put(
            f"/api/admin/courses/{slug}",
            json={"title": "Hijacked"},
            headers=headers_b,
        )
        assert res.status_code == 403, res.text

    def test_professor_cannot_delete_non_owned_course(self, test_client: TestClient):
        _, headers_a = _professor_headers(test_client, "delowner")
        _, headers_b = _professor_headers(test_client, "delother")
        slug = f"prof-nodelete-{uuid.uuid4().hex[:8]}"
        _create_course(test_client, headers_a, slug)
        res = test_client.delete(f"/api/admin/courses/{slug}", headers=headers_b)
        assert res.status_code == 403, res.text

    def test_module_lesson_scoped_to_owned_course(self, test_client: TestClient):
        _, headers_a = _professor_headers(test_client, "modowner")
        _, headers_b = _professor_headers(test_client, "modother")
        slug = f"prof-modscope-{uuid.uuid4().hex[:8]}"
        _create_course(test_client, headers_a, slug)

        # Non-owner cannot create a module under someone else's course.
        res = test_client.post(
            "/api/admin/modules",
            json={
                "id": f"mod-x-{uuid.uuid4().hex[:6]}",
                "course_id": slug,
                "title": "Intruder module",
                "description": "",
                "order": 1,
            },
            headers=headers_b,
        )
        assert res.status_code == 403, res.text

        # Owner creates module + lesson fine.
        mod_id = f"mod-o-{uuid.uuid4().hex[:6]}"
        res = test_client.post(
            "/api/admin/modules",
            json={
                "id": mod_id,
                "course_id": slug,
                "title": "Owner module",
                "description": "",
                "order": 1,
            },
            headers=headers_a,
        )
        assert res.status_code == 200, res.text

        les_id = f"les-o-{uuid.uuid4().hex[:6]}"
        res = test_client.post(
            "/api/admin/lessons",
            json={
                "id": les_id,
                "title": "Owner lesson",
                "type": "theory",
                "content": "# hi",
                "order": 1,
                "language": "python",
                "module_id": mod_id,
                "course_id": slug,
            },
            headers=headers_a,
        )
        assert res.status_code == 200, res.text

        # Non-owner cannot touch the module/lesson via scoped ids.
        res = test_client.put(
            f"/api/admin/modules/{mod_id}",
            json={"title": "Hijacked module"},
            headers=headers_b,
        )
        assert res.status_code == 403, res.text
        res = test_client.put(
            f"/api/admin/lessons/{les_id}",
            json={"title": "Hijacked lesson"},
            headers=headers_b,
        )
        assert res.status_code == 403, res.text
        res = test_client.delete(f"/api/admin/lessons/{les_id}", headers=headers_b)
        assert res.status_code == 403, res.text
        res = test_client.delete(f"/api/admin/modules/{mod_id}", headers=headers_b)
        assert res.status_code == 403, res.text

    def test_professor_tree_lists_only_owned(self, test_client: TestClient):
        _, headers_a = _professor_headers(test_client, "treea")
        _, headers_b = _professor_headers(test_client, "treeb")
        slug_a = f"prof-tree-a-{uuid.uuid4().hex[:8]}"
        slug_b = f"prof-tree-b-{uuid.uuid4().hex[:8]}"
        _create_course(test_client, headers_a, slug_a)
        _create_course(test_client, headers_b, slug_b)

        tree_a = test_client.get("/api/admin/courses/tree", headers=headers_a).json()
        ids_a = {c["id"] for c in tree_a["courses"]}
        assert slug_a in ids_a
        assert slug_b not in ids_a

    def test_admin_sees_all_and_bypasses_ownership(self, test_client: TestClient):
        _, headers_p = _professor_headers(test_client, "adminsees")
        admin = _admin_headers(test_client, "sees")
        slug = f"prof-adminall-{uuid.uuid4().hex[:8]}"
        _create_course(test_client, headers_p, slug)

        tree = test_client.get("/api/admin/courses/tree", headers=admin)
        assert tree.status_code == 200
        assert slug in {c["id"] for c in tree.json()["courses"]}

        res = test_client.put(
            f"/api/admin/courses/{slug}",
            json={"title": "Admin edit"},
            headers=admin,
        )
        assert res.status_code == 200, res.text

    def test_ta_and_student_denied_curriculum_writes(self, test_client: TestClient):
        for role in ("ta", "user"):
            headers = _user_headers(test_client, f"denied{role}", role)
            res = test_client.post(
                "/api/admin/courses",
                json=_course_payload(f"denied-{role}-{uuid.uuid4().hex[:6]}"),
                headers=headers,
            )
            assert res.status_code == 403, res.text
