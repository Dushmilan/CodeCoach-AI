"""Unit tests for settings resolution (non-cached)."""


class TestSettings:
    def test_get_settings_reads_env_each_call(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("JWT_SECRET_KEY", "first-key")
        assert get_settings().JWT_SECRET_KEY == "first-key"

        monkeypatch.setenv("JWT_SECRET_KEY", "second-key")
        assert get_settings().JWT_SECRET_KEY == "second-key"

    def test_get_settings_respects_env_file_defaults(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.delenv("REDIS_ENABLED", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        settings = get_settings()
        assert settings.REDIS_ENABLED is True
        assert "postgresql+asyncpg" in settings.DATABASE_URL

    def test_get_settings_returns_new_instance(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")

        assert get_settings() is not get_settings()
