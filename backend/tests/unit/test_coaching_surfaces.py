"""Unit: two AI surfaces — questions (graph-aware) vs learn (graph-free).

Red phase for the dual-mode coaching split:
- `surface` discriminator on CoachingRequest (default "questions", back-compat)
- Learn persona is a distinct curriculum companion, never the interview tutor
- Learn prompts never carry skill-graph blocks (defense in depth)
- Learn uses the cheap model tier; cache keys are isolated per surface
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.adapters.coaching_prompts import PromptBuilder


def _coaching_request(**overrides):
    from app.models.schemas import CoachingRequest

    base = {
        "problem": "Two Sum",
        "code": "def f(): pass",
        "language": "python",
        "message": "help",
        "mode": "hint",
    }
    base.update(overrides)
    return CoachingRequest(**base)


class TestCoachingSurfaceSchema:
    def test_surface_defaults_to_questions(self):
        req = _coaching_request()
        assert req.surface == "questions"

    def test_surface_accepts_learn(self):
        req = _coaching_request(surface="learn", lesson_context="Loops 101")
        assert req.surface == "learn"

    def test_surface_rejects_unknown(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _coaching_request(surface="interview")

    def test_learn_requires_lesson_context(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _coaching_request(surface="learn")

    def test_questions_does_not_require_lesson_context(self):
        req = _coaching_request(surface="questions")
        assert req.lesson_context is None


class TestLearnPersona:
    def test_learn_uses_companion_persona_not_interview_tutor(self):
        system, _ = PromptBuilder().build(
            mode="explain",
            language="python",
            problem="Loops",
            code="for i in x: pass",
            message="what is a loop?",
            structured=True,
            lesson_context="Loops 101",
            surface="learn",
        )
        assert "Learn Companion" in system
        assert "Socratic coding interview tutor" not in system

    def test_learn_scopes_to_lesson_and_checks_understanding(self):
        system, _ = PromptBuilder().build(
            mode="explain",
            language="python",
            problem="Loops",
            code="for i in x: pass",
            message="what is a loop?",
            structured=True,
            lesson_context="Loops 101",
            surface="learn",
        )
        assert "Loops 101" in system
        assert "check" in system.lower()

    def test_learn_never_carries_skill_graph_blocks(self):
        system, _ = PromptBuilder().build(
            mode="explain",
            language="python",
            problem="Loops",
            code="c",
            message="m",
            structured=True,
            lesson_context="Loops 101",
            surface="learn",
            learner_context="## Learner Skill Context\n- arrays: mastery 0.10",
            submission_context="## Recent Attempts\n- q1 failed",
        )
        assert "Learner Skill Context" not in system
        assert "Recent Attempts" not in system
        assert "mastery 0.10" not in system

    def test_questions_keeps_socratic_persona_and_graph_blocks(self):
        system, _ = PromptBuilder().build(
            mode="hint",
            language="python",
            problem="Two Sum",
            code="c",
            message="m",
            structured=True,
            surface="questions",
            learner_context="## Learner Skill Context\n- arrays: mastery 0.10",
            submission_context="## Recent Attempts\n- q1 failed",
        )
        assert "Socratic" in system
        assert "Learner Skill Context" in system
        assert "Recent Attempts" in system

    def test_default_surface_is_questions_persona(self):
        system, _ = PromptBuilder().build(
            mode="hint",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
        )
        assert "Socratic" in system
        assert "Learn Companion" not in system


STRUCTURED_CONTENT = (
    '{"summary": "Great work?", "hints": [], "code_review": null, '
    '"complexity_analysis": null, "suggestions": [], "edge_cases": [], '
    '"explanation": null, "debug_help": null}'
)


def _mock_groq_post(mock_async_client, body=None):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = body or {
        "choices": [{"message": {"content": STRUCTURED_CONTENT}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }
    mock_async_client.post.return_value = mock_response


class TestGroqSurfaceBehavior:
    @pytest.mark.asyncio
    async def test_learn_uses_cheap_model_tier(self):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_cls.return_value = mock_instance
            _mock_groq_post(mock_instance)

            from app.services.groq_service import GroqService

            service = GroqService(api_key="gsk_test")
            await service.get_structured_coaching_response(
                problem="Loops",
                code="c",
                language="python",
                message="m",
                mode="explain",
                difficulty="hard",
                lesson_context="Loops 101",
                surface="learn",
            )
            call = mock_instance.post.call_args
            assert call.kwargs["json"]["model"] == "openai/gpt-oss-20b"

    @pytest.mark.asyncio
    async def test_questions_keeps_difficulty_tier(self):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_cls.return_value = mock_instance
            _mock_groq_post(mock_instance)

            from app.services.groq_service import GroqService

            service = GroqService(api_key="gsk_test")
            await service.get_structured_coaching_response(
                problem="Two Sum",
                code="c",
                language="python",
                message="m",
                mode="hint",
                difficulty="hard",
                surface="questions",
            )
            call = mock_instance.post.call_args
            assert call.kwargs["json"]["model"] == "openai/gpt-oss-120b"

    @pytest.mark.asyncio
    async def test_cache_keys_isolated_per_surface(self):
        seen_keys: list[str] = []

        class RecordingCache:
            async def get(self, key):
                seen_keys.append(key)
                return None

            async def set(self, key, value, ttl=0):
                pass

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_cls.return_value = mock_instance
            _mock_groq_post(mock_instance)

            from app.services.groq_service import GroqService

            for surface in ("questions", "learn"):
                service = GroqService(api_key="gsk_test", cache=RecordingCache())
                await service.get_structured_coaching_response(
                    problem="P",
                    code="c",
                    language="python",
                    message="m",
                    mode="hint",
                    difficulty="medium",
                    lesson_context="Loops 101",
                    surface=surface,
                )
        assert len(seen_keys) == 2
        assert seen_keys[0] != seen_keys[1]
