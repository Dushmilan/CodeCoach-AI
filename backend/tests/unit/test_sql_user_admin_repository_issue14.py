"""Issue #14: SqlUserAdminRepository must include hashed_password when
constructing UserInDB (it is a required field). Without it, the call 500s.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.orm import UserORM
from app.repositories.sql_user_admin_repository import SqlUserAdminRepository


def _fake_orm_user(hashed_password="stored-hash"):
    u = MagicMock(spec=UserORM)
    u.id = "u1"
    u.username = "alice"
    u.email = "alice@example.com"
    u.is_active = True
    u.role = "admin"
    u.oauth_provider = None
    u.oauth_id = None
    u.created_at = "2024-01-01T00:00:00Z"
    u.hashed_password = hashed_password
    u.plan = "free"
    return u


def _make_repo(orm_user):
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = orm_user
    result.scalars.return_value.all.return_value = [orm_user]
    session.execute.return_value = result
    return SqlUserAdminRepository(session)


@pytest.mark.asyncio
async def test_get_user_by_id_includes_hashed_password():
    repo = _make_repo(_fake_orm_user())
    user = await repo.get_user_by_id("u1")
    assert user is not None
    assert user.hashed_password == "stored-hash"


@pytest.mark.asyncio
async def test_get_user_by_username_includes_hashed_password():
    repo = _make_repo(_fake_orm_user())
    user = await repo.get_user_by_username("alice")
    assert user is not None
    assert user.hashed_password == "stored-hash"


@pytest.mark.asyncio
async def test_list_users_includes_hashed_password():
    repo = _make_repo(_fake_orm_user())
    users, _ = await repo.list_users()
    assert users
    assert users[0].hashed_password == "stored-hash"
