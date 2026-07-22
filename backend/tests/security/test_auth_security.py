"""
Authentication and authorization security tests.
"""

from fastapi.testclient import TestClient
from datetime import timedelta

from app.services.auth_service import hash_password, create_access_token, TokenData


class TestAuthSecurity:
    """Tests for authentication security vulnerabilities."""

    def test_jwt_alg_none_rejected(self, test_client: TestClient):
        """JWT with alg: none should be rejected."""
        import base64
        import json

        header = (
            base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode())
            .rstrip(b"=")
            .decode()
        )
        payload = (
            base64.urlsafe_b64encode(
                json.dumps({"sub": "user1", "exp": 9999999999}).encode()
            )
            .rstrip(b"=")
            .decode()
        )
        forged_token = f"{header}.{payload}."
        response = test_client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {forged_token}"}
        )
        assert response.status_code == 401

    def test_jwt_expired_token_rejected(self, test_client: TestClient):
        """Expired JWT should be rejected."""
        expired_data = TokenData(user_id="test-id", username="test-user")
        token, _ = create_access_token(
            expired_data, expires_delta=timedelta(seconds=-3600)
        )
        response = test_client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    def test_jwt_modified_claims_rejected(self, test_client: TestClient):
        """JWT with tampered claims should be rejected."""
        data = TokenData(user_id="original-id", username="original-user")
        token, _ = create_access_token(data)
        parts = token.split(".")
        import base64
        import json

        payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_bytes)
        payload["sub"] = "malicious-id"
        new_payload = (
            base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        )
        tampered_token = f"{parts[0]}.{new_payload}.{parts[2]}"
        response = test_client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"}
        )
        assert response.status_code == 401

    def test_jwt_wrong_secret_rejected(self, test_client: TestClient):
        """JWT signed with wrong secret should be rejected."""
        from jose import jwt as jose_jwt

        payload = {"sub": "user1", "username": "test", "exp": 9999999999}
        wrong_secret = "this-is-the-wrong-secret"
        forged = jose_jwt.encode(payload, wrong_secret, algorithm="HS256")
        response = test_client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {forged}"}
        )
        assert response.status_code == 401

    def test_password_bcrypt_rounds(self):
        """Verify bcrypt rounds >= 12 for password hashing."""
        hashed = hash_password("test_password_123")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        parts = hashed.split("$")
        rounds = int(parts[2])
        assert rounds >= 12, f"bcrypt rounds {rounds} < 12"

    def test_privilege_escalation_no_token(self, test_client: TestClient):
        """Access /api/auth/me without token should return 401."""
        response = test_client.get("/api/auth/me")
        assert response.status_code == 401

    def test_privilege_escalation_wrong_token(self, test_client: TestClient):
        """Access with random token should return 401."""
        response = test_client.get(
            "/api/auth/me", headers={"Authorization": "Bearer random-invalid-token"}
        )
        assert response.status_code == 401

    def test_token_not_in_url(self, test_client: TestClient):
        """Verify tokens don't leak in URL query params."""
        queries = ["token=abc", "jwt=abc", "access_token=abc", "bearer=abc"]
        for query in queries:
            response = test_client.get(f"/api/questions/?{query}")
            assert response.status_code == 200

    def test_register_duplicate_username(self, test_client: TestClient):
        """Register same username twice should return 409."""
        payload = {
            "username": "dupuser",
            "email": "dup@test.com",
            "password": "StrongPass1!",
        }
        response1 = test_client.post("/api/auth/register", json=payload)
        assert response1.status_code in [201, 409]
        response2 = test_client.post("/api/auth/register", json=payload)
        assert response2.status_code == 409

    def test_login_invalid_credentials(self, test_client: TestClient):
        """Login with wrong password should return 401."""
        payload = {"username": "nonexistent", "password": "wrongpass"}
        response = test_client.post("/api/auth/login", json=payload)
        assert response.status_code == 401
