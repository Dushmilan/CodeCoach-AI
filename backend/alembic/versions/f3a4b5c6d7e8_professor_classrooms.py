"""add professor ownership, classrooms, and classroom enrollments

Revision ID: f3a4b5c6d7e8
Revises: b4c5d6e7f8a1
Create Date: 2026-09-15 00:00:00.000000

Issue #159 professor dashboard DB wiring (Task 1): courses gain a nullable
``owner_id`` (professor) referencing ``users.id`` with ``ON DELETE SET NULL``;
``classrooms`` scopes a course to an owned cohort (unique invite code);
``classroom_enrollments`` links users to classrooms with a role
(``student``/``ta``) and one row per (classroom, user).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "b4c5d6e7f8a1"
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


def _index_exists(bind, name: str) -> bool:
    return bool(
        bind.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM pg_indexes "
                "WHERE schemaname='public' AND indexname=:n)"
            ),
            {"n": name},
        ).scalar_one()
    )


def _constraint_exists(bind, table: str, name: str) -> bool:
    return bool(
        bind.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints "
                "WHERE table_schema='public' AND table_name=:t "
                "AND constraint_name=:n)"
            ),
            {"t": table, "n": name},
        ).scalar_one()
    )


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    if not _column_exists(bind, "courses", "owner_id"):
        op.add_column(
            "courses", sa.Column("owner_id", sa.String(length=36), nullable=True)
        )
        op.create_foreign_key(
            "fk_courses_owner_id_users",
            "courses",
            "users",
            ["owner_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not _table_exists(bind, "classrooms"):
        op.create_table(
            "classrooms",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("course_id", sa.String(length=36), nullable=False),
            sa.Column("owner_id", sa.String(length=36), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("invite_code", sa.String(length=64), nullable=False),
            sa.Column("term", sa.String(length=64), nullable=True),
            sa.Column("schedule", sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(
                ["course_id"],
                ["courses.id"],
                name="fk_classrooms_course_id_courses",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["owner_id"],
                ["users.id"],
                name="fk_classrooms_owner_id_users",
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("invite_code", name="uq_classrooms_invite_code"),
        )
        op.create_index("ix_classrooms_owner", "classrooms", ["owner_id"], unique=False)

    if not _table_exists(bind, "classroom_enrollments"):
        op.create_table(
            "classroom_enrollments",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("classroom_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column(
                "role",
                sa.String(length=10),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["classroom_id"],
                ["classrooms.id"],
                name="fk_enrollments_classroom_id_classrooms",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name="fk_enrollments_user_id_users",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "classroom_id", "user_id", name="uq_enrollment_classroom_user"
            ),
        )
        op.create_index(
            "ix_enrollments_classroom",
            "classroom_enrollments",
            ["classroom_id"],
            unique=False,
        )
        op.create_index(
            "ix_enrollments_user", "classroom_enrollments", ["user_id"], unique=False
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Only Supabase/PostgreSQL is supported")

    if _table_exists(bind, "classroom_enrollments"):
        if _index_exists(bind, "ix_enrollments_user"):
            op.drop_index("ix_enrollments_user", table_name="classroom_enrollments")
        if _index_exists(bind, "ix_enrollments_classroom"):
            op.drop_index(
                "ix_enrollments_classroom", table_name="classroom_enrollments"
            )
        op.drop_table("classroom_enrollments")
    if _table_exists(bind, "classrooms"):
        if _index_exists(bind, "ix_classrooms_owner"):
            op.drop_index("ix_classrooms_owner", table_name="classrooms")
        op.drop_table("classrooms")
    if _column_exists(bind, "courses", "owner_id"):
        if _constraint_exists(bind, "courses", "fk_courses_owner_id_users"):
            op.drop_constraint(
                "fk_courses_owner_id_users", "courses", type_="foreignkey"
            )
        op.drop_column("courses", "owner_id")
