"""add skill graph tables

Revision ID: 5bb567dd8649
Revises: a5369fbca804
Create Date: 2026-08-13 23:53:26.662224

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5bb567dd8649"
down_revision: Union[str, Sequence[str], None] = "a5369fbca804"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_JSON = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "mysql")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "skills",
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.String(length=64), nullable=True),
        sa.Column("prerequisite_ids", _JSON, nullable=False),
        sa.PrimaryKeyConstraint("slug"),
    )
    op.create_table(
        "learning_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=True),
        sa.Column("lesson_id", sa.String(length=36), nullable=True),
        sa.Column("skill_slug", sa.String(length=64), nullable=True),
        sa.Column("event_metadata", _JSON, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_events_occurred_at"),
        "learning_events",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_events_skill_slug"),
        "learning_events",
        ["skill_slug"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_events_user_id"),
        "learning_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_learning_events_user_occurred",
        "learning_events",
        ["user_id", "occurred_at"],
        unique=False,
    )
    op.create_table(
        "question_skills",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("skill_slug", sa.String(length=64), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_slug"], ["skills.slug"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_question_skills_question",
        "question_skills",
        ["question_id", "skill_slug"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_skills_question_id"),
        "question_skills",
        ["question_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_skills_skill_slug"),
        "question_skills",
        ["skill_slug"],
        unique=False,
    )
    op.create_table(
        "user_skill_states",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("skill_slug", sa.String(length=64), nullable=False),
        sa.Column("mastery_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("recent_error_count", sa.Integer(), nullable=False),
        sa.Column("distinct_question_ids", _JSON, nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_slug"], ["skills.slug"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_skill_states_skill_slug"),
        "user_skill_states",
        ["skill_slug"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_skill_states_user_id"),
        "user_skill_states",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_skill_states_user_slug",
        "user_skill_states",
        ["user_id", "skill_slug"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_user_skill_states_user_id"), table_name="user_skill_states")
    op.drop_index(
        op.f("ix_user_skill_states_skill_slug"), table_name="user_skill_states"
    )
    op.drop_index("ix_user_skill_states_user_slug", table_name="user_skill_states")
    op.drop_table("user_skill_states")
    op.drop_index(op.f("ix_question_skills_skill_slug"), table_name="question_skills")
    op.drop_index(op.f("ix_question_skills_question_id"), table_name="question_skills")
    op.drop_index("ix_question_skills_question", table_name="question_skills")
    op.drop_table("question_skills")
    op.drop_index(op.f("ix_learning_events_user_id"), table_name="learning_events")
    op.drop_index(op.f("ix_learning_events_skill_slug"), table_name="learning_events")
    op.drop_index(op.f("ix_learning_events_occurred_at"), table_name="learning_events")
    op.drop_index("ix_learning_events_user_occurred", table_name="learning_events")
    op.drop_table("learning_events")
    op.drop_table("skills")
