"""add submissions table (attempt history)

Revision ID: d9e1f2a3b4c5
Revises: c8d0e1f2a3b4
Create Date: 2026-08-15 00:00:00.000000

Persists every graded submit so the product can build the mistake-memory
moat: per-user error graphs, spaced-repetition reviews, and attempt-journey
replay (Ideas #1/#3/#5).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d9e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "c8d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the submissions table (idempotent for re-runs)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    table_exists = bind.execute(
        sa.text("SELECT to_regclass('submissions') IS NOT NULL")
    ).scalar_one()
    if table_exists:
        return

    op.create_table(
        "submissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error_signature", sa.String(length=255), nullable=True),
        sa.Column("attempt_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_submissions_user_id"), "submissions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_submissions_question_id"),
        "submissions",
        ["question_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_submissions_created_at"),
        "submissions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_user_question",
        "submissions",
        ["user_id", "question_id"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_user_created",
        "submissions",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the submissions table."""
    op.drop_index("ix_submissions_user_created", table_name="submissions")
    op.drop_index("ix_submissions_user_question", table_name="submissions")
    op.drop_index(op.f("ix_submissions_created_at"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_question_id"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_user_id"), table_name="submissions")
    op.drop_table("submissions")
