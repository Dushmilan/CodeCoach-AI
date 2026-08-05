import pytest
from fastapi import HTTPException, status

from app.models.auth_schemas import UserResponse


def make_user(plan: str = "free") -> UserResponse:
    return UserResponse(
        id="user-1",
        username="testuser",
        email="test@example.com",
        is_active=True,
        created_at="2025-01-01T00:00:00Z",
        plan=plan,
    )


class TestRequirePremium:
    @pytest.mark.asyncio
    async def test_premium_user_passes(self):
        from app.api.auth_deps import require_premium

        user = make_user(plan="premium")
        result = await require_premium(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_free_user_raises_403(self):
        from app.api.auth_deps import require_premium

        user = make_user(plan="free")
        with pytest.raises(HTTPException) as exc:
            await require_premium(user)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "premium" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_default_plan_is_free(self):
        from app.api.auth_deps import require_premium

        user = make_user(plan="free")
        assert user.plan == "free"
        with pytest.raises(HTTPException) as exc:
            await require_premium(user)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
