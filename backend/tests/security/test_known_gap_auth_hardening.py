"""Characterization tests for known auth hardening gaps (Issue #202).

These tests DOCUMENT current behavior — they pass today and must keep
passing until the corresponding hardening feature lands, at which point
they must be rewritten to assert the new behavior (never weakened to
accommodate a regression).

Known gaps:
  * No login brute-force throttle/lockout (limiter covers coach/run/questions).
  * Refresh tokens are stateless JWTs: rotation issues a new pair but the
    old refresh token stays valid (no revocation, no reuse detection).
  * Logout only clears cookies client-side; outstanding tokens stay valid.
"""

import pytest

from tests.fixtures.auth_helpers import aregister_headers

pytestmark = pytest.mark.asyncio


async def _login(async_client, username, password):
    return await async_client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )


def _refresh_cookie(res):
    """Extract the httpOnly refresh_token cookie (body carries None by design)."""
    for chunk in res.headers.get_list("set-cookie"):
        name, _, rest = chunk.partition("=")
        if name.strip() == "refresh_token":
            return rest.split(";")[0]
    return None


class TestKnownGapNoLoginThrottle:
    async def test_rapid_wrong_passwords_never_429(self, async_client):
        """25 rapid bad-password logins: all 401, none throttled.

        Documents the missing brute-force throttle. If a throttle lands,
        this test must be updated to expect 429s after the threshold.
        """
        await aregister_headers(async_client, "gap_brute_target")
        statuses = set()
        for _ in range(25):
            res = await _login(async_client, "gap_brute_target", "wrong-password-x")
            statuses.add(res.status_code)
        assert statuses == {401}, statuses


class TestKnownGapRefreshReuse:
    async def test_old_refresh_token_still_valid_after_rotation(self, async_client):
        """Rotate via /refresh, then replay the ORIGINAL refresh token.

        Stateless JWTs mean the old token still works — no reuse detection.
        """
        await aregister_headers(async_client, "gap_refresh_reuse")
        first = await _login(async_client, "gap_refresh_reuse", "testpass123")
        assert first.status_code == 200, first.text
        old_refresh = _refresh_cookie(first)
        assert old_refresh

        rotated = await async_client.post(
            "/api/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert rotated.status_code == 200, rotated.text
        assert rotated.json()["refresh_token"] != old_refresh

        replay = await async_client.post(
            "/api/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert replay.status_code == 200, replay.text

    async def test_logout_does_not_revoke_refresh_token(self, async_client):
        """Logout clears cookies but the refresh token body replay still works."""
        await aregister_headers(async_client, "gap_logout_revoke")
        logged = await _login(async_client, "gap_logout_revoke", "testpass123")
        assert logged.status_code == 200, logged.text
        refresh = _refresh_cookie(logged)
        assert refresh
        csrf = logged.json().get("csrf_token")

        cookies = {
            "refresh_token": refresh,
            **({"csrf_token": csrf} if csrf else {}),
        }
        res = await async_client.post("/api/auth/logout", cookies=cookies)
        assert res.status_code in (204, 403), res.text

        replay = await async_client.post(
            "/api/auth/refresh", json={"refresh_token": refresh}
        )
        assert replay.status_code == 200, replay.text
