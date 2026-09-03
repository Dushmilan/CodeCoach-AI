"""Seed prune: stale taxonomy rows are removed on reseed (Issue #138).

The seed owns the ``skills`` table and the taxonomy-covered
``question_skills`` pairs, so rows the taxonomy no longer defines
(e.g. post-#135 ``dynamic-programming``) must be pruned, not left to
attribute events to unknown slugs. Reseed must be a no-op afterwards.
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models.orm import QuestionSkillORM, SkillORM
from tests.conftest import _test_db_url, _test_engine_kwargs


def _run(coro):
    return asyncio.run(coro)


async def _counts() -> tuple[int, int, int]:
    engine = create_async_engine(
        _test_db_url(), poolclass=NullPool, **_test_engine_kwargs()
    )
    try:
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as session:
            stale_skills = (
                await session.execute(
                    select(func.count())
                    .select_from(SkillORM)
                    .where(SkillORM.slug == "dynamic-programming")
                )
            ).scalar_one()
            stale_pairs = (
                await session.execute(
                    select(func.count())
                    .select_from(QuestionSkillORM)
                    .where(QuestionSkillORM.skill_slug == "dynamic-programming")
                )
            ).scalar_one()
            total_pairs = (
                await session.execute(
                    select(func.count()).select_from(QuestionSkillORM)
                )
            ).scalar_one()
            return stale_skills, stale_pairs, total_pairs
    finally:
        await engine.dispose()


async def _plant_stale_rows() -> None:
    engine = create_async_engine(
        _test_db_url(), poolclass=NullPool, **_test_engine_kwargs()
    )
    try:
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as session:
            # Ordered commits: the pair's FK requires the skill row first.
            session.add(
                SkillORM(
                    slug="dynamic-programming",
                    name="Dynamic Programming",
                    description="",
                    prerequisite_ids=[],
                )
            )
            await session.commit()
            session.add(
                QuestionSkillORM(
                    id="two-sum:dynamic-programming",
                    question_id="two-sum",
                    skill_slug="dynamic-programming",
                    weight=1.0,
                )
            )
            await session.commit()
    finally:
        await engine.dispose()


class TestSeedSkillPrune:
    def test_reseed_prunes_stale_rows_and_is_idempotent(self, test_client):
        _run(_plant_stale_rows())

        from scripts.seed_skill_graph import seed

        _run(seed())

        stale_skills, stale_pairs, total_pairs = _run(_counts())
        assert stale_skills == 0
        assert stale_pairs == 0
        assert total_pairs > 0, "seed must not wipe valid mappings"

        _run(seed())
        assert _run(_counts()) == (0, 0, total_pairs)
