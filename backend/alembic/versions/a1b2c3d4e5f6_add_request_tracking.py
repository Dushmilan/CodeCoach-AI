"""add request tracking schema

Revision ID: a1b2c3d4e5f6
Revises: 7fc9e8c06939
Create Date: 2026-08-06 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7fc9e8c06939"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add request tracking schema: plan, request_count, rate_limit_events."""
    op.add_column(
        "users",
        sa.Column("plan", sa.String(length=20), server_default="free", nullable=False),
    )
    op.create_index(op.f("ix_users_plan"), "users", ["plan"], unique=False)

    op.add_column(
        "user_daily_usage",
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
    )

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


def downgrade() -> None:
    """Revert request tracking schema."""
    is_postgres = op.get_bind().dialect.name == "postgresql"
    op.drop_constraint(
        "rate_limit_events_user_id_fkey" if is_postgres else "rate_limit_events_ibfk_1",
        "rate_limit_events",
        type_="foreignkey",
    )
    op.drop_index("ix_rate_limit_events_ip_created", table_name="rate_limit_events")
    op.drop_index("ix_rate_limit_events_user_created", table_name="rate_limit_events")
    op.drop_index(op.f("ix_rate_limit_events_ip"), table_name="rate_limit_events")
    op.drop_index(op.f("ix_rate_limit_events_user_id"), table_name="rate_limit_events")
    op.drop_index(
        op.f("ix_rate_limit_events_created_at"), table_name="rate_limit_events"
    )
    op.drop_table("rate_limit_events")

    op.drop_column("user_daily_usage", "request_count")

    op.drop_index(op.f("ix_users_plan"), table_name="users")
    op.drop_column("users", "plan")
