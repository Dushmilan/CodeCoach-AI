#!/usr/bin/env python3
"""Seed a minimal E2E environment: admin users + sample questions.

Runs the admin seed, then upserts a small curated question set used by the
Playwright specs (problems table, code-execution flow). Idempotent and
non-destructive: existing rows are left alone.

Usage:
    DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_test \
    DATABASE_SEARCH_PATH=public \
    python scripts/seed_e2e.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.models.orm import QuestionORM
from scripts.seed_admin import seed as seed_admins

E2E_QUESTIONS = [
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "category": "arrays",
        "company_tags": ["Google"],
        "description": (
            "Given an array of integers nums and an integer target, return "
            "indices of the two numbers such that they add up to target."
        ),
        "starter_code": {
            "python": "def two_sum(nums, target):\n    pass",
            "javascript": "function twoSum(nums, target) {}",
            "java": "class Solution { public int[] twoSum(int[] nums, int target) { return null; } }",
        },
        "examples": [{"input": "[2,7,11,15], 9", "output": "[0,1]"}],
        "test_cases": [
            {
                "input": "[2,7,11,15], 9",
                "expected_output": "[0,1]",
                "hidden": False,
            }
        ],
        "hints": ["Try a hash map to remember complements."],
        "solution": "Use a hash map from value to index for an O(n) pass.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "constraints": ["2 <= nums.length <= 10^4"],
        "is_interactive": 0,
    },
    {
        "id": "contains-duplicate",
        "title": "Contains Duplicate",
        "difficulty": "easy",
        "category": "arrays",
        "company_tags": ["Amazon"],
        "description": (
            "Given an integer array nums, return true if any value appears "
            "at least twice in the array."
        ),
        "starter_code": {
            "python": "def contains_duplicate(nums):\n    pass",
            "javascript": "function containsDuplicate(nums) {}",
            "java": "class Solution { public boolean containsDuplicate(int[] nums) { return false; } }",
        },
        "examples": [{"input": "[1,2,3,1]", "output": "true"}],
        "test_cases": [
            {
                "input": "[1,2,3,1]",
                "expected_output": "true",
                "hidden": False,
            }
        ],
        "hints": ["Compare the set size to the array length."],
        "solution": "def contains_duplicate(nums):\n    return len(set(nums)) != len(nums)",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "constraints": ["1 <= nums.length <= 10^5"],
        "is_interactive": 0,
    },
]


def _connect_args() -> dict:
    search_path = os.getenv("DATABASE_SEARCH_PATH")
    if not search_path:
        return {"statement_cache_size": 0}
    return {
        "server_settings": {"search_path": search_path},
        "statement_cache_size": 0,
    }


async def seed_questions(session: AsyncSession) -> None:
    for q in E2E_QUESTIONS:
        existing = await session.execute(
            select(QuestionORM).where(QuestionORM.id == q["id"])
        )
        if existing.scalar_one_or_none() is not None:
            print(f"  Question '{q['id']}' already present — skipped")
            continue
        session.add(QuestionORM(**q))
        print(f"  Inserted question '{q['id']}'")
    await session.commit()


async def _main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("ERROR: DATABASE_URL is required.")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(url, poolclass=NullPool, connect_args=_connect_args())
    try:
        async with async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )() as session:
            await seed_admins(session)
            await seed_questions(session)
    finally:
        await engine.dispose()
    print("\nDone. E2E seed complete.")


if __name__ == "__main__":
    asyncio.run(_main())
