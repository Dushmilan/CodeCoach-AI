"""Issue #316: the migration suite must never wipe a per-branch working DB.

`_drop_all_tables` runs ``DROP SCHEMA public CASCADE`` against the database
named by ``DATABASE_URL``. Locally that variable points at the developer's
branch database (``codecoach_<slug>``), so running ``pytest tests/migrations``
silently wiped every seeded row. These tests pin the new contract:

- dedicated test databases (``codecoach_test``) pass through unchanged (CI);
- any other database name is rerouted to the **scratch migration database**
  (``codecoach_migration_test``) on the same server;
- an explicit opt-in env var restores the (dangerous) pass-through for
  deliberate offline debugging against another database.
"""

import urllib.parse

import pytest

from tests.migrations.conftest import (
    MIGRATION_SCRATCH_DB,
    MIGRATION_TESTS_USE_DATABASE_URL_DB,
    _migration_url,
)


def _db_name(url: str) -> str:
    return (urllib.parse.urlparse(url).path or "").lstrip("/").split("?")[0]


def _set_db_url(monkeypatch: pytest.MonkeyPatch, db: str) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        f"postgresql://codecoach:codecoach@127.0.0.1:5432/{db}",
    )


def test_branch_db_is_rerouted_to_scratch(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_db_url(monkeypatch, "codecoach_316_migration_wipe")
    assert _db_name(_migration_url()) == MIGRATION_SCRATCH_DB


def test_dedicated_test_db_passes_through(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_db_url(monkeypatch, "codecoach_test")
    assert _db_name(_migration_url()) == "codecoach_test"


def test_default_fallback_is_the_dedicated_test_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The built-in default (codecoach_test) is dedicated — pass-through."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert _db_name(_migration_url()) == "codecoach_test"


def test_explicit_opt_in_keeps_the_named_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_db_url(monkeypatch, "codecoach_316_migration_wipe")
    monkeypatch.setenv(MIGRATION_TESTS_USE_DATABASE_URL_DB, "1")
    assert _db_name(_migration_url()) == "codecoach_316_migration_wipe"


def test_async_driver_is_always_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_db_url(monkeypatch, "codecoach_test")
    assert _migration_url().startswith("postgresql+asyncpg://")


def test_reroute_preserves_server_and_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_db_url(monkeypatch, "codecoach_316_migration_wipe")
    parsed = urllib.parse.urlparse(_migration_url())
    assert parsed.hostname == "127.0.0.1"
    assert parsed.port == 5432
    assert parsed.username == "codecoach"
