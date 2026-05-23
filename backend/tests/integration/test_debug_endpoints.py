import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.mark.usefixtures("test_env_vars")
class TestDebugApiKeyStatus:
    def test_api_key_present_valid(self, test_client: TestClient, test_env_vars):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_instance.post.return_value = mock_response

            os.environ["NVIDIA_API_KEY"] = "nvapi-" + "x" * 40

            response = test_client.get("/debug/api-key-status")
            assert response.status_code == 200
            data = response.json()
            assert data["api_key_present"] is True
            assert data["api_key_format_valid"] is True
            assert data["api_key_length"] == 46

    def test_api_key_missing(self, test_client: TestClient, test_env_vars):
        if "NVIDIA_API_KEY" in os.environ:
            del os.environ["NVIDIA_API_KEY"]

        response = test_client.get("/debug/api-key-status")
        assert response.status_code == 200
        data = response.json()
        assert data["api_key_present"] is False
        assert "not set" in (data.get("error") or "")

    def test_api_key_invalid_format(self, test_client: TestClient, test_env_vars):
        os.environ["NVIDIA_API_KEY"] = "short"

        response = test_client.get("/debug/api-key-status")
        assert response.status_code == 200
        data = response.json()
        assert data["api_key_present"] is True
        assert data["api_key_format_valid"] is False

    def test_api_key_unauthorized(self, test_client: TestClient, test_env_vars):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance

            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_instance.post.return_value = mock_response

            os.environ["NVIDIA_API_KEY"] = "nvapi-" + "x" * 40

            response = test_client.get("/debug/api-key-status")
            assert response.status_code == 200
            data = response.json()
            assert data["api_test_result"] == "invalid_key"


@pytest.mark.usefixtures("test_env_vars")
class TestDebugEnvironment:
    def test_environment_info(self, test_client: TestClient, test_env_vars):
        os.environ["NVIDIA_API_KEY"] = "nvapi-" + "x" * 40
        os.environ["ENVIRONMENT"] = "testing"

        response = test_client.get("/debug/environment")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "python_version" in data
        assert "working_directory" in data
        assert "nvidia_api_key_present" in data
        assert data["environment"] == "testing"

    def test_environment_no_key(self, test_client: TestClient, test_env_vars):
        if "NVIDIA_API_KEY" in os.environ:
            del os.environ["NVIDIA_API_KEY"]

        response = test_client.get("/debug/environment")
        assert response.status_code == 200
        data = response.json()
        assert data["nvidia_api_key_present"] is False


@pytest.mark.usefixtures("test_env_vars")
class TestDebugTestConnection:
    def test_connection_with_key(self, test_client: TestClient, test_env_vars):
        with patch("app.api.debug.NIMService") as mock_nim_cls:
            mock_instance = MagicMock()
            mock_nim_cls.return_value = mock_instance

            async def mock_get_coaching_response(*args, **kwargs):
                yield "Connection successful! API is working."

            mock_instance.get_coaching_response = mock_get_coaching_response

            os.environ["NVIDIA_API_KEY"] = "nvapi-" + "x" * 40

            response = test_client.get("/debug/test-connection")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_connection_no_key(self, test_client: TestClient, test_env_vars):
        if "NVIDIA_API_KEY" in os.environ:
            del os.environ["NVIDIA_API_KEY"]

        response = test_client.get("/debug/test-connection")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not configured" in data["error"]
