"""Alembic migration harness: linear-chain, forward/rollback, and drift checks.

Runs against the isolated per-suite schema. These tests are purely sync
(alembic.command drives its own event loop), which is why they live outside
pytest-asyncio's auto loop management.

Back-to-back create/drop of the same table can transiently fail on the
pooler backed by Supabase, so migration ops are wrapped in a bounded retry —
the same resilience pattern recommended for CI migration jobs.
"""

import time
from typing import Callable, List, Tuple

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from tests.migrations.conftest import BACKEND_DIR

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
    return create_engine(url.replace("postgresql+asyncpg://", "postgresql+psycopg://"))


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
        if op in ("add_fk", "remove_fk"):
            constraint = diff[1]
            name = getattr(constraint, "name", None)
            if name:
                return f"{op}:{name}"
            table = getattr(getattr(constraint, "table", None), "name", "?")
            cols = ",".join(sorted(c.name for c in constraint.columns))
            return f"{op}:{table}:{cols}"
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
    with _sync_engine(migration_url).connect() as conn:
        row = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'alembic_version'"
            )
        ).scalar_one()
    assert row == 1


def test_repair_migration_recreates_missing_request_tracking(
    alembic_config: Config, migration_url: str
) -> None:
    """Simulate live-DB drift — migration a1b2c3d4e5f6 stamped but never
    executed, so `rate_limit_events` and `user_daily_usage.request_count` are
    missing — and verify the guarded repair migration restores both."""
    # Normalize state regardless of prior tests in the session, then stop at
    # the pre-repair head (old chain head).
    _retry(lambda: command.downgrade(alembic_config, "base"), "downgrade to base")
    _retry(
        lambda: command.upgrade(alembic_config, "5bb567dd8649"),
        "upgrade to pre-repair head 5bb567dd8649",
    )
    assert _current_version(migration_url) == "5bb567dd8649"

    # Simulate the drift: objects absent while the revision is stamped.
    with _sync_engine(migration_url).connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS rate_limit_events CASCADE"))
        conn.execute(
            text("ALTER TABLE user_daily_usage DROP COLUMN IF EXISTS request_count")
        )
        conn.commit()

    # The repair migration (new head) must recreate the missing objects.
    _retry(
        lambda: command.upgrade(alembic_config, "head"),
        "upgrade head (repair migration)",
    )

    with _sync_engine(migration_url).connect() as conn:
        table_ok = conn.execute(
            text("SELECT to_regclass('public.rate_limit_events') IS NOT NULL")
        ).scalar_one()
        col_ok = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'public' "
                "AND table_name = 'user_daily_usage' "
                "AND column_name = 'request_count'"
            )
        ).scalar_one()
    assert table_ok, "rate_limit_events was not recreated by the repair migration"
    assert col_ok, (
        "public.user_daily_usage.request_count was not recreated by the repair "
        "migration (the guard must scope to 'public', not any schema)"
    )


def test_ensure_public_request_count_migration_repairs_public_only(
    alembic_config: Config, migration_url: str
) -> None:
    """A stray schema carrying `user_daily_usage.request_count` must not fool
    the ensure-public migration: `public` gets the column regardless (this is
    the exact live-DB condition the first repair migration missed)."""
    # Step back below the ensure-public migration so it runs again.
    _retry(
        lambda: command.downgrade(alembic_config, "d9e1f2a3b4c5"),
        "downgrade to d9e1f2a3b4c5",
    )

    # Simulate the drift: public column missing + a stray schema has it.
    with _sync_engine(migration_url).connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE public.user_daily_usage "
                "DROP COLUMN IF EXISTS request_count"
            )
        )
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS stray_test"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS stray_test.user_daily_usage "
                "(id text, request_count integer)"
            )
        )
        conn.commit()

    _retry(
        lambda: command.upgrade(alembic_config, "head"),
        "upgrade head (ensure-public migration)",
    )

    try:
        with _sync_engine(migration_url).connect() as conn:
            col = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'user_daily_usage' "
                    "AND column_name = 'request_count'"
                )
            ).scalar_one()
        assert col == 1, (
            "ensure-public migration did not add request_count to public "
            "when a stray schema already had it"
        )
    finally:
        with _sync_engine(migration_url).connect() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS stray_test CASCADE"))
            conn.commit()


