"""Add domain column to courses

Revision ID: b3d1e5a9c7f4
Revises: 7fc9e8c06939
Create Date: 2026-08-04 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b3d1e5a9c7f4"
down_revision: Union[str, Sequence[str], None] = "7fc9e8c06939"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the domain column to the courses table."""
    op.add_column(
        "courses",
        sa.Column("domain", sa.String(length=20), server_default="se", nullable=False),
    )


def downgrade() -> None:
    """Drop the domain column from the courses table."""
    op.drop_column("courses", "domain")
