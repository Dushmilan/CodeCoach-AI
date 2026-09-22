"""Issue #264: process-wide shared httpx clients (connection reuse)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.http_clients import (
    get_shared_client,
    reset_shared_clients,
)


def test_same_name_returns_same_client():
    reset_shared_clients()
    try:
        assert get_shared_client("groq") is get_shared_client("groq")
    finally:
        reset_shared_clients()


def test_different_names_are_isolated():
    reset_shared_clients()
    try:
        assert get_shared_client("groq") is not get_shared_client("piston")
    finally:
        reset_shared_clients()


def test_reset_drops_cached_clients():
    reset_shared_clients()
    first = get_shared_client("groq")
    reset_shared_clients()
    try:
        assert get_shared_client("groq") is not first
    finally:
        reset_shared_clients()


@pytest.mark.asyncio
async def test_piston_reuses_client_across_calls():
    """Two executions must share one httpx client (no handshake per call)."""
    from app.services.piston_service import PistonService

    reset_shared_clients()
    try:
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "run": {"stdout": "1\n", "stderr": "", "code": 0},
                "language": "python",
                "version": "3.10.0",
            }
            mock_instance.post.return_value = mock_response

            service = PistonService()
            await service.execute("python", "print(1)")
            await service.execute("python", "print(2)")

            assert mock_cls.call_count == 1
    finally:
        reset_shared_clients()


@pytest.mark.asyncio
async def test_groq_reuses_client_across_calls():
    """Two structured calls must share one httpx client."""
    from app.services.groq_service import GroqService

    reset_shared_clients()
    try:
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"summary": "hi", "hints": [], '
                            '"code_review": null, "complexity_analysis": null, '
                            '"suggestions": [], "edge_cases": [], '
                            '"explanation": null, "debug_help": null}'
                        }
                    }
                ],
                "usage": {},
            }
            mock_instance.post.return_value = mock_response

            service = GroqService(api_key="gsk_test")
            msgs = [{"role": "user", "content": "hi"}]
            await service._fetch_structured(msgs, "model", 100, 0.1)
            await service._fetch_structured(msgs, "model", 100, 0.1)

            assert mock_cls.call_count == 1
    finally:
        reset_shared_clients()
