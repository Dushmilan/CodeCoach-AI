"""Shared auth helpers for integration tests (sync TestClient + async)."""

import asyncio
from typing import Tuple

from fastapi.testclient import TestClient

PASSWORD = "testpass123"


def register_user_headers(test_client: TestClient, username: str) -> dict:
    """Register (or log into) a user; return Bearer headers."""
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": PASSWORD,
        },
    )
    if res.status_code != 201:
        res = test_client.post(
            "/api/auth/login",
            json={"username": username, "password": PASSWORD},
        )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def register_user_id_headers(
    test_client: TestClient, username: str
) -> Tuple[str, dict]:
    """Register a user; return (user_id, Bearer headers)."""
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": PASSWORD,
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    return body["user"]["id"], {"Authorization": f"Bearer {body['access_token']}"}


def admin_headers(test_client: TestClient, username: str = "testadmin") -> dict:
    """Register (or log into) a user, promote to admin, return headers."""
    from tests.db_helpers import promote_to_admin

    res = test_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": PASSWORD,
        },
    )
    if res.status_code != 201:
        res = test_client.post(
            "/api/auth/login",
            json={"username": username, "password": PASSWORD},
        )
    asyncio.run(promote_to_admin(username))
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def aregister_user_headers(async_client, username: str) -> dict:
    """Async variant of register_user_headers for AsyncClient tests."""
    res = await async_client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": PASSWORD,
        },
    )
    if res.status_code != 201:
        res = await async_client.post(
            "/api/auth/login",
            json={"username": username, "password": PASSWORD},
        )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
