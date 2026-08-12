#!/usr/bin/env python3
"""Seed admin and super_admin users into the database.

The app is fully DB-backed (PostgreSQL/Supabase primary); this script writes
directly to the ``users`` table instead of the legacy ``data/users.json`` file.

Usage:
    DATABASE_URL=postgresql://... python scripts/seed_admin.py
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.models.orm import UserORM


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


ADMIN_USERS = [
    {
        "username": "admin",
        "email": "admin@codecoach.ai",
        "password": "admin123",
        "role": "admin",
    },
    {
        "username": "superadmin",
        "email": "superadmin@codecoach.ai",
        "password": "superadmin123",
        "role": "super_admin",
    },
]


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        url = "postgresql+asyncpg://codecoach:codecoach@host.docker.internal:5432/codecoach"
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def seed(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    for au in ADMIN_USERS:
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
                    hashed_password=hash_password(au["password"]),
                    created_at=now,
                    is_active=1,
                    role=au["role"],
                )
            )
            print(f"  Created user '{au['username']}' with role '{au['role']}'")

    await session.commit()


async def _main() -> None:
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
