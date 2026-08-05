"""add user plan column

Revision ID: a5369fbca804
Revises: 7fc9e8c06939
Create Date: 2026-08-05 16:29:42.970959

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a5369fbca804"
down_revision: Union[str, Sequence[str], None] = "7fc9e8c06939"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("plan", sa.String(length=20), server_default="free", nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "plan")
