from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from typing import AsyncIterator, Optional
import asyncio
import json
import logging
import os

from app.models.schemas import CoachingRequest, CoachingResponse, CoachingMode, Language
from app.services.nim_service import NIMService
from app.api.auth import get_current_user
from app.models.auth_schemas import UserResponse
from app.middleware.rate_limit import limiter, COACH_RATE_LIMIT

logger = logging.getLogger(__name__)
router = APIRouter()


def get_nim_service(
    x_nvidia_api_key: Optional[str] = Header(None, alias="X-NVIDIA-API-Key"),
) -> NIMService:
    """Dependency injection for NIM service."""
    api_key = x_nvidia_api_key or os.getenv("NVIDIA_API_KEY")
    environment = os.getenv("ENVIRONMENT", "production")

    if not api_key:
        api_key = os.getenv("NVIDIA_API_KEY")

    if environment == "testing":
        class MockNIMService:
            responses = {
                "hint": "Consider using a hash map to solve this problem.",
                "review": "Your code looks good, but consider edge cases like empty arrays.",
                "explain": "This is a classic problem that requires understanding of data structures.",
                "debug": "The issue appears to be in your loop condition. Check line 5.",
            }

            async def get_coaching_response(
                self,
                problem: str,
                code: str,
                language: str,
                message: str,
                mode: str,
                difficulty: str,
                lesson_context: str = None,
                **kwargs,
            ):
                yield self.responses.get(mode, "Here's some guidance for your problem.")

            async def get_structured_coaching_response(
                self,
                problem: str,
                code: str,
                language: str,
                message: str,
                mode: str,
                difficulty: str,
                lesson_context: str = None,
                **kwargs,
            ):
                return {
                    "summary": self.responses.get(mode, "Here's some guidance for your problem."),
                    "hints": [],
                    "code_review": None,
                    "complexity_analysis": None,
                    "suggestions": [],
                    "edge_cases": [],
                    "explanation": None,
                    "debug_help": None,
                }

        logger.info("Using MockNIMService for testing environment")
        return MockNIMService()

    if not api_key:
        raise HTTPException(status_code=500, detail="NVIDIA API key not configured")

    return NIMService(api_key=api_key)


@router.post("/", response_model=CoachingResponse)
@limiter.limit(COACH_RATE_LIMIT)
async def get_coaching(
    request: Request,
    coaching_request: CoachingRequest,
    nim_service: NIMService = Depends(get_nim_service),
    user: UserResponse = Depends(get_current_user),
):
    """
    Get AI coaching response for coding problems.

    This endpoint provides structured AI coaching using NVIDIA NIM API.
    Returns both raw text response and structured JSON response.
    """
    logger.debug("=== COACH API REQUEST (structured) ===")
    logger.debug(
        f"Problem (first 100 chars): {coaching_request.problem[:100] if coaching_request.problem else 'EMPTY'}..."
    )
    logger.debug(
        f"Code (first 100 chars): {coaching_request.code[:100] if coaching_request.code else 'EMPTY'}..."
    )
    logger.debug(f"Language: {coaching_request.language.value}")
    logger.debug(f"Message: {coaching_request.message}")
    logger.debug(f"Mode: {coaching_request.mode.value}")
    logger.debug(f"Difficulty: {coaching_request.difficulty.value}")
    logger.debug(f"NIM Service initialized: {nim_service is not None}")
    logger.debug("=========================================")

    try:
        chat_history_list = [m.model_dump() for m in coaching_request.chat_history] if coaching_request.chat_history else []

        structured_data = await nim_service.get_structured_coaching_response(
            problem=coaching_request.problem,
            code=coaching_request.code,
            language=coaching_request.language.value,
            message=coaching_request.message,
            mode=coaching_request.mode.value,
            difficulty=coaching_request.difficulty.value,
            lesson_context=coaching_request.lesson_context,
            chat_history=chat_history_list,
        )

        # Create raw text response from structured data for backward compatibility
        raw_response = _format_structured_as_text(structured_data)

        logger.debug("=== COACH API RESPONSE ===")
        logger.debug(f"Structured response keys: {list(structured_data.keys())}")
        logger.debug(f"Summary: {structured_data.get('summary', 'N/A')[:100]}...")
        logger.debug("==========================")

        return CoachingResponse(
            response=raw_response,
            structured=structured_data,
            mode=coaching_request.mode,
            language=coaching_request.language,
        )

    except Exception as e:
        logger.error("=== COACH API ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Error args: {e.args}")
        logger.error("=======================")
        raise HTTPException(
            status_code=500, detail=f"Error generating coaching response: {str(e)}"
        )


