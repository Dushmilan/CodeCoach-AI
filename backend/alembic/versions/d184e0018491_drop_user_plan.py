"""Remove users.plan + ix_users_plan (Issue #184: open source, no payments).

Destructive: drops the plan tier column and its index. Downgrade restores
both (server_default free, matching a5369fbca804).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d184e0018491"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_users_plan"), table_name="users")
    op.drop_column("users", "plan")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("plan", sa.String(length=20), server_default="free", nullable=False),
    )
    op.create_index(op.f("ix_users_plan"), "users", ["plan"], unique=False)
