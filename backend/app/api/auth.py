from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.models.auth_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    SupabaseAuthRequest,
    TokenResponse,
    UserResponse,
)
from app.ports.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.api.dependencies import get_user_repo

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=True)
security_optional = HTTPBearer(auto_error=False)


def _get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    return AuthService(repository=user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(_get_auth_service),
) -> UserResponse:
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_optional),
    auth_service: AuthService = Depends(_get_auth_service),
) -> Optional[UserResponse]:
    if credentials is None:
        return None
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except ValueError:
        return None

router = APIRouter()


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(_get_auth_service),
):
    try:
        return await auth_service.register(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(_get_auth_service),
):
    try:
        return await auth_service.login(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/supabase", response_model=TokenResponse)
async def login_with_supabase(
    request: SupabaseAuthRequest,
    auth_service: AuthService = Depends(_get_auth_service),
):
    try:
        return await auth_service.login_with_supabase(request.access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
