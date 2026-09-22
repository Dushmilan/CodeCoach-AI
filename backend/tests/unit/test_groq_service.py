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

    def __init__(self, cached_value=None, fail_set=False):
        self.cached_value = cached_value
        self.fail_set = fail_set
        self.set_calls = []

    async def get(self, key):
        return self.cached_value

    async def set(self, key, value, ttl=0):
        if self.fail_set:
            raise RuntimeError("redis down")
        self.set_calls.append((key, value, ttl))


class RaisingRecorder:
    """Recorder whose record() always raises — metering must be best-effort."""

    async def record(self, **kwargs):
        raise RuntimeError("db down")


STRUCTURED_CONTENT = (
    '{"summary": "Great work", "hints": [], "code_review": null, '
    '"complexity_analysis": null, "suggestions": [], "edge_cases": [], '
    '"explanation": null, "debug_help": null}'
)

STRUCTURED_CONTENT_WITH_ANIMATION = (
    '{"summary": "Watch the search unfold", "hints": [], "code_review": null, '
    '"complexity_analysis": null, "suggestions": [], "edge_cases": [], '
    '"explanation": null, "debug_help": null, '
    '"animation": {"title": "Searching for 4", '
    '"data": {"values": [5, 1, 2, 3, 4, 6], "target": 4}, '
    '"steps": [{"narration": "5 is not the target.", '
    '"shapes": [{"id": "cell_0", "type": "rect", "x": -240, "y": 0, '
    '"width": 88, "height": 88, "fill": "#1e293b"}], '
    '"motion": [{"target": "cell_0", "op": "appear", "duration": 0.3}]}, '
    '{"narration": "Moving on.", '
    '"motion": [{"target": "cell_0", "op": "move", "to": [0, 0], '
    '"duration": 0.3}]}, '
    '{"narration": "Found 4!", '
    '"shapes": [{"id": "ptr", "type": "polygon", "x": 0, "y": -80, '
    '"points": [[-12, -30], [0, -60], [12, -30]], "fill": "#facc15"}], '
    '"motion": [{"target": "ptr", "op": "appear", "duration": 0.3}, '
    '{"target": "cell_0", "op": "fill", "to": "#22c55e", "duration": 0.3}]}]}}'
)

LEGACY_CACHED_ANIMATION = {
    "summary": "cached legacy",
    "hints": [],
    "animation": {
        "type": "linear_search",
        "title": "Your code vs the solution",
        "steps": [{"operation": "compare_code", "narration": "x"}],
    },
}

VALID_CACHED_ANIMATION = {
    "summary": "cached",
    "hints": [],
    "animation": {
        "title": "Searching for 4",
        "data": {"values": [5, 1, 2, 3, 4, 6], "target": 4},
        "steps": [
            {
                "narration": "a",
                "shapes": [
                    {"id": "c", "type": "rect", "width": 10, "height": 10},
                    {"id": "d", "type": "rect", "width": 10, "height": 10},
                ],
                "motion": [{"target": "c", "op": "appear", "duration": 0.3}],
            },
            {
                "narration": "b",
                "motion": [
                    {"target": "c", "op": "move", "to": [10, 0], "duration": 0.3}
                ],
            },
            {
                "narration": "c",
                "motion": [
                    {"target": "d", "op": "fill", "to": "#22c55e", "duration": 0.3}
                ],
            },
        ],
    },
}


