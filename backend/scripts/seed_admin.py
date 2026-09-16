#!/usr/bin/env python3
"""Seed admin and super_admin users into the database.

The app is fully DB-backed (local PostgreSQL branch database or hosted live);
this script writes
directly to the ``users`` table instead of the legacy ``data/users.json`` file.

Seed passwords resolve from the environment (``backend/.env.seed``, gitignored;
see ``backend/.env.seed.example``) with the dev defaults below as fallback:

Usage:
    DATABASE_URL=postgresql://... python scripts/seed_admin.py
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from app.models.orm import UserORM  # noqa: E402


def _load_env_seed() -> None:
    """Load gitignored ``backend/.env.seed`` (if present) without overriding
    real environment variables."""
    load_dotenv(Path(__file__).resolve().parent.parent / ".env.seed", override=False)


_load_env_seed()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_password(env_var: str, default: str) -> str:
    """Seed password for one account class: env override, else dev default."""
    return os.getenv(env_var, default)


ADMIN_USERS = [
    {
        "username": "admin",
        "email": "admin@codecoach.ai",
        "password": "admin123",
        "password_env": "SEED_ADMIN_PASSWORD",
        "role": "admin",
    },
    {
        "username": "superadmin",
        "email": "superadmin@codecoach.ai",
        "password": "superadmin123",
        "password_env": "SEED_SUPERADMIN_PASSWORD",
        "role": "super_admin",
    },
]

# Issue #159 (phase 2) — instructor logins for the professor + demonstrator
# dashboards. Usernames match frontend/src/data/instructor-demo.json so the
# demo dataset and real logins refer to the same identities. Dev-only
# passwords, same convention as ADMIN_USERS above.
# Issue #166 — second TA (demonstrator.curie) for the full demo school.
INSTRUCTOR_SEED_USERS = [
    {
        "username": "professor.ada",
        "email": "ada@university.edu",
        "password": "professor123",
        "password_env": "SEED_PROFESSOR_PASSWORD",
        "role": "professor",
    },
    {
        "username": "professor.grace",
        "email": "grace@university.edu",
        "password": "professor123",
        "password_env": "SEED_PROFESSOR_PASSWORD",
        "role": "professor",
    },
    {
        "username": "demonstrator.turing",
        "email": "alex@university.edu",
        "password": "demonstrator123",
        "password_env": "SEED_TA_PASSWORD",
        "role": "ta",
    },
    {
        "username": "demonstrator.curie",
        "email": "curie@university.edu",
        "password": "demonstrator123",
        "password_env": "SEED_TA_PASSWORD",
        "role": "ta",
    },
]


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit(
            "ERROR: DATABASE_URL is required (PostgreSQL connection "
            "string); no remote fallback without confirmation."
        )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def seed(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    for au in ADMIN_USERS + INSTRUCTOR_SEED_USERS:
        result = await session.execute(
            select(UserORM).where(UserORM.username == au["username"])
        )
        user = result.scalar_one_or_none()
        if user is not None:
            user.role = au["role"]
            print(f"  Updated role for '{au['username']}' to '{au['role']}'")
        else:
            session.add(
                UserORM(
                    id=str(uuid.uuid4()),
                    username=au["username"],
                    email=au["email"],
                    hashed_password=hash_password(
                        seed_password(au["password_env"], au["password"])
                    ),
                    created_at=now,
                    is_active=1,
                    role=au["role"],
                )
            )
            print(f"  Created user '{au['username']}' with role '{au['role']}'")

    await session.commit()


_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _seed_allowed() -> bool:
    """Admin seeds carry login-capable accounts: allow local branch databases
    by host; remote targets need the explicit live-confirm secret."""
    url = os.getenv("DATABASE_URL", "")
    if (urlparse(url).hostname or "").lower() in _LOCAL_HOSTS:
        return True
    return os.getenv("SEED_LIVE_CONFIRM") == "YES-I-AM-SURE"


async def _main() -> None:
    if not _seed_allowed():
        raise SystemExit(
            "ERROR: refusing to seed admin users into a remote database "
            "without SEED_LIVE_CONFIRM=YES-I-AM-SURE."
        )
    engine = create_async_engine(_get_database_url(), poolclass=NullPool)
    try:
        async with async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )() as session:
            await seed(session)
    finally:
        await engine.dispose()
    print("\nDone. Admin users seeded into the database.")


if __name__ == "__main__":
    asyncio.run(_main())
