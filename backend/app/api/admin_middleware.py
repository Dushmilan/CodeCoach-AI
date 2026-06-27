from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.services.auth_service import AuthService
from app.ports.user_repository import UserRepository
from app.api.dependencies import get_user_repo
from app.models.auth_schemas import UserResponse

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=True)


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
    credentials: Optional[HTTPAuthorizationCredentials] = None,
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
    """Middleware to require admin role or higher."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: admin role required",
        )
    return current_user


async def require_super_admin(
    current_user: UserResponse = Depends(get_current_user),
):
    """Middleware to require super_admin role."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: super_admin role required",
        )
    return current_user
