import os
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.models.auth_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenData,
    UserInDB,
)
from app.services.auth_service import (
    AuthService,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
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
    repo.get_by_oauth = AsyncMock(return_value=None)
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
            mock_dt.side_effect = lambda *a, **kw: (
                datetime(*a, **kw)
                if a
                else datetime.now(timezone.utc) - timedelta(hours=48)
            )
            token, _ = create_access_token(
                TokenData(user_id="user-1", username="testuser"),
                expires_delta=timedelta(hours=1),
            )

        decoded = decode_access_token(token)
        assert decoded is None


class TestRefreshToken:
    def test_create_and_decode_refresh_token(self):
        token, _ = create_refresh_token(
            TokenData(user_id="user-1", username="testuser")
        )
        decoded = decode_refresh_token(token)
        assert decoded is not None
        assert decoded.user_id == "user-1"
        assert decoded.username == "testuser"

    def test_access_token_is_not_a_refresh_token(self):
        access, _ = create_access_token(TokenData(user_id="u", username="n"))
        refresh, _ = create_refresh_token(TokenData(user_id="u", username="n"))

        # An access token must not be accepted as a refresh token and vice versa
        assert decode_refresh_token(access) is None
        assert decode_access_token(refresh) is None

    def test_decode_invalid_refresh_token(self):
        assert decode_refresh_token("not.a.token") is None


class TestAuthServiceRefresh:
    @pytest.mark.asyncio
    async def test_refresh_issues_new_token_pair(self, mock_repo):
        user = UserInDB(
            id="user-1",
            username="testuser",
            email="test@test.com",
            hashed_password=hash_password("pw"),
            created_at=datetime.now(timezone.utc),
        )
        mock_repo.get_by_id = AsyncMock(return_value=user)

        service = AuthService(repository=mock_repo)
        refresh_token, _ = create_refresh_token(
            TokenData(user_id="user-1", username="testuser")
        )

        result = await service.refresh(refresh_token)

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user.id == "user-1"

    @pytest.mark.asyncio
    async def test_refresh_rejects_deactivated_user(self, mock_repo):
        user = UserInDB(
            id="user-1",
            username="disabled",
            email="disabled@test.com",
            hashed_password=hash_password("pw"),
            created_at=datetime.now(timezone.utc),
            is_active=False,
        )
        mock_repo.get_by_id = AsyncMock(return_value=user)

        service = AuthService(repository=mock_repo)
        refresh_token, _ = create_refresh_token(
            TokenData(user_id="user-1", username="disabled")
        )

        with pytest.raises(ValueError):
            await service.refresh(refresh_token)

    @pytest.mark.asyncio
    async def test_refresh_rejects_invalid_token(self, mock_repo):
        service = AuthService(repository=mock_repo)
        with pytest.raises(ValueError):
            await service.refresh("garbage.token.value")

    @pytest.mark.asyncio
    async def test_refresh_rejects_access_token(self, mock_repo):
        service = AuthService(repository=mock_repo)
        access, _ = create_access_token(
            TokenData(user_id="user-1", username="testuser")
        )
        with pytest.raises(ValueError):
            await service.refresh(access)


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
                id="existing",
                username="newuser",
                email="other@test.com",
                hashed_password="hash",
                created_at=datetime.now(timezone.utc),
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
                id="existing",
                username="other",
                email="new@test.com",
                hashed_password="hash",
                created_at=datetime.now(timezone.utc),
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
            id="user-1",
            username="testuser",
            email="test@test.com",
            hashed_password=hash_password("correctpass"),
            created_at=datetime.now(timezone.utc),
            is_active=True,
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
            id="user-1",
            username="testuser",
            email="test@test.com",
            hashed_password=hash_password("correctpass"),
            created_at=datetime.now(timezone.utc),
            is_active=True,
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
            id="user-1",
            username="inactive",
            email="test@test.com",
            hashed_password=hash_password("pass"),
            created_at=datetime.now(timezone.utc),
            is_active=False,
        )
        mock_repo.get_by_username = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)
        request = UserLoginRequest(username="inactive", password="pass")

        with pytest.raises(ValueError, match="deactivated"):
            await service.login(request)

    @pytest.mark.asyncio
    async def test_login_by_email(self, mock_repo):
        user = UserInDB(
            id="user-1",
            username="testuser",
            email="test@test.com",
            hashed_password=hash_password("pass"),
            created_at=datetime.now(timezone.utc),
            is_active=True,
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
            id="user-1",
            username="testuser",
            email="test@test.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
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
        token, _ = create_access_token(
            TokenData(user_id="nonexistent", username="ghost")
        )

        with pytest.raises(ValueError, match="User not found"):
            await service.get_current_user(token)

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, mock_repo):
        user = UserInDB(
            id="user-1",
            username="disabled",
            email="test@test.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=False,
        )
        mock_repo.get_by_id = AsyncMock(return_value=user)
        service = AuthService(repository=mock_repo)
        token, _ = create_access_token(TokenData(user_id="user-1", username="disabled"))

        with pytest.raises(ValueError, match="deactivated"):
            await service.get_current_user(token)


class TestAuthServiceSupabaseLogin:
    @pytest.fixture(autouse=True)
    def setup_env(self):
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-anon-key",
            },
        ):
            yield

    @pytest.mark.asyncio
    async def test_login_with_supabase_creates_new_user(self, mock_repo):
        supabase_user = {"id": "google-123", "email": "newuser@gmail.com"}

        async def mock_get(url, headers=None):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = supabase_user
            return mock_resp

        with patch.object(httpx, "AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__aenter__.return_value.get = mock_get
            mock_client_cls.return_value = mock_client

            service = AuthService(repository=mock_repo)
            result = await service.login_with_supabase("valid_token")

        assert result.user.username == "newuser"
        assert result.user.email == "newuser@gmail.com"
        assert result.access_token is not None
        mock_repo.add.assert_called_once()
        added_user = mock_repo.add.call_args[0][0]
        assert added_user.oauth_provider == "google"
        assert added_user.oauth_id == "google-123"

    @pytest.mark.asyncio
    async def test_login_with_supabase_returns_existing_user(self, mock_repo):
        existing_user = UserInDB(
            id="user-1",
            username="existing",
            email="existing@gmail.com",
            hashed_password="",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            oauth_provider="google",
            oauth_id="google-123",
        )
        mock_repo.get_by_oauth = AsyncMock(return_value=existing_user)

        supabase_user = {"id": "google-123", "email": "existing@gmail.com"}

        async def mock_get(url, headers=None):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = supabase_user
            return mock_resp

        with patch.object(httpx, "AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__aenter__.return_value.get = mock_get
            mock_client_cls.return_value = mock_client

            service = AuthService(repository=mock_repo)
            result = await service.login_with_supabase("valid_token")

        assert result.user.username == "existing"
        assert result.user.email == "existing@gmail.com"
        mock_repo.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_with_supabase_invalid_token(self, mock_repo):
        async def mock_get(url, headers=None):
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            return mock_resp

        with patch.object(httpx, "AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__aenter__.return_value.get = mock_get
            mock_client_cls.return_value = mock_client

            service = AuthService(repository=mock_repo)
            with pytest.raises(ValueError, match="Invalid Supabase token"):
                await service.login_with_supabase("bad_token")

        mock_repo.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_with_supabase_no_config(self, mock_repo):
        with patch.dict(os.environ, {}, clear=True):
            service = AuthService(repository=mock_repo)
            with pytest.raises(ValueError, match="Supabase not configured"):
                await service.login_with_supabase("token")
