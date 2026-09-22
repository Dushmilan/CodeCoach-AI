"""Edge-branch tests for #241 (chat animate anchor + shadow-check).

Pins every skip/reject branch so the coverage budget holds for the new
groq_service code. Helpers mirror tests/unit/test_groq_service.py.
"""

import pytest
from fastapi import HTTPException

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


def _anim_dict(animated_code):
    import json as _json

    data = _json.loads(_anim_content(animated_code))
    return data["animation"]


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
        import contextlib
        import io

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


class _RaisingExecutor:
    """Executor double that fails like Piston infra would."""

    def __init__(self, error):
        self.error = error

    async def execute(self, language, code, stdin="", version=None):
        raise self.error


class _ExitCodeExecutor(LocalExecExecutor):
    async def execute(self, language, code, stdin="", version=None):
        from app.ports.code_executor import ExecutionResult

        return ExecutionResult(
            stdout="", stderr="Traceback: boom", exit_code=1, language=language
        )


def _service(executor=LocalExecExecutor()):
    from app.services.groq_service import GroqService

    return GroqService(api_key="gsk_test", executor=executor)


class TestAnimateShadowCheckEdges:
    @pytest.mark.asyncio
    async def test_non_dict_animation_skips(self):
        ok, reason = await _service()._shadow_check_animation(
            ["not-a-dict"], CUSTOM_ADD_QUESTION, None
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_question_without_examples_skips(self):
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict(WRONG_ANIMATED_CODE), {"title": "No examples here"}, None
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_blank_example_input_skips(self):
        question = {"title": "Blank", "examples": [{"input": "   ", "output": "5"}]}
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict(WRONG_ANIMATED_CODE), question, None
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_anchored_question_without_code_skips(self):
        animation = _anim_dict(VALID_ANIMATED_CODE)
        del animation["animated_code"]
        ok, reason = await _service()._shadow_check_animation(
            animation, CUSTOM_ADD_QUESTION, "def add(a, b):\n    return a + b\n"
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_unanchored_question_without_code_rejected(self):
        animation = _anim_dict(VALID_ANIMATED_CODE)
        del animation["animated_code"]
        ok, reason = await _service()._shadow_check_animation(
            animation, CUSTOM_ADD_QUESTION, None
        )
        assert ok is False
        assert "animated_code" in (reason or "")

    @pytest.mark.asyncio
    async def test_syntax_error_rejected(self):
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict("def add(a, b):\n    return a + \n"),
            CUSTOM_ADD_QUESTION,
            None,
        )
        assert ok is False
        assert "does not parse" in (reason or "")

    @pytest.mark.asyncio
    async def test_code_without_function_rejected(self):
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict("X = 1\n"), CUSTOM_ADD_QUESTION, None
        )
        assert ok is False
        assert "no top-level function" in (reason or "")

    @pytest.mark.asyncio
    async def test_method_definition_rejected(self):
        code = "def add(self, a, b):\n    return a + b\n"
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict(code), CUSTOM_ADD_QUESTION, None
        )
        assert ok is False
        assert "self-contained" in (reason or "")

    @pytest.mark.asyncio
    async def test_nested_function_rejected_as_missing(self):
        code = "class A:\n    def add(self, a, b):\n        return a + b\n"
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict(code), CUSTOM_ADD_QUESTION, None
        )
        assert ok is False
        assert "no top-level function" in (reason or "")

    @pytest.mark.asyncio
    async def test_unparseable_input_skips(self, monkeypatch):
        import app.services.animation_inputs as anim_inputs

        def _raise(raw, signature=None):
            raise ValueError("nope")

        monkeypatch.setattr(anim_inputs, "parse_input_kwargs", _raise)
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict(VALID_ANIMATED_CODE), CUSTOM_ADD_QUESTION, None
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_empty_kwargs_skips(self):
        question = {"title": "Empty", "examples": [{"input": {}, "output": "5"}]}
        ok, reason = await _service()._shadow_check_animation(
            _anim_dict(VALID_ANIMATED_CODE), question, None
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_executor_transport_failure_skips(self):
        service = _service(
            _RaisingExecutor(HTTPException(status_code=503, detail="piston down"))
        )
        ok, reason = await service._shadow_check_animation(
            _anim_dict(VALID_ANIMATED_CODE), CUSTOM_ADD_QUESTION, None
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_executor_unexpected_error_skips(self):
        service = _service(_RaisingExecutor(RuntimeError("boom")))
        ok, reason = await service._shadow_check_animation(
            _anim_dict(VALID_ANIMATED_CODE), CUSTOM_ADD_QUESTION, None
        )
        assert (ok, reason) == (True, None)

    @pytest.mark.asyncio
    async def test_nonzero_exit_rejected(self):
        service = _service(_ExitCodeExecutor())
        ok, reason = await service._shadow_check_animation(
            _anim_dict(VALID_ANIMATED_CODE), CUSTOM_ADD_QUESTION, None
        )
        assert ok is False
        assert "raised on the visible example" in (reason or "")


class TestAnimateAnchorEdges:
    def test_resolve_verified_code_missing_entry_returns_none(self, monkeypatch):
        import app.services.groq_service as groq_module

        monkeypatch.setattr(groq_module, "get_reference_solution", lambda algo: None)
        assert (
            groq_module.GroqService._resolve_verified_code(BANK_TWO_SUM_QUESTION)
            is None
        )

    def test_resolve_verified_code_error_returns_none(self, monkeypatch):
        import app.services.groq_service as groq_module

        def _raise(question):
            raise RuntimeError("catalog down")

        monkeypatch.setattr(groq_module, "resolve_algorithm", _raise)
        assert (
            groq_module.GroqService._resolve_verified_code(BANK_TWO_SUM_QUESTION)
            is None
        )

    def test_legacy_non_dict_animation_dropped(self):
        from app.services.groq_service import GroqService

        data, reason = GroqService._validate_animation_checked(
            {"summary": "s", "animation": ["not", "a", "dict"]}
        )
        assert "animation" not in data
        assert "legacy" in (reason or "")

    def test_validation_exception_dropped_with_reason(self, monkeypatch):
        import app.services.groq_service as groq_module

        class _RaisingValidator:
            def validate(self, animation):
                raise RuntimeError("validator boom")

        monkeypatch.setattr(
            groq_module, "AnimationValidator", lambda: _RaisingValidator()
        )
        data, reason = groq_module.GroqService._validate_animation_checked(
            {"summary": "s", "animation": {"title": "t"}}
        )
        assert "animation" not in data
        assert "animation validation raised" in (reason or "")

    @pytest.mark.asyncio
    async def test_retry_transport_failure_keeps_first_attempt(self):
        service = _service()
        fallback_data = {"summary": "first"}
        fallback_result = {"meta": 1}

        async def _raise(messages, model, max_tokens, temperature):
            raise HTTPException(status_code=503, detail="groq down")

        service._fetch_structured = _raise
        data, result = await service._retry_animate(
            [],
            "model",
            10,
            "bad animation",
            CUSTOM_ADD_QUESTION,
            None,
            fallback_data,
            fallback_result,
        )
        assert data == fallback_data
        assert result == fallback_result

    @pytest.mark.asyncio
    async def test_retry_repairs_schema_mismatch(self):
        service = _service()

        async def _invalid(messages, model, max_tokens, temperature):
            return {"bogus": 1}, {"meta": 1}

        service._fetch_structured = _invalid
        data, _ = await service._retry_animate(
            [],
            "model",
            10,
            "bad animation",
            CUSTOM_ADD_QUESTION,
            None,
            {"summary": "first"},
            {"meta": 0},
        )
        assert isinstance(data["summary"], str)
        assert data.get("animation") is None

    def test_normalize_shadow_value_forms(self):
        from app.services.groq_service import GroqService

        assert GroqService._normalize_shadow_value({"a": 1}) == {"a": 1}
        assert GroqService._normalize_shadow_value("  [1, 2]  ") == [1, 2]
        assert GroqService._normalize_shadow_value("plain") == "plain"
        assert GroqService._normalize_shadow_value(7) == 7
