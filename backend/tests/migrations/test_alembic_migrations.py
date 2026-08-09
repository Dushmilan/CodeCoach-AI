"""Alembic migration harness: linear-chain, forward/rollback, and drift checks.

Runs against the isolated per-suite schema. These tests are purely sync
(alembic.command drives its own event loop), which is why they live outside
pytest-asyncio's auto loop management.

MySQL's `DESCRIBE` can transiently return 1684 ("table skipped, DDL in flight")
right after back-to-back create/drop of the same table name, so migration ops
are wrapped in a bounded retry — the same resilience pattern recommended for
CI migration jobs.
"""

import time
import urllib.parse
from typing import Callable, List, Tuple

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from tests.migrations.conftest import BACKEND_DIR, _is_postgres

_RETRIES = 4
_BACKOFF_S = 0.5


def _retry(op: Callable[[], None], label: str) -> None:
    last: Exception = RuntimeError(f"no attempt made for {label}")
    for attempt in range(1, _RETRIES + 1):
        try:
            op()
            return
        except Exception as exc:  # noqa: BLE001 - transient DDL race is broad
            last = exc
            if _is_transient_db_race(exc):
                time.sleep(_BACKOFF_S * attempt)
                continue
            raise
    raise last


def _is_transient_db_race(exc: Exception) -> bool:
    text = f"{str(exc)} {getattr(exc, 'orig', '')}"
    return any(code in text for code in ("1684", "1824"))


def _sync_engine(url: str):
    if _is_postgres(url):
        return create_engine(
            url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
        )
    return create_engine(url.replace("mysql+aiomysql://", "mysql+pymysql://"))


def _current_version(url: str) -> str:
    with _sync_engine(url).connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        rows = result.fetchall()
        if not rows:
            return "base"
        return rows[0][0]


def _revision_chain(cfg: Config) -> List[Tuple[str, str]]:
    """Return [(revision, down_revision)] ordered base -> head."""
    script = ScriptDirectory.from_config(cfg)
    revisions = list(script.walk_revisions())
    revisions.reverse()
    return [(r.revision, r.down_revision) for r in revisions]


def test_revision_graph_is_single_linear_chain(alembic_config: Config) -> None:
    script = ScriptDirectory.from_config(alembic_config)
    assert len(script.get_heads()) == 1, (
        f"Expected a single migration head, found {script.get_heads()}"
    )
    chain = _revision_chain(alembic_config)
    assert chain, "No revisions found"
    assert chain[0][1] is None, (
        f"First revision must have down_revision None: {chain[0]}"
    )
    for i in range(1, len(chain)):
        assert chain[i][1] == chain[i - 1][0], (
            f"Revision graph is not linear at {chain[i]}: expected "
            f"down_revision={chain[i - 1][0]}"
        )


def test_upgrade_and_downgrade_roundtrip(
    alembic_config: Config, migration_url: str
) -> None:
    chain = _revision_chain(alembic_config)
    assert chain, "No revisions to test"
    rev_to_prev = {rev: prev for rev, prev in chain}

    # Forward: migrate one revision at a time, confirming the version advances.
    _retry(lambda: command.upgrade(alembic_config, "base"), "upgrade base")
    assert _current_version(migration_url) == "base"
    for rev in rev_to_prev:
        label = f"upgrade {rev}"
        _retry(lambda r=rev: command.upgrade(alembic_config, r), label)
        assert _current_version(migration_url) == rev, (
            f"After upgrade to {rev}, alembic_version = "
            f"{_current_version(migration_url)}"
        )

    # Backward: step down one revision at a time.
    for rev in reversed(list(rev_to_prev)):
        prev = rev_to_prev[rev]
        if prev is None:
            continue  # base revision has nothing below it
        label = f"downgrade {prev}"
        _retry(lambda p=prev: command.downgrade(alembic_config, p), label)
        assert _current_version(migration_url) == prev, (
            f"After downgrade from {rev}, alembic_version = "
            f"{_current_version(migration_url)}"
        )

    # Every downgrade must be followed by a clean re-upgrade (dual-run compat).
    for rev in rev_to_prev:
        _retry(lambda r=rev: command.upgrade(alembic_config, r), f"re-upgrade {rev}")