EXPECTED_PROFESSOR_CLASSROOM_INDEXES = {
    "ix_classrooms_owner",
    "ix_enrollments_classroom",
    "ix_enrollments_user",
}

EXPECTED_PROFESSOR_CLASSROOM_FKS = {
    ("courses", "owner_id", "users", "SET NULL", "fk_courses_owner_id_users"),
    (
        "classrooms",
        "course_id",
        "courses",
        "CASCADE",
        "fk_classrooms_course_id_courses",
    ),
    ("classrooms", "owner_id", "users", "SET NULL", "fk_classrooms_owner_id_users"),
    (
        "classroom_enrollments",
        "classroom_id",
        "classrooms",
        "CASCADE",
        "fk_enrollments_classroom_id_classrooms",
    ),
    (
        "classroom_enrollments",
        "user_id",
        "users",
        "CASCADE",
        "fk_enrollments_user_id_users",
    ),
}


def test_professor_classrooms_tables_exist(
    alembic_config: Config, migration_url: str
) -> None:
    """Issue #159 Task 1: professor ownership migration.

    At head, `courses.owner_id` plus the `classrooms` and
    `classroom_enrollments` tables (with the brief's indexes and FKs)
    must exist. Upgrades to head first so the test is order-independent.
    """
    _retry(lambda: command.upgrade(alembic_config, "head"), "upgrade head")

    with _sync_engine(migration_url).connect() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' "
                    "AND table_name IN ('classrooms', 'classroom_enrollments')"
                )
            ).fetchall()
        }
        owner_col = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'public' "
                "AND table_name = 'courses' "
                "AND column_name = 'owner_id'"
            )
        ).scalar_one()
        indexes = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename IN ('classrooms', 'classroom_enrollments')"
                )
            ).fetchall()
        }
        fks = {
            (row[0], row[1], row[2], row[3], row[4])
            for row in conn.execute(
                text(
                    "SELECT tc.table_name, kcu.column_name, "
                    "ccu.table_name AS ref_table, "
                    "rc.delete_rule, tc.constraint_name "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "ON tc.constraint_name = kcu.constraint_name "
                    "AND tc.table_schema = kcu.table_schema "
                    "JOIN information_schema.constraint_column_usage ccu "
                    "ON tc.constraint_name = ccu.constraint_name "
                    "AND tc.table_schema = ccu.table_schema "
                    "JOIN information_schema.referential_constraints rc "
                    "ON tc.constraint_name = rc.constraint_name "
                    "AND tc.table_schema = rc.constraint_schema "
                    "WHERE tc.constraint_type = 'FOREIGN KEY' "
                    "AND tc.table_schema = 'public'"
                )
            ).fetchall()
        }
    assert "classrooms" in tables, "classrooms table missing at head"
    assert "classroom_enrollments" in tables, (
        "classroom_enrollments table missing at head"
    )
    assert owner_col == 1, "courses.owner_id column missing at head"
    missing_indexes = EXPECTED_PROFESSOR_CLASSROOM_INDEXES - indexes
    assert not missing_indexes, f"missing indexes at head: {sorted(missing_indexes)}"
    missing_fks = EXPECTED_PROFESSOR_CLASSROOM_FKS - fks
    assert not missing_fks, f"missing foreign keys at head: {sorted(missing_fks)}"


def test_questions_id_is_varchar_64_at_head(
    alembic_config: Config, migration_url: str
) -> None:
    """Live-DB recovery (#166): the ORM declares questions.id String(64) but
    the initial migration created VARCHAR(36), so the 100-question bank
    (ids up to 46 chars) cannot sync. At head the column must be 64."""
    _retry(lambda: command.upgrade(alembic_config, "head"), "upgrade head")

    with _sync_engine(migration_url).connect() as conn:
        max_len = conn.execute(
            text(
                "SELECT character_maximum_length FROM information_schema.columns "
                "WHERE table_schema = 'public' "
                "AND table_name = 'questions' "
                "AND column_name = 'id'"
            )
        ).scalar_one()
    assert max_len == 64, (
        f"public.questions.id must be VARCHAR(64) at head, found {max_len}"
    )
