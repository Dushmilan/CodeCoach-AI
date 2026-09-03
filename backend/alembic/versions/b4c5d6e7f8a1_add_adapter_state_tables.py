"""add adapter state tables (coaching + execution sent/submitted/failed)

Revision ID: b4c5d6e7f8a1
Revises: a3b4c5d6e7f8
Create Date: 2026-09-03 00:00:00.000000

Every coaching/execution intent persists sent before the external call and
transitions to a terminal state after, so timeouts and failures remain
auditable. Submissions gain an explicit status machine (sent -> graded /
failed) while preserving the legacy passed flag.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "b4c5d6e7f8a1"
down_revision: Union[str, Sequence[str], None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, name: str) -> bool:
    return bool(
        bind.execute(
            sa.text("SELECT to_regclass(:name) IS NOT NULL"), {"name": f"public.{name}"}
        ).scalar_one()
    )


def _column_exists(bind, table: str, column: str) -> bool:
    return bool(
        bind.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t AND column_name=:c)"
            ),
            {"t": table, "c": column},
        ).scalar_one()
    )


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    if not _table_exists(bind, "coaching_interactions"):
        op.create_table(
            "coaching_interactions",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("question_id", sa.String(length=64), nullable=True),
            sa.Column("lesson_id", sa.String(length=36), nullable=True),
            sa.Column("mode", sa.String(length=20), nullable=False),
            sa.Column("language", sa.String(length=20), nullable=False),
            sa.Column("problem_hash", sa.String(length=64), nullable=False),
            sa.Column("code_hash", sa.String(length=64), nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column(
                "status", sa.String(length=20), nullable=False, server_default="sent"
            ),
            sa.Column("request_payload", JSONB(), nullable=False, server_default="{}"),
            sa.Column("response_payload", JSONB(), nullable=True),
            sa.Column("error_code", sa.String(length=50), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("model", sa.String(length=100), nullable=True),
            sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "output_tokens", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("request_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["question_id"], ["questions.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "uq_coaching_user_idempotency",
            "coaching_interactions",
            ["user_id", "idempotency_key"],
            unique=True,
        )
        op.create_index(
            "ix_coaching_user_status_created",
            "coaching_interactions",
            ["user_id", "status", "created_at"],
        )
        # Single-column indexes implied by ORM index=True.
        op.create_index(
            "ix_coaching_interactions_user_id",
            "coaching_interactions",
            ["user_id"],
        )
        op.create_index(
            "ix_coaching_interactions_question_id",
            "coaching_interactions",
            ["question_id"],
        )
        op.create_index(
            "ix_coaching_interactions_created_at",
            "coaching_interactions",
            ["created_at"],
        )

    if not _table_exists(bind, "execution_jobs"):
        op.create_table(
            "execution_jobs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("question_id", sa.String(length=64), nullable=True),
            sa.Column("language", sa.String(length=20), nullable=False),
            sa.Column("code_hash", sa.String(length=64), nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column(
                "status", sa.String(length=20), nullable=False, server_default="sent"
            ),
            sa.Column("request_payload", JSONB(), nullable=False, server_default="{}"),
            sa.Column("response_payload", JSONB(), nullable=True),
            sa.Column("test_results", JSONB(), nullable=True),
            sa.Column("error_code", sa.String(length=50), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("execution_time_ms", sa.Integer(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("request_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["question_id"], ["questions.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "uq_execution_user_idempotency",
            "execution_jobs",
            ["user_id", "idempotency_key"],
            unique=True,
        )
        op.create_index(
            "ix_execution_user_status_created",
            "execution_jobs",
            ["user_id", "status", "created_at"],
        )
        op.create_index(
            "ix_execution_jobs_user_id",
            "execution_jobs",
            ["user_id"],
        )
        op.create_index(
            "ix_execution_jobs_question_id",
            "execution_jobs",
            ["question_id"],
        )
        op.create_index(
            "ix_execution_jobs_created_at",
            "execution_jobs",
            ["created_at"],
        )

    # Augment submissions with an explicit status machine (default graded
    # preserves legacy rows and existing graded writes).
    if not _column_exists(bind, "submissions", "status"):
        op.add_column(
            "submissions",
            sa.Column(
                "status", sa.String(length=20), nullable=False, server_default="graded"
            ),
        )
    if not _column_exists(bind, "submissions", "idempotency_key"):
        op.add_column(
            "submissions",
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        )
    if not _column_exists(bind, "submissions", "execution_job_id"):
        op.add_column(
            "submissions",
            sa.Column("execution_job_id", sa.String(length=36), nullable=True),
        )
    if not _column_exists(bind, "submissions", "request_id"):
        op.add_column(
            "submissions", sa.Column("request_id", sa.String(length=64), nullable=True)
        )
    bind.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_submissions_user_status_created "
            "ON public.submissions (user_id, status, created_at)"
        )
    )
    bind.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_submissions_user_idempotency "
            "ON public.submissions (user_id, idempotency_key) "
            "WHERE idempotency_key IS NOT NULL"
        )
    )
    bind.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_submissions_execution_job_id "
            "ON public.submissions (execution_job_id)"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DROP INDEX IF EXISTS ix_submissions_execution_job_id"))
    bind.execute(sa.text("DROP INDEX IF EXISTS uq_submissions_user_idempotency"))
    bind.execute(sa.text("DROP INDEX IF EXISTS ix_submissions_user_status_created"))
    for col in ("request_id", "execution_job_id", "idempotency_key", "status"):
        bind.execute(
            sa.text(f"ALTER TABLE public.submissions DROP COLUMN IF EXISTS {col}")
        )
    op.drop_index("ix_execution_jobs_created_at", table_name="execution_jobs")
    op.drop_index("ix_execution_jobs_question_id", table_name="execution_jobs")
    op.drop_index("ix_execution_jobs_user_id", table_name="execution_jobs")
    op.drop_index("ix_execution_user_status_created", table_name="execution_jobs")
    op.drop_index("uq_execution_user_idempotency", table_name="execution_jobs")
    op.drop_table("execution_jobs")
    op.drop_index(
        "ix_coaching_interactions_created_at", table_name="coaching_interactions"
    )
    op.drop_index(
        "ix_coaching_interactions_question_id", table_name="coaching_interactions"
    )
    op.drop_index(
        "ix_coaching_interactions_user_id", table_name="coaching_interactions"
    )
    op.drop_index("ix_coaching_user_status_created", table_name="coaching_interactions")
    op.drop_index("uq_coaching_user_idempotency", table_name="coaching_interactions")
    op.drop_table("coaching_interactions")
