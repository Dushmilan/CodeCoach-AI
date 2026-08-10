"""Unit tests for GroqService — Groq adapter for AI coaching.

Covers: key handling, model mapping, structured usage extraction + recording,
streaming usage extraction + recording, caching (cache hits do not meter),
and Groq error mapping (401/429/timeout).
"""

import json
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
                "request_count": 1,
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


class TestGroqServiceDebriefReport:
    """debrief_report mode must preserve captured Q&A exchanges end-to-end."""

    @pytest.fixture
    def mock_async_client(self):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_cls.return_value = mock_instance
            yield mock_instance

    def _make_response(self, content):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_response.headers = {}
        mock_response.json.return_value = {
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        return mock_response

    def _message(self, exchanges):
        return json.dumps(
            {"problem": "Two Sum", "code": "code()", "exchanges": exchanges}
        )

    @pytest.mark.asyncio
    async def test_preserves_captured_exchanges_when_model_returns_prose(
        self, mock_async_client
    ):
        """Model prose (no JSON) must not blank the report — captured Q&A survives."""
        captured = [
            {"question": "Why a hashmap?", "answer": "For O(1) lookups."},
            {"question": "What about space?", "answer": "Still O(n)."},
        ]
        mock_async_client.post.return_value = self._make_response(
            "Great session! The user explained a hashmap well and mentioned O(1)."
        )

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="Two Sum",
            code="code()",
            language="python",
            message=self._message(captured),
            mode="debrief_report",
            difficulty="medium",
        )

        assert len(result["exchanges"]) == 2
        assert result["exchanges"][0]["question"] == "Why a hashmap?"
        assert result["exchanges"][0]["answer"] == "For O(1) lookups."
        assert result["exchanges"][0]["strengths"] == []
        assert result["exchanges"][0]["improvements"] == []
        assert result["exchanges"][0]["stronger_answer_should_include"] == []
        assert result["takeaway"]

    @pytest.mark.asyncio
    async def test_overlays_partial_model_feedback(self, mock_async_client):
        """Model JSON feedback is overlaid on captured exchanges by index."""
        captured = [
            {"question": "Why a hashmap?", "answer": "For O(1) lookups."},
            {"question": "What about space?", "answer": "Still O(n)."},
        ]
        model_json = json.dumps(
            {
                "summary": "Solid session",
                "exchanges": [
                    {
                        "strengths": ["Right structure"],
                        "improvements": [],
                        "stronger_answer_should_include": ["Mention space"],
                    }
                ],
                "takeaway": "Justify space too.",
            }
        )
        mock_async_client.post.return_value = self._make_response(model_json)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="Two Sum",
            code="code()",
            language="python",
            message=self._message(captured),
            mode="debrief_report",
            difficulty="medium",
        )

        assert result["summary"] == "Solid session"
        assert result["takeaway"] == "Justify space too."
        assert len(result["exchanges"]) == 2
        assert result["exchanges"][0]["strengths"] == ["Right structure"]
        assert result["exchanges"][0]["stronger_answer_should_include"] == [
            "Mention space"
        ]
        assert result["exchanges"][1]["strengths"] == []
        assert result["exchanges"][1]["question"] == "What about space?"

    @pytest.mark.asyncio
    async def test_preserves_ai_feedback_for_wrong_and_unsure_answers(
        self, mock_async_client
    ):
        """Critique/improvement feedback from the model survives repair."""
        captured = [
            {"question": "Why a hashmap?", "answer": "Because arrays are slow."},
            {"question": "What about space?", "answer": "I'm not sure."},
        ]
        model_json = json.dumps(
            {
                "summary": "Mixed session",
                "exchanges": [
                    {
                        "strengths": [],
                        "improvements": ["A hashmap gives O(1) average lookups"],
                        "stronger_answer_should_include": [
                            "Mention amortized O(1) and hashing"
                        ],
                    },
                    {
                        "strengths": [],
                        "improvements": ["Space is O(n) for the hashmap"],
                        "stronger_answer_should_include": ["Talk through the tradeoff"],
                    },
                ],
                "takeaway": "Keep going.",
            }
        )
        mock_async_client.post.return_value = self._make_response(model_json)

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="Two Sum",
            code="code()",
            language="python",
            message=self._message(captured),
            mode="debrief_report",
            difficulty="medium",
        )

        assert result["exchanges"][0]["improvements"] == [
            "A hashmap gives O(1) average lookups"
        ]
        assert result["exchanges"][0]["stronger_answer_should_include"] == [
            "Mention amortized O(1) and hashing"
        ]
        assert result["exchanges"][1]["improvements"] == [
            "Space is O(n) for the hashmap"
        ]
        assert result["exchanges"][1]["question"] == "What about space?"

    @pytest.mark.asyncio
    async def test_debrief_report_records_usage_under_own_endpoint(
        self, mock_async_client
    ):
        """Debrief usage meters tokens under debrief-report and does not count
        as a chat message (request_count=0)."""
        captured = [
            {"question": "Why a hashmap?", "answer": "For O(1) lookups."},
        ]
        mock_async_client.post.return_value = self._make_response(
            json.dumps(
                {
                    "summary": "s",
                    "exchanges": [
                        {
                            "question": "q",
                            "answer": "a",
                            "strengths": [],
                            "improvements": [],
                            "stronger_answer_should_include": [],
                        }
                    ],
                    "takeaway": "t",
                }
            )
        )
        recorder = FakeRecorder()

        from app.services.groq_service import GroqService

        service = GroqService(
            api_key="gsk_test", usage_recorder=recorder, user_id="user-1"
        )
        await service.get_structured_coaching_response(
            problem="P",
            code="c",
            language="python",
            message=self._message(captured),
            mode="debrief_report",
            difficulty="medium",
            endpoint="debrief-report",
        )
        assert recorder.calls == [
            {
                "user_id": "user-1",
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "endpoint": "debrief-report",
                "input_tokens": 1,
                "output_tokens": 1,
                "request_count": 0,
            }
        ]

    @pytest.mark.asyncio
    async def test_requests_json_response_format(self, mock_async_client):
        mock_async_client.post.return_value = self._make_response(
            json.dumps(
                {
                    "summary": "s",
                    "exchanges": [
                        {"question": "q", "answer": "a", "strengths": [], "improvements": [], "stronger_answer_should_include": []}
                    ],
                    "takeaway": "t",
                }
            )
        )

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        await service.get_structured_coaching_response(
            problem="P",
            code="c",
            language="python",
            message=self._message(
                [{"question": "q", "answer": "a"}]
            ),
            mode="debrief_report",
            difficulty="medium",
        )
        call = mock_async_client.post.call_args
        assert call.kwargs["json"]["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_does_not_crash_when_model_returns_json_array(
        self, mock_async_client
    ):
        """A JSON array (not object) from Groq must not 500 — report uses captured Q&A."""
        captured = [
            {"question": "Why a hashmap?", "answer": "For O(1) lookups."},
            {"question": "What about space?", "answer": "Still O(n)."},
        ]
        mock_async_client.post.return_value = self._make_response(
            '[{"summary": "not an object"}]'
        )

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="Two Sum",
            code="code()",
            language="python",
            message=self._message(captured),
            mode="debrief_report",
            difficulty="medium",
        )

        assert len(result["exchanges"]) == 2
        assert result["exchanges"][0]["question"] == "Why a hashmap?"
        assert result["exchanges"][1]["answer"] == "Still O(n)."
        assert result["summary"]
        assert result["takeaway"]

    @pytest.mark.asyncio
    async def test_does_not_crash_when_model_returns_plain_string(
        self, mock_async_client
    ):
        captured = [
            {"question": "Why a hashmap?", "answer": "For O(1) lookups."}
        ]
        mock_async_client.post.return_value = self._make_response('"just prose"')

        from app.services.groq_service import GroqService

        service = GroqService(api_key="gsk_test")
        result = await service.get_structured_coaching_response(
            problem="Two Sum",
            code="code()",
            language="python",
            message=self._message(captured),
            mode="debrief_report",
            difficulty="medium",
        )

        assert len(result["exchanges"]) == 1
        assert result["exchanges"][0]["question"] == "Why a hashmap?"

    def test_repair_non_dict_data_does_not_throw(self):
        """Direct repair call with a list/string must not raise AttributeError."""
        from app.services.groq_service import GroqService

        message = json.dumps(
            {
                "problem": "p",
                "code": "c",
                "exchanges": [{"question": "Q", "answer": "A"}],
            }
        )
        for bad in ([], "string", None, 42):
            result = GroqService._repair_debrief_report(bad, message)
            assert len(result["exchanges"]) == 1
            assert result["exchanges"][0]["question"] == "Q"
            assert result["exchanges"][0]["strengths"] == []

    @pytest.mark.asyncio
    async def test_non_debrief_mode_does_not_crash_on_json_array(
        self, mock_async_client
    ):
        """A JSON array from Groq for hint/senior mode must not 500."""
        mock_async_client.post.return_value = self._make_response(
            '[{"summary": "not an object"}]'
        )

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
        assert isinstance(result, dict)
        assert "summary" in result


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
                "request_count": 1,
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