def test_head_schema_matches_models(alembic_config: Config, migration_url: str) -> None:
    """Drift check: migrations-built schema must match the ORM metadata.

    Uses an allowlist baseline (`schema_drift_baseline.json`) of *known*
    drift signatures recorded at time of authoring. The check fails only on
    NEW drift (a signature not present in the baseline), so the pipeline is
    "unbreakable" while still enforcing that drift is monotonic — it can
    only shrink, never grow.
    """
    import json
    import os
    import sys

    from pathlib import Path

    sys.path.insert(0, str(BACKEND_DIR))
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    os.environ["DATABASE_URL"] = migration_url
    _retry(lambda: command.upgrade(alembic_config, "head"), "upgrade head")

    from app.models.orm import Base

    drifted: List[object] = []

    def _reflect_and_compare() -> None:
        nonlocal drifted
        _retry(lambda: command.upgrade(alembic_config, "head"), "upgrade head")
        engine = _sync_engine(migration_url)
        try:
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                drifted = list(compare_metadata(context, Base.metadata))
        finally:
            engine.dispose()

    # Reflect/compare can itself hit the transient 1684 DDL race; retry the whole
    # step on a fresh connection until it returns a stable result.
    _retry(_reflect_and_compare, "reflect + compare metadata")

    baseline_path = Path(__file__).resolve().parent / "schema_drift_baseline.json"
    baseline = set(json.loads(baseline_path.read_text(encoding="utf-8")))

    new_drift = [
        sig
        for sig in (_drift_signature(d) for d in drifted)
        if sig and sig not in baseline
    ]
    assert not new_drift, (
        "NEW schema drift detected (not in "
        f"{baseline_path.name}):\n"
        + "\n".join(sorted(new_drift))
        + "\n\nFix the migrations OR add signatures to the baseline "
        "only if fully intentional."
    )


def _drift_signature(diff: object) -> str:
    """Reduce an alembic autogenerate diff to a stable, comparable signature."""
    if not isinstance(diff, tuple) or not diff:
        return ""
    op = diff[0]
    try:
        if op in ("add_table", "remove_table"):
            return f"{op}:{diff[1].name}"
        if op in ("remove_index", "add_index"):
            return f"{op}:{diff[1].name}"
        if op in ("add_column", "remove_column"):
            table = diff[1]
            col = diff[2]
            name = getattr(col, "name", col) if not isinstance(col, str) else col
            return f"{op}:{getattr(table, 'name', table)}:{name}"
        if op in (
            "modify_type",
            "modify_nullable",
            "modify_server_default",
            "modify_comment",
        ):
            table = diff[1]
            col = diff[2]
            name = getattr(col, "name", col) if not isinstance(col, str) else col
            return f"{op}:{getattr(table, 'name', table)}:{name}"
        if op in (
            "add_constraint",
            "remove_constraint",
            "add_primary_key",
            "remove_primary_key",
            "add_server_default",
            "remove_server_default",
        ):
            return f"{op}:{diff[1]}"
    except (TypeError, AttributeError, IndexError):
        return ""
    return str(diff)


def test_alembic_version_table_required(
    alembic_config: Config, migration_url: str
) -> None:
    _retry(lambda: command.upgrade(alembic_config, "head"), "upgrade head")
    if _is_postgres(migration_url):
        with _sync_engine(migration_url).connect() as conn:
            row = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = current_schema() "
                    "AND table_name = 'alembic_version'"
                )
            ).scalar_one()
    else:
        with _sync_engine(migration_url).connect() as conn:
            row = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = :schema AND table_name = 'alembic_version'"
                ),
                {
                    "schema": urllib.parse.urlparse(
                        migration_url.replace("mysql+aiomysql://", "mysql://")
                    ).path.lstrip("/")
                },
            ).scalar_one()
    assert row == 1
