"""add usage tracking tables

Revision ID: 7fc9e8c06939
Revises: 4476164f80b7
Create Date: 2026-08-04 10:11:19.208381

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7fc9e8c06939"
down_revision: Union[str, Sequence[str], None] = "4476164f80b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_usage_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("endpoint", sa.String(length=50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_usage_events_created_at"),
        "user_usage_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_usage_events_user_id"),
        "user_usage_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_usage_events_user_created",
        "user_usage_events",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "user_daily_usage",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_daily_usage_user_id"),
        "user_daily_usage",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_daily_user_date",
        "user_daily_usage",
        ["user_id", "usage_date"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    is_postgres = op.get_bind().dialect.name == "postgresql"
    op.drop_constraint(
        "user_daily_usage_user_id_fkey" if is_postgres else "user_daily_usage_ibfk_1",
        "user_daily_usage",
        type_="foreignkey",
    )
    op.drop_constraint(
        "user_usage_events_user_id_fkey" if is_postgres else "user_usage_events_ibfk_1",
        "user_usage_events",
        type_="foreignkey",
    )
    op.drop_index("ix_daily_user_date", table_name="user_daily_usage")
    op.drop_index(op.f("ix_user_daily_usage_user_id"), table_name="user_daily_usage")
    op.drop_table("user_daily_usage")
    op.drop_index("ix_usage_events_user_created", table_name="user_usage_events")
    op.drop_index(op.f("ix_user_usage_events_user_id"), table_name="user_usage_events")
    op.drop_index(
        op.f("ix_user_usage_events_created_at"), table_name="user_usage_events"
    )
    op.drop_table("user_usage_events")
