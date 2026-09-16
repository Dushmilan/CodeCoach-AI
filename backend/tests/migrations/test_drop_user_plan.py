"""Drop users.plan + ix_users_plan (#184: open source, no payments).

Destructive intent is user-authorized (issue #184): at head the column and
its index must be gone, while a one-step downgrade restores them, and a
re-upgrade drops them again.
"""

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text


def _sync_engine(url: str):
    return create_engine(url.replace("postgresql+asyncpg://", "postgresql+psycopg://"))


def _plan_present(url: str) -> tuple[bool, bool]:
    eng = _sync_engine(url)
    try:
        with eng.connect() as conn:
            col = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'users' "
                    "AND column_name = 'plan'"
                )
            ).scalar_one()
            idx = conn.execute(
                text(
                    "SELECT COUNT(*) FROM pg_indexes "
                    "WHERE schemaname = 'public' AND indexname = 'ix_users_plan'"
                )
            ).scalar_one()
            return bool(col), bool(idx)
    finally:
        eng.dispose()


def test_head_drops_user_plan(alembic_config: Config, migration_url: str) -> None:
    command.upgrade(alembic_config, "head")
    has_col, has_idx = _plan_present(migration_url)
    assert has_col is False
    assert has_idx is False


def test_drop_user_plan_downgrade_restores_column(
    alembic_config: Config, migration_url: str
) -> None:
    # Pinned to the drop revision (not "head") so later migrations stacking on
    # top cannot break the reversibility assertion.
    drop_rev = "d184e0018491"
    script = ScriptDirectory.from_config(alembic_config)
    parent = script.get_revision(drop_rev).down_revision
    assert parent is not None, "drop migration must have a parent revision"

    command.upgrade(alembic_config, drop_rev)
    command.downgrade(alembic_config, parent)
    has_col, has_idx = _plan_present(migration_url)
    assert has_col is True
    assert has_idx is True

    command.upgrade(alembic_config, drop_rev)
    has_col, has_idx = _plan_present(migration_url)
    assert has_col is False
    assert has_idx is False
