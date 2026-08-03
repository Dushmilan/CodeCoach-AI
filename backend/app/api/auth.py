from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
import logging
import os

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

REFRESH_COOKIE_NAME = "codecoach_refresh"


def _cookie_settings() -> dict:
    """HttpOnly cookie config. Secure is enabled outside local dev."""
    secure = os.getenv("ENVIRONMENT", "production") != "development"
    return {
        "key": REFRESH_COOKIE_NAME,
        "httponly": True,
        "samesite": "lax",
        "secure": secure,
        "path": "/",
        "max_age": 7 * 24 * 60 * 60,  # 7 days, matches REFRESH_TOKEN_EXPIRE_DAYS
    }


def _set_refresh_cookie(response: Response, refresh_token: str | None) -> None:
    if refresh_token:
        response.set_cookie(value=refresh_token, **_cookie_settings())
    else:
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/")


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: UserRegisterRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.register(request)
        _set_refresh_cookie(response, result.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    refresh_body: RefreshRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Exchange a refresh token for a fresh access + refresh token pair.

    Accepts the refresh token from the HttpOnly cookie when the body omits it.
    """
    try:
        refresh_token = refresh_body.refresh_token or _read_refresh_cookie(request)
        result = await auth_service.refresh(refresh_token)
        _set_refresh_cookie(response, result.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def _read_refresh_cookie(request) -> str:
    """Read the refresh token from the HttpOnly cookie."""
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise ValueError("Missing refresh token")
    return token


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.login(request)
        _set_refresh_cookie(response, result.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/supabase", response_model=TokenResponse)
async def login_with_supabase(
    request: SupabaseAuthRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.login_with_supabase(request.access_token)
        _set_refresh_cookie(response, result.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """Clear the refresh-token cookie."""
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
