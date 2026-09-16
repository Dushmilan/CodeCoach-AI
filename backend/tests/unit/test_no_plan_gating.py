"""Issue #184: no plan/payment gating — flat daily limit for everyone.

RED test: asserts the plan-gating surface is gone. Must FAIL before the
removal lands (require_premium / plan fields / per-plan caps still exist)
and PASS after.
"""


class TestNoPlanGating:
    def test_auth_schemas_have_no_plan(self):
        from app.models.auth_schemas import UserResponse, UserInDB

        assert "plan" not in UserResponse.model_fields
        assert "plan" not in UserInDB.model_fields

    def test_no_require_premium(self):
        import app.api.auth_deps as auth_deps

        assert not hasattr(auth_deps, "require_premium")

    def test_no_cap_for_plan_flat_cap(self):
        import app.api.daily_limits as dl

        assert not hasattr(dl, "cap_for_plan")

    def test_daily_limit_headers_have_no_policy(self):
        from app.api.daily_limits import daily_limit_headers

        headers = daily_limit_headers(cap=20, remaining=19)
        assert "X-RateLimit-Policy" not in headers
        assert headers["X-RateLimit-Limit"] == "20"

    def test_config_flat_cap_only(self):
        from app.core.config import Settings

        fields = Settings.model_fields
        assert "DAILY_REQUEST_CAP" in fields
        assert "FREE_DAILY_REQUEST_CAP" not in fields
        assert "PRO_DAILY_REQUEST_CAP" not in fields
        assert "DAILY_TOKEN_INPUT_CAP" not in fields
        assert "DAILY_TOKEN_OUTPUT_CAP" not in fields

    def test_coach_has_no_token_cap_guard(self):
        import app.api.coach as coach

        assert not hasattr(coach, "check_daily_token_cap")

    def test_orm_has_no_plan(self):
        from app.models.orm import UserORM

        assert not hasattr(UserORM, "plan")
