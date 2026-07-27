import pytest
import json
import os
from fastapi.testclient import TestClient

from app.main import app

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


def _load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return []


def _save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


@pytest.fixture
def client():
    return TestClient(app)


def _admin_headers(client: TestClient) -> dict:
    """Register a test admin user and return auth headers."""
    username = "admintestanalytics"
    res = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "Test1234!",
        },
    )
    if res.status_code != 201:
        res = client.post(
            "/api/auth/login",
            json={"username": username, "password": "Test1234!"},
        )
    token = res.json()["access_token"]

    users = _load_users()
    for u in users:
        if u.get("username") == username:
            u["role"] = "admin"
            break
    _save_users(users)

    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestUserAnalytics:
    def test_returns_200_with_correct_schema(self, client):
        headers = _admin_headers(client)
        res = client.get("/api/admin/analytics/users", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "new_users_30d" in data
        assert "role_distribution" in data
        assert isinstance(data["total_users"], int)
        assert isinstance(data["role_distribution"], dict)

    def test_non_admin_gets_403(self, client):
        res = client.post(
            "/api/auth/register",
            json={
                "username": "regularuseranalytics",
                "email": "reg@test.com",
                "password": "Test1234!",
            },
        )
        if res.status_code != 201:
            res = client.post(
                "/api/auth/login",
                json={"username": "regularuseranalytics", "password": "Test1234!"},
            )
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/admin/analytics/users", headers=headers)
        assert res.status_code == 403


@pytest.mark.integration
class TestQuestionProgress:
    def test_returns_200_with_correct_schema(self, client):
        headers = _admin_headers(client)
        res = client.get("/api/admin/analytics/question-progress", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "by_difficulty" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["by_difficulty"], dict)

    def test_non_admin_gets_403(self, client):
        res = client.post(
            "/api/auth/register",
            json={
                "username": "regularuserqp",
                "email": "regqp@test.com",
                "password": "Test1234!",
            },
        )
        if res.status_code != 201:
            res = client.post(
                "/api/auth/login",
                json={"username": "regularuserqp", "password": "Test1234!"},
            )
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/admin/analytics/question-progress", headers=headers)
        assert res.status_code == 403


@pytest.mark.integration
class TestSettings:
    def test_get_settings_returns_defaults(self, client):
        headers = _admin_headers(client)
        res = client.get("/api/admin/settings", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "piston_url" in data
        assert "piston_timeout" in data
        assert "enabled_languages" in data
        assert isinstance(data["enabled_languages"], list)

    def test_patch_settings_updates(self, client):
        headers = _admin_headers(client)
        res = client.patch(
            "/api/admin/settings",
            json={"piston_timeout": 60},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["piston_timeout"] == 60

    def test_non_admin_gets_403_on_get(self, client):
        res = client.post(
            "/api/auth/register",
            json={
                "username": "regularusersettings",
                "email": "regsettings@test.com",
                "password": "Test1234!",
            },
        )
        if res.status_code != 201:
            res = client.post(
                "/api/auth/login",
                json={"username": "regularusersettings", "password": "Test1234!"},
            )
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/admin/settings", headers=headers)
        assert res.status_code == 403

    def test_non_admin_gets_403_on_patch(self, client):
        res = client.post(
            "/api/auth/register",
            json={
                "username": "regularusersettings2",
                "email": "regsettings2@test.com",
                "password": "Test1234!",
            },
        )
        if res.status_code != 201:
            res = client.post(
                "/api/auth/login",
                json={"username": "regularusersettings2", "password": "Test1234!"},
            )
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        res = client.patch(
            "/api/admin/settings", json={"piston_timeout": 10}, headers=headers
        )
        assert res.status_code == 403
