import json
import logging
import os
from typing import AsyncIterator, Dict, Any, Optional

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.adapters.coaching_prompts import PromptBuilder
from app.adapters.coaching_response_parser import CoachingResponseParser
from app.ports.coaching_provider import CoachingProvider
from app.services.animation_validator import AnimationValidator
from app.services.redis_service import RedisCache, _content_hash

logger = logging.getLogger(__name__)


def _jsonable(value: Optional[Dict[str, Any]]) -> str:
    """Deterministic string form of an optional payload, for cache keys."""
    if value is None:
        return ""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class GroqService(CoachingProvider):
    """Groq adapter for AI coaching (OpenAI-compatible chat completions)."""

    BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_MODELS = {
        "easy": "openai/gpt-oss-20b",
        "medium": "openai/gpt-oss-120b",
        "hard": "openai/gpt-oss-120b",
        "stream": "openai/gpt-oss-20b",
        "animate": "openai/gpt-oss-120b",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[RedisCache] = None,
        usage_recorder: Any = None,
        user_id: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.error("GROQ_API_KEY environment variable is required but not found")
            raise ValueError("GROQ_API_KEY environment variable is required")

        self.cache = cache
        self.usage_recorder = usage_recorder
        self.user_id = user_id
        self.base_url = os.getenv("GROQ_BASE_URL", self.BASE_URL)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        self.models = {
            tier: os.getenv(f"GROQ_MODEL_{tier.upper()}", model)
            for tier, model in self.DEFAULT_MODELS.items()
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
    ) -> Dict[str, Any]:
        from app.models.schemas import StructuredCoachingResponse

        cache_key = None
        if self.cache and not chat_history:
            content_hash = _content_hash(
                problem,
                code,
                message,
                mode,
                difficulty,
                lesson_context or "",
                initial_code or "",
                _jsonable(question),
                "v6",
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
        if mode == "animate":
            model = self.models["animate"]
        else:
            model = self.models.get(difficulty, self.models["medium"])

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
        payload = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
            "temperature": 0.1,
            "top_p": 0.9,
            "stream": False,
        }

        try:
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
                structured_data = self.parser.parse_structured(content)
                structured_data = self._validate_animation(structured_data)
                try:
                    StructuredCoachingResponse(**structured_data)
                except ValidationError as e:
                    logger.warning(
                        "Groq structured response failed schema validation: %s",
                        e,
                    )
                    structured_data = self._repair_structured(structured_data)
                    StructuredCoachingResponse(**structured_data)

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
    ) -> AsyncIterator[str]:
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
    def _validate_animation(data: Dict[str, Any]) -> Dict[str, Any]:
        """Drop invalid animation scripts, keep the rest of the response.

        The generic scene validator enforces structural rules (bounds,
        uniqueness, caps, motion-target resolution) plus the richness floor
        (at least 3 steps, at least 2 shapes, motion in every step). A scene
        that fails them is dropped so the viewer never receives unrenderable
        data — the coaching text still renders, so the student experience
        degrades gracefully instead of showing a broken animation.
        """
        if not data.get("animation"):
            return data
        try:
            animation = data["animation"]
            if GroqService._is_legacy_animation(animation):
                logger.warning(
                    "Dropping legacy-format animation (generic scene required)"
                )
                data.pop("animation", None)
                return data
            validated, reason = AnimationValidator().validate(animation)
        except Exception as e:  # defensive: a bad script must never 500 the endpoint
            logger.warning("Animation validation raised: %s", e)
            data.pop("animation", None)
            return data
        if validated is None:
            logger.warning("Dropping invalid animation script: %s", reason)
            data.pop("animation", None)
        else:
            data["animation"] = validated
        return data

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
