import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.models.auth_schemas import UserResponse


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid.token.here"
        )

        with patch("app.api.auth.AuthService") as mock_auth_cls:
            mock_auth = AsyncMock()
            mock_auth_cls.return_value = mock_auth

            expected_user = UserResponse(
                id="user-1",
                username="testuser",
                email="test@test.com",
                created_at=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
                is_active=True,
            )
            mock_auth.get_current_user = AsyncMock(return_value=expected_user)

            from app.api.auth_deps import get_current_user

            result = await get_current_user(creds, mock_auth)

            assert result.username == "testuser"
            assert result.email == "test@test.com"
            mock_auth.get_current_user.assert_called_once_with("valid.token.here")

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")

        with patch("app.api.auth.AuthService") as mock_auth_cls:
            mock_auth = AsyncMock()
            mock_auth_cls.return_value = mock_auth
            mock_auth.get_current_user = AsyncMock(
                side_effect=ValueError("Invalid or expired token")
            )

            from app.api.auth_deps import get_current_user

            with pytest.raises(HTTPException) as exc:
                await get_current_user(creds, mock_auth)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid or expired token" in exc.value.detail

    @pytest.mark.asyncio
    async def test_deactivated_user_raises_401(self):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")

        with patch("app.api.auth.AuthService") as mock_auth_cls:
            mock_auth = AsyncMock()
            mock_auth_cls.return_value = mock_auth
            mock_auth.get_current_user = AsyncMock(
                side_effect=ValueError("Account is deactivated")
            )

            from app.api.auth_deps import get_current_user

            with pytest.raises(HTTPException) as exc:
                await get_current_user(creds, mock_auth)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "deactivated" in exc.value.detail


class TestGetOptionalCurrentUser:
    @pytest.mark.asyncio
    async def test_optional_no_token_returns_none(self):
        with patch("app.api.auth.AuthService"):
            from app.api.auth_deps import get_optional_current_user

            result = await get_optional_current_user(None)
            assert result is None

    @pytest.mark.asyncio
    async def test_optional_valid_token_returns_user(self):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        expected_user = UserResponse(
            id="user-1",
            username="testuser",
            email="test@test.com",
            created_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
            is_active=True,
        )

        with patch("app.api.auth.AuthService") as mock_auth_cls:
            mock_auth = AsyncMock()
            mock_auth_cls.return_value = mock_auth
            mock_auth.get_current_user = AsyncMock(return_value=expected_user)

            from app.api.auth_deps import get_optional_current_user

            result = await get_optional_current_user(creds, mock_auth)
            assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_optional_invalid_token_returns_none(self):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")

        with patch("app.api.auth.AuthService") as mock_auth_cls:
            mock_auth = AsyncMock()
            mock_auth_cls.return_value = mock_auth
            mock_auth.get_current_user = AsyncMock(
                side_effect=ValueError("Invalid token")
            )

            from app.api.auth_deps import get_optional_current_user

            result = await get_optional_current_user(creds, mock_auth)
            assert result is None
