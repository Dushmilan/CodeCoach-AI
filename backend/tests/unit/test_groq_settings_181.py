"""Issue #181: GROQ_API_KEY from backend/.env ignored (os.getenv bypass).

Red tests: Settings must be the single source of truth for Groq config.
"""

from types import SimpleNamespace


def _settings_double(**overrides):
    base = {
        "GROQ_API_KEY": "gsk_from_settings",
        "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "GROQ_MODEL_EASY": "openai/gpt-oss-20b",
        "GROQ_MODEL_MEDIUM": "openai/gpt-oss-120b",
        "GROQ_MODEL_HARD": "openai/gpt-oss-120b",
        "GROQ_MODEL_STREAM": "openai/gpt-oss-20b",
        "GROQ_MODEL_ANIMATE": "openai/gpt-oss-120b",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class TestGroqSettingsSource:
    def test_settings_has_groq_base_url_default(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach",
        )
        monkeypatch.chdir("/tmp")
        monkeypatch.delenv("GROQ_BASE_URL", raising=False)
        from app.core.config import get_settings

        assert get_settings().GROQ_BASE_URL == "https://api.groq.com/openai/v1"

    def test_service_init_reads_key_from_settings(self, monkeypatch):
        """GroqService() must pick up the key via Settings, not os env."""
        import app.services.groq_service as mod

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_BASE_URL", raising=False)
        for tier in ("EASY", "MEDIUM", "HARD", "STREAM", "ANIMATE"):
            monkeypatch.delenv(f"GROQ_MODEL_{tier}", raising=False)
        monkeypatch.setattr(
            mod, "get_settings", lambda: _settings_double(), raising=False
        )
        from app.services.groq_service import GroqService

        service = GroqService()
        assert service.api_key == "gsk_from_settings"
        assert service.base_url == "https://api.groq.com/openai/v1"

    def test_coach_provider_uses_key_from_settings(self, monkeypatch):
        """get_coaching_provider must read the key from Settings."""
        import app.api.coach as coach_mod

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setattr(
            coach_mod, "get_settings", lambda: _settings_double(), raising=False
        )
        from app.api.coach import get_coaching_provider
        from app.models.auth_schemas import UserResponse

        user = UserResponse(
            id="user-1",
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
        )
        provider = get_coaching_provider(cache=None, user=user, usage_service=object())
        assert provider.api_key == "gsk_from_settings"

    def test_groq_verification_reads_key_from_settings(self, monkeypatch):
        """check_groq_status must consult Settings when no explicit key."""
        import asyncio

        import app.services.groq_verification as mod

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setattr(
            mod,
            "get_settings",
            lambda: _settings_double(GROQ_API_KEY=None),
            raising=False,
        )
        from app.services.groq_verification import check_groq_status

        result = asyncio.run(check_groq_status())
        assert result["valid"] is False
        assert "not set" in (result.get("error") or "")

    def test_health_reports_groq_from_settings(self, monkeypatch):
        import app.api.health as mod

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setattr(
            mod, "get_settings", lambda: _settings_double(), raising=False
        )
        # Health must no longer consult os.environ directly for the key.
        import inspect

        assert 'os.getenv("GROQ_API_KEY")' not in inspect.getsource(mod)

    def test_debug_reports_groq_present_from_settings(self, monkeypatch):
        import app.api.debug as mod

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setattr(
            mod, "get_settings", lambda: _settings_double(), raising=False
        )
        import inspect

        assert 'os.getenv("GROQ_API_KEY")' not in inspect.getsource(mod)
