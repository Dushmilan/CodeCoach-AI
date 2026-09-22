"""Instructor role guards (Issue #159, phase 2).

Professors own classrooms/courses; demonstrators (TAs) get limited access:
roster + analytics + coaching only. See TA permission matrix in #159.
"""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.auth_schemas import UserResponse


def _user(role: str) -> UserResponse:
    return UserResponse(
        id="u1",
        username="instructor",
        email="instructor@codecoach.ai",
        created_at=datetime.now(timezone.utc),
        role=role,
    )


class TestRequireProfessor:
    @pytest.mark.asyncio
    async def test_allows_professor_and_admins(self):
        from app.api.auth_deps import require_professor

        for role in ("professor", "admin", "super_admin"):
            result = await require_professor(_user(role))
            assert result.role == role

    @pytest.mark.asyncio
    async def test_denies_student_and_ta(self):
        from app.api.auth_deps import require_professor

        for role in ("user", "ta"):
            with pytest.raises(HTTPException) as exc:
                await require_professor(_user(role))
            assert exc.value.status_code == 403


class TestRequireInstructor:
    @pytest.mark.asyncio
    async def test_allows_professor_ta_and_admins(self):
        from app.api.auth_deps import require_instructor

        for role in ("professor", "ta", "admin", "super_admin"):
            result = await require_instructor(_user(role))
            assert result.role == role

    @pytest.mark.asyncio
    async def test_denies_student(self):
        from app.api.auth_deps import require_instructor

        with pytest.raises(HTTPException) as exc:
            await require_instructor(_user("user"))
        assert exc.value.status_code == 403


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_allows_admin_and_super_admin(self):
        from app.api.auth_deps import require_admin

        for role in ("admin", "super_admin"):
            result = await require_admin(_user(role))
            assert result.role == role

    @pytest.mark.asyncio
    async def test_denies_non_admin_with_403(self):
        # Round 9 probe pin: this deny branch (auth_deps.py:55) was covered
        # only via integration HTTP tests, so unit-only coverage measured
        # 92.3% lines while combined measured 98.4%. Pinning it here makes
        # the branch independent of integration execution/timing/order.
        from app.api.auth_deps import require_admin

        for role in ("user", "ta", "professor"):
            with pytest.raises(HTTPException) as exc:
                await require_admin(_user(role))
            assert exc.value.status_code == 403


class TestRequireSuperAdmin:
    @pytest.mark.asyncio
    async def test_allows_super_admin(self):
        # Round 9: the allow path (auth_deps.py:70) was the single line
        # missing from COMBINED coverage -- no test, unit or integration,
        # exercised it. Pinned here.
        from app.api.auth_deps import require_super_admin

        result = await require_super_admin(_user("super_admin"))
        assert result.role == "super_admin"

    @pytest.mark.asyncio
    async def test_denies_non_super_admin_with_403(self):
        from app.api.auth_deps import require_super_admin

        for role in ("user", "ta", "professor", "admin"):
            with pytest.raises(HTTPException) as exc:
                await require_super_admin(_user(role))
            assert exc.value.status_code == 403


class TestRequireCourseEditor:
    @pytest.mark.asyncio
    async def test_allows_professor_and_admins(self):
        from app.api.auth_deps import require_course_editor

        for role in ("professor", "admin", "super_admin"):
            result = await require_course_editor(_user(role))
            assert result.role == role

    @pytest.mark.asyncio
    async def test_denies_ta_and_student_with_403(self):
        # Round 9 probe pin: deny branch (auth_deps.py:111), same story as
        # require_admin above -- integration-only coverage until now.
        from app.api.auth_deps import require_course_editor

        for role in ("user", "ta"):
            with pytest.raises(HTTPException) as exc:
                await require_course_editor(_user(role))
            assert exc.value.status_code == 403


class TestTAPermissionMatrix:
    def test_roster_management_is_professor_only(self):
        from app.api.auth_deps import instructor_can_manage_roster

        assert instructor_can_manage_roster("professor") is True
        assert instructor_can_manage_roster("admin") is True
        assert instructor_can_manage_roster("super_admin") is True
        assert instructor_can_manage_roster("ta") is False
        assert instructor_can_manage_roster("user") is False

    def test_course_editing_is_professor_only(self):
        from app.api.auth_deps import instructor_can_edit_courses

        assert instructor_can_edit_courses("professor") is True
        assert instructor_can_edit_courses("admin") is True
        assert instructor_can_edit_courses("ta") is False
        assert instructor_can_edit_courses("user") is False

    def test_analytics_visible_to_professor_and_ta(self):
        from app.api.auth_deps import instructor_can_view_analytics

        assert instructor_can_view_analytics("professor") is True
        assert instructor_can_view_analytics("ta") is True
        assert instructor_can_view_analytics("user") is False
