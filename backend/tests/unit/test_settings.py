"""Unit tests for settings resolution (non-cached)."""

import pytest


class TestSettings:
    def test_get_settings_reads_env_each_call(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("JWT_SECRET_KEY", "first-key")
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach"
        )
        assert get_settings().JWT_SECRET_KEY == "first-key"

        monkeypatch.setenv("JWT_SECRET_KEY", "second-key")
        assert get_settings().JWT_SECRET_KEY == "second-key"

    def test_get_settings_respects_env_file_defaults(self, monkeypatch, tmp_path):
        from app.core.config import get_settings

        # Hermetic: Settings reads .env from the CWD, so isolate from any
        # developer-local .env (e.g. REDIS_ENABLED=false) that would leak in.
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.delenv("REDIS_ENABLED", raising=False)
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach",
        )
        settings = get_settings()
        assert settings.REDIS_ENABLED is True
        assert "postgresql+asyncpg" in settings.DATABASE_URL

    def test_get_settings_returns_new_instance(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach",
        )

        assert get_settings() is not get_settings()


class TestSupabaseOnlyDatabase:
    def test_missing_database_url_is_rejected(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")
        # An empty env value overrides any DATABASE_URL in the local .env file.
        monkeypatch.setenv("DATABASE_URL", "")
        with pytest.raises(ValueError, match="DATABASE_URL is required"):
            get_settings()

    def test_postgres_url_forces_asyncpg_driver(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://postgres.ref.pooler.supabase.com:6543/postgres",
        )
        settings = get_settings()
        assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")

    def test_prefixed_postgres_driver_is_accepted(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres.ref.supabase.co:5432/postgres",
        )
        settings = get_settings()
        assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")

    def test_mysql_url_is_rejected(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@host:3306/db")
        with pytest.raises(ValueError, match="Supabase/PostgreSQL"):
            get_settings()

    def test_sqlite_url_is_rejected(self, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")
        with pytest.raises(ValueError, match="Supabase/PostgreSQL"):
            get_settings()
