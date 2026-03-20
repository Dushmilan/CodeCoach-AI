import os
import httpx
import json
from typing import AsyncIterator, Dict, Any, Optional
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

    async def get_structured_coaching_response(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Get structured AI coaching response from NVIDIA NIM as JSON.

        Args:
            problem: The coding problem description
            code: User's current code attempt
            language: Programming language
            message: User's message or question
            mode: Coaching mode
            difficulty: Problem difficulty level

        Returns:
            Parsed JSON response with structured coaching data
        """
        from app.models.schemas import StructuredCoachingResponse
        
        model = self.models.get(difficulty, self.models["medium"])

        # Construct coaching prompt based on mode
        system_prompt = self._build_system_prompt(mode, language, structured=True)
        user_prompt = self._build_user_prompt(problem, code, message, mode, structured=True)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.3,  # Lower temperature for more deterministic JSON
            "stream": False
        }

        try:
            logger.info("=== NIM API CALL (Structured) ===")
            logger.info(f"URL: {self.base_url}/chat/completions")
            logger.info(f"Model: {model}")
            logger.info(f"Mode: {mode}")
            logger.info("====================")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                logger.info(f"NIM API Response status: {response.status_code}")

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"NIM API Error response: {error_text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"NVIDIA NIM API error: {error_text}"
                    )

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                logger.info(f"Raw response (first 200 chars): {content[:200]}...")

                # Try to parse as JSON
                try:
                    # Sometimes the response might have markdown code blocks
                    if content.startswith("```json"):
                        content = content.replace("```json", "").replace("```", "").strip()
                    elif content.startswith("```"):
                        content = content.replace("```", "").replace("```", "").strip()
                    
                    structured_data = json.loads(content)
                    
                    # Validate against schema
                    structured_response = StructuredCoachingResponse(**structured_data)
                    
                    logger.info("Successfully parsed structured response")
                    return structured_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    logger.error(f"Raw content: {content}")
                    # Return a fallback structured response
                    return {
                        "summary": content[:500] if len(content) > 500 else content,
                        "hints": [],
                        "code_review": None,
                        "complexity_analysis": None,
                        "suggestions": [],
                        "edge_cases": [],
                        "explanation": content if len(content) <= 1000 else content[:1000],
                        "debug_help": None
                    }

        except httpx.TimeoutException:
            logger.error("NVIDIA NIM API timeout after 60 seconds")
            raise HTTPException(
                status_code=504,
                detail="NVIDIA NIM API timeout"
            )
        except Exception as e:
            logger.error(f"Error calling NVIDIA NIM API for structured response: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating structured response: {str(e)}"
            )

    async def get_coaching_response(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        structured: bool = False
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
            structured: If True, request structured JSON response

        Yields:
            Streaming response chunks from the AI model
        """

        model = self.models.get(difficulty, self.models["medium"])

        # Construct coaching prompt based on mode
        system_prompt = self._build_system_prompt(mode, language, structured)
        user_prompt = self._build_user_prompt(problem, code, message, mode, structured)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.7,
            "stream": not structured  # Don't stream for structured responses
        }

        # For structured responses, request JSON format
        if structured:
            payload["temperature"] = 0.3  # Lower temperature for more deterministic JSON
        
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
    
    def _build_system_prompt(self, mode: str, language: str, structured: bool = False) -> str:
        """Build system prompt based on coaching mode."""

        if structured:
            return self._build_structured_system_prompt(mode, language)

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

    def _build_structured_system_prompt(self, mode: str, language: str) -> str:
        """Build system prompt for structured JSON response."""
        
        return f"""You are CodeCoach AI, an expert coding interview coach. You MUST respond with ONLY valid JSON in this exact format:

{{
    "summary": "Brief 1-2 sentence summary of your response",
    "hints": ["hint 1", "hint 2", ...],
    "code_review": "Detailed code review feedback (optional, null if not applicable)",
    "complexity_analysis": "Time and space complexity analysis (optional, null if not applicable)",
    "suggestions": ["suggestion 1", "suggestion 2", ...],
    "edge_cases": ["edge case 1", "edge case 2", ...],
    "explanation": "Detailed explanation if needed (optional, null if not applicable)",
    "debug_help": "Debugging help if needed (optional, null if not applicable)"
}}

Rules:
1. Respond with ONLY the JSON object - no text before or after
2. All fields must be present (use null for optional ones)
3. Arrays can be empty [] if not applicable
4. Be concise but helpful
5. Focus on guiding, not giving complete solutions

Language: {language}

Mode-specific focus:
- hint: Provide 2-3 gentle hints without revealing the full solution
- review: Focus on code_review field with detailed feedback
- explain: Focus on explanation field with clear teaching
- debug: Focus on debug_help field identifying issues
- freeform: Distribute content across relevant fields"""

    def _build_user_prompt(self, problem: str, code: str, message: str, mode: str, structured: bool = False) -> str:
        """Build user prompt with context."""

        if structured:
            return self._build_structured_user_prompt(problem, code, message, mode)

        prompt = f"""Problem: {problem}

Current code:
```{code}
```

User message: {message}

Mode: {mode}

Please provide helpful coaching feedback."""

        return prompt

    def _build_structured_user_prompt(self, problem: str, code: str, message: str, mode: str) -> str:
        """Build user prompt for structured JSON response."""
        
        return f"""Problem: {problem}

Current code:
```{code}
```

User message: {message}

Mode: {mode}

Respond with ONLY a valid JSON object matching the required schema."""