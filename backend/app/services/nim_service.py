import os
import httpx
import logging
from typing import AsyncIterator, Dict, Any, Optional
from fastapi import HTTPException

from app.adapters.coaching_prompts import PromptBuilder
from app.adapters.coaching_response_parser import CoachingResponseParser
from app.ports.coaching_provider import CoachingProvider
from app.services.redis_service import RedisCache, _content_hash

logger = logging.getLogger(__name__)


class NIMService(CoachingProvider):
    """NVIDIA NIM adapter for AI coaching."""

    def __init__(self, api_key: str = None, cache: Optional[RedisCache] = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            logger.error(
                "NVIDIA_API_KEY environment variable is required but not found"
            )
            raise ValueError("NVIDIA_API_KEY environment variable is required")

        self.cache = cache
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        self.models = {
            "easy": "meta/llama-3.1-8b-instruct",
            "medium": "meta/llama-3.1-8b-instruct",
            "hard": "meta/llama-3.1-8b-instruct",
        }

        self.parser = CoachingResponseParser()
        self.prompts = PromptBuilder()

    async def get_structured_coaching_response(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        lesson_context: str = None,
        chat_history: list = None,
    ) -> Dict[str, Any]:
        from app.models.schemas import StructuredCoachingResponse

        cache_key = None
        if self.cache and not chat_history:
            content_hash = _content_hash(
                problem, code, message, mode, difficulty, lesson_context or "", "v2"
            )
            cache_key = RedisCache.key("nim", "coaching", content_hash)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cached

        model = self.models.get(difficulty, self.models["medium"])

        system_prompt, user_prompt = self.prompts.build(
            mode=mode,
            language=language,
            problem=problem,
            code=code,
            message=message,
            structured=True,
            lesson_context=lesson_context,
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
            "max_tokens": 1000,
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
                    error_text = response.text
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"NVIDIA NIM API error: {error_text}",
                    )

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                structured_data = self.parser.parse_structured(content)
                StructuredCoachingResponse(**structured_data)

                if self.cache and cache_key:
                    await self.cache.set(cache_key, structured_data, ttl=86400)

                return structured_data

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="NVIDIA NIM API timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error calling NVIDIA NIM API for structured response: {str(e)}"
            )
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
        lesson_context: str = None,
        structured: bool = False,
        chat_history: list = None,
    ) -> AsyncIterator[str]:
        model = self.models.get(difficulty, self.models["medium"])

        system_prompt, user_prompt = self.prompts.build(
            mode=mode,
            language=language,
            problem=problem,
            code=code,
            message=message,
            structured=False,
            lesson_context=lesson_context,
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
            "max_tokens": 1500,
            "temperature": 0.7,
            "stream": not structured,
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
                        error_text = await response.aread()
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"NVIDIA NIM API error: {error_text.decode()}",
                        )

                    async for line in response.aiter_lines():
                        chunk = self.parser.parse_stream_chunk(line)
                        if chunk:
                            yield chunk

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="NVIDIA NIM API timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calling NVIDIA NIM API: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    # ── CoachingProvider port ──────────────────────────────────────────

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
        ):
            yield chunk
