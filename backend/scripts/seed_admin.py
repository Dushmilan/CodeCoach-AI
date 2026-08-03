"""Seed admin and super_admin users into MySQL.

The application is MySQL-only (since commit 956f5d0); the previous file-based
seed wrote to data/users.json which the app no longer reads. Credentials are
taken from environment variables and only default usernames are fixed — no
passwords are hardcoded in the repository.

Usage:
    python scripts/seed_admin.py [--url DATABASE_URL]

Environment:
    ADMIN_USERNAME  (default: admin)
    ADMIN_PASSWORD  (required unless ADMIN_PASSWORD_FILE is set)
    ADMIN_EMAIL     (default: admin@codecoach.ai)
    SUPERADMIN_USERNAME (default: superadmin)
    SUPERADMIN_PASSWORD (required unless SUPERADMIN_PASSWORD_FILE is set)
    SUPERADMIN_EMAIL    (default: superadmin@codecoach.ai)

Passwords can also be supplied via files (ADMIN_PASSWORD_FILE /
SUPERADMIN_PASSWORD_FILE) so they never appear on a command line.
"""

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt

from app.models.orm import UserORM


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        url = "mysql+aiomysql://codecoach:codecoach@host.docker.internal:3306/codecoach"
    return url


def _load_secret(env_password: str, env_file: str) -> Optional[str]:
    """Read a secret from an env var, falling back to a file path env var."""
    if env_password:
        return env_password
    file_env = os.getenv(env_file)
    if file_env and os.path.isfile(file_env):
        with open(file_env, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def _require_password(username: str, value: Optional[str]) -> str:
    if not value:
        sys.exit(
            f"ERROR: No password provided for '{username}'. Set the "
            "corresponding *_PASSWORD or *_PASSWORD_FILE environment variable."
        )
    return value


def _hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def _seed() -> None:
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        create_async_engine,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from sqlalchemy import select

    admin_password = _require_password(
        os.getenv("ADMIN_USERNAME", "admin"),
        _load_secret(os.getenv("ADMIN_PASSWORD", ""), "ADMIN_PASSWORD_FILE"),
    )
    superadmin_password = _require_password(
        os.getenv("SUPERADMIN_USERNAME", "superadmin"),
        _load_secret(os.getenv("SUPERADMIN_PASSWORD", ""), "SUPERADMIN_PASSWORD_FILE"),
    )

    users_to_seed = [
        {
            "username": os.getenv("ADMIN_USERNAME", "admin"),
            "email": os.getenv("ADMIN_EMAIL", "admin@codecoach.ai"),
            "password": admin_password,
            "role": "admin",
        },
        {
            "username": os.getenv("SUPERADMIN_USERNAME", "superadmin"),
            "email": os.getenv("SUPERADMIN_EMAIL", "superadmin@codecoach.ai"),
            "password": superadmin_password,
            "role": "super_admin",
        },
    ]

    engine = create_async_engine(_get_database_url(), poolclass=NullPool)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        for u in users_to_seed:
            existing = (
                await session.execute(
                    select(UserORM).where(UserORM.username == u["username"])
                )
            ).scalar_one_or_none()

            now = datetime.now(timezone.utc)
            if existing:
                existing.role = u["role"]
                if not existing.email:
                    existing.email = u["email"]
                print(f"  Updated role for '{u['username']}' to '{u['role']}'")
            else:
                session.add(
                    UserORM(
                        id=str(uuid.uuid4()),
                        username=u["username"],
                        email=u["email"],
                        hashed_password=_hash_password(u["password"]),
                        created_at=now,
                        is_active=1,
                        oauth_provider=None,
                        oauth_id=None,
                        role=u["role"],
                    )
                )
                print(f"  Created user '{u['username']}' with role '{u['role']}'")
        await session.commit()

    await engine.dispose()
    print("\nDone. Admin users seeded into the database.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed admin users into MySQL")
    parser.add_argument(
        "--url",
        default=None,
        help="Database URL (overrides DATABASE_URL env var)",
    )
    args = parser.parse_args()
    if args.url:
        os.environ["DATABASE_URL"] = args.url
    asyncio.run(_seed())


if __name__ == "__main__":
    main()
