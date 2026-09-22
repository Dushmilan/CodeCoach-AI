"""Process-wide shared httpx clients (Issue #264).

Per-request clients pay TCP+TLS setup on every call — Groq is HTTPS, so
each coaching call burned a fresh handshake. Services must use
``get_shared_client`` instead of constructing ``httpx.AsyncClient``.

Tests: holders are process-global; ``tests/conftest.py`` resets them via
an autouse fixture so patched ``httpx.AsyncClient`` mocks never leak
across tests.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_clients: dict[str, httpx.AsyncClient] = {}


def get_shared_client(name: str) -> httpx.AsyncClient:
    """Return the process-wide client for ``name``, creating it once.

    No timeout is set at the client level — every call passes its own
    per-request timeout so one slow endpoint cannot set policy for all.
    """
    client = _clients.get(name)
    if client is None:
        client = httpx.AsyncClient()
        _clients[name] = client
    return client


def reset_shared_clients() -> None:
    """Drop cached clients (tests + shutdown paths)."""
    _clients.clear()


async def aclose_shared_clients() -> None:
    """Close and drop all cached clients (app shutdown)."""
    while _clients:
        _, client = _clients.popitem()
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001 - shutdown must not raise
            logger.debug("Shared HTTP client close failed", exc_info=True)
