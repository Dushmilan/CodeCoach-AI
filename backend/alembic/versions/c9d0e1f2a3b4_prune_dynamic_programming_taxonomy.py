"""prune stale dynamic-programming taxonomy rows

Revision ID: c9d0e1f2a3b4
Revises: a3b4c5d6e7f8
Create Date: 2026-09-03

Why this exists
---------------
#135 split the monolithic ``dynamic-programming`` skill into ``dp-1d`` /
``dp-2d`` and moved interval questions off ``sorting``. The seed script
upserts only, so databases seeded before #135 keep rows that attribute
events to an unknown slug (orphaned per-user states, invisible in the
graph). This is a data-only migration (no schema change):

- ensure the ``dp-1d`` skill row exists (the seed backfills its details)
- remap ``user_skill_states`` ``dynamic-programming`` -> ``dp-1d``,
  preserving mastery/evidence (``dp-1d`` states cannot pre-exist, so the
  unique ``(user_id, skill_slug)`` constraint stays safe)
- delete ``question_skills`` rows pointing at ``dynamic-programming``
- delete the ``skills`` row ``dynamic-programming``

Pair-level leftovers (e.g. the old ``(merge-intervals, sorting)`` pairing,
where ``sorting`` is still a valid slug) are owned by the seed prune in
``scripts/seed_skill_graph.py`` — run the seed after migrating.

``learning_events`` history is immutable and untouched; re-ingest already
ignores unknown slugs, so old events cannot corrupt the graph.

Deploy order: ``alembic upgrade head`` BEFORE ``seed_skill_graph.py`` —
otherwise the seed's skills-row prune would cascade-delete ``dp`` user
states instead of this migration remapping them.

The downgrade is best-effort (restores the skill row + old mappings for
questions that exist); user states are never moved back.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Pre-#135 (question_id, weight) pairs for the monolith, used only by the
# best-effort downgrade. Frozen in time — never import the live taxonomy here.
_DP_PAIRS = (
    ("longest-valid-parentheses", 0.3),
    ("binary-tree-maximum-path-sum", 0.2),
    ("climbing-stairs", 0.8),
    ("coin-change", 1.0),
    ("house-robber", 1.0),
    ("word-break", 0.8),
    ("edit-distance", 0.8),
    ("decode-ways", 0.8),
    ("longest-increasing-subsequence", 0.9),
    ("burst-balloons", 0.9),
    ("maximum-product-subarray", 0.7),
    ("1f3e5d7c-9b8a-4c6d-0e2f-4a5b6c7d8e9f", 0.8),
    ("8c3d2e4f-6a5b-4f7c-9d0e-1a2b3c4d5e6f", 0.8),
    ("9e4f5a6b-7c8d-4e9f-0a1b-2c3d4e5f6a7b", 0.8),
    ("4a3f7c1e-5d6b-4e8f-9a0c-2b3d4e5f6a7b", 0.7),
)


def upgrade() -> None:
    """Remap dp states to dp-1d; delete stale dp rows. Re-runnable."""
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO skills (slug, name, description, prerequisite_ids) "
            "VALUES ('dp-1d', '1-D Dynamic Programming', '', '[\"recursion\"]') "
            "ON CONFLICT (slug) DO NOTHING"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE user_skill_states SET skill_slug = 'dp-1d' "
            "WHERE skill_slug = 'dynamic-programming'"
        )
    )
    conn.execute(
        sa.text("DELETE FROM question_skills WHERE skill_slug = 'dynamic-programming'")
    )
    conn.execute(sa.text("DELETE FROM skills WHERE slug = 'dynamic-programming'"))


def downgrade() -> None:
    """Best-effort restore of the skill row + old mappings. User states stay."""
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO skills (slug, name, description, prerequisite_ids) "
            "VALUES ('dynamic-programming', 'Dynamic Programming', '', "
            "'[\"recursion\"]') ON CONFLICT (slug) DO NOTHING"
        )
    )
    conn.execute(
        sa.text(
            "INSERT INTO question_skills (id, question_id, skill_slug, weight) "
            "SELECT :row_id, q.id, 'dynamic-programming', :weight "
            "FROM questions q WHERE q.id = :question_id "
            "ON CONFLICT (id) DO NOTHING"
        ),
        [
            {
                "row_id": f"{question_id}:dynamic-programming",
                "question_id": question_id,
                "weight": weight,
            }
            for question_id, weight in _DP_PAIRS
        ],
    )
