import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sql_user_admin_repository import SqlUserAdminRepository


def _make_user_orm(**overrides):
    user = MagicMock()
    user.id = overrides.get("id", "user-1")
    user.username = overrides.get("username", "testuser")
    user.email = overrides.get("email", "test@example.com")
    user.hashed_password = overrides.get("hashed_password", "hashed_secret")
    user.is_active = overrides.get("is_active", 1)
    user.role = overrides.get("role", "user")
    user.oauth_provider = overrides.get("oauth_provider", None)
    user.oauth_id = overrides.get("oauth_id", None)
    user.created_at = overrides.get("created_at", "2025-01-01T00:00:00Z")
    return user


@pytest.fixture
def session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session):
    return SqlUserAdminRepository(session)


@pytest.mark.asyncio
async def test_get_user_by_id_includes_hashed_password(repo, session):
    user = _make_user_orm()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute = AsyncMock(return_value=result)

    result_user = await repo.get_user_by_id("user-1")

    assert result_user is not None
    assert result_user.hashed_password == "hashed_secret"
    assert result_user.id == "user-1"
    assert result_user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_id_returns_none_for_missing(repo, session):
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    result_user = await repo.get_user_by_id("nonexistent")

    assert result_user is None


@pytest.mark.asyncio
async def test_get_user_by_username_includes_hashed_password(repo, session):
    user = _make_user_orm()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute = AsyncMock(return_value=result)

    result_user = await repo.get_user_by_username("testuser")

    assert result_user is not None
    assert result_user.hashed_password == "hashed_secret"
    assert result_user.username == "testuser"


@pytest.mark.asyncio
async def test_list_users_includes_hashed_password(repo, session):
    users = [_make_user_orm(id=f"user-{i}") for i in range(3)]

    query_result = MagicMock()
    query_result.scalars.return_value.all.return_value = users

    count_result = MagicMock()
    count_result.scalar_one.return_value = 3

    session.execute = AsyncMock(side_effect=[query_result, count_result])

    parsed, total = await repo.list_users(skip=0, limit=20)

    assert total == 3
    assert len(parsed) == 3
    for u in parsed:
        assert u.hashed_password == "hashed_secret"


@pytest.mark.asyncio
async def test_list_users_empty(repo, session):
    query_result = MagicMock()
    query_result.scalars.return_value.all.return_value = []

    count_result = MagicMock()
    count_result.scalar_one.return_value = 0

    session.execute = AsyncMock(side_effect=[query_result, count_result])

    parsed, total = await repo.list_users(skip=0, limit=20)

    assert total == 0
    assert len(parsed) == 0


@pytest.mark.asyncio
async def test_user_in_db_has_all_required_fields(repo, session):
    user = _make_user_orm()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute = AsyncMock(return_value=result)

    result_user = await repo.get_user_by_id("user-1")

    assert result_user.id == "user-1"
    assert result_user.username == "testuser"
    assert result_user.email == "test@example.com"
    assert result_user.hashed_password == "hashed_secret"
    assert result_user.is_active is True
    assert result_user.role == "user"
