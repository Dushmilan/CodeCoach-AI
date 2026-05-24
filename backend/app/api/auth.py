from fastapi import APIRouter, Depends, HTTPException, status

from app.models.auth_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    SupabaseAuthRequest,
    TokenResponse,
    UserResponse,
)
from app.dependencies.auth import get_current_user
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(request: UserRegisterRequest):
    auth_service = AuthService()
    try:
        return await auth_service.register(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    auth_service = AuthService()
    try:
        return await auth_service.login(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/supabase", response_model=TokenResponse)
async def login_with_supabase(request: SupabaseAuthRequest):
    auth_service = AuthService()
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
