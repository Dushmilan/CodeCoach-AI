"""Unit tests for require_csrf (SEC-2 double-submit check).

Covers every branch of app/api/auth_deps.require_csrf so the
coverage-budget regression gate stays green and the security contract is
explicitly pinned:
  * no session cookie  -> pass through (nothing to protect)
  * session + valid X-CSRF-Token == csrf_token cookie -> pass
  * session + missing csrf cookie / missing header / mismatch -> 403
"""

import pytest
from fastapi import HTTPException

from app.api.auth_deps import CSRF_COOKIE, REFRESH_COOKIE, require_csrf


class _FakeHeaders:
    def __init__(self, raw: list[tuple[bytes, bytes]]):
        self._raw = raw

    def get(self, key: str, default=None):
        want = key.lower().encode()
        for k, v in self._raw:
            if k.lower() == want:
                return v.decode()
        return default


class _FakeRequest:
    """Duck-typed stand-in exposing only what require_csrf reads."""

    def __init__(self, cookies: dict[str, str], headers: dict[str, str]):
        self.cookies = cookies
        self.headers = _FakeHeaders(
            [(k.lower().encode(), v.encode()) for k, v in headers.items()]
        )


def _request_with_session(header_token=None, csrf_cookie="tok-123"):
    cookies = {REFRESH_COOKIE: "rt-abc"}
    if csrf_cookie is not None:
        cookies[CSRF_COOKIE] = csrf_cookie
    headers = {}
    if header_token is not None:
        headers["X-CSRF-Token"] = header_token
    return _FakeRequest(cookies, headers)


@pytest.mark.asyncio
async def test_no_session_cookie_passes_through():
    request = _FakeRequest({}, {})  # Bearer-only request, no cookies at all
    assert await require_csrf(request) is None


@pytest.mark.asyncio
async def test_matching_header_and_cookie_passes():
    request = _request_with_session(header_token="tok-123")
    assert await require_csrf(request) is None


@pytest.mark.asyncio
async def test_missing_csrf_cookie_rejected():
    request = _request_with_session(header_token="tok-123", csrf_cookie=None)
    with pytest.raises(HTTPException) as exc:
        await require_csrf(request)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_missing_header_rejected():
    request = _request_with_session(header_token=None)
    with pytest.raises(HTTPException) as exc:
        await require_csrf(request)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_mismatched_header_rejected():
    request = _request_with_session(header_token="evil-token")
    with pytest.raises(HTTPException) as exc:
        await require_csrf(request)
    assert exc.value.status_code == 403
    assert "CSRF" in exc.value.detail
