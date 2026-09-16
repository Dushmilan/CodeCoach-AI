"""widen questions.id VARCHAR(36) -> VARCHAR(64) (live-DB recovery, #166)

Revision ID: f4a5b6c7d8e9
Revises: e7a8b9c0d1e2
Create Date: 2026-09-16 00:00:00.000000

The ORM declares ``QuestionORM.id`` as ``String(64)`` but the initial
migration created ``VARCHAR(36)``. The recovered 100-question bank has ids
up to 46 chars, so the sync fails with StringDataRightTruncationError.
Widening is data-safe (never truncates). Downgrade back to 36 refuses when
rows would be truncated.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "e7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Widen public.questions.id to VARCHAR(64) when narrower (idempotent)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    max_len = bind.execute(
        sa.text(
            "SELECT character_maximum_length FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "AND table_name = 'questions' "
            "AND column_name = 'id'"
        )
    ).scalar_one_or_none()
    if max_len is not None and max_len >= 64:
        return

    op.alter_column(
        "questions",
        "id",
        existing_type=sa.String(length=36),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Narrow back to VARCHAR(36); refuses when rows would be truncated."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    too_long = bind.execute(
        sa.text("SELECT COUNT(*) FROM public.questions WHERE length(id) > 36")
    ).scalar_one()
    if too_long:
        raise RuntimeError(
            f"Cannot narrow questions.id to VARCHAR(36): {too_long} rows "
            "have longer ids."
        )

    op.alter_column(
        "questions",
        "id",
        existing_type=sa.String(length=64),
        type_=sa.String(length=36),
        existing_nullable=False,
    )
