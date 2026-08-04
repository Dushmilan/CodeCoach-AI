"""Unit tests for GroqService — Groq adapter for AI coaching.

Covers: key handling, model mapping, structured usage extraction + recording,
streaming usage extraction + recording, caching (cache hits do not meter),
and Groq error mapping (401/429/timeout).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException


class FakeRecorder:
    """Test double that records usage calls."""

    def __init__(self):
        self.calls = []

    async def record(self, **kwargs):
        self.calls.append(kwargs)


class FakeCache:
    """Minimal cache double to exercise cache-hit behavior."""

    def __init__(self, cached_value=None):
        self.cached_value = cached_value
        self.set_calls = []

    async def get(self, key):
        return self.cached_value

    async def set(self, key, value, ttl=0):
        self.set_calls.append((key, value, ttl))


STRUCTURED_CONTENT = (
    '{"summary": "Great work", "hints": [], "code_review": null, '
    '"complexity_analysis": null, "suggestions": [], "edge_cases": [], '
    '"explanation": null, "debug_help": null}'
)


class TestGroqServiceInit:
    def test_init_with_api_key_arg(self):
        with patch.dict("os.environ", {}, clear=True):
            from app.services.groq_service import GroqService

            service = GroqService(api_key="gsk_test_key_12345")
            assert service.api_key == "gsk_test_key_12345"
            assert service.base_url == "https://api.groq.com/openai/v1"

    def test_init_with_env_var(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_from_env"}):
            from app.services.groq_service import GroqService

            service = GroqService()
            assert service.api_key == "gsk_from_env"

    def test_init_without_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            from app.services.groq_service import GroqService

            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                GroqService()

    def test_model_map_defaults(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_test"}):
            from app.services.groq_service import GroqService

            service = GroqService()
            assert service.models["easy"] == "llama-3.1-8b-instant"
            assert service.models["medium"] == "llama-3.3-70b-versatile"
            assert service.models["hard"] == "llama-3.3-70b-versatile"
            assert service.models["stream"] == "llama-3.1-8b-instant"

    def test_model_map_env_overrides(self):
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "gsk_test",
                "GROQ_MODEL_EASY": "custom-easy",
                "GROQ_MODEL_MEDIUM": "custom-medium",
            },
        ):
            from app.services.groq_service import GroqService

            service = GroqService()
            assert service.models["easy"] == "custom-easy"
            assert service.models["medium"] == "custom-medium"
            assert service.models["hard"] == "llama-3.3-70b-versatile"


class TestGroqServiceStructured:
    @pytest.fixture
    def mock_async_client(self):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_cls.return_value = mock_instance
            yield mock_instance

    def _make_response(self, status_code=200, body=None):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = "error body"
        mock_response.headers = {"retry-after": "5"}
        if body is not None:
            mock_response.json.return_value = body
        return mock_response

    @pytest.mark.asyncio
    async def test_structured_success_records_usage(self, mock_async_client):
        recorder = FakeRecorder()
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 34, "total_tokens": 46},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(
            api_key="gsk_test", usage_recorder=recorder, user_id="user-1"
        )
        result = await service.get_structured_coaching_response(
            problem="Test",
            code="print(1)",
            language="python",
            message="help",
            mode="hint",
            difficulty="medium",
        )

        assert result["summary"] == "Great work"
        assert recorder.calls == [
            {
                "user_id": "user-1",
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "endpoint": "coach",
                "input_tokens": 12,
                "output_tokens": 34,
            }
        ]

    @pytest.mark.asyncio
    async def test_structured_uses_easy_model(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        mock_async_client.post.return_value = self._make_response(200, body)
        recorder = FakeRecorder()

        from app.services.groq_service import GroqService

        service = GroqService(
            api_key="gsk_test",
            usage_recorder=recorder,
            user_id="u",
        )
        await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        call = mock_async_client.post.call_args
        assert call.kwargs["json"]["model"] == "llama-3.1-8b-instant"
        assert recorder.calls[0]["model"] == "llama-3.1-8b-instant"

    @pytest.mark.asyncio
    async def test_structured_uses_hard_model(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(
            api_key="gsk_test", usage_recorder=FakeRecorder(), user_id="u"
        )
        await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="hard",
        )
        call = mock_async_client.post.call_args
        assert call.kwargs["json"]["model"] == "llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_structured_payload_uses_max_completion_tokens(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        call = mock_async_client.post.call_args
        payload = call.kwargs["json"]
        assert "max_completion_tokens" in payload
        assert "max_tokens" not in payload
        assert payload["stream"] is False

    @pytest.mark.asyncio
    async def test_structured_cache_hit_does_not_call_api_or_record(
        self, mock_async_client
    ):
        recorder = FakeRecorder()
        cached = {"summary": "cached summary", "hints": []}
        cache = FakeCache(cached_value=cached)

        from app.services.groq_service import GroqService

        service = GroqService(
            api_key="gsk_test",
            cache=cache,
            usage_recorder=recorder,
            user_id="user-1",
        )
        result = await service.get_structured_coaching_response(
            problem="Same",
            code="same",
            language="python",
            message="same",
            mode="hint",
            difficulty="easy",
        )

        assert result == cached
        mock_async_client.post.assert_not_called()
        assert recorder.calls == []

    @pytest.mark.asyncio
    async def test_structured_401_maps_to_500(self, mock_async_client):
        mock_async_client.post.return_value = self._make_response(401)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_bad")
        with pytest.raises(HTTPException) as exc:
            await service.get_structured_coaching_response(
                problem="T",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="easy",
            )
        assert exc.value.status_code == 500
        assert "key" in str(exc.value.detail).lower()

    @pytest.mark.asyncio
    async def test_structured_429_maps_to_429_with_retry_after(self, mock_async_client):
        mock_async_client.post.return_value = self._make_response(429)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        with pytest.raises(HTTPException) as exc:
            await service.get_structured_coaching_response(
                problem="T",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="easy",
            )
        assert exc.value.status_code == 429
        assert exc.value.headers["Retry-After"] == "5"

    @pytest.mark.asyncio
    async def test_structured_timeout_maps_to_504(self, mock_async_client):
        import httpx

        mock_async_client.post.side_effect = httpx.TimeoutException("timeout")

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        with pytest.raises(HTTPException) as exc:
            await service.get_structured_coaching_response(
                problem="T",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="easy",
            )
        assert exc.value.status_code == 504

    @pytest.mark.asyncio
    async def test_structured_no_usage_does_not_record(self, mock_async_client):
        recorder = FakeRecorder()
        body = {"choices": [{"message": {"content": STRUCTURED_CONTENT}}]}
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", usage_recorder=recorder, user_id="u")
        result = await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert result["summary"] == "Great work"
        assert recorder.calls == []


class TestGroqServiceStreaming:
    def _stream_response(self, lines):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"retry-after": "5"}

        async def aiter_lines():
            for line in lines:
                yield line

        async def aread():
            return b"error body"

        mock_response.aiter_lines = aiter_lines
        mock_response.aread = aread
        return mock_response

    @pytest.mark.asyncio
    async def test_stream_yields_content_and_records_usage(self):
        recorder = FakeRecorder()
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":7,"total_tokens":12}}',
            "data: [DONE]",
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_instance.stream.return_value.__aenter__.return_value = (
                self._stream_response(lines)
            )

            from app.services.groq_service import GroqService

            service = GroqService(
                api_key="gsk_test", usage_recorder=recorder, user_id="user-1"
            )
            chunks = []
            async for chunk in service.get_coaching_response(
                problem="Test",
                code="x",
                language="python",
                message="h",
                mode="hint",
                difficulty="medium",
            ):
                chunks.append(chunk)

        assert chunks == ["Hello", " world"]
        assert recorder.calls == [
            {
                "user_id": "user-1",
                "provider": "groq",
                "model": "llama-3.1-8b-instant",
                "endpoint": "coach_stream",
                "input_tokens": 5,
                "output_tokens": 7,
            }
        ]

    @pytest.mark.asyncio
    async def test_stream_sends_include_usage_option(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_instance.stream.return_value.__aenter__.return_value = (
                self._stream_response(
                    ['data: {"choices":[{"delta":{"content":"hi"}}]}', "data: [DONE]"]
                )
            )

            from app.services.groq_service import GroqService

            service = GroqService(api_key="gsk_test")
            async for _ in service.get_coaching_response(
                problem="T",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="hard",
            ):
                pass

        call = mock_instance.stream.call_args
        assert call.kwargs["json"]["stream"] is True
        assert call.kwargs["json"]["stream_options"] == {"include_usage": True}
        assert call.kwargs["json"]["model"] == "llama-3.1-8b-instant"

    @pytest.mark.asyncio
    async def test_stream_429_maps_to_429(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"retry-after": "10"}
            mock_response.aiter_lines = AsyncMock(return_value=iter([]))

            async def aread():
                return b"rate limited"

            mock_response.aread = aread
            mock_instance.stream.return_value.__aenter__.return_value = mock_response

            from app.services.groq_service import GroqService

            service = GroqService(api_key="gsk_test")
            with pytest.raises(HTTPException) as exc:
                async for _ in service.get_coaching_response(
                    problem="T",
                    code="c",
                    language="python",
                    message="m",
                    mode="hint",
                    difficulty="easy",
                ):
                    pass

        assert exc.value.status_code == 429
        assert exc.value.headers["Retry-After"] == "10"

    @pytest.mark.asyncio
    async def test_stream_no_usage_chunk_does_not_record(self):
        recorder = FakeRecorder()
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_instance.stream.return_value.__aenter__.return_value = (
                self._stream_response(
                    ['data: {"choices":[{"delta":{"content":"hi"}}]}', "data: [DONE]"]
                )
            )

            from app.services.groq_service import GroqService

            service = GroqService(
                api_key="gsk_test", usage_recorder=recorder, user_id="u"
            )
            async for _ in service.get_coaching_response(
                problem="T",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="easy",
            ):
                pass

        assert recorder.calls == []
