"""Shared auth helpers for integration tests.

Covers the two client styles used across the suite:
- sync ``TestClient`` (most files): :func:`register_headers`,
  :func:`register_user_headers`, :func:`admin_headers`
- async client (coach/rate-limit flows): :func:`aregister_headers`

Files that test the auth endpoints themselves (``test_auth_endpoints``,
``test_auth_cookies``) intentionally keep raw register/login calls because
they assert on the auth responses, not just the bearer header.
"""

import asyncio
from typing import Tuple

from fastapi.testclient import TestClient

from tests.db_helpers import promote_to_admin

_DEFAULT_PASSWORD = "testpass123"


def _email_for(username: str, email=None) -> str:
    return email or f"{username}@test.com"


def register_headers(
    client: TestClient,
    username: str,
    email: str | None = None,
    password: str = _DEFAULT_PASSWORD,
) -> dict:
    """Register (or log back in as) a user; return an Authorization header."""
    res = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": _email_for(username, email),
            "password": password,
        },
    )
    if res.status_code != 201:
        res = client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def register_user_headers(
    client: TestClient,
    username: str,
    email: str | None = None,
    password: str = _DEFAULT_PASSWORD,
) -> Tuple[str, dict]:
    """Sync variant returning ``(user_id, headers)``.

    Register-only (asserts 201) — callers use fresh usernames per test.
    """
    res = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": _email_for(username, email),
            "password": password,
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    return data["user"]["id"], {"Authorization": f"Bearer {data['access_token']}"}


def admin_headers(
    client: TestClient,
    username: str,
    email: str | None = None,
    password: str = _DEFAULT_PASSWORD,
) -> dict:
    """Register a user, promote to admin, return an Authorization header."""
    headers = register_headers(client, username, email, password)
    asyncio.run(promote_to_admin(username))
    return headers


async def aregister_headers(
    async_client,
    username: str,
    email: str | None = None,
    password: str = _DEFAULT_PASSWORD,
) -> Tuple[str, dict]:
    """Async-client variant; returns ``(user_id, headers)``.

    Register-only (asserts 201), matching the original per-file helpers —
    callers use fresh usernames per test.
    """
    res = await async_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": _email_for(username, email),
            "password": password,
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    return data["user"]["id"], {"Authorization": f"Bearer {data['access_token']}"}
