from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
import logging
import secrets
from typing import Optional

from app.models.auth_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    SupabaseAuthRequest,
    TokenResponse,
    UserResponse,
    RefreshRequest,
)
from app.services.auth_service import AuthService
from app.api.auth_deps import get_auth_service, get_current_user, require_csrf
from app.core.config import is_production

logger = logging.getLogger(__name__)

router = APIRouter()

REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days, matches refresh token TTL
COOKIE_PATH = "/api/auth"


def _cookie_secure() -> bool:
    """Secure cookies in production; plain HTTP in dev/testing."""
    return is_production()


def _set_auth_cookies(response: Response, refresh_token: str, csrf_token: str) -> None:
    """Set the httpOnly refresh cookie + JS-readable CSRF cookie (double-submit)."""
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        path=COOKIE_PATH,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
    )
    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        path=COOKIE_PATH,
        httponly=False,  # JS must be able to read it to echo as a header
        samesite="lax",
        secure=_cookie_secure(),
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    response.delete_cookie(CSRF_COOKIE, path=COOKIE_PATH)


def _new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _issue_with_cookies(response: Response, result: TokenResponse) -> TokenResponse:
    """Attach the refresh + CSRF cookies and return the response body.

    The refresh token moves out of the JSON body into the httpOnly cookie; the
    CSRF token is echoed in the body (and its cookie) so the frontend can send
    it back as the X-CSRF-Token header on mutating requests.
    """
    refresh_token = result.refresh_token
    csrf_token = _new_csrf_token()
    if refresh_token:
        _set_auth_cookies(response, refresh_token, csrf_token)
    return result.model_copy(update={"refresh_token": None, "csrf_token": csrf_token})


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
        return _issue_with_cookies(response, result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    raw_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    request: Optional[RefreshRequest] = Body(default=None),
):
    """Exchange a refresh token for a fresh access + refresh token pair.

    Reads the refresh token from the httpOnly cookie when present, falling back
    to the request body for backwards compatibility.

    NOTE: refresh is deliberately NOT CSRF-checked. The refresh_token cookie is
    HttpOnly + SameSite=Lax, so a cross-site POST never carries it. And after a
    page reload the JS has lost its in-memory CSRF token, so a CSRF requirement
    here would deadlock session restore. The response rotates both the refresh
    cookie and a fresh CSRF token (used by /logout).
    """
    cookie_token = raw_request.cookies.get(REFRESH_COOKIE)
    refresh_token = cookie_token or (request.refresh_token if request else None)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        result = await auth_service.refresh(refresh_token)
        return _issue_with_cookies(response, result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.login(request)
        return _issue_with_cookies(response, result)
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
        return _issue_with_cookies(response, result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    _: None = Depends(require_csrf),
):
    """Clear the refresh + CSRF cookies. CSRF-protected: only a browser with a
    matching csrf_token cookie (i.e. the real session holder) can force a logout."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
