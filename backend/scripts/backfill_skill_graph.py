#!/usr/bin/env python3
"""Backfill skill graphs for all existing users from submission history.

For every user who has submissions but no learning_events-derived skill state,
synthesize idempotent LearningEvents (one per submission) and feed them
through SkillGraphService. Existing learning_events are never duplicated —
event id ``backfill:{submission.id}`` is deterministic.

Idempotent, re-runnable, non-destructive. Supabase-only.

Usage:
    DATABASE_URL=postgresql://... python scripts/backfill_skill_graph.py [--dry-run] [--user USER_ID]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.orm import SubmissionORM, UserORM
from app.models.skill_graph_schemas import LearningEvent, LearningEventType
from app.repositories.sql_skill_graph_repository import SqlSkillGraphRepository
from app.services.skill_graph_service import SkillGraphService


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit(
            "ERROR: DATABASE_URL is required (Supabase/PostgreSQL connection string)"
        )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _create_engine():
    search_path = os.getenv("DATABASE_SEARCH_PATH")
    kwargs: dict = {}
    if search_path:
        kwargs["connect_args"] = {"server_settings": {"search_path": search_path}}
    return create_async_engine(_get_database_url(), poolclass=NullPool, **kwargs)


async def backfill(*, dry_run: bool = False, user_id_filter: str | None = None) -> dict:
    engine = _create_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    stats = {
        "users_scanned": 0,
        "users_backfilled": 0,
        "events_created": 0,
        "duplicates": 0,
        "skipped_no_submissions": 0,
    }

    async with async_session() as session:
        user_q = select(UserORM.id)
        if user_id_filter:
            user_q = user_q.where(UserORM.id == user_id_filter)
        user_ids = (await session.execute(user_q)).scalars().all()

        for uid in user_ids:
            stats["users_scanned"] += 1
            # Skip users who already have skill states — they already have a graph.
            repo = SqlSkillGraphRepository(session)
            existing_states = await repo.get_states(uid)
            if existing_states:
                continue

            subs = (
                (
                    await session.execute(
                        select(SubmissionORM)
                        .where(SubmissionORM.user_id == uid)
                        .order_by(SubmissionORM.created_at.asc())
                    )
                )
                .scalars()
                .all()
            )

            if not subs:
                stats["skipped_no_submissions"] += 1
                continue

            events: list[LearningEvent] = []
            for sub in subs:
                events.append(
                    LearningEvent(
                        id=f"backfill:{sub.id}",
                        user_id=uid,
                        event_type=LearningEventType.SUBMISSION_PASSED
                        if sub.passed
                        else LearningEventType.SUBMISSION_FAILED,
                        question_id=sub.question_id,
                        metadata={},
                        occurred_at=sub.created_at,
                    )
                )

            if dry_run:
                stats["users_backfilled"] += 1
                stats["events_created"] += len(events)
                continue

            svc = SkillGraphService(repository=repo)
            result = await svc.ingest_events(events, user_id=uid)
            stats["users_backfilled"] += 1
            stats["events_created"] += result.accepted
            stats["duplicates"] += result.duplicate

        if not dry_run:
            await session.commit()

    await engine.dispose()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill skill graphs from submissions"
    )
    parser.add_argument("--dry-run", action="store_true", help="Count without writing")
    parser.add_argument(
        "--user", dest="user_id", default=None, help="Limit to one user id"
    )
    args = parser.parse_args()

    stats = asyncio.run(backfill(dry_run=args.dry_run, user_id_filter=args.user_id))
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(
        f"[{mode}] users_scanned={stats['users_scanned']} users_backfilled={stats['users_backfilled']} events_created={stats['events_created']} duplicates={stats['duplicates']} skipped_no_submissions={stats['skipped_no_submissions']}"
    )


if __name__ == "__main__":
    main()
