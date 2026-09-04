"""add review_cards table (mistake-memory spaced repetition)

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-08-24 00:00:00.000000

One SM-2 review card per (user_id, question_id, error_signature): failing a
question with a stable error signature opens/refreshes an 'active' card;
passing the question promotes it into the spaced-repetition rotation as
'scheduled' (Ideas #1 - mistake-memory moat).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the review_cards table (idempotent for re-runs)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    table_exists = bind.execute(
        sa.text("SELECT to_regclass('review_cards') IS NOT NULL")
    ).scalar_one()
    if table_exists:
        return

    op.create_table(
        "review_cards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("error_signature", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("ease", sa.Float(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("lapses", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_review_cards_user_id"), "review_cards", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_review_cards_question_id"),
        "review_cards",
        ["question_id"],
        unique=False,
    )
    # One card per (user, question, error signature).
    op.create_index(
        "uq_review_cards_user_question_signature",
        "review_cards",
        ["user_id", "question_id", "error_signature"],
        unique=True,
    )
    op.create_index(
        "ix_review_cards_user_state_due",
        "review_cards",
        ["user_id", "state", "due_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the review_cards table."""
    op.drop_index("ix_review_cards_user_state_due", table_name="review_cards")
    op.drop_index("uq_review_cards_user_question_signature", table_name="review_cards")
    op.drop_index(op.f("ix_review_cards_question_id"), table_name="review_cards")
    op.drop_index(op.f("ix_review_cards_user_id"), table_name="review_cards")
    op.drop_table("review_cards")