def _format_structured_as_text(structured_data: dict) -> str:
    """Format structured data as readable text for backward compatibility."""
    lines = []

    # Summary
    if structured_data.get("summary"):
        lines.append(f"📝 {structured_data['summary']}")
        lines.append("")

    # Hints
    if structured_data.get("hints"):
        lines.append("💡 **Hints:**")
        for i, hint in enumerate(structured_data["hints"], 1):
            lines.append(f"  {i}. {hint}")
        lines.append("")

    # Code Review
    if structured_data.get("code_review"):
        lines.append("🔍 **Code Review:**")
        lines.append(structured_data["code_review"])
        lines.append("")

    # Complexity Analysis
    if structured_data.get("complexity_analysis"):
        lines.append("⏱️ **Complexity Analysis:**")
        lines.append(structured_data["complexity_analysis"])
        lines.append("")

    # Suggestions
    if structured_data.get("suggestions"):
        lines.append("✨ **Suggestions:**")
        for i, suggestion in enumerate(structured_data["suggestions"], 1):
            lines.append(f"  {i}. {suggestion}")
        lines.append("")

    # Edge Cases
    if structured_data.get("edge_cases"):
        lines.append("⚠️ **Edge Cases:**")
        for i, edge_case in enumerate(structured_data["edge_cases"], 1):
            lines.append(f"  {i}. {edge_case}")
        lines.append("")

    # Explanation
    if structured_data.get("explanation"):
        lines.append("📚 **Explanation:**")
        lines.append(structured_data["explanation"])
        lines.append("")

    # Debug Help
    if structured_data.get("debug_help"):
        lines.append("🐛 **Debug Help:**")
        lines.append(structured_data["debug_help"])

    return "\n".join(lines).strip()


@router.post("/stream")
@limiter.limit(COACH_RATE_LIMIT)
async def get_coaching_stream(
    request: Request,
    coaching_request: CoachingRequest,
    nim_service: NIMService = Depends(get_nim_service),
    user: UserResponse = Depends(get_current_user),
):
    """
    Get streaming AI coaching response using Server-Sent Events.

    Returns a streaming response with Server-Sent Events format.
    Each chunk is sent as a separate SSE event.
    """
    logger.debug("=== COACH API STREAM REQUEST ===")
    logger.debug(
        f"Problem (first 100 chars): {coaching_request.problem[:100] if coaching_request.problem else 'EMPTY'}..."
    )
    logger.debug(
        f"Code (first 100 chars): {coaching_request.code[:100] if coaching_request.code else 'EMPTY'}..."
    )
    logger.debug(f"Language: {coaching_request.language.value}")
    logger.debug(f"Message: {coaching_request.message}")
    logger.debug(f"Mode: {coaching_request.mode.value}")
    logger.debug(f"Difficulty: {coaching_request.difficulty.value}")
    logger.debug(f"NIM Service initialized: {nim_service is not None}")
    logger.debug("================================")

    async def generate_stream() -> AsyncIterator[str]:
        chunk_count = 0
        try:
            logger.debug("Starting to stream chunks from NIM service...")
            chat_history_list = [m.model_dump() for m in coaching_request.chat_history] if coaching_request.chat_history else []

            async for chunk in nim_service.get_coaching_response(
                problem=coaching_request.problem,
                code=coaching_request.code,
                language=coaching_request.language.value,
                message=coaching_request.message,
                mode=coaching_request.mode.value,
                difficulty=coaching_request.difficulty.value,
                lesson_context=coaching_request.lesson_context,
                chat_history=chat_history_list,
            ):
                chunk_count += 1
                # Format as SSE
                data = json.dumps({"chunk": chunk})
                yield f"data: {data}\n\n"

                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)

            logger.debug("=== STREAM COMPLETE ===")
            logger.debug(f"Total chunks sent: {chunk_count}")
            logger.debug("=======================")

            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error("=== STREAM ERROR ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Chunks sent before error: {chunk_count}")
            logger.error("====================")
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/modes")
async def get_coaching_modes():
    """Get available coaching modes."""
    return {
        "modes": [mode.value for mode in CoachingMode],
        "descriptions": {
            CoachingMode.HINT.value: "Get gentle hints to guide your thinking",
            CoachingMode.REVIEW.value: "Get code review and feedback",
            CoachingMode.EXPLAIN.value: "Get explanations of concepts or approaches",
            CoachingMode.DEBUG.value: "Get help debugging your code",
            CoachingMode.FREEFORM.value: "Ask any question and get a natural response",
        },
    }


@router.get("/languages")
async def get_supported_languages():
    """Get supported programming languages."""
    return {
        "languages": [lang.value for lang in Language],
        "descriptions": {
            Language.PYTHON.value: "Python 3.x",
            Language.JAVASCRIPT.value: "JavaScript (Node.js)",
            Language.JAVA.value: "Java",
            Language.CPP.value: "C++",
            Language.C.value: "C",
            Language.GO.value: "Go",
            Language.RUST.value: "Rust",
            Language.TYPESCRIPT.value: "TypeScript",
        },
    }
