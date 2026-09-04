"""add rescue_queue table (durable rescue re-surface queue)

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-08-23 00:00:00.000000

Every abandoned problem becomes a durable row that resurfaces as a tiny
re-entry step (Ideas #4 - the "never-alone" contract's re-surface loop).
"Due" is derived from due_at at read time; a partial unique index enforces
one OPEN row per (user_id, question_id).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the rescue_queue table (idempotent for re-runs)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    table_exists = bind.execute(
        sa.text("SELECT to_regclass('rescue_queue') IS NOT NULL")
    ).scalar_one()
    if table_exists:
        return

    op.create_table(
        "rescue_queue",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("first_abandoned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resurface_count", sa.Integer(), nullable=False),
        sa.Column("last_intervention_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rescue_queue_user_id"), "rescue_queue", ["user_id"], unique=False
    )
    op.create_index(
        "ix_rescue_queue_user_status_due",
        "rescue_queue",
        ["user_id", "status", "due_at"],
        unique=False,
    )
    # Exactly one OPEN (status='abandoned') row per (user, question).
    op.create_index(
        "uq_rescue_queue_open_user_question",
        "rescue_queue",
        ["user_id", "question_id"],
        unique=True,
        postgresql_where=sa.text("status = 'abandoned'"),
    )


def downgrade() -> None:
    """Drop the rescue_queue table."""
    op.drop_index("uq_rescue_queue_open_user_question", table_name="rescue_queue")
    op.drop_index("ix_rescue_queue_user_status_due", table_name="rescue_queue")
    op.drop_index(op.f("ix_rescue_queue_user_id"), table_name="rescue_queue")
    op.drop_table("rescue_queue")
