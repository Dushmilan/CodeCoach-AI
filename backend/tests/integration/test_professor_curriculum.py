"""Issue #185: professor-scoped curriculum flow (integration).

Professors manage only their own courses via ``/api/professor/*``:
- tree lists owned courses only (cross-owner invisible)
- create stamps ``owner_id`` with the caller
- update of a foreign course/module/lesson -> 403 (404 when unknown)
- deletes are admin-only -> 403 for professors
- non-professor roles (student, TA) -> 403
- ``/api/admin`` behaviour is unchanged (covered by test_admin_curriculum_crud)
"""

import asyncio
import uuid

from fastapi.testclient import TestClient

from tests.db_helpers import truncate_course_tables_sync, update_user
from tests.fixtures.auth_helpers import admin_headers, register_headers


def teardown_module():
    truncate_course_tables_sync()


def _prof_headers(test_client: TestClient, username: str) -> dict:
    headers = register_headers(test_client, username, f"{username}@test.com")
    asyncio.run(update_user("role='professor'", {}, username))
    return headers


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _create_course(test_client: TestClient, headers: dict, cid: str) -> dict:
    res = test_client.post(
        "/api/professor/courses",
        json={
            "id": cid,
            "title": f"Course {cid}",
            "description": "prof-owned",
            "language": "python",
            "order": 1,
        },
        headers=headers,
    )
    assert res.status_code == 200, res.text
    return res.json()


class TestProfessorTreeOwnedOnly:
    def test_tree_lists_only_owned_courses(self, test_client: TestClient):
        prof_a = _prof_headers(test_client, f"profA{_uid('a')}")
        prof_b = _prof_headers(test_client, f"profB{_uid('b')}")
        cid_a = _uid("course-a")
        cid_b = _uid("course-b")
        _create_course(test_client, prof_a, cid_a)
        _create_course(test_client, prof_b, cid_b)

        tree_a = test_client.get("/api/professor/courses/tree", headers=prof_a)
        assert tree_a.status_code == 200
        ids_a = {c["id"] for c in tree_a.json()["courses"]}
        assert cid_a in ids_a
        assert cid_b not in ids_a

    def test_create_stamps_owner(self, test_client: TestClient):
        prof = _prof_headers(test_client, f"profC{_uid('c')}")
        cid = _uid("owned-course")
        created = _create_course(test_client, prof, cid)
        assert created["owner_id"] is not None

        tree = test_client.get("/api/professor/courses/tree", headers=prof)
        assert tree.status_code == 200
        row = next(c for c in tree.json()["courses"] if c["id"] == cid)
        assert row["owner_id"] == created["owner_id"]


class TestProfessorCrossOwnerForbidden:
    def _owned_course_and_module(
        self, test_client: TestClient, owner_headers: dict
    ) -> tuple[str, str]:
        cid = _uid("xcourse")
        _create_course(test_client, owner_headers, cid)
        mid = _uid("xmod")
        res = test_client.post(
            "/api/professor/modules",
            json={
                "id": mid,
                "course_id": cid,
                "title": "M",
                "description": "",
                "order": 1,
            },
            headers=owner_headers,
        )
        assert res.status_code == 200, res.text
        return cid, mid

    def test_update_foreign_course_403(self, test_client: TestClient):
        owner = _prof_headers(test_client, f"own{_uid('o')}")
        other = _prof_headers(test_client, f"oth{_uid('t')}")
        cid, _ = self._owned_course_and_module(test_client, owner)
        res = test_client.put(
            f"/api/professor/courses/{cid}",
            json={"title": "Hijacked"},
            headers=other,
        )
        assert res.status_code == 403

    def test_update_unknown_course_404(self, test_client: TestClient):
        prof = _prof_headers(test_client, f"prof404{_uid('n')}")
        res = test_client.put(
            "/api/professor/courses/no-such-course",
            json={"title": "x"},
            headers=prof,
        )
        assert res.status_code == 404

    def test_create_module_under_foreign_course_403(self, test_client: TestClient):
        owner = _prof_headers(test_client, f"ownm{_uid('o')}")
        other = _prof_headers(test_client, f"othm{_uid('t')}")
        cid, _ = self._owned_course_and_module(test_client, owner)
        res = test_client.post(
            "/api/professor/modules",
            json={
                "id": _uid("hijack-mod"),
                "course_id": cid,
                "title": "Hijack",
                "description": "",
                "order": 1,
            },
            headers=other,
        )
        assert res.status_code == 403

    def test_update_foreign_module_403(self, test_client: TestClient):
        owner = _prof_headers(test_client, f"ownu{_uid('o')}")
        other = _prof_headers(test_client, f"othu{_uid('t')}")
        _, mid = self._owned_course_and_module(test_client, owner)
        res = test_client.put(
            f"/api/professor/modules/{mid}",
            json={"title": "Hijacked"},
            headers=other,
        )
        assert res.status_code == 403

    def test_lesson_scoped_to_owner(self, test_client: TestClient):
        owner = _prof_headers(test_client, f"ownl{_uid('o')}")
        other = _prof_headers(test_client, f"othl{_uid('t')}")
        cid, mid = self._owned_course_and_module(test_client, owner)
        lid = _uid("les")
        res = test_client.post(
            "/api/professor/lessons",
            json={
                "id": lid,
                "course_id": cid,
                "module_id": mid,
                "title": "L1",
                "type": "theory",
                "content": "hello",
                "order": 1,
                "language": "python",
            },
            headers=owner,
        )
        assert res.status_code == 200, res.text

        res = test_client.put(
            f"/api/professor/lessons/{lid}",
            json={"title": "Hijacked"},
            headers=other,
        )
        assert res.status_code == 403


class TestProfessorDeletesAdminOnly:
    def test_professor_delete_course_403(self, test_client: TestClient):
        prof = _prof_headers(test_client, f"profdel{_uid('d')}")
        cid = _uid("del-course")
        _create_course(test_client, prof, cid)
        for url in (
            f"/api/professor/courses/{cid}",
            "/api/professor/modules/anything",
            "/api/professor/lessons/anything",
        ):
            res = test_client.delete(url, headers=prof)
            assert res.status_code == 403, url

    def test_admin_delete_still_works(self, test_client: TestClient):
        admin = admin_headers(test_client, f"admindel{_uid('a')}")
        res = test_client.post(
            "/api/admin/courses",
            json={
                "id": _uid("admin-del"),
                "title": "gone",
                "description": "",
                "language": "python",
                "order": 1,
            },
            headers=admin,
        )
        assert res.status_code == 200
        cid = res.json()["id"]
        res = test_client.delete(f"/api/admin/courses/{cid}", headers=admin)
        assert res.status_code == 200


class TestProfessorRoleGate:
    def test_student_and_ta_forbidden(self, test_client: TestClient):
        student_name = f"stu{_uid('s')}"
        student = register_headers(
            test_client, student_name, f"{student_name}@test.com"
        )
        res = test_client.get("/api/professor/courses/tree", headers=student)
        assert res.status_code == 403

        ta_name = f"ta{_uid('w')}"
        ta = register_headers(test_client, ta_name, f"{ta_name}@test.com")
        asyncio.run(update_user("role='ta'", {}, ta_name))
        res = test_client.get("/api/professor/courses/tree", headers=ta)
        assert res.status_code == 403
