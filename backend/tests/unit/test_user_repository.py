import pytest
import json
import tempfile
import os
from datetime import datetime, timezone

from app.models.auth_schemas import UserInDB


@pytest.fixture
def temp_user_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def sample_user():
    return UserInDB(
        id="user-1",
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$abc123hash",
        created_at=datetime.now(timezone.utc),
        is_active=True,
    )


class TestFileUserRepository:
    def test_add_and_get_by_id(self, temp_user_file, sample_user):
        from app.repositories.file_user_repository import FileUserRepository

        repo = FileUserRepository(temp_user_file)
        import asyncio

        asyncio.run(repo.add(sample_user))

        repo2 = FileUserRepository(temp_user_file)
        result = asyncio.run(repo2.get_by_id("user-1"))
        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    def test_get_by_username(self, temp_user_file, sample_user):
        from app.repositories.file_user_repository import FileUserRepository

        repo = FileUserRepository(temp_user_file)
        import asyncio

        asyncio.run(repo.add(sample_user))

        result = asyncio.run(repo.get_by_username("testuser"))
        assert result is not None
        assert result.id == "user-1"

    def test_get_by_username_not_found(self, temp_user_file):
        from app.repositories.file_user_repository import FileUserRepository
        import asyncio

        repo = FileUserRepository(temp_user_file)
        result = asyncio.run(repo.get_by_username("nonexistent"))
        assert result is None

    def test_get_by_email(self, temp_user_file, sample_user):
        from app.repositories.file_user_repository import FileUserRepository

        repo = FileUserRepository(temp_user_file)
        import asyncio

        asyncio.run(repo.add(sample_user))

        result = asyncio.run(repo.get_by_email("test@example.com"))
        assert result is not None
        assert result.id == "user-1"

    def test_get_by_email_not_found(self, temp_user_file):
        from app.repositories.file_user_repository import FileUserRepository
        import asyncio

        repo = FileUserRepository(temp_user_file)
        result = asyncio.run(repo.get_by_email("unknown@test.com"))
        assert result is None

    def test_get_by_id_not_found(self, temp_user_file):
        from app.repositories.file_user_repository import FileUserRepository
        import asyncio

        repo = FileUserRepository(temp_user_file)
        result = asyncio.run(repo.get_by_id("nonexistent"))
        assert result is None

    def test_add_duplicate_id_overwrites(self, temp_user_file, sample_user):
        from app.repositories.file_user_repository import FileUserRepository

        repo = FileUserRepository(temp_user_file)
        import asyncio

        asyncio.run(repo.add(sample_user))
        modified = UserInDB(
            id="user-1",
            username="updated",
            email="updated@test.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
        )
        asyncio.run(repo.add(modified))

        result = asyncio.run(repo.get_by_id("user-1"))
        assert result.username == "updated"

    def test_load_existing_file(self, temp_user_file, sample_user):
        from app.repositories.file_user_repository import FileUserRepository

        repo1 = FileUserRepository(temp_user_file)
        import asyncio

        asyncio.run(repo1.add(sample_user))

        repo2 = FileUserRepository(temp_user_file)
        result = asyncio.run(repo2.get_by_id("user-1"))
        assert result is not None
        assert result.email == "test@example.com"

    def test_empty_file_on_init(self, temp_user_file):
        from app.repositories.file_user_repository import FileUserRepository

        repo = FileUserRepository(temp_user_file)
        import asyncio

        result = asyncio.run(repo.get_by_id("any"))
        assert result is None

    def test_nonexistent_file(self):
        from app.repositories.file_user_repository import FileUserRepository

        repo = FileUserRepository("nonexistent_file_12345.json")
        import asyncio

        result = asyncio.run(repo.get_by_id("x"))
        assert result is None
        assert os.path.exists("nonexistent_file_12345.json") is False
