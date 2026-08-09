"""Integration tests for the database sync tool against live Supabase.

These tests require working credentials in the environment:
- MYSQL_DATABASE_URL  (source, local MySQL)
- DIRECT_URL          (target, Supabase session pooler)

The tests are skipped automatically when either is not configured.
"""

import os
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (os.getenv("MYSQL_DATABASE_URL") and os.getenv("DIRECT_URL")),
        reason="MYSQL_DATABASE_URL / DIRECT_URL not configured",
    ),
]


def _target():
    from app.services.database_sync_adapters import build_prisma

    return build_prisma(os.environ["DIRECT_URL"])


@pytest.mark.asyncio
async def test_sync_from_mysql_to_supabase_matches_counts():
    from prisma import Prisma

    from app.services.database_sync import TABLE_ORDER, run_sync
    from app.services.database_sync_adapters import MySQLSyncSource, PrismaSyncTarget

    source = MySQLSyncSource(os.environ["MYSQL_DATABASE_URL"])
    await source.connect()
    prisma = _target()
    await prisma.connect()
    try:
        # Dry-run first: report source counts without touching the target.
        report = await run_sync(
            source,
            PrismaSyncTarget(prisma),
            flush=False,
            confirm=False,
            dry_run=True,
        )
        assert report.source_counts, "source should contain rows"

        # Live sync: flush target and repopulate from source.
        report = await run_sync(
            source,
            PrismaSyncTarget(prisma),
            flush=True,
            confirm=True,
        )
        for table in TABLE_ORDER:
            assert report.target_counts[table] == report.source_counts[table]
    finally:
        await source.close()
        await prisma.disconnect()


@pytest.mark.asyncio
async def test_sync_requires_confirm_before_flush():
    from app.services.database_sync import run_sync
    from app.services.database_sync_adapters import MySQLSyncSource, PrismaSyncTarget

    source = MySQLSyncSource(os.environ["MYSQL_DATABASE_URL"])
    await source.connect()
    prisma = _target()
    await prisma.connect()
    try:
        with pytest.raises(RuntimeError, match="confirm"):
            await run_sync(
                source,
                PrismaSyncTarget(prisma),
                flush=True,
                confirm=False,
            )
    finally:
        await source.close()
        await prisma.disconnect()


@pytest.mark.asyncio
async def test_sync_roundtrip_preserves_sample_rows():
    from app.services.database_sync_adapters import MySQLSyncSource

    source = MySQLSyncSource(os.environ["MYSQL_DATABASE_URL"])
    await source.connect()
    prisma = _target()
    await prisma.connect()
    try:
        first_user = (await source.read_all("users"))[0]
        first_question = (await source.read_all("questions"))[0]

        target_user = await prisma.user.find_unique(
            where={"id": first_user["id"]}
        )
        assert target_user is not None
        assert target_user.username == first_user["username"]
        assert target_user.email == first_user["email"]

        target_question = await prisma.question.find_unique(
            where={"id": first_question["id"]}
        )
        assert target_question is not None
        assert target_question.title == first_question["title"]
    finally:
        await source.close()
        await prisma.disconnect()
