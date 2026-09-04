#!/usr/bin/env python3
"""Seed the skill taxonomy + question-skill mappings into Supabase.

Idempotent and re-runnable: upserts by natural key (skills.slug,
question_skills.question_id+skill_slug), then prunes taxonomy-unknown rows
so past renames (e.g. #135's ``dynamic-programming`` split) self-heal
instead of attributing events to unknown slugs. Never deletes rows outside
the taxonomy-owned ``skills`` / ``question_skills`` tables.

Deploy order: run ``alembic upgrade head`` BEFORE this seed — the taxonomy
cleanup migration remaps user states first, otherwise this prune would
cascade-delete them.

Usage:
    DATABASE_URL=postgresql://... python scripts/seed_skill_graph.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.models.orm import QuestionORM, QuestionSkillORM, SkillORM
from app.services.skill_taxonomy import QUESTION_SKILLS, SKILLS


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit(
            "ERROR: DATABASE_URL is required (Supabase/PostgreSQL connection "
            "string); no local fallback is allowed."
        )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _create_engine():
    """Engine honoring DATABASE_SEARCH_PATH (same convention as the app).

    Isolated-schema environments (tests, staging previews) set
    DATABASE_SEARCH_PATH; production Supabase leaves it unset and defaults
    to the public schema.
    """

    search_path = os.getenv("DATABASE_SEARCH_PATH")
    kwargs = {}
    if search_path:
        kwargs["connect_args"] = {"server_settings": {"search_path": search_path}}
    return create_async_engine(_get_database_url(), poolclass=NullPool, **kwargs)


async def _prune_stale_rows(session) -> int:
    """Delete taxonomy-unknown skills and question-skill pairs.

    The seed owns the taxonomy-defined content of these tables: ``skills``
    rows are exactly ``SKILLS``, and ``question_skills`` rows for
    taxonomy-covered questions are exactly ``QUESTION_SKILLS`` pairs.
    Anything else is stale (a past rename) and must go, otherwise events
    attribute to unknown slugs. Rows for questions outside the taxonomy
    are left alone — this seed cannot judge them.
    """
    pruned = 0
    valid_slugs = {s.slug for s in SKILLS}
    stale_skills = (
        (
            await session.execute(
                select(SkillORM).where(SkillORM.slug.not_in(valid_slugs))
            )
        )
        .scalars()
        .all()
    )
    for row in stale_skills:
        await session.delete(row)
        pruned += 1

    expected_pairs = {
        (question_id, m.skill_slug)
        for question_id, mappings in QUESTION_SKILLS.items()
        for m in mappings
    }
    pairs = (await session.execute(select(QuestionSkillORM))).scalars().all()
    for row in pairs:
        if (
            row.question_id in QUESTION_SKILLS
            and (row.question_id, row.skill_slug) not in expected_pairs
        ):
            await session.delete(row)
            pruned += 1
    return pruned


async def seed() -> int:
    engine = _create_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    total = 0
    async with async_session() as session:
        for skill in SKILLS:
            existing = (
                await session.execute(
                    select(SkillORM).where(SkillORM.slug == skill.slug)
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    SkillORM(
                        slug=skill.slug,
                        name=skill.name,
                        description=skill.description,
                        parent_id=skill.parent_id,
                        prerequisite_ids=skill.prerequisite_ids,
                    )
                )
                total += 1
            else:
                existing.name = skill.name
                existing.description = skill.description
                existing.parent_id = skill.parent_id
                existing.prerequisite_ids = skill.prerequisite_ids

        for question_id, mappings in QUESTION_SKILLS.items():
            question_exists = (
                await session.execute(
                    select(QuestionORM.id).where(QuestionORM.id == question_id)
                )
            ).scalar_one_or_none()
            if question_exists is None:
                # Test-only question IDs are part of the taxonomy so the
                # simulation and unit tests share one source of truth; they are
                # skipped in a real database that lacks those questions.
                continue
            for mapping in mappings:
                existing = (
                    await session.execute(
                        select(QuestionSkillORM).where(
                            QuestionSkillORM.question_id == question_id,
                            QuestionSkillORM.skill_slug == mapping.skill_slug,
                        )
                    )
                ).scalar_one_or_none()
                row_id = f"{question_id}:{mapping.skill_slug}"
                if existing is None:
                    session.add(
                        QuestionSkillORM(
                            id=row_id,
                            question_id=question_id,
                            skill_slug=mapping.skill_slug,
                            weight=mapping.weight,
                        )
                    )
                    total += 1
                else:
                    existing.weight = mapping.weight

        pruned = await _prune_stale_rows(session)

        await session.commit()
    await engine.dispose()
    print(f"Skill graph seed pruned {pruned} stale taxonomy rows.")
    return total


if __name__ == "__main__":
    created = asyncio.run(seed())
    print(f"Skill graph seed complete ({created} new rows written).")
