from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.models.auth_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    SupabaseAuthRequest,
    TokenResponse,
    UserResponse,
    RefreshRequest,
)
from app.services.auth_service import AuthService
from app.api.auth_deps import get_auth_service, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return await auth_service.register(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Exchange a refresh token for a fresh access + refresh token pair."""
    try:
        return await auth_service.refresh(request.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
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
    auth_service: AuthService = Depends(get_auth_service),
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
