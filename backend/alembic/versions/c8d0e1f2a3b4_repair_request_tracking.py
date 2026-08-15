"""repair missing request-tracking schema

Revision ID: c8d0e1f2a3b4
Revises: 5bb567dd8649
Create Date: 2026-08-15 00:00:00.000000

Why this exists
---------------
Migration ``a1b2c3d4e5f6`` was stamped on the live database without actually
executing, so ``rate_limit_events`` and ``user_daily_usage.request_count``
were never created. The app no longer runs ``Base.metadata.create_all`` at
startup, so those objects will never appear on their own — every code path
that reads/writes them (abuse detection, /health/monitoring, the daily-cap DB
fallback) would fail at runtime.

This migration is a **guarded, idempotent repair**: it creates each object
only when missing. On a fresh database (where ``a1b2c3d4e5f6`` ran normally)
it is a no-op. It must not re-run ``a1b2c3d4e5f6`` wholesale, because that
would also re-add ``users.plan`` and collide with the existing column.

The downgrade is intentionally a no-op: removal of these objects is owned by
``a1b2c3d4e5f6.downgrade`` (same pattern as ``a5369fbca804``).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "5bb567dd8649"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rate_limit_events_table_exists(conn) -> bool:
    """True when `rate_limit_events` already exists in the public schema."""
    row = conn.execute(
        sa.text("SELECT to_regclass('public.rate_limit_events') IS NOT NULL")
    ).scalar_one()
    return bool(row)


def _request_count_column_exists(conn) -> bool:
    """True when `user_daily_usage.request_count` already exists."""
    row = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = 'user_daily_usage' "
            "AND column_name = 'request_count'"
        )
    ).scalar_one()
    return bool(row)


def upgrade() -> None:
    """Create the missing request-tracking objects if (and only if) absent."""
    conn = op.get_bind()

    if not _rate_limit_events_table_exists(conn):
        op.create_table(
            "rate_limit_events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=True),
            sa.Column("ip", sa.String(length=45), nullable=False),
            sa.Column("reason", sa.String(length=50), nullable=False),
            sa.Column("endpoint", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_rate_limit_events_created_at"),
            "rate_limit_events",
            ["created_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_rate_limit_events_user_id"),
            "rate_limit_events",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_rate_limit_events_ip"),
            "rate_limit_events",
            ["ip"],
            unique=False,
        )
        op.create_index(
            "ix_rate_limit_events_user_created",
            "rate_limit_events",
            ["user_id", "created_at"],
            unique=False,
        )
        op.create_index(
            "ix_rate_limit_events_ip_created",
            "rate_limit_events",
            ["ip", "created_at"],
            unique=False,
        )

    if not _request_count_column_exists(conn):
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
    """No-op: removal of these objects is owned by ``a1b2c3d4e5f6``."""
