#!/usr/bin/env python3
"""Sync application data from a local SQL source into a Supabase/PostgreSQL
target (flush all + update).

Usage:
    python scripts/sync_database.py \
        --source-url "mysql+aiomysql://..." \
        --target-url "postgresql://...pooler.supabase.com:5432/postgres" \
        --flush --confirm

Defaults:
    --source-url  env MYSQL_DATABASE_URL (local MySQL)
    --target-url  env DIRECT_URL (Supabase session pooler; schema ops)

Safety:
    * Without --flush, rows are only appended (upsert-style copy).
    * --flush requires --confirm; it deletes all target rows first.
    * Row counts are validated after the copy and mismatches raise.
    * --dry-run reports source counts and validates target access only.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.database_sync import run_sync
from app.services.database_sync_adapters import (
    MySQLSyncSource,
    PrismaSyncTarget,
    build_prisma,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync local SQL -> Supabase")
    parser.add_argument(
        "--source-url",
        default=os.getenv("MYSQL_DATABASE_URL"),
        help="Source DB URL (default: MYSQL_DATABASE_URL env)",
    )
    parser.add_argument(
        "--target-url",
        default=os.getenv("DIRECT_URL"),
        help="Target DB URL (default: DIRECT_URL env)",
    )
    parser.add_argument(
        "--flush", action="store_true", help="Empty target tables before copying"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Confirm destructive operations"
    )
    parser.add_argument("--dry-run", action="store_true", help="Report only")
    return parser.parse_args()


async def _main(args: argparse.Namespace) -> int:
    if not args.source_url:
        print("ERROR: --source-url not provided and MYSQL_DATABASE_URL unset")
        return 1
    if not args.target_url:
        print("ERROR: --target-url not provided and DIRECT_URL unset")
        return 1

    source = MySQLSyncSource(args.source_url)
    await source.connect()
    prisma = build_prisma(args.target_url)
    await prisma.connect()
    try:
        target = PrismaSyncTarget(prisma)
        report = await run_sync(
            source,
            target,
            flush=args.flush,
            confirm=args.confirm,
            dry_run=args.dry_run,
        )
        print("Source counts:", report.source_counts)
        if not args.dry_run:
            print("Target counts:", report.target_counts)
            print("Flushed tables:", report.flushed)
        return 0
    finally:
        await source.close()
        await prisma.disconnect()


def main() -> int:
    args = _parse_args()
    try:
        return asyncio.run(_main(args))
    except Exception as exc:  # noqa: BLE001 - CLI surface
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
