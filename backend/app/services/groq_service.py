import ast
import json
import logging
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Dict,
    Any,
    Optional,
    Tuple,
    TYPE_CHECKING,
)

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.adapters.coaching_prompts import PromptBuilder
from app.adapters.coaching_response_parser import CoachingResponseParser
from app.core.config import get_settings
from app.ports.coaching_provider import CoachingProvider
from app.services.animation_validator import AnimationValidator
from app.services.redis_service import RedisCache, _content_hash
from app.services.reference_solutions import get_reference_solution, resolve_algorithm

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids import weight
    from app.ports.code_executor import CodeExecutor

logger = logging.getLogger(__name__)


# One-shot animate self-correction: appended as a follow-up user message when
# the first attempt's animation is missing, malformed, or fails the Piston
# shadow-check. Temperature 0.0 keeps the correction deterministic.
_ANIMATE_RETRY_SUFFIX = (
    "Your previous animate response was rejected for this reason: {reason}. "
    "Return the full JSON response again with a corrected non-null animation "
    "that satisfies the Animate Mode Contract (including the animated_code "
    "field with the exact code the steps choreograph)."
)


def _jsonable(value: Optional[Dict[str, Any]]) -> str:
    """Deterministic string form of an optional payload, for cache keys."""
    if value is None:
        return ""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class GroqService(CoachingProvider):
    """Groq adapter for AI coaching (OpenAI-compatible chat completions)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[RedisCache] = None,
        usage_recorder: Any = None,
        user_id: Optional[str] = None,
        executor: Optional["CodeExecutor"] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            logger.error("GROQ_API_KEY is required but not found in settings")
            raise ValueError("GROQ_API_KEY is required but not set")

        self.cache = cache
        self.usage_recorder = usage_recorder
        self.user_id = user_id
        # Optional Piston-backed executor for the animate-mode shadow-check
        # (#241). When None the check is skipped and any animated_code is
        # trusted as-is (bank questions stay anchored via verified code).
        self.executor = executor
        self.base_url = settings.GROQ_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        self.models = {
            "easy": settings.GROQ_MODEL_EASY,
            "medium": settings.GROQ_MODEL_MEDIUM,
            "hard": settings.GROQ_MODEL_HARD,
            "stream": settings.GROQ_MODEL_STREAM,
            "animate": settings.GROQ_MODEL_ANIMATE,
        }

        self.parser = CoachingResponseParser()
        self.prompts = PromptBuilder()
        self.animation_validator = AnimationValidator()

    async def get_structured_coaching_response(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        chat_history: Optional[list] = None,
        endpoint: str = "coach",
        initial_code: Optional[str] = None,
        question: Optional[Dict[str, Any]] = None,
        learner_context: Optional[str] = None,
        submission_context: Optional[str] = None,
        surface: str = "questions",
        retry_animate: bool = True,
    ) -> Dict[str, Any]:
        """Return a structured coaching dict, validating any animation.

        In animate mode the prompt is anchored to the verified canonical
        solution when the question resolves to one (#241), the emitted
        animated_code is shadow-executed against the visible example, and a
        failed animation triggers exactly one correction retry at
        temperature 0.0. Pass retry_animate=False to disable the retry (the
        standalone Animate endpoint guarantees a single Groq call).
        """
        from app.models.schemas import StructuredCoachingResponse

        cache_key = None
        has_personalization = bool(learner_context or submission_context)
        if self.cache and not chat_history and not has_personalization:
            content_hash = _content_hash(
                problem,
                code,
                message,
                mode,
                difficulty,
                lesson_context or "",
                initial_code or "",
                _jsonable(question),
                surface,
                "v8",
            )
            cache_key = RedisCache.key("groq", "coaching", content_hash)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                if mode == "animate":
                    # Animate cache entries must be revalidated on read: stale
                    # legacy-format or too-thin scripts from older versions would
                    # otherwise reach the viewer as a title-plus-narration frame.
                    cached = self._validate_animation(cached)
                    if cached.get("animation") is None:
                        cached = None
                if cached is not None:
                    return cached

        # Animate embeds full user/solution code arrays plus steps, so it always
        # uses a capable dedicated model rather than the difficulty-tied tier.
        # The Learn companion is a curriculum guide, not an interview tutor, so
        # it always uses the cheap tier regardless of question difficulty.
        if mode == "animate":
            model = self.models["animate"]
        elif surface == "learn":
            model = self.models["easy"]
        else:
            model = self.models.get(difficulty, self.models["medium"])

        # Defense in depth: the Learn surface is graph-free even if a caller
        # passes graph blocks directly.
        if surface == "learn":
            learner_context = None
            submission_context = None

        # Reference anchor (#241): in animate mode resolve the canonical
        # optimal solution and inject its verified code into the prompt so the
        # model choreographs instead of solving. Bank questions resolve via
        # the catalog; anything else falls back to keyword matching on the
        # problem text (the chat route carries no question object).
        verified_optimal_code: Optional[str] = None
        if mode == "animate":
            verified_optimal_code = self._resolve_verified_code(question, problem)

        system_prompt, user_prompt = self.prompts.build(
            mode=mode,
            language=language,
            problem=problem,
            code=code,
            message=message,
            structured=True,
            lesson_context=lesson_context,
            initial_code=initial_code,
            question=question,
            learner_context=learner_context,
            submission_context=submission_context,
            surface=surface,
            verified_optimal_code=verified_optimal_code,
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": user_prompt})

        # Animate responses embed full user/solution code arrays plus steps —
        # 1000 tokens truncates the JSON, and the brace-repair parser then
        # yields no usable animation. Give animate mode a larger budget.
        max_tokens = 2000 if mode == "animate" else 1000

        try:
            structured_data, result = await self._fetch_structured(
                messages, model, max_tokens, temperature=0.1
            )
            structured_data, anim_error = self._validate_animation_checked(
                structured_data
            )
            schema_repaired = False
            try:
                StructuredCoachingResponse(**structured_data)
            except ValidationError as e:
                logger.warning(
                    "Groq structured response failed schema validation: %s",
                    e,
                )
                structured_data = self._repair_structured(structured_data)
                StructuredCoachingResponse(**structured_data)
                schema_repaired = True

            shadow_error: Optional[str] = None
            if (
                mode == "animate"
                and anim_error is None
                and not schema_repaired
                and structured_data.get("animation") is not None
            ):
                ok, shadow_error = await self._shadow_check_animation(
                    structured_data.get("animation"),
                    question,
                    verified_optimal_code,
                )
                if not ok:
                    # A shadow mismatch means the animation shows wrong logic
                    # — it must never reach the viewer.
                    structured_data.pop("animation", None)

            if (
                mode == "animate"
                and retry_animate
                and structured_data.get("animation") is None
            ):
                reason = (
                    anim_error
                    or shadow_error
                    or (
                        "schema repair dropped the animation"
                        if schema_repaired
                        else None
                    )
                    or "the response contained no animation"
                )
                structured_data, result = await self._retry_animate(
                    messages,
                    model,
                    max_tokens,
                    reason,
                    question,
                    verified_optimal_code,
                    structured_data,
                    result,
                )

            if self.cache and cache_key:
                try:
                    await self.cache.set(cache_key, structured_data, ttl=86400)
                except Exception as e:  # pragma: no cover - defensive
                    logger.debug("Failed to write Groq cache: %s", e)

            await self._record_usage(model, result, endpoint)

            return structured_data

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Groq API timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calling Groq API for structured response: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating structured response: {str(e)}",
            )

    async def get_coaching_response(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        structured: bool = False,
        chat_history: Optional[list] = None,
        endpoint: str = "coach_stream",
        initial_code: Optional[str] = None,
        surface: str = "questions",
    ) -> AsyncIterator[str]:
        model = self.models["stream"]

        system_prompt, user_prompt = self.prompts.build(
            mode=mode,
            language=language,
            problem=problem,
            code=code,
            message=message,
            structured=structured,
            lesson_context=lesson_context,
            initial_code=initial_code,
            surface=surface,
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": 1500,
            "temperature": 0.7,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        if structured:
            payload["temperature"] = 0.3

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        self._raise_for_groq_status(
                            response.status_code, response.headers, error_body.decode()
                        )

                    usage: Dict[str, Any] = {}
                    async for line in response.aiter_lines():
                        chunk = self.parser.parse_stream_chunk(line)
                        if chunk:
                            yield chunk
                        stream_usage = self._parse_stream_usage(line)
                        if stream_usage:
                            usage = stream_usage

                    await self._record_usage(model, {"usage": usage}, endpoint)

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Groq API timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_animation_script(
        self,
        problem: str,
        code: str,
        language: str,
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        initial_code: Optional[str] = None,
        question: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return a validated visual algorithm animation (no chat text).

        Backs the standalone Animate viewer endpoint. Returns None when the
        model produces no usable animation so the endpoint can fail cleanly
        instead of rendering a text-only chat response.

        Exactly one Groq request is made: the dedicated animation model is
        expected to follow the Animate contract, and a second attempt would
        both double our provider load and risk a 429 surfacing to the user
        after an already-usable first response.
        """
        structured = await self.get_structured_coaching_response(
            problem=problem,
            code=code,
            language=language,
            message="animate",
            mode="animate",
            difficulty=difficulty,
            lesson_context=lesson_context,
            initial_code=initial_code,
            endpoint="animate",
            question=question,
            retry_animate=False,
        )
        animation = structured.get("animation")
        if animation is None:
            logger.warning(
                "Animate: produced no usable animation (problem=%.80r, language=%s)",
                problem,
                language,
            )
            return None
        return animation

    # ── CoachingProvider port ─────────────────────────────────────────

    async def get_structured(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        chat_history: Optional[list] = None,
        initial_code: Optional[str] = None,
        learner_context: Optional[str] = None,
        submission_context: Optional[str] = None,
        surface: str = "questions",
    ) -> Dict[str, Any]:
        return await self.get_structured_coaching_response(
            problem=problem,
            code=code,
            language=language,
            message=message,
            mode=mode,
            difficulty=difficulty,
            lesson_context=lesson_context,
            chat_history=chat_history,
            initial_code=initial_code,
            learner_context=learner_context,
            submission_context=submission_context,
            surface=surface,
        )

    async def stream(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        chat_history: Optional[list] = None,
        initial_code: Optional[str] = None,
        surface: str = "questions",
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.get_coaching_response(
            problem=problem,
            code=code,
            language=language,
            message=message,
            mode=mode,
            difficulty=difficulty,
            lesson_context=lesson_context,
            chat_history=chat_history,
            initial_code=initial_code,
            surface=surface,
        ):
            yield chunk

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _is_legacy_animation(animation: Any) -> bool:
        """True when the model returned a pre-generic typed animation.

        Legacy animations carry a top-level ``type`` or per-step ``operation``
        fields. They contain no renderable shapes/motion, so they would reach
        the viewer as a title-plus-narration frame — reject them outright.
        """
        if not isinstance(animation, dict):
            return True
        if "type" in animation:
            return True
        steps = animation.get("steps")
        return isinstance(steps, list) and any(
            isinstance(step, dict) and "operation" in step for step in steps
        )

    @staticmethod
    def _validate_animation_checked(
        data: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Drop invalid animation scripts, keep the rest of the response.

        Returns (data, None) on success (or when no animation is present) and
        (data-without-animation, reason) on failure so the animate flow can
        re-prompt once with the reason (#241). The generic scene validator
        enforces structural rules (bounds, uniqueness, caps, motion-target
        resolution) plus the richness floor (at least 3 steps, at least 2
        shapes, motion in every step).
        """
        if not data.get("animation"):
            return data, None
        try:
            animation = data["animation"]
            if GroqService._is_legacy_animation(animation):
                reason = "legacy-format animation (generic scene required)"
                logger.warning("Dropping %s", reason)
                data.pop("animation", None)
                return data, reason
            validated, reason = AnimationValidator().validate(animation)
        except Exception as e:  # defensive: a bad script must never 500 the endpoint
            logger.warning("Animation validation raised: %s", e)
            data.pop("animation", None)
            return data, f"animation validation raised: {e}"
        if validated is None:
            logger.warning("Dropping invalid animation script: %s", reason)
            data.pop("animation", None)
            return data, reason
        data["animation"] = validated
        return data, None

    @staticmethod
    def _validate_animation(data: Dict[str, Any]) -> Dict[str, Any]:
        """Drop invalid animation scripts, keep the rest of the response.

        Backward-compatible wrapper — the animate flow uses
        _validate_animation_checked when it needs the failure reason.
        """
        checked, _ = GroqService._validate_animation_checked(data)
        return checked

    async def _fetch_structured(
        self,
        messages: list,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """POST one chat-completions request and parse the structured dict.

        Raises HTTPException for transport/API failures (mapped by the
        caller) — a retryable failure surfaces, never a silent fallback.
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            if response.status_code != 200:
                self._raise_for_groq_status(
                    response.status_code, response.headers, response.text
                )
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return self.parser.parse_structured(content), result

    @staticmethod
    def _resolve_verified_code(
        question: Optional[Dict[str, Any]], problem: str = ""
    ) -> Optional[str]:
        """Return the verified canonical solution code for animate mode.

        Resolves via resolve_algorithm + get_reference_solution against the
        question when present, else against the problem text (the chat route
        carries no question object, but its problem statement names the
        algorithm for bank questions). Returns None for custom/unknown
        questions — those are covered by the Piston shadow-check instead.
        """
        try:
            anchor: Dict[str, Any]
            if isinstance(question, dict) and question:
                anchor = question
            else:
                anchor = {"title": problem or "", "description": problem or ""}
            algorithm = resolve_algorithm(anchor)
            if not algorithm:
                return None
            entry = get_reference_solution(algorithm)
            if not entry:
                return None
            code = entry.get("code")
            return code if isinstance(code, str) and code.strip() else None
        except Exception:  # defensive: anchoring must never break coaching
            logger.debug("Reference anchor resolution failed", exc_info=True)
            return None

    async def _retry_animate(
        self,
        messages: list,
        model: str,
        max_tokens: int,
        reason: str,
        question: Optional[Dict[str, Any]],
        verified_optimal_code: Optional[str],
        fallback_data: Dict[str, Any],
        fallback_result: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """One-shot animate self-correction at temperature 0.0.

        Re-prompts once with the rejection reason; a second failure keeps the
        coaching text but still drops the animation (never show wrong logic).
        A transport failure on the retry keeps the first attempt's data.
        """
        from app.models.schemas import StructuredCoachingResponse

        retry_messages = list(messages) + [
            {"role": "user", "content": _ANIMATE_RETRY_SUFFIX.format(reason=reason)}
        ]
        try:
            structured_data, result = await self._fetch_structured(
                retry_messages, model, max_tokens, temperature=0.0
            )
        except Exception as e:  # noqa: BLE001 - retry is best-effort
            logger.warning("Animate retry request failed, keeping first attempt: %s", e)
            return fallback_data, fallback_result
        structured_data, _ = self._validate_animation_checked(structured_data)
        try:
            StructuredCoachingResponse(**structured_data)
        except ValidationError:
            structured_data = self._repair_structured(structured_data)
        if structured_data.get("animation") is not None:
            ok, _ = await self._shadow_check_animation(
                structured_data.get("animation"), question, verified_optimal_code
            )
            if not ok:
                structured_data.pop("animation", None)
        return structured_data, result

    async def _shadow_check_animation(
        self,
        animation: Any,
        question: Optional[Dict[str, Any]],
        verified_optimal_code: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Shadow-execute animated_code against the visible example (#241).

        Returns (True, None) when the code reproduces examples[0].output, or
        when the check cannot run (no executor, no visible example, or an
        anchored bank question whose model omitted animated_code — the anchor
        already pins the logic). Returns (False, reason) when the emitted
        code is wrong, so the caller rejects it instead of showing it.
        """
        if not isinstance(animation, dict):
            return True, None
        if self.executor is None:
            return True, None
        examples = None
        if isinstance(question, dict):
            examples = question.get("examples")
        if (
            not isinstance(examples, list)
            or not examples
            or not isinstance(examples[0], dict)
        ):
            return True, None
        raw_input = examples[0].get("input")
        if raw_input is None or (isinstance(raw_input, str) and not raw_input.strip()):
            return True, None
        expected = examples[0].get("output", "")

        code = animation.get("animated_code")
        if not isinstance(code, str) or not code.strip():
            if verified_optimal_code:
                # Anchored bank question: the prompt already pins the logic,
                # so an omitted field is not worth a retry.
                return True, None
            return (
                False,
                "shadow-check setup failed: the animation omits the required "
                "animated_code field holding the code its steps choreograph",
            )

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"shadow-check failed: animated_code does not parse ({e})"
        funcs = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if not funcs:
            return (
                False,
                "shadow-check failed: animated_code defines no top-level "
                "function to execute",
            )
        func = funcs[0]
        if func.args.args and func.args.args[0].arg in ("self", "cls"):
            return (
                False,
                "shadow-check failed: animated_code must be a self-contained "
                "function, not a method",
            )
        params = [arg.arg for arg in func.args.args]
        from app.services.animation_inputs import parse_input_kwargs

        try:
            kwargs = parse_input_kwargs(raw_input, signature=params or None)
        except Exception:  # noqa: BLE001 - unparseable input shape
            logger.debug("Shadow-check input parse failed, skipping", exc_info=True)
            return True, None
        if not kwargs:
            return True, None

        try:
            driver = (
                code
                + "\nimport json as __shadow_json\n"
                + f"__shadow_kwargs = {json.dumps(kwargs, sort_keys=True, default=str)}\n"
                + f"__shadow_result = {func.name}(**__shadow_kwargs)\n"
                + "print(__shadow_json.dumps(__shadow_result, sort_keys=True, default=str))\n"
            )
            exec_result = await self.executor.execute(
                language="python", code=driver, stdin=""
            )
        except HTTPException as e:
            # Transport/infra failure — never punish the model for it.
            logger.warning("Shadow-check execution unavailable: %s", e.detail)
            return True, None
        except Exception:  # noqa: BLE001 - defensive
            logger.warning("Shadow-check execution raised", exc_info=True)
            return True, None
        if exec_result.exit_code != 0:
            stderr = (exec_result.stderr or "")[:200]
            return (
                False,
                f"shadow-check failed: animated_code raised on the visible "
                f"example ({stderr})",
            )
        actual = self._normalize_shadow_value(
            (exec_result.stdout or "").strip().splitlines()[-1]
            if (exec_result.stdout or "").strip()
            else ""
        )
        if actual != self._normalize_shadow_value(expected):
            return (
                False,
                "shadow-check failed: animated_code output "
                f"{actual!r} does not match the visible example output "
                f"{self._normalize_shadow_value(expected)!r}",
            )
        return True, None

    @staticmethod
    def _normalize_shadow_value(value: Any) -> Any:
        """Lenient equality form: JSON-decoded when possible, else stripped."""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            text = value.strip()
            try:
                return json.loads(text)
            except (json.JSONDecodeError, ValueError):
                return text
        return value

    @staticmethod
    def _repair_structured(data: Dict[str, Any]) -> Dict[str, Any]:
        """Repair a schema-mismatched structured dict into a valid shape.

        Called when the model returns valid JSON that fails
        StructuredCoachingResponse validation (e.g. missing summary, wrong
        types). Preserves any usable fields and defaults the rest.
        """
        summary = data.get("summary") or data.get("explanation")
        if not isinstance(summary, str):
            summary = json.dumps(summary) if summary is not None else ""
            summary = summary[:500]
        summary = summary or "Coaching response generated"
        return {
            "summary": summary[:2000],
            "hints": data.get("hints") if isinstance(data.get("hints"), list) else [],
            "code_review": (
                data.get("code_review")
                if isinstance(data.get("code_review"), str)
                else None
            ),
            "complexity_analysis": (
                data.get("complexity_analysis")
                if isinstance(data.get("complexity_analysis"), str)
                else None
            ),
            "suggestions": (
                data.get("suggestions")
                if isinstance(data.get("suggestions"), list)
                else []
            ),
            "edge_cases": (
                data.get("edge_cases")
                if isinstance(data.get("edge_cases"), list)
                else []
            ),
            "explanation": (
                data.get("explanation")
                if isinstance(data.get("explanation"), str)
                else None
            ),
            "debug_help": (
                data.get("debug_help")
                if isinstance(data.get("debug_help"), str)
                else None
            ),
            "animation": None,
        }

    def _raise_for_groq_status(
        self, status_code: int, headers: Any, body: str = ""
    ) -> None:
        """Map Groq HTTP errors to friendly HTTPExceptions."""
        if status_code == 429:
            retry_after = (headers or {}).get("retry-after", "60")
            raise HTTPException(
                status_code=429,
                detail="Groq API rate limit exceeded",
                headers={"Retry-After": retry_after},
            )
        if status_code in (400, 401, 403):
            raise HTTPException(
                status_code=500,
                detail="Groq API key is invalid or unauthorized",
            )
        raise HTTPException(
            status_code=status_code,
            detail=f"Groq API error: {body}",
        )

    @staticmethod
    def _parse_stream_usage(line: str) -> Optional[Dict[str, Any]]:
        """Extract usage from a streamed SSE line (final chunk before [DONE])."""
        if not line.startswith("data: "):
            return None
        data = line[6:]
        if data == "[DONE]":
            return None
        try:
            chunk = json.loads(data)
            usage = chunk.get("usage")
            if isinstance(usage, dict) and usage:
                return usage
        except json.JSONDecodeError:
            pass
        return None

    async def _record_usage(
        self, model: str, result: Dict[str, Any], endpoint: str
    ) -> None:
        """Best-effort token metering — never fails the caller."""
        if not self.usage_recorder or not self.user_id:
            return
        usage = result.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("completion_tokens", 0) or 0)
        if input_tokens == 0 and output_tokens == 0:
            return
        try:
            await self.usage_recorder.record(
                user_id=self.user_id,
                provider="groq",
                model=model,
                endpoint=endpoint,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.debug(f"Failed to record usage: {e}")
