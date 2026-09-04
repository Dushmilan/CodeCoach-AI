"""Data migration: prune stale ``dynamic-programming`` taxonomy rows (#138).

#135 split the monolith into ``dp-1d``/``dp-2d`` and moved interval
questions off ``sorting``. Seed upserts only, so live DBs keep stale rows
that attribute events to an unknown slug. The migration must cover all:

- ``skills`` row ``dynamic-programming`` deleted
- ``question_skills`` rows for unknown slugs deleted
- ``user_skill_states`` ``dynamic-programming`` remapped to ``dp-1d``
  (``dp-1d`` states cannot pre-exist, so the unique constraint is safe)
- ``learning_events`` history left immutable
- re-runnable (second upgrade is a no-op); downgrade restores the skill row
"""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

PARENT = "a3b4c5d6e7f8"


def _sync_engine(url: str):
    return create_engine(url.replace("postgresql+asyncpg://", "postgresql+psycopg://"))


def _exec(url: str, sql: str, params: dict | None = None) -> None:
    eng = _sync_engine(url)
    try:
        with eng.connect() as conn:
            conn.execute(text(sql), params or {})
            conn.commit()
    finally:
        eng.dispose()


def _scalar(url: str, sql: str, params: dict | None = None):
    eng = _sync_engine(url)
    try:
        with eng.connect() as conn:
            return conn.execute(text(sql), params or {}).scalar()
    finally:
        eng.dispose()


def _seed_stale_rows(url: str) -> None:
    _exec(
        url,
        "INSERT INTO users (id, username, email, hashed_password, created_at, "
        "is_active) VALUES ('u-cleanup', 'cleanupuser', 'cleanup@test.com', "
        "'x', now(), 1) ON CONFLICT (id) DO NOTHING",
    )
    _exec(
        url,
        "INSERT INTO questions (id, title, difficulty, category, company_tags, "
        "description, starter_code, examples, test_cases, hints, constraints, "
        "is_interactive) VALUES ('coin-change', 'Coin Change', 'medium', "
        "'dynamic-programming', '[]', 'desc', '{}', '[]', '[]', '[]', '[]', 0) "
        "ON CONFLICT (id) DO NOTHING",
    )
    _exec(
        url,
        "INSERT INTO skills (slug, name, description, prerequisite_ids) "
        "VALUES ('dynamic-programming', 'Dynamic Programming', '', '[]') "
        "ON CONFLICT (slug) DO NOTHING",
    )
    _exec(
        url,
        "INSERT INTO question_skills (id, question_id, skill_slug, weight) "
        "VALUES ('coin-change:dynamic-programming', 'coin-change', "
        "'dynamic-programming', 1.0) ON CONFLICT (id) DO NOTHING",
    )
    _exec(
        url,
        "INSERT INTO user_skill_states (id, user_id, skill_slug, mastery_score, "
        "confidence, evidence_count, recent_error_count, distinct_question_ids, "
        "last_seen_at, updated_at) VALUES ('u-cleanup:dynamic-programming', "
        "'u-cleanup', 'dynamic-programming', 0.5, 0.3, 4, 1, '[]', now(), now()) "
        "ON CONFLICT (id) DO NOTHING",
    )


def test_cleanup_migration_prunes_and_remaps(
    alembic_config: Config, migration_url: str
) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, PARENT)
    _seed_stale_rows(migration_url)
    command.upgrade(alembic_config, "head")

    assert (
        _scalar(
            migration_url,
            "SELECT COUNT(*) FROM skills WHERE slug = 'dynamic-programming'",
        )
        == 0
    )
    assert (
        _scalar(
            migration_url,
            "SELECT COUNT(*) FROM question_skills "
            "WHERE skill_slug = 'dynamic-programming'",
        )
        == 0
    )
    remapped = _scalar(
        migration_url,
        "SELECT mastery_score FROM user_skill_states "
        "WHERE user_id = 'u-cleanup' AND skill_slug = 'dp-1d'",
    )
    assert remapped is not None and abs(float(remapped) - 0.5) < 1e-6
    assert (
        _scalar(
            migration_url,
            "SELECT COUNT(*) FROM user_skill_states "
            "WHERE skill_slug = 'dynamic-programming'",
        )
        == 0
    )

    # Re-runnable: a second upgrade changes nothing.
    before = _scalar(migration_url, "SELECT COUNT(*) FROM question_skills")
    command.upgrade(alembic_config, "head")
    assert _scalar(migration_url, "SELECT COUNT(*) FROM question_skills") == before

    # Downgrade restores the skill row (best-effort); re-upgrade cleans again.
    command.downgrade(alembic_config, PARENT)
    assert (
        _scalar(
            migration_url,
            "SELECT COUNT(*) FROM skills WHERE slug = 'dynamic-programming'",
        )
        == 1
    )
    command.upgrade(alembic_config, "head")
    assert (
        _scalar(
            migration_url,
            "SELECT COUNT(*) FROM skills WHERE slug = 'dynamic-programming'",
        )
        == 0
    )
