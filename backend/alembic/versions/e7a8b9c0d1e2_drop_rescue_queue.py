"""drop rescue_queue table (rescue system removed, #163)

Revision ID: e7a8b9c0d1e2
Revises: b4c5d6e7f8a1
Create Date: 2026-09-15 00:00:00.000000

Tasks 1-2 deleted the entire Rescue stuck-learner system (router, service,
repository, schemas, ORM); the durable re-surface queue is written by
nothing. Dropping destroys queued rows — explicitly user-authorized
(issue #163). Downgrade recreates the exact original shape from
f2a3b4c5d6e7_add_rescue_queue.py.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the rescue_queue table (idempotent for re-runs)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only PostgreSQL is supported")

    table_exists = bind.execute(
        sa.text("SELECT to_regclass('public.rescue_queue') IS NOT NULL")
    ).scalar_one()
    if not table_exists:
        return

    op.drop_index("uq_rescue_queue_open_user_question", table_name="rescue_queue")
    op.drop_index("ix_rescue_queue_user_status_due", table_name="rescue_queue")
    op.drop_index("ix_rescue_queue_user_id", table_name="rescue_queue")
    op.drop_table("rescue_queue")


def downgrade() -> None:
    """Recreate the rescue_queue table (exact shape from f2a3b4c5d6e7)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only PostgreSQL is supported")

    table_exists = bind.execute(
        sa.text("SELECT to_regclass('public.rescue_queue') IS NOT NULL")
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
