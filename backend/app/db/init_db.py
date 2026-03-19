import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, Base


async def init_db() -> None:
    """Initialize the database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())