import uuid
import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import bcrypt
import httpx
from jose import JWTError, jwt

from app.models.auth_schemas import (
    UserInDB,
    UserResponse,
    TokenResponse,
    TokenData,
    UserRegisterRequest,
    UserLoginRequest,
)
from app.ports.user_repository import UserRepository
from app.repositories.file_user_repository import FileUserRepository

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
_USERS_FILE = str(Path(__file__).parent.parent.parent / "data" / "users.json")


def _get_secret_key() -> str:
    key = os.getenv("JWT_SECRET_KEY")
    if not key:
        key = "dev-secret-key-change-in-production"
        logger.warning("JWT_SECRET_KEY not set, using insecure default")
    return key


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(
    data: TokenData, expires_delta: Optional[timedelta] = None
) -> tuple[str, int]:
    to_encode = {"sub": data.user_id or "", "username": data.username or ""}
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    encoded = jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)
    expires_in = int((expire - datetime.now(timezone.utc)).total_seconds())
    return encoded, expires_in


def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None:
            return None
        return TokenData(user_id=user_id, username=username)
    except JWTError:
        return None


def _user_to_response(user: UserInDB) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        is_active=user.is_active,
    )


class AuthService:
    def __init__(self, repository: Optional[UserRepository] = None):
        self.repository = repository or FileUserRepository(_USERS_FILE)

    async def register(self, request: UserRegisterRequest) -> TokenResponse:
        existing = await self.repository.get_by_username(request.username)
        if existing:
            raise ValueError("Username already taken")

        existing_email = await self.repository.get_by_email(request.email)
        if existing_email:
            raise ValueError("Email already registered")

        user = UserInDB(
            id=str(uuid.uuid4()),
            username=request.username,
            email=request.email,
            hashed_password=hash_password(request.password),
            created_at=datetime.now(timezone.utc),
        )
        await self.repository.add(user)

        token, expires_in = create_access_token(
            TokenData(user_id=user.id, username=user.username)
        )
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=_user_to_response(user),
        )

    async def login(self, request: UserLoginRequest) -> TokenResponse:
        user = await self.repository.get_by_username(request.username)
        if not user:
            user = await self.repository.get_by_email(request.username)

        if not user:
            raise ValueError("Invalid username or password")

        if not verify_password(request.password, user.hashed_password):
            raise ValueError("Invalid username or password")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        token, expires_in = create_access_token(
            TokenData(user_id=user.id, username=user.username)
        )
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=_user_to_response(user),
        )

    async def login_with_supabase(self, access_token: str) -> TokenResponse:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        if not supabase_url or not supabase_anon_key:
            logger.error("SUPABASE_URL or SUPABASE_ANON_KEY not set")
            raise ValueError("Supabase not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "apikey": supabase_anon_key,
                },
            )

        if response.status_code != 200:
            raise ValueError("Invalid Supabase token")

        supabase_user = response.json()
        oauth_id = supabase_user.get("id")
        email = supabase_user.get("email", "")
        if not oauth_id:
            raise ValueError("Invalid Supabase token")

        existing = await self.repository.get_by_oauth("google", oauth_id)
        if existing:
            token, expires_in = create_access_token(
                TokenData(user_id=existing.id, username=existing.username)
            )
            return TokenResponse(
                access_token=token,
                expires_in=expires_in,
                user=_user_to_response(existing),
            )

        username = email.split("@")[0] if email else f"user_{oauth_id[:8]}"
        base_username = username
        counter = 1
        while await self.repository.get_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1

        user = UserInDB(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password="",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            oauth_provider="google",
            oauth_id=oauth_id,
        )
        await self.repository.add(user)

        token, expires_in = create_access_token(
            TokenData(user_id=user.id, username=user.username)
        )
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=_user_to_response(user),
        )

    async def get_current_user(self, token: str) -> UserResponse:
        token_data = decode_access_token(token)
        if not token_data or not token_data.user_id:
            raise ValueError("Invalid or expired token")

        user = await self.repository.get_by_id(token_data.user_id)
        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        return _user_to_response(user)
