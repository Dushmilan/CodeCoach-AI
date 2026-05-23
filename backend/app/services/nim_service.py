import os
import httpx
import logging
from typing import AsyncIterator, Dict, Any
from fastapi import HTTPException

from app.adapters.coaching_prompts import (
    build_system_prompt,
    build_structured_system_prompt,
    build_user_prompt,
    build_structured_user_prompt,
)
from app.adapters.coaching_response_parser import CoachingResponseParser

logger = logging.getLogger(__name__)


class NIMService:
    """Service for interacting with NVIDIA NIM API for AI coaching."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        logger.info(
            f"Initializing NIMService with API key: {'***' + self.api_key[-4:] if self.api_key else 'None'}"
        )
        if not self.api_key:
            logger.error("NVIDIA_API_KEY environment variable is required but not found")
            raise ValueError("NVIDIA_API_KEY environment variable is required")
        logger.info("NVIDIA_API_KEY successfully loaded")

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

    async def get_structured_coaching_response(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
    ) -> Dict[str, Any]:
        from app.models.schemas import StructuredCoachingResponse

        model = self.models.get(difficulty, self.models["medium"])

        system_prompt = build_structured_system_prompt(mode, language)
        user_prompt = build_structured_user_prompt(problem, code, message, mode)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
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

                return structured_data

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="NVIDIA NIM API timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calling NVIDIA NIM API for structured response: {str(e)}")
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
        structured: bool = False,
    ) -> AsyncIterator[str]:
        model = self.models.get(difficulty, self.models["medium"])

        system_prompt = build_system_prompt(mode, language)
        user_prompt = build_user_prompt(problem, code, message, mode)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
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
