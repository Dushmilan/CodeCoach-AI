"""Unit tests for the coach provider factory (server-side-only API key)."""

import pytest
from fastapi import HTTPException

from app.api.coach import get_coaching_provider
from app.services.nim_service import NIMService


class TestGetCoachingProvider:
    def test_raises_when_env_key_missing(self, monkeypatch):
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        with pytest.raises(HTTPException) as exc:
            get_coaching_provider(cache=None)
        assert exc.value.status_code == 500

    def test_uses_server_env_key(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "server-side-key")
        provider = get_coaching_provider(cache=None)
        assert isinstance(provider, NIMService)
        assert provider.api_key == "server-side-key"

    def test_does_not_accept_client_supplied_key_argument(self):
        """The provider must not be constructible with a client header value."""
        import inspect

        signature = inspect.signature(get_coaching_provider)
        assert "x_nvidia_api_key" not in signature.parameters
