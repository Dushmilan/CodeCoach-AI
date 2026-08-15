from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
import secrets

from app.services.auth_service import AuthService
from app.ports.user_repository import UserRepository
from app.api.dependencies import get_user_repo
from app.models.auth_schemas import UserResponse

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=True)
security_optional = HTTPBearer(auto_error=False)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    return AuthService(repository=user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
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
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[UserResponse]:
    if credentials is None:
        return None
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except ValueError:
        return None


async def require_admin(
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: admin role required",
        )
    return current_user


async def require_super_admin(
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: super_admin role required",
        )
    return current_user


REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"


async def require_csrf(request: Request) -> None:
    """Double-submit CSRF check for cookie-authenticated mutating endpoints.

    Only enforced when a session (refresh_token cookie) is present — Bearer-only
    requests have no cookie to protect. When a session exists, the X-CSRF-Token
    header must match the csrf_token cookie value; otherwise 403.
    """
    if not request.cookies.get(REFRESH_COOKIE):
        return  # No cookie session -> nothing to protect.
    csrf_cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get("x-csrf-token")
    if not csrf_cookie or not header or not secrets.compare_digest(header, csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )


async def require_premium(
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.plan != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium feature — upgrade required",
        )
    return current_user
