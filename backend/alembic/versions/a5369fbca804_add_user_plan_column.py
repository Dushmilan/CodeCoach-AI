"""add user plan column

Revision ID: a5369fbca804
Revises: 7fc9e8c06939
Create Date: 2026-08-05 16:29:42.970959

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "a5369fbca804"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    No-op: `users.plan` is already added by a1b2c3d4e5f6 (add request tracking),
    which is a superset of the original `a5369fbca804` work. Re-parented after
    a1b2c3d4e5f6 to keep the migration graph linear (two migrations previously
    branched off 7fc9e8c06939, producing duplicate `users.plan` columns).
    """


def downgrade() -> None:
    """Downgrade schema.

    No-op: `users.plan` is owned by a1b2c3d4e5f6, which removes it in its own
    downgrade.
    """
