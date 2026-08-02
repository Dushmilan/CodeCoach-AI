"""Unit tests for the debug endpoint environment guard."""

from fastapi.testclient import TestClient


class TestDebugGuard:
    def test_debug_disabled_in_production(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        from app.main import app

        client = TestClient(app)
        assert client.get("/debug/api-key-status").status_code == 404
        assert client.get("/debug/environment").status_code == 404
        assert client.get("/debug/test-connection").status_code == 404

    def test_debug_disabled_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        from app.main import app

        client = TestClient(app)
        assert client.get("/debug/environment").status_code == 404

    def test_debug_enabled_in_development(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        from app.main import app

        client = TestClient(app)
        assert client.get("/debug/environment").status_code == 200
