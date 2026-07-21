import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.auth_schemas import TokenResponse, UserResponse


@pytest.fixture
def mock_auth_service():
    with patch("app.api.auth.AuthService") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


class TestAuthRegister:
    def test_register_success(self, test_client: TestClient, mock_auth_service):
        mock_auth_service.register = AsyncMock(
            return_value=TokenResponse(
                access_token="jwt_token_abc",
                token_type="bearer",
                expires_in=86400,
                user=UserResponse(
                    id="user-1",
                    username="newuser",
                    email="new@example.com",
                    created_at=datetime.now(timezone.utc),
                    is_active=True,
                ),
            )
        )

        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["access_token"] == "jwt_token_abc"
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "new@example.com"

    def test_register_duplicate_username(
        self, test_client: TestClient, mock_auth_service
    ):
        mock_auth_service.register = AsyncMock(
            side_effect=ValueError("Username already taken")
        )

        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "existing",
                "email": "existing@example.com",
                "password": "securepass123",
            },
        )

        assert response.status_code == 409
        assert "Username already taken" in response.json()["detail"]

    def test_register_duplicate_email(self, test_client: TestClient, mock_auth_service):
        mock_auth_service.register = AsyncMock(
            side_effect=ValueError("Email already registered")
        )

        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "another",
                "email": "used@example.com",
                "password": "securepass123",
            },
        )

        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    def test_register_validation_short_username(self, test_client: TestClient):
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "ab",
                "email": "test@example.com",
                "password": "securepass123",
            },
        )
        assert response.status_code == 422

    def test_register_validation_short_password(self, test_client: TestClient):
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "validuser",
                "email": "test@example.com",
                "password": "12345",
            },
        )
        assert response.status_code == 422

    def test_register_validation_invalid_email(self, test_client: TestClient):
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": "validuser",
                "email": "not-an-email",
                "password": "securepass123",
            },
        )
        assert response.status_code == 422


class TestAuthLogin:
    def test_login_success(self, test_client: TestClient, mock_auth_service):
        mock_auth_service.login = AsyncMock(
            return_value=TokenResponse(
                access_token="jwt_token_xyz",
                token_type="bearer",
                expires_in=86400,
                user=UserResponse(
                    id="user-1",
                    username="testuser",
                    email="test@example.com",
                    created_at=datetime.now(timezone.utc),
                    is_active=True,
                ),
            )
        )

        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "correctpassword",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt_token_xyz"
        assert data["user"]["username"] == "testuser"

    def test_login_wrong_password(self, test_client: TestClient, mock_auth_service):
        mock_auth_service.login = AsyncMock(
            side_effect=ValueError("Invalid username or password")
        )

        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_inactive_user(self, test_client: TestClient, mock_auth_service):
        mock_auth_service.login = AsyncMock(
            side_effect=ValueError("Account is deactivated")
        )

        response = test_client.post(
            "/api/auth/login",
            json={
                "username": "inactive",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401
        assert "deactivated" in response.json()["detail"]


class TestAuthMe:
    def test_get_me_authenticated(self, test_client: TestClient):
        from app.api.auth_deps import get_current_user

        async def override_get_current_user():
            return UserResponse(
                id="user-1",
                username="testuser",
                email="test@example.com",
                created_at=datetime.now(timezone.utc),
                is_active=True,
            )

        app.dependency_overrides[get_current_user] = override_get_current_user
        try:
            response = test_client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testuser"
            assert data["email"] == "test@example.com"
            assert data["is_active"] is True
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_get_me_no_auth(self, test_client: TestClient):
        response = test_client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, test_client: TestClient):
        response = test_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


class TestAuthErrorHandling:
    def test_wrong_http_methods(self, test_client: TestClient):
        response = test_client.get("/api/auth/register")
        assert response.status_code == 405

        response = test_client.put("/api/auth/login")
        assert response.status_code == 405

        response = test_client.post("/api/auth/me")
        assert response.status_code == 405

    def test_invalid_json_body(self, test_client: TestClient):
        response = test_client.post("/api/auth/register", data="not json")
        assert response.status_code == 422

        response = test_client.post("/api/auth/login", data="not json")
        assert response.status_code == 422
