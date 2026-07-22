import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.models.auth_schemas import TokenResponse, UserResponse


@pytest.fixture
def mock_auth_service():
    with patch("app.api.auth.AuthService") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


class TestAuthSupabase:
    def test_supabase_login_success(self, test_client: TestClient, mock_auth_service):
        mock_auth_service.login_with_supabase = AsyncMock(
            return_value=TokenResponse(
                access_token="our_jwt_token",
                token_type="bearer",
                expires_in=86400,
                user=UserResponse(
                    id="user-1",
                    username="google_user",
                    email="google_user@example.com",
                    created_at=datetime.now(timezone.utc),
                    is_active=True,
                ),
            )
        )

        response = test_client.post(
            "/api/auth/supabase",
            json={"access_token": "valid_supabase_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "our_jwt_token"
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "google_user"
        assert data["user"]["email"] == "google_user@example.com"

    def test_supabase_login_invalid_token(
        self, test_client: TestClient, mock_auth_service
    ):
        mock_auth_service.login_with_supabase = AsyncMock(
            side_effect=ValueError("Invalid Supabase token")
        )

        response = test_client.post(
            "/api/auth/supabase",
            json={"access_token": "invalid_token"},
        )

        assert response.status_code == 401
        assert "Invalid Supabase token" in response.json()["detail"]

    def test_supabase_login_missing_token(self, test_client: TestClient):
        response = test_client.post(
            "/api/auth/supabase",
            json={},
        )

        assert response.status_code == 422
