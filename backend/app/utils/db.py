"""Database helpers shared across repositories."""

from typing import Any

from sqlalchemy import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession


async def execute_write(session: AsyncSession, stmt: Any) -> CursorResult:
    """Execute an UPDATE/DELETE statement and return its CursorResult.

    ``AsyncSession.execute`` is statically typed to return ``Result``, which
    has no ``rowcount`` attribute; write statements return a ``CursorResult``
    at runtime. This helper narrows the type so callers can use ``rowcount``.
    """
    result = await session.execute(stmt)
    return result  # type: ignore[return-value]
