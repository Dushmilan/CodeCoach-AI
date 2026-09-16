import pytest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


def _settings_double(api_key):
    return SimpleNamespace(
        GROQ_API_KEY=api_key,
        GROQ_BASE_URL="https://api.groq.com/openai/v1",
    )


@contextmanager
def _mock_httpx_get(status_code: int, body=None):
    """Patch httpx.AsyncClient so GET returns a canned response."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_client.return_value = mock_instance

        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = body or {}
        mock_instance.get.return_value = mock_response
        yield mock_instance


@pytest.mark.usefixtures("test_env_vars")
class TestDebugGroqStatus:
    def test_groq_status_valid(self, test_client: TestClient, test_env_vars):
        body = {
            "object": "list",
            "data": [{"id": "openai/gpt-oss-120b", "active": True}],
        }
        settings = _settings_double("gsk_" + "x" * 40)
        with (
            _mock_httpx_get(200, body),
            patch(
                "app.services.groq_verification.get_settings",
                return_value=settings,
            ),
        ):
            response = test_client.get("/debug/groq-status")

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["api_key_present"] is True
            assert data["api_key_format_valid"] is True
            assert "openai/gpt-oss-120b" in data["models"]

    def test_groq_status_missing_key(self, test_client: TestClient, test_env_vars):
        settings = _settings_double(None)
        with patch(
            "app.services.groq_verification.get_settings",
            return_value=settings,
        ):
            response = test_client.get("/debug/groq-status")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "not set" in (data.get("error") or "")

    def test_groq_status_invalid_format(self, test_client: TestClient, test_env_vars):
        settings = _settings_double("short")
        with patch(
            "app.services.groq_verification.get_settings",
            return_value=settings,
        ):
            response = test_client.get("/debug/groq-status")
        assert response.status_code == 200
        data = response.json()
        assert data["api_key_present"] is True
        assert data["api_key_format_valid"] is False

    def test_groq_status_unauthorized(self, test_client: TestClient, test_env_vars):
        settings = _settings_double("gsk_" + "x" * 40)
        with (
            _mock_httpx_get(401),
            patch(
                "app.services.groq_verification.get_settings",
                return_value=settings,
            ),
        ):
            response = test_client.get("/debug/groq-status")

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert "Invalid API key" in data["error"]


@pytest.mark.usefixtures("test_env_vars")
class TestDebugEnvironment:
    def test_environment_info(
        self, test_client: TestClient, test_env_vars, monkeypatch
    ):
        monkeypatch.setenv("ENVIRONMENT", "testing")
        settings = _settings_double("gsk_" + "x" * 40)
        with patch(
            "app.api.debug.get_settings",
            return_value=settings,
        ):
            response = test_client.get("/debug/environment")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "python_version" in data
        assert "working_directory" in data
        assert "groq_api_key_present" in data
        assert data["environment"] == "testing"
        assert data["groq_api_key_present"] is True

    def test_environment_no_key(self, test_client: TestClient, test_env_vars):
        settings = _settings_double(None)
        with patch(
            "app.api.debug.get_settings",
            return_value=settings,
        ):
            response = test_client.get("/debug/environment")
        assert response.status_code == 200
        data = response.json()
        assert data["groq_api_key_present"] is False
