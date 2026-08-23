"""SEC-4: Piston URL SSRF guard tests.

The backend must never POST code to a Piston URL that points at loopback,
link-local (metadata) or private hosts in production — an attacker-controlled
or misconfigured PISTON_API_URL would otherwise turn the backend into an SSRF
proxy. Scheme is restricted to http/https everywhere.
"""

import pytest

from app.services.piston_service import validate_piston_url


class TestPistonUrlScheme:
    def test_non_http_scheme_rejected_everywhere(self, monkeypatch):
        for env in ("production", "testing"):
            monkeypatch.setenv("ENVIRONMENT", env)
            for bad in ("file:///etc/passwd", "gopher://internal:70", "ftp://host/x"):
                with pytest.raises(ValueError):
                    validate_piston_url(bad)

    def test_missing_host_rejected(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(ValueError):
            validate_piston_url("http:///api/v2")

    def test_http_and_https_allowed(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("PISTON_ALLOWED_HOSTS", "piston,piston.example.com")
        assert (
            validate_piston_url("http://piston:2000/api/v2")
            == "http://piston:2000/api/v2"
        )
        assert validate_piston_url("https://piston.example.com/api/v2") == (
            "https://piston.example.com/api/v2"
        )


class TestPistonUrlSsrfTargets:
    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://169.254.170.2/creds",  # ECS metadata
            "http://127.0.0.1:2000/api/v2",  # loopback
            "http://localhost:2000/api/v2",  # loopback hostname
            "http://[::1]:2000/api/v2",  # IPv6 loopback
            "http://10.0.0.5:2000/api/v2",  # private
            "http://192.168.1.10:2000/api/v2",  # private
        ],
    )
    def test_ssrf_targets_rejected_in_production(self, url, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("PISTON_ALLOWED_HOSTS", "piston")
        with pytest.raises(ValueError):
            validate_piston_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost:2000/api/v2",
            "http://127.0.0.1:2000/api/v2",
        ],
    )
    def test_loopback_allowed_outside_production(self, url, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "testing")
        assert validate_piston_url(url) == url

    def test_metadata_rejected_even_outside_production(self, monkeypatch):
        """Link-local/metadata targets are never legitimate Piston endpoints."""
        monkeypatch.setenv("ENVIRONMENT", "testing")
        with pytest.raises(ValueError):
            validate_piston_url("http://169.254.169.254/latest/meta-data/")

    def test_hostname_outside_allowlist_rejected_in_production(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("PISTON_ALLOWED_HOSTS", "piston")
        with pytest.raises(ValueError):
            validate_piston_url("http://internal-piston.lan:2000/api/v2")

    def test_allowlist_override_allows_custom_host(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("PISTON_ALLOWED_HOSTS", "piston,internal-piston.lan")
        assert validate_piston_url("http://internal-piston.lan:2000/api/v2") == (
            "http://internal-piston.lan:2000/api/v2"
        )
