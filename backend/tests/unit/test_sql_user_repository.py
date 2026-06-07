import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.orm import Base
from app.models.auth_schemas import UserInDB
from datetime import datetime, timezone
import uuid


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_user_repository import SqlUserRepository
    return SqlUserRepository(test_db)


@pytest_asyncio.fixture
def sample_user():
    return UserInDB(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$hashhashhashhashhashhash",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        oauth_provider=None,
        oauth_id=None,
    )


class TestSqlUserRepository:
    @pytest.mark.asyncio
    async def test_add_and_get_by_id(self, repo, sample_user):
        await repo.add(sample_user)
        await repo.session.commit()

        fetched = await repo.get_by_id(sample_user.id)
        assert fetched is not None
        assert fetched.username == "testuser"
        assert fetched.email == "test@example.com"
        assert fetched.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        fetched = await repo.get_by_id("nonexistent")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_by_username(self, repo, sample_user):
        await repo.add(sample_user)
        await repo.session.commit()

        fetched = await repo.get_by_username("testuser")
        assert fetched is not None
        assert fetched.id == sample_user.id

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, repo):
        fetched = await repo.get_by_username("nonexistent")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, repo, sample_user):
        await repo.add(sample_user)
        await repo.session.commit()

        fetched = await repo.get_by_email("test@example.com")
        assert fetched is not None
        assert fetched.id == sample_user.id

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, repo):
        fetched = await repo.get_by_email("nonexistent@test.com")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_by_oauth(self, repo):
        user = UserInDB(
            id=str(uuid.uuid4()),
            username="oauthuser",
            email="oauth@example.com",
            hashed_password="",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            oauth_provider="google",
            oauth_id="google-id-123",
        )
        await repo.add(user)
        await repo.session.commit()

        fetched = await repo.get_by_oauth("google", "google-id-123")
        assert fetched is not None
        assert fetched.username == "oauthuser"

        not_found = await repo.get_by_oauth("google", "nonexistent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_username_unique(self, repo, sample_user):
        await repo.add(sample_user)
        await repo.session.commit()

        duplicate = UserInDB(
            id=str(uuid.uuid4()),
            username="testuser",
            email="other@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
        with pytest.raises(Exception):
            await repo.add(duplicate)
            await repo.session.flush()
        await repo.session.rollback()

    @pytest.mark.asyncio
    async def test_email_unique(self, repo, sample_user):
        await repo.add(sample_user)
        await repo.session.commit()

        duplicate = UserInDB(
            id=str(uuid.uuid4()),
            username="otheruser",
            email="test@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
        with pytest.raises(Exception):
            await repo.add(duplicate)
            await repo.session.flush()
        await repo.session.rollback()

    @pytest.mark.asyncio
    async def test_inactive_user(self, repo):
        user = UserInDB(
            id=str(uuid.uuid4()),
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=False,
        )
        await repo.add(user)
        await repo.session.commit()

        fetched = await repo.get_by_id(user.id)
        assert fetched is not None
        assert fetched.is_active is False
