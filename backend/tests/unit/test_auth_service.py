import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.models.auth_schemas import (
    UserRegisterRequest, UserLoginRequest, TokenData,
    UserInDB, UserResponse,
)
from app.services.auth_service import (
    AuthService, hash_password, verify_password,
    create_access_token, decode_access_token,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("my_password")
        assert hashed != "my_password"
        assert verify_password("my_password", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_hash_is_different_each_time(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        assert verify_password("same", h1) is True
        assert verify_password("same", h2) is True


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_by_username = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.add = AsyncMock()
    return repo


class TestTokenCreation:
    def test_create_and_decode_token(self):
        token, expires_in = create_access_token(
            TokenData(user_id="user-1", username="testuser")
        )
        assert isinstance(token, str)
        assert expires_in > 0

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded.user_id == "user-1"
        assert decoded.username == "testuser"

    def test_decode_invalid_token(self):
        decoded = decode_access_token("invalid.token.here")
        assert decoded is None

    def test_decode_expired_token(self):
        with patch("app.services.auth_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime.now(timezone.utc) - timedelta(hours=48)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else datetime.now(timezone.utc) - timedelta(hours=48)
            token, _ = create_access_token(
                TokenData(user_id="user-1", username="testuser"),
                expires_delta=timedelta(hours=1),
            )

        decoded = decode_access_token(token)
        assert decoded is None


class TestAuthServiceRegister:
    @pytest.mark.asyncio
    async def test_register_new_user(self, mock_repo):
        service = AuthService(repository=mock_repo)
        request = UserRegisterRequest(
            username="newuser", email="new@test.com", password="secure123"
        )

        result = await service.register(request)

        assert result.access_token is not None
        assert result.user.username == "newuser"
        assert result.user.email == "new@test.com"
        assert result.user.is_active is True

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, mock_repo):
        mock_repo.get_by_username = AsyncMock(
            return_value=UserInDB(
                id="existing", username="newuser", email="other@test.com",
                hashed_password="hash", created_at=datetime.now(timezone.utc),
            )
        )
        service = AuthService(repository=mock_repo)
        request = UserRegisterRequest(
            username="newuser", email="new@test.com", password="secure123"
        )

        with pytest.raises(ValueError, match="Username already taken"):
            await service.register(request)

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_repo):
        mock_repo.get_by_email = AsyncMock(
            return_value=UserInDB(
                id="existing", username="other", email="new@test.com",
                hashed_password="hash", created_at=datetime.now(timezone.utc),
            )
        )
        service = AuthService(repository=mock_repo)
        request = UserRegisterRequest(
            username="newuser", email="new@test.com", password="secure123"
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await service.register(request)


class TestAuthServiceLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, mock_repo):
        user = UserInDB(
            id="user-1", username="testuser", email="test@test.com",
            hashed_password=hash_password("correctpass"),
            created_at=datetime.now(timezone.utc), is_active=True,
        )
        mock_repo.get_by_username = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)
        request = UserLoginRequest(username="testuser", password="correctpass")

        result = await service.login(request)

        assert result.user.username == "testuser"
        assert result.access_token is not None

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_repo):
        user = UserInDB(
            id="user-1", username="testuser", email="test@test.com",
            hashed_password=hash_password("correctpass"),
            created_at=datetime.now(timezone.utc), is_active=True,
        )
        mock_repo.get_by_username = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)
        request = UserLoginRequest(username="testuser", password="wrongpass")

        with pytest.raises(ValueError, match="Invalid username or password"):
            await service.login(request)

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, mock_repo):
        mock_repo.get_by_username = AsyncMock(return_value=None)
        mock_repo.get_by_email = AsyncMock(return_value=None)
        service = AuthService(repository=mock_repo)
        request = UserLoginRequest(username="unknown", password="pass")

        with pytest.raises(ValueError, match="Invalid username or password"):
            await service.login(request)

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_repo):
        user = UserInDB(
            id="user-1", username="inactive", email="test@test.com",
            hashed_password=hash_password("pass"),
            created_at=datetime.now(timezone.utc), is_active=False,
        )
        mock_repo.get_by_username = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)
        request = UserLoginRequest(username="inactive", password="pass")

        with pytest.raises(ValueError, match="deactivated"):
            await service.login(request)

    @pytest.mark.asyncio
    async def test_login_by_email(self, mock_repo):
        user = UserInDB(
            id="user-1", username="testuser", email="test@test.com",
            hashed_password=hash_password("pass"),
            created_at=datetime.now(timezone.utc), is_active=True,
        )
        mock_repo.get_by_username = AsyncMock(return_value=None)
        mock_repo.get_by_email = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)
        request = UserLoginRequest(username="test@test.com", password="pass")

        result = await service.login(request)
        assert result.user.username == "testuser"


class TestAuthServiceGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_repo):
        user = UserInDB(
            id="user-1", username="testuser", email="test@test.com",
            hashed_password="hash", created_at=datetime.now(timezone.utc), is_active=True,
        )
        mock_repo.get_by_id = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)

        token, _ = create_access_token(TokenData(user_id="user-1", username="testuser"))
        result = await service.get_current_user(token)

        assert result.username == "testuser"
        assert result.email == "test@test.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_repo):
        service = AuthService(repository=mock_repo)
        with pytest.raises(ValueError, match="Invalid or expired token"):
            await service.get_current_user("bad.token.here")

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_repo):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        service = AuthService(repository=mock_repo)
        token, _ = create_access_token(TokenData(user_id="nonexistent", username="ghost"))

        with pytest.raises(ValueError, match="User not found"):
            await service.get_current_user(token)

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, mock_repo):
        user = UserInDB(
            id="user-1", username="disabled", email="test@test.com",
            hashed_password="hash", created_at=datetime.now(timezone.utc), is_active=False,
        )
        mock_repo.get_by_id = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)
        token, _ = create_access_token(TokenData(user_id="user-1", username="disabled"))

        with pytest.raises(ValueError, match="deactivated"):
            await service.get_current_user(token)
