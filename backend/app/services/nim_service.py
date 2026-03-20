import os
import httpx
import json
from typing import AsyncIterator, Dict, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class NIMService:
    """Service for interacting with NVIDIA NIM API for AI coaching."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        logger.info(f"Initializing NIMService with API key: {'***' + self.api_key[-4:] if self.api_key else 'None'}")
        if not self.api_key:
            logger.error("NVIDIA_API_KEY environment variable is required but not found")
            raise ValueError("NVIDIA_API_KEY environment variable is required")
        logger.info("NVIDIA_API_KEY successfully loaded")
        
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Model routing based on problem complexity
        # Using meta/llama-3.1-8b-instruct for faster responses
        self.models = {
            "easy": "meta/llama-3.1-8b-instruct",
            "medium": "meta/llama-3.1-8b-instruct",
            "hard": "meta/llama-3.1-8b-instruct"
        }
    
    async def get_coaching_response(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium"
    ) -> AsyncIterator[str]:
        """
        Get streaming AI coaching response from NVIDIA NIM.
        
        Args:
            problem: The coding problem description
            code: User's current code attempt
            language: Programming language (python, javascript, java)
            message: User's message or question
            mode: Coaching mode - "hint", "review", "explain", "debug"
            difficulty: Problem difficulty level
        
        Yields:
            Streaming response chunks from the AI model
        """
        
        model = self.models.get(difficulty, self.models["medium"])
        
        # Construct coaching prompt based on mode
        system_prompt = self._build_system_prompt(mode, language)
        user_prompt = self._build_user_prompt(problem, code, message, mode)
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "stream": True
        }
        
        try:
            logger.info("=== NIM API CALL ===")
            logger.info(f"URL: {self.base_url}/chat/completions")
            logger.info(f"Model: {model}")
            logger.info(f"System prompt (first 100 chars): {system_prompt[:100]}...")
            logger.info(f"User prompt (first 100 chars): {user_prompt[:100]}...")
            logger.info("====================")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    logger.info(f"NIM API Response status: {response.status_code}")

                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"NIM API Error response: {error_text.decode()}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"NVIDIA NIM API error: {error_text.decode()}"
                        )

                    line_count = 0
                    content_yielded = 0
                    async for line in response.aiter_lines():
                        line_count += 1
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                logger.info(f"NIM stream complete. Lines processed: {line_count}, Chunks yielded: {content_yielded}")
                                break

                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        content_yielded += 1
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode JSON from line {line_count}: {data[:50]}...")
                                continue

        except httpx.TimeoutException:
            logger.error("NVIDIA NIM API timeout after 30 seconds")
            raise HTTPException(
                status_code=504,
                detail="NVIDIA NIM API timeout"
            )
        except Exception as e:
            logger.error(f"Error calling NVIDIA NIM API: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    def _build_system_prompt(self, mode: str, language: str) -> str:
        """Build system prompt based on coaching mode."""
        
        base_prompt = """You are CodeCoach AI, an expert coding interview coach. Your role is to help users improve their coding skills through guided practice.

Key principles:
1. Be encouraging and constructive
2. Provide specific, actionable feedback
3. Focus on problem-solving approach, not just solutions
4. Adapt explanations to the user's level
5. Never give complete solutions - guide users to discover answers themselves

Language: {language}

Guidelines:
- Keep responses concise but helpful
- Use code examples when they aid understanding
- Ask probing questions to guide thinking
- Point out edge cases and optimizations
- Explain time/space complexity implications"""

        mode_specific = {
            "hint": """
Provide gentle hints that guide the user toward the solution without giving it away. Focus on:
- Identifying what the user might be missing
- Suggesting alternative approaches
- Pointing out patterns or insights""",
            
            "review": """
Review the user's code for correctness, efficiency, and style. Focus on:
- Logic errors or edge cases
- Performance improvements
- Code readability and best practices
- Language-specific idioms""",
            
            "explain": """
Explain concepts, algorithms, or approaches clearly. Focus on:
- Breaking down complex ideas
- Providing intuition behind algorithms
- Visual explanations when helpful
- Step-by-step reasoning""",
            
            "debug": """
    Help debug code issues. Focus on:
    - Identifying specific bugs or errors
    - Suggesting debugging strategies
    - Explaining why the current approach fails
    - Guiding toward the fix""",
    
            "freeform": """
    Respond naturally to the user's question or request. Focus on:
    - Answering their specific question directly
    - Providing helpful context and examples
    - Offering guidance appropriate to their question
    - Being conversational while staying educational"""
        }
    
        return base_prompt.format(language=language) + mode_specific.get(mode, "")
    
    def _build_user_prompt(self, problem: str, code: str, message: str, mode: str) -> str:
        """Build user prompt with context."""
        
        prompt = f"""Problem: {problem}

Current code:
```{code}
```

User message: {message}

Mode: {mode}

Please provide helpful coaching feedback."""
        
        return prompt