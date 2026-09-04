from logging.config import fileConfig
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.orm import Base
from app.core.config import get_settings
from app.core.db_url import (
    escape_configparser,
    migration_connect_args,
    normalize_db_url,
    strip_pgbouncer,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from environment if DATABASE_URL is set
settings = get_settings()
db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
if db_url:
    # Force the asyncpg driver, strip Supabase's `?pgbouncer=true` param (not a
    # real connection option), and escape `%` characters so the ConfigParser
    # (interpolation) accepts percent-encoded passwords.
    config.set_main_option(
        "sqlalchemy.url",
        escape_configparser(strip_pgbouncer(normalize_db_url(db_url))),
    )

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=migration_connect_args(os.getenv("DATABASE_SEARCH_PATH")),
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
