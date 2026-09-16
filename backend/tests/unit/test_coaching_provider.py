"""Unit tests for the coach provider factory (platform-owned Groq key)."""

import pytest
from fastapi import HTTPException
from types import SimpleNamespace
from unittest.mock import patch

from app.api.coach import get_coaching_provider
from app.services.groq_service import GroqService
from app.models.auth_schemas import UserResponse


def _user(user_id: str = "user-1") -> UserResponse:
    return UserResponse(
        id=user_id,
        username="testuser",
        email="test@example.com",
        is_active=True,
        created_at="2025-01-01T00:00:00Z",
    )


def _settings_double(api_key=None):
    return SimpleNamespace(
        GROQ_API_KEY=api_key,
        GROQ_BASE_URL="https://api.groq.com/openai/v1",
        GROQ_MODEL_EASY="openai/gpt-oss-20b",
        GROQ_MODEL_MEDIUM="openai/gpt-oss-120b",
        GROQ_MODEL_HARD="openai/gpt-oss-120b",
        GROQ_MODEL_STREAM="openai/gpt-oss-20b",
        GROQ_MODEL_ANIMATE="openai/gpt-oss-120b",
    )


class _FakeUsageService:
    pass


class TestGetCoachingProvider:
    def test_raises_when_env_key_missing(self):
        with (
            patch(
                "app.api.coach.get_settings",
                return_value=_settings_double(None),
            ),
            patch(
                "app.services.groq_service.get_settings",
                return_value=_settings_double(None),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                get_coaching_provider(
                    cache=None, user=_user(), usage_service=_FakeUsageService()
                )
        assert exc.value.status_code == 500

    def test_uses_server_env_key(self):
        with (
            patch(
                "app.api.coach.get_settings",
                return_value=_settings_double("server-side-key"),
            ),
            patch(
                "app.services.groq_service.get_settings",
                return_value=_settings_double("server-side-key"),
            ),
        ):
            provider = get_coaching_provider(
                cache=None, user=_user(), usage_service=_FakeUsageService()
            )
        assert isinstance(provider, GroqService)
        assert provider.api_key == "server-side-key"

    def test_provider_is_constructed_with_user_id(self):
        with (
            patch(
                "app.api.coach.get_settings",
                return_value=_settings_double("server-side-key"),
            ),
            patch(
                "app.services.groq_service.get_settings",
                return_value=_settings_double("server-side-key"),
            ),
        ):
            provider = get_coaching_provider(
                cache=None, user=_user("user-42"), usage_service=_FakeUsageService()
            )
        assert provider.user_id == "user-42"

    def test_does_not_accept_client_supplied_key_argument(self):
        """The provider must not be constructible with a client header value."""
        import inspect

        signature = inspect.signature(get_coaching_provider)
        assert "x_nvidia_api_key" not in signature.parameters
        assert "x_groq_api_key" not in signature.parameters
