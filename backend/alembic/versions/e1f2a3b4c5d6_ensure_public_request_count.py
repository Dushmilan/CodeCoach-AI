"""ensure public.user_daily_usage.request_count exists

Revision ID: e1f2a3b4c5d6
Revises: d9e1f2a3b4c5
Create Date: 2026-08-15 00:00:00.000000

Why this exists
---------------
The repair migration ``c8d0e1f2a3b4`` guarded the ``request_count`` column
with an *unscoped* information_schema query. When a stray test schema
(``codecoach_test``) left on the live database already contained a column of
the same name, the guard believed the column existed and skipped creating it
in ``public`` — leaving ``public.user_daily_usage`` without ``request_count``
and every app query against it failing with UndefinedColumnError.

This migration is the guarded, schema-scoped repair: it adds
``request_count`` to ``public.user_daily_usage`` if (and only if) it is
missing there. The downgrade is a no-op — removal is owned by
``a1b2c3d4e5f6.downgrade``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d9e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _public_request_count_exists(conn) -> bool:
    """True when `user_daily_usage.request_count` exists.

    Scoped to the migration schema (``current_schema()``) — a same-named
    column in another schema must not satisfy this guard.
    """
    row = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = current_schema() "
            "AND table_name = 'user_daily_usage' "
            "AND column_name = 'request_count'"
        )
    ).scalar_one()
    return bool(row)


def upgrade() -> None:
    """Add `public.user_daily_usage.request_count` if missing."""
    conn = op.get_bind()
    if not _public_request_count_exists(conn):
        op.add_column(
            "user_daily_usage",
            sa.Column(
                "request_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade() -> None:
    """No-op: removal of the column is owned by ``a1b2c3d4e5f6``."""