class TestGroqServiceInit:
    @staticmethod
    def _settings_double(**overrides):
        from types import SimpleNamespace

        base = {
            "GROQ_API_KEY": "gsk_test",
            "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
            "GROQ_MODEL_EASY": "openai/gpt-oss-20b",
            "GROQ_MODEL_MEDIUM": "openai/gpt-oss-120b",
            "GROQ_MODEL_HARD": "openai/gpt-oss-120b",
            "GROQ_MODEL_STREAM": "openai/gpt-oss-20b",
            "GROQ_MODEL_ANIMATE": "openai/gpt-oss-120b",
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    def test_init_with_api_key_arg(self):
        from app.services.groq_service import GroqService

        settings = self._settings_double(GROQ_API_KEY=None)
        with patch("app.services.groq_service.get_settings", return_value=settings):
            service = GroqService(api_key="gsk_test_key_12345")
            assert service.api_key == "gsk_test_key_12345"
            assert service.base_url == "https://api.groq.com/openai/v1"

    def test_init_with_env_var(self):
        from app.services.groq_service import GroqService

        settings = self._settings_double(GROQ_API_KEY="gsk_from_env")
        with patch("app.services.groq_service.get_settings", return_value=settings):
            service = GroqService()
            assert service.api_key == "gsk_from_env"

    def test_init_without_key_raises(self):
        from app.services.groq_service import GroqService

        settings = self._settings_double(GROQ_API_KEY=None)
        with patch("app.services.groq_service.get_settings", return_value=settings):
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                GroqService()

    def test_model_map_defaults(self):
        from app.services.groq_service import GroqService

        settings = self._settings_double()
        with patch("app.services.groq_service.get_settings", return_value=settings):
            service = GroqService()
            assert service.models["easy"] == "openai/gpt-oss-20b"
            assert service.models["medium"] == "openai/gpt-oss-120b"
            assert service.models["hard"] == "openai/gpt-oss-120b"
            assert service.models["stream"] == "openai/gpt-oss-20b"
            assert service.models["animate"] == "openai/gpt-oss-120b"

    def test_model_map_env_overrides(self):
        from app.services.groq_service import GroqService

        settings = self._settings_double(
            GROQ_MODEL_EASY="custom-easy",
            GROQ_MODEL_MEDIUM="custom-medium",
            GROQ_MODEL_ANIMATE="custom-animate",
        )
        with patch("app.services.groq_service.get_settings", return_value=settings):
            service = GroqService()
            assert service.models["easy"] == "custom-easy"
            assert service.models["medium"] == "custom-medium"
            assert service.models["hard"] == "openai/gpt-oss-120b"
            assert service.models["animate"] == "custom-animate"


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
                "model": "openai/gpt-oss-120b",
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
        assert call.kwargs["json"]["model"] == "openai/gpt-oss-20b"
        assert recorder.calls[0]["model"] == "openai/gpt-oss-20b"

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
        assert call.kwargs["json"]["model"] == "openai/gpt-oss-120b"

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
    async def test_animate_cache_hit_with_valid_animation_skips_api(
        self, mock_async_client
    ):
        cache = FakeCache(cached_value=VALID_CACHED_ANIMATION)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", cache=cache, user_id="u")
        result = await service.get_structured_coaching_response(
            problem="Find 4",
            code="def s(): pass",
            language="python",
            message="animate",
            mode="animate",
            difficulty="easy",
        )

        mock_async_client.post.assert_not_called()
        assert result["animation"]["title"] == "Searching for 4"

    @pytest.mark.asyncio
    async def test_animate_cache_hit_with_legacy_animation_regenerates(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)
        cache = FakeCache(cached_value=LEGACY_CACHED_ANIMATION)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", cache=cache, user_id="u")
        result = await service.get_structured_coaching_response(
            problem="Find 4",
            code="def s(): pass",
            language="python",
            message="animate",
            mode="animate",
            difficulty="easy",
        )

        mock_async_client.post.assert_called_once()
        assert result["animation"]["title"] == "Searching for 4"
        assert result["animation"]["steps"][0]["shapes"][0]["id"] == "cell_0"

    @pytest.mark.asyncio
    async def test_animate_cache_key_includes_content_version_v8(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)
        cache = FakeCache()

        from app.services.groq_service import GroqService
        from app.services.groq_service import _jsonable
        from app.services.redis_service import RedisCache, _content_hash

        service = GroqService(api_key="gsk_test", cache=cache, user_id="u")
        await service.get_structured_coaching_response(
            problem="P",
            code="c",
            language="python",
            message="animate",
            mode="animate",
            difficulty="medium",
        )

        expected_hash = _content_hash(
            "P",
            "c",
            "animate",
            "animate",
            "medium",
            "",
            "",
            _jsonable(None),
            "questions",
            "v8",
        )
        assert cache.set_calls[0][0] == RedisCache.key(
            "groq", "coaching", expected_hash
        )

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

    @pytest.mark.asyncio
    async def test_structured_no_choices_maps_to_500(self, mock_async_client):
        body = {"choices": [], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
        mock_async_client.post.return_value = self._make_response(200, body)

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
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_structured_empty_content_uses_fallback(self, mock_async_client):
        body = {"choices": [{"message": {"content": ""}}]}
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert isinstance(result["summary"], str)
        assert isinstance(result["hints"], list)

    @pytest.mark.asyncio
    async def test_structured_schema_mismatch_is_repaired(self, mock_async_client):
        recorder = FakeRecorder()
        body = {
            "choices": [{"message": {"content": '{"hints": "not-a-list"}'}}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 9},
        }
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
        assert isinstance(result["summary"], str)
        assert isinstance(result["hints"], list)
        assert result["hints"] == []
        assert recorder.calls[0]["input_tokens"] == 7

    @pytest.mark.asyncio
    async def test_structured_schema_mismatch_nonstring_summary_repaired(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": '{"summary": {"nested": true}}'}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert isinstance(result["summary"], str)

    @pytest.mark.asyncio
    async def test_structured_usage_missing_prompt_tokens(self, mock_async_client):
        recorder = FakeRecorder()
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"completion_tokens": 5},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", usage_recorder=recorder, user_id="u")
        await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert recorder.calls[0]["input_tokens"] == 0
        assert recorder.calls[0]["output_tokens"] == 5

    @pytest.mark.asyncio
    async def test_structured_usage_missing_completion_tokens(self, mock_async_client):
        recorder = FakeRecorder()
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 12},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", usage_recorder=recorder, user_id="u")
        await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert recorder.calls[0]["input_tokens"] == 12
        assert recorder.calls[0]["output_tokens"] == 0

    @pytest.mark.asyncio
    async def test_structured_string_tokens_are_coerced(self, mock_async_client):
        recorder = FakeRecorder()
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": "10", "completion_tokens": "5"},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", usage_recorder=recorder, user_id="u")
        await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert recorder.calls[0]["input_tokens"] == 10
        assert recorder.calls[0]["output_tokens"] == 5

    @pytest.mark.asyncio
    async def test_structured_recorder_failure_does_not_break_response(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(
            api_key="gsk_test", usage_recorder=RaisingRecorder(), user_id="u"
        )
        result = await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert result["summary"] == "Great work"

    @pytest.mark.asyncio
    async def test_structured_429_without_retry_after_defaults_to_60(
        self, mock_async_client
    ):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "rate limited"
        mock_response.headers = {}
        mock_async_client.post.return_value = mock_response

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
        assert exc.value.headers["Retry-After"] == "60"

    @pytest.mark.asyncio
    async def test_structured_cache_write_failure_does_not_break(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        mock_async_client.post.return_value = self._make_response(200, body)
        cache = FakeCache(cached_value=None, fail_set=True)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", cache=cache)
        result = await service.get_structured_coaching_response(
            problem="T",
            code="c",
            language="python",
            message="m",
            mode="hint",
            difficulty="easy",
        )
        assert result["summary"] == "Great work"


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
                "model": "openai/gpt-oss-20b",
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
        assert call.kwargs["json"]["model"] == "openai/gpt-oss-20b"

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

    @pytest.mark.asyncio
    async def test_stream_ignores_heartbeat_and_malformed_lines(self):
        recorder = FakeRecorder()
        lines = [
            ": keep-alive comment line",
            "data: {malformed json",
            'data: {"choices":[{"delta":{}}]}',
            'data: {"choices":[{"delta":{"content":"ok"}}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":4}}',
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
                api_key="gsk_test", usage_recorder=recorder, user_id="u"
            )
            chunks = []
            async for chunk in service.get_coaching_response(
                problem="T",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="easy",
            ):
                chunks.append(chunk)

        assert chunks == ["ok"]
        assert recorder.calls[0]["input_tokens"] == 3
        assert recorder.calls[0]["output_tokens"] == 4

    @pytest.mark.asyncio
    async def test_stream_chunk_with_content_and_usage_both_handled(self):
        recorder = FakeRecorder()
        lines = [
            'data: {"choices":[{"delta":{"content":"hi"}}],"usage":{"prompt_tokens":2,"completion_tokens":6}}',
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
                api_key="gsk_test", usage_recorder=recorder, user_id="u"
            )
            chunks = []
            async for chunk in service.get_coaching_response(
                problem="T",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="easy",
            ):
                chunks.append(chunk)

        assert chunks == ["hi"]
        assert recorder.calls[0]["input_tokens"] == 2
        assert recorder.calls[0]["output_tokens"] == 6


class TestGroqServiceAnimateScript:
    """get_animation_script returns only the validated animation, no chat text."""

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
    async def test_returns_valid_animation_script(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", user_id="u")
        result = await service.get_animation_script(
            problem="Find 4",
            code="def s(): pass",
            language="python",
        )

        assert result is not None
        assert result["title"] == "Searching for 4"
        assert result["data"]["target"] == 4
        assert len(result["steps"]) == 3
        assert result["steps"][0]["shapes"][0]["id"] == "cell_0"
        # Never leaks chat text
        assert "summary" not in result

    @pytest.mark.asyncio
    async def test_returns_none_when_model_omits_animation(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", user_id="u")
        result = await service.get_animation_script(
            problem="Find 4",
            code="def s(): pass",
            language="python",
        )

        assert result is None
        # The Animate endpoint must not burn a second Groq call on a retry.
        assert mock_async_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_none_when_animation_invalid(self, mock_async_client):
        invalid = (
            '{"summary": "x", "hints": [], "code_review": null, '
            '"complexity_analysis": null, "suggestions": [], "edge_cases": [], '
            '"explanation": null, "debug_help": null, '
            '"animation": {"title": "broken", "data": {}, "steps": []}}'
        )
        body = {
            "choices": [{"message": {"content": invalid}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", user_id="u")
        result = await service.get_animation_script(
            problem="Find 2",
            code="def s(): pass",
            language="python",
        )

        assert result is None
        assert mock_async_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_when_first_animation_attempt_omits_animation(
        self, mock_async_client
    ):
        no_anim = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        with_anim = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        # A second response exists only to prove the endpoint does not retry.
        mock_async_client.post.side_effect = [
            self._make_response(200, no_anim),
            self._make_response(200, with_anim),
        ]

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", user_id="u")
        result = await service.get_animation_script(
            problem="Find 4",
            code="def s(): pass",
            language="python",
        )

        assert result is None
        assert mock_async_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_animate_uses_dedicated_animation_model(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(
            api_key="gsk_test", usage_recorder=FakeRecorder(), user_id="u"
        )
        await service.get_animation_script(
            problem="Find 4",
            code="def s(): pass",
            language="python",
            difficulty="easy",
        )

        call = mock_async_client.post.call_args
        # Animate needs a capable model regardless of problem difficulty; it
        # must never fall back to the fast 8b model.
        assert call.kwargs["json"]["model"] == "openai/gpt-oss-120b"

    @pytest.mark.asyncio
    async def test_animate_payload_uses_raised_max_completion_tokens(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", user_id="u")
        await service.get_animation_script(
            problem="Find 4",
            code="def s(): pass",
            language="python",
        )

        payload = mock_async_client.post.call_args.kwargs["json"]
        # code_comparison JSON is long; 1000 tokens truncates it into a
        # brace-repaired response with no usable animation.
        assert payload["max_completion_tokens"] == 2000


VALID_ANIMATED_CODE = "def add(a, b):\n    return a + b\n"

WRONG_ANIMATED_CODE = "def add(a, b):\n    return a - b\n"

CUSTOM_ADD_QUESTION = {
    "title": "Custom: pairwise total",
    "description": "Given two integers a and b, return their total.",
    "examples": [{"input": {"a": 2, "b": 3}, "output": "5"}],
}

BANK_TWO_SUM_QUESTION = {
    "title": "Two Sum",
    "description": (
        "Given an array of integers nums and an integer target, "
        "return indices of the two numbers that add up to target."
    ),
    "examples": [{"input": "[2, 7, 11, 15], 9", "output": "[0, 1]"}],
}


def _anim_content(animated_code):
    import json as _json

    return _json.dumps(
        {
            "summary": "Watch the addition unfold?",
            "hints": [],
            "code_review": None,
            "complexity_analysis": None,
            "suggestions": [],
            "edge_cases": [],
            "explanation": None,
            "debug_help": None,
            "animation": {
                "title": "Adding 2 and 3",
                "animated_code": animated_code,
                "data": {"values": [2, 3]},
                "steps": [
                    {
                        "narration": "a",
                        "shapes": [
                            {"id": "c", "type": "rect", "width": 10, "height": 10},
                            {"id": "d", "type": "rect", "width": 10, "height": 10},
                        ],
                        "motion": [{"target": "c", "op": "appear", "duration": 0.3}],
                    },
                    {
                        "narration": "b",
                        "motion": [
                            {
                                "target": "c",
                                "op": "move",
                                "to": [10, 0],
                                "duration": 0.3,
                            }
                        ],
                    },
                    {
                        "narration": "c",
                        "motion": [
                            {
                                "target": "d",
                                "op": "fill",
                                "to": "#22c55e",
                                "duration": 0.3,
                            }
                        ],
                    },
                ],
            },
        }
    )


class LocalExecExecutor:
    """Test double that really executes the shadow driver locally."""

    async def execute(self, language, code, stdin="", version=None):
        import io
        import contextlib
        from app.ports.code_executor import ExecutionResult

        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(code, "<shadow>", "exec"), {})
        except Exception as e:  # noqa: BLE001
            return ExecutionResult(
                stdout="", stderr=str(e), exit_code=1, language=language
            )
        return ExecutionResult(
            stdout=buf.getvalue(), stderr="", exit_code=0, language=language
        )

    async def evaluate_suite(self, language, code, test_cases):
        return []

    async def get_runtimes(self):
        return []


class TestAnimateReferenceAnchor:
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
    async def test_bank_question_injects_resolved_canonical_code(
        self, mock_async_client
    ):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService
        from app.services.reference_solutions import REFERENCE_SOLUTIONS
        import json as _json

        service = GroqService(api_key="gsk_test")
        await service.get_structured_coaching_response(
            problem="Two Sum: Given an array of integers nums and an integer "
            "target, return indices of the two numbers that add up to target.",
            code="def f(): pass",
            language="python",
            message="animate",
            mode="animate",
            difficulty="medium",
            question=BANK_TWO_SUM_QUESTION,
        )

        sent = mock_async_client.post.call_args.kwargs["json"]
        user_data = _json.loads(sent["messages"][-1]["content"])
        assert (
            user_data["verified_optimal_code"] == REFERENCE_SOLUTIONS["two_sum"]["code"]
        )

    @pytest.mark.asyncio
    async def test_hidden_test_cases_never_sent_with_anchor(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": STRUCTURED_CONTENT_WITH_ANIMATION}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService
        import json as _json

        service = GroqService(api_key="gsk_test")
        question = dict(BANK_TWO_SUM_QUESTION)
        question["test_cases"] = [{"input": "top-secret", "output": "x"}]
        await service.get_structured_coaching_response(
            problem="Two Sum problem",
            code="def f(): pass",
            language="python",
            message="animate",
            mode="animate",
            difficulty="medium",
            question=question,
        )

        sent = mock_async_client.post.call_args.kwargs["json"]
        raw = sent["messages"][-1]["content"]
        assert "top-secret" not in raw
        user_data = _json.loads(raw)
        assert "test_cases" not in user_data["question"]


class TestAnimateShadowCheck:
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
    async def test_matching_code_passes_with_single_call(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": _anim_content(VALID_ANIMATED_CODE)}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", executor=LocalExecExecutor())
        result = await service.get_structured_coaching_response(
            problem="Custom: pairwise total",
            code="def f(): pass",
            language="python",
            message="animate",
            mode="animate",
            difficulty="medium",
            question=CUSTOM_ADD_QUESTION,
        )

        assert mock_async_client.post.call_count == 1
        assert result["animation"]["title"] == "Adding 2 and 3"

    @pytest.mark.asyncio
    async def test_wrong_code_rejected_and_retried_once(self, mock_async_client):
        bodies = [
            {
                "choices": [
                    {"message": {"content": _anim_content(WRONG_ANIMATED_CODE)}}
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 8},
            },
            {
                "choices": [
                    {"message": {"content": _anim_content(WRONG_ANIMATED_CODE)}}
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 8},
            },
        ]
        mock_async_client.post.side_effect = [
            self._make_response(200, bodies[0]),
            self._make_response(200, bodies[1]),
        ]

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test", executor=LocalExecExecutor())
        result = await service.get_structured_coaching_response(
            problem="Custom: pairwise total",
            code="def f(): pass",
            language="python",
            message="animate",
            mode="animate",
            difficulty="medium",
            question=CUSTOM_ADD_QUESTION,
        )

        # Retried exactly once, then the bad animation is dropped, not shown.
        assert mock_async_client.post.call_count == 2
        assert "animation" not in result
        assert isinstance(result["summary"], str)
        # The retry re-prompts at temperature 0.0 with the failure reason.
        retry_payload = mock_async_client.post.call_args_list[1].kwargs["json"]
        assert retry_payload["temperature"] == 0.0
        assert "shadow" in retry_payload["messages"][-1]["content"].lower()

    @pytest.mark.asyncio
    async def test_no_executor_skips_shadow_check(self, mock_async_client):
        body = {
            "choices": [{"message": {"content": _anim_content(WRONG_ANIMATED_CODE)}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        }
        mock_async_client.post.return_value = self._make_response(200, body)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="Custom: pairwise total",
            code="def f(): pass",
            language="python",
            message="animate",
            mode="animate",
            difficulty="medium",
            question=CUSTOM_ADD_QUESTION,
        )

        assert mock_async_client.post.call_count == 1
        assert result["animation"]["title"] == "Adding 2 and 3"
