"""SEC-2 red tests: httpOnly refresh cookie + CSRF protection.

These tests define the target behavior:
- login/register/supabase set an httpOnly SameSite=Lax refresh cookie
  AND a JS-readable csrf_token cookie, and return the csrf token in the body.
- /api/auth/refresh reads the refresh token from the cookie (body fallback
  preserved for backward compatibility).
- /api/auth/logout clears both cookies.
- Cookie-authenticated mutating endpoints require X-CSRF-Token to match the
  csrf_token cookie (double-submit pattern).
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.models.auth_schemas import TokenResponse, UserResponse


@pytest.fixture
def client() -> TestClient:
    """Fresh client per test: cookie state must never leak across tests."""
    with TestClient(app) as c:
        yield c


REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"


@pytest.fixture
def mock_auth_service():
    from app.api.auth_deps import get_auth_service

    instance = MagicMock()

    async def override_get_auth_service():
        return instance

    app.dependency_overrides[get_auth_service] = override_get_auth_service
    try:
        yield instance
    finally:
        app.dependency_overrides.pop(get_auth_service, None)


def _token_response(refresh: str = "refresh_abc") -> TokenResponse:
    return TokenResponse(
        access_token="access_xyz",
        token_type="bearer",
        expires_in=1800,
        refresh_token=refresh,
        user=UserResponse(
            id="user-1",
            username="testuser",
            email="test@example.com",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        ),
    )


class TestAuthCookies:
    def test_login_sets_http_only_refresh_cookie(
        self, client: TestClient, mock_auth_service
    ):
        mock_auth_service.login = AsyncMock(return_value=_token_response())

        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "secret123"},
        )

        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        assert f"{REFRESH_COOKIE}=" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "samesite=lax" in set_cookie.lower()
        assert "Max-Age=" in set_cookie

    def test_login_sets_csrf_cookie_and_returns_token_in_body(
        self, client: TestClient, mock_auth_service
    ):
        mock_auth_service.login = AsyncMock(return_value=_token_response())

        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "secret123"},
        )

        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        assert f"{CSRF_COOKIE}=" in set_cookie
        body = response.json()
        assert "csrf_token" in body
        csrf_cookie_value = response.cookies.get(CSRF_COOKIE)
        assert body["csrf_token"] == csrf_cookie_value

    def test_refresh_uses_cookie_without_body(
        self, client: TestClient, mock_auth_service
    ):
        mock_auth_service.refresh = AsyncMock(
            return_value=_token_response("new_refresh")
        )

        client.cookies.set(REFRESH_COOKIE, "old_refresh_token")
        client.cookies.set(CSRF_COOKIE, "csrf_value")

        response = client.post(
            "/api/auth/refresh", headers={"X-CSRF-Token": "csrf_value"}
        )

        assert response.status_code == 200
        mock_auth_service.refresh.assert_awaited_once_with("old_refresh_token")
        data = response.json()
        assert data["access_token"] == "access_xyz"
        # Refresh rotates the cookie.
        set_cookie = response.headers.get("set-cookie", "")
        assert "new_refresh" in set_cookie

    def test_refresh_without_cookie_and_without_body_rejected(
        self, client: TestClient, mock_auth_service
    ):
        response = client.post("/api/auth/refresh")
        assert response.status_code in (401, 422)

    def test_logout_clears_both_cookies(self, client: TestClient, mock_auth_service):
        client.cookies.set(REFRESH_COOKIE, "refresh_abc")
        client.cookies.set(CSRF_COOKIE, "csrf_value")

        response = client.post(
            "/api/auth/logout", headers={"X-CSRF-Token": "csrf_value"}
        )

        assert response.status_code in (200, 204)
        set_cookie = response.headers.get("set-cookie", "")
        assert REFRESH_COOKIE in set_cookie
        assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()


class TestCsrfProtection:
    def test_logout_without_csrf_header_rejected(
        self, client: TestClient, mock_auth_service
    ):
        client.cookies.set(REFRESH_COOKIE, "refresh_abc")
        client.cookies.set(CSRF_COOKIE, "csrf_value")

        # Cookie-authenticated mutation without the X-CSRF-Token header -> 403.
        response = client.post("/api/auth/logout")
        assert response.status_code == 403

    def test_logout_with_wrong_csrf_rejected(
        self, client: TestClient, mock_auth_service
    ):
        client.cookies.set(REFRESH_COOKIE, "refresh_abc")
        client.cookies.set(CSRF_COOKIE, "csrf_value")

        response = client.post(
            "/api/auth/logout", headers={"X-CSRF-Token": "wrong_value"}
        )
        assert response.status_code == 403

    def test_csrf_check_skipped_when_no_session_cookie(
        self, client: TestClient, mock_auth_service
    ):
        # No refresh cookie -> nothing to protect -> mutation proceeds.
        mock_auth_service.login = AsyncMock(return_value=_token_response())
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "secret123"},
        )
        assert response.status_code == 200

    def test_refresh_without_csrf_header_still_works(
        self, client: TestClient, mock_auth_service
    ):
        # Refresh is deliberately CSRF-exempt (SameSite=Lax + HttpOnly protect
        # it; a CSRF requirement would deadlock session restore after reload).
        mock_auth_service.refresh = AsyncMock(return_value=_token_response("new_r"))
        client.cookies.set(REFRESH_COOKIE, "old_refresh")
        client.cookies.set(CSRF_COOKIE, "csrf_value")

        response = client.post("/api/auth/refresh")
        assert response.status_code == 200
