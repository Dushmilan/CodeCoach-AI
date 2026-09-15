"""Drop rescue_queue table (#163, Task 3).

Tasks 1-2 deleted the entire Rescue stuck-learner system (router, service,
repository, schemas, ORM); the durable re-surface queue is written by nothing.
Dropping destroys queued rows — explicitly user-authorized (issue #163).

This pins the destructive intent: at head the table (and its indexes) must be
gone, while a one-step downgrade restores the exact original shape (reversible
migration), and a re-upgrade drops it again.
"""

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

EXPECTED_COLUMNS = {
    "id",
    "user_id",
    "question_id",
    "status",
    "first_abandoned_at",
    "due_at",
    "resurface_count",
    "last_intervention_at",
    "created_at",
    "updated_at",
}

EXPECTED_INDEXES = {
    "ix_rescue_queue_user_id",
    "ix_rescue_queue_user_status_due",
    "uq_rescue_queue_open_user_question",
}


def _sync_engine(url: str):
    return create_engine(url.replace("postgresql+asyncpg://", "postgresql+psycopg://"))


def _table_present(url: str) -> bool:
    eng = _sync_engine(url)
    try:
        with eng.connect() as conn:
            return bool(
                conn.execute(
                    text("SELECT to_regclass('public.rescue_queue') IS NOT NULL")
                ).scalar_one()
            )
    finally:
        eng.dispose()


def _columns(url: str) -> set[str]:
    eng = _sync_engine(url)
    try:
        with eng.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'rescue_queue'"
                )
            ).fetchall()
            return {r[0] for r in rows}
    finally:
        eng.dispose()


def _indexes(url: str) -> set[str]:
    eng = _sync_engine(url)
    try:
        with eng.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename = 'rescue_queue'"
                )
            ).fetchall()
            return {r[0] for r in rows}
    finally:
        eng.dispose()


def test_head_drops_rescue_queue(alembic_config: Config, migration_url: str) -> None:
    command.upgrade(alembic_config, "head")
    assert not _table_present(migration_url), (
        "rescue_queue still exists at migration head — expected drop migration"
    )


def test_drop_rescue_queue_downgrade_restores_original_shape(
    alembic_config: Config, migration_url: str
) -> None:
    script = ScriptDirectory.from_config(alembic_config)
    heads = script.get_heads()
    assert len(heads) == 1
    parent = script.get_revision(heads[0]).down_revision
    assert parent is not None, "migration head must have a parent revision"

    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, parent)
    assert _table_present(migration_url), (
        f"downgrade to {parent} did not restore rescue_queue"
    )
    assert _columns(migration_url) == EXPECTED_COLUMNS
    assert EXPECTED_INDEXES <= _indexes(migration_url)

    command.upgrade(alembic_config, "head")
    assert not _table_present(migration_url), (
        "re-upgrade to head did not drop rescue_queue again"
    )
