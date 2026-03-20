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
            "max_tokens": 1000,  # Reduced to encourage concise responses
            "temperature": 0.1,  # Very low temperature for deterministic JSON
            "top_p": 0.9,
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

                    # Try to extract JSON from markdown or raw text
                    import re
                    
                    # First, try to find JSON within markdown code blocks
                    markdown_json = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if markdown_json:
                        content = markdown_json.group(1)
                    
                    # Try to extract the most complete JSON object using regex
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            partial_json = json_match.group(0)
                            
                            # Try to fix common JSON issues (missing closing brackets)
                            open_braces = partial_json.count('{')
                            close_braces = partial_json.count('}')
                            if open_braces > close_braces:
                                partial_json += '}' * (open_braces - close_braces)

                            # Fix missing array closings
                            open_brackets = partial_json.count('[')
                            close_brackets = partial_json.count(']')
                            if open_brackets > close_brackets:
                                # Add missing closing brackets at appropriate positions
                                missing = open_brackets - close_brackets
                                partial_json += ']' * missing

                            structured_data = json.loads(partial_json)
                            logger.info(f"Successfully parsed partial JSON")
                            
                            # Validate and fill missing fields
                            for field in ['summary', 'hints', 'suggestions', 'edge_cases']:
                                if field not in structured_data:
                                    structured_data[field] = [] if field != 'summary' else ''
                            for field in ['code_review', 'complexity_analysis', 'explanation', 'debug_help']:
                                if field not in structured_data:
                                    structured_data[field] = None
                                    
                            return structured_data
                        except Exception as parse_error:
                            logger.error(f"Failed to parse partial JSON: {str(parse_error)}")

                    # Return a fallback structured response with clean text
                    # Remove any JSON-like fragments from the content
                    clean_content = re.sub(r'\{[^}]*\}', '', content)
                    clean_content = re.sub(r'\[.*?\]', '', clean_content)
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    return {
                        "summary": clean_content[:200] if clean_content else "Unable to generate structured response. Please try again.",
                        "hints": [],
                        "code_review": None,
                        "complexity_analysis": None,
                        "suggestions": [],
                        "edge_cases": [],
                        "explanation": clean_content if clean_content else content[:1000],
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

        return f"""You are CodeCoach AI, a friendly and expert coding interview coach.

## Your Persona
- Warm, encouraging, and approachable
- Expert in algorithms, data structures, and system design
- Adapt your explanation to the user's skill level
- Guide users to discover solutions rather than giving direct answers
- Use clear, conversational language

## Response Formatting
Use simple, clean text formatting:
- Start with a brief, friendly acknowledgment
- Use short paragraphs (2-4 sentences each)
- Use numbered lists (1. 2. 3.) for step-by-step explanations
- Use bullet points (- or •) for multiple related items
- Keep it concise and scannable

## Response Types

### 1. Hints (mode: hint)
- Start with encouragement
- Give 2-3 progressive hints (gentle → more specific)
- End with an encouraging question

### 2. Code Review (mode: review)
- Start with something positive
- Organize feedback: Logic → Efficiency → Style
- Be specific about issues
- Suggest concrete improvements

### 3. Explanations (mode: explain)
- Start with a high-level overview
- Break down into digestible parts
- Use analogies when helpful
- Include a simple example if relevant
- Check understanding at the end

### 4. Debug Help (mode: debug)
- Acknowledge the issue
- Identify the specific problem
- Explain WHY it's wrong
- Guide toward the fix

### 5. General Questions (mode: freeform)
- Answer directly and conversationally
- Provide relevant context
- Offer follow-up suggestions

## When Asked About Data Structures
- Explain the trade-offs (time/space complexity)
- Give concrete use cases
- Show brief code examples when helpful (use single backticks for code)

## Language
Respond in: {language}

## General Guidelines
- Be concise but thorough
- Always end with an invitation for follow-up
- Never give complete solutions - guide discovery
- Use **bold** sparingly for key terms only
- Use `backticks` for code, variables, and technical terms"""

    def _build_structured_system_prompt(self, mode: str, language: str) -> str:
        """Build system prompt for structured JSON response with coaching persona."""

        return f"""You are CodeCoach AI, a friendly and expert coding interview coach.

## Your Role
Help users improve their coding skills through guided practice and constructive feedback.

## Response Format
You MUST respond with ONLY a valid JSON object. No text before or after.

## JSON Structure
{{
    "summary": "Your main response - conversational and helpful",
    "hints": ["hint 1", "hint 2"],
    "code_review": "Detailed feedback or null",
    "complexity_analysis": "Time/space complexity or null",
    "suggestions": ["suggestion 1"],
    "edge_cases": ["edge case 1"],
    "explanation": "Detailed explanation or null",
    "debug_help": "Debug guidance or null"
}}

## Rules
1. ALL 8 fields must be present in every response
2. Use null for fields not applicable, [] for empty arrays
3. Keep summary under 200 characters
4. Use simple, conversational language
5. No markdown code blocks (```) in values
6. Use **bold** sparingly, `backticks` for code terms
7. Escape quotes properly in strings

## Field Usage by Mode

**hint mode:**
- summary: Brief encouraging statement
- hints: 2-3 progressive hints
- Other fields: null or []

**review mode:**
- summary: Overall assessment
- code_review: Detailed feedback organized as Logic, Efficiency, Style
- Other fields: null or []

**explain mode:**
- summary: High-level answer
- explanation: Detailed breakdown with examples
- Other fields: null or []

**debug mode:**
- summary: Acknowledge the issue
- debug_help: Explain the problem and guide to fix
- Other fields: null or []

**freeform mode:**
- summary: Main answer
- Use other fields as appropriate for the question

Language: {language}"""

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