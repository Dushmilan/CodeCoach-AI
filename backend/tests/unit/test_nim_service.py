import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException


class TestNIMServiceInit:
    def test_init_with_api_key_arg(self):
        with patch.dict("os.environ", {}, clear=True):
            from app.services.nim_service import NIMService
            service = NIMService(api_key="nvapi-test-key-12345")
            assert service.api_key == "nvapi-test-key-12345"

    def test_init_with_env_var(self):
        with patch.dict("os.environ", {"NVIDIA_API_KEY": "nvapi-from-env-xxx"}):
            from app.services.nim_service import NIMService
            service = NIMService()
            assert service.api_key == "nvapi-from-env-xxx"

    def test_init_without_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            from app.services.nim_service import NIMService
            with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
                NIMService()


class TestNIMServiceStructured:
    @pytest.fixture
    def mock_async_client(self):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_cls.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_get_structured_coaching_response_success(self, mock_async_client):
        with patch.dict("os.environ", {"NVIDIA_API_KEY": "nvapi-test-key-12345"}):
            from app.services.nim_service import NIMService

            mock_response_data = {
                "choices": [{
                    "message": {
                        "content": '{"summary": "Great work", "hints": [], "code_review": null, "complexity_analysis": null, "suggestions": [], "edge_cases": [], "explanation": null, "debug_help": null}'
                    }
                }]
            }

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_async_client.post.return_value = mock_response

            service = NIMService(api_key="nvapi-test")
            result = await service.get_structured_coaching_response(
                problem="Test", code="print(1)", language="python",
                message="help", mode="hint", difficulty="easy",
            )

            assert result["summary"] == "Great work"
            assert result["hints"] == []

    @pytest.mark.asyncio
    async def test_get_structured_coaching_response_api_error(self, mock_async_client):
        from app.services.nim_service import NIMService

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_async_client.post.return_value = mock_response

        with patch.dict("os.environ", {"NVIDIA_API_KEY": "nvapi-test"}):
            service = NIMService(api_key="nvapi-test")
            with pytest.raises(HTTPException) as exc:
                await service.get_structured_coaching_response(
                    problem="Test", code="x", language="python",
                    message="h", mode="hint", difficulty="easy",
                )
            assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_structured_coaching_response_timeout(self, mock_async_client):
        from app.services.nim_service import NIMService

        mock_async_client.post.side_effect = HTTPException(status_code=504, detail="Timeout")

        with patch.dict("os.environ", {"NVIDIA_API_KEY": "nvapi-test"}):
            service = NIMService(api_key="nvapi-test")
            with pytest.raises(HTTPException) as exc:
                await service.get_structured_coaching_response(
                    problem="Test", code="x", language="python",
                    message="h", mode="hint", difficulty="easy",
                )
            assert exc.value.status_code == 504

    @pytest.mark.asyncio
    async def test_get_structured_coaching_response_malformed_json(self, mock_async_client):
        with patch.dict("os.environ", {"NVIDIA_API_KEY": "nvapi-test"}):
            from app.services.nim_service import NIMService

            mock_response_data = {
                "choices": [{"message": {"content": "Not valid JSON at all"}}]
            }

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_async_client.post.return_value = mock_response

            service = NIMService(api_key="nvapi-test")
            result = await service.get_structured_coaching_response(
                problem="Test", code="x", language="python",
                message="h", mode="hint", difficulty="easy",
            )

            assert "summary" in result
            assert isinstance(result["hints"], list)


class TestNIMServiceStreaming:
    @pytest.mark.asyncio
    async def test_get_coaching_response_streaming(self):
        with patch.dict("os.environ", {"NVIDIA_API_KEY": "nvapi-test"}):
            from app.services.nim_service import NIMService

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = MagicMock()
                mock_instance.__aenter__.return_value = mock_instance
                mock_client.return_value = mock_instance

                async def mock_lines():
                    yield 'data: {"choices":[{"delta":{"content":"Hello"}}]}'
                    yield 'data: {"choices":[{"delta":{"content":" world"}}]}'
                    yield "data: [DONE]"

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.aiter_lines = mock_lines
                mock_instance.stream.return_value.__aenter__.return_value = mock_response

                service = NIMService(api_key="nvapi-test")
                chunks = []
                async for chunk in service.get_coaching_response(
                    problem="Test", code="x", language="python",
                    message="h", mode="hint", difficulty="easy",
                ):
                    chunks.append(chunk)

                assert chunks == ["Hello", " world"]
