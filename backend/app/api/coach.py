from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import AsyncIterator
import asyncio
import json
import os
import sys

from app.models.schemas import CoachingRequest, CoachingResponse, CoachingMode, Language, Difficulty
from app.services.nim_service import NIMService

router = APIRouter()

def get_nim_service() -> NIMService:
    """Dependency injection for NIM service."""
    api_key = os.getenv("NVIDIA_API_KEY")
    environment = os.getenv("ENVIRONMENT", "production")
    
    import logging
    logger = logging.getLogger(__name__)

    # Force load environment variables in get_nim_service
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    # Re-check API key after forced reload
    api_key = os.getenv("NVIDIA_API_KEY")
    
    logger.info(f"Environment: {environment}")
    logger.info(f"Forced .env reload from: {env_path}")
    logger.info(f"NVIDIA_API_KEY present: {bool(api_key)}")
    if api_key:
        logger.info(f"NVIDIA_API_KEY format check: starts with {api_key[:8] if len(api_key) >= 8 else 'too short'}... ends with ...{api_key[-4:] if api_key else 'N/A'}")
        logger.info(f"NVIDIA_API_KEY length: {len(api_key) if api_key else 0} characters")
    else:
        logger.error("NVIDIA_API_KEY is None - checking all environment variables:")
        logger.error(f"All NVIDIA-related vars: {[k for k in os.environ.keys() if 'NVIDIA' in k.upper()]}")
        logger.error(f"All KEY-related vars: {[k for k in os.environ.keys() if 'KEY' in k.upper()]}")
        logger.error(f"All environment variables: {list(os.environ.keys())}")

    if environment == "testing":
        # Create a simple mock service for testing
        class MockNIMService:
            async def get_coaching_response(self, problem: str, code: str, language: str,
                                          message: str, mode: str, difficulty: str):
                responses = {
                    "hint": f"Consider using a hash map to solve this {difficulty} problem.",
                    "review": "Your code looks good, but consider edge cases like empty arrays.",
                    "explain": f"This is a classic {difficulty} difficulty problem that requires...",
                    "debug": "The issue appears to be in your loop condition. Check line 5."
                }
                yield responses.get(mode, "Here's some guidance for your problem.")

        logger.info("Using MockNIMService for testing environment")
        return MockNIMService()

    if not api_key:
        logger.error("NVIDIA_API_KEY environment variable is not set")
        logger.error("Available environment variables: %s", [k for k in os.environ.keys() if 'NVIDIA' in k.upper() or 'KEY' in k.upper()])
        
        # Force load environment variables for debugging
        from dotenv import load_dotenv
        from pathlib import Path
        env_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(env_path)
        
        # Check again after forced reload
        api_key = os.getenv("NVIDIA_API_KEY")
        logger.error(f"After forced reload, NVIDIA_API_KEY: {api_key}")
        
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="NVIDIA API key not configured"
            )

    logger.info("Successfully initializing NIMService with provided API key")
    return NIMService(api_key=api_key)

@router.post("/", response_model=CoachingResponse)
async def get_coaching(
    request: CoachingRequest,
    nim_service: NIMService = Depends(get_nim_service)
):
    """
    Get AI coaching response for coding problems.

    This endpoint provides streaming AI coaching using NVIDIA NIM API.
    The response is returned as a Server-Sent Events stream for real-time interaction.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # DEBUG: Log incoming request details
    logger.info("=== COACH API REQUEST (non-streaming) ===")
    logger.info(f"Problem (first 100 chars): {request.problem[:100] if request.problem else 'EMPTY'}...")
    logger.info(f"Code (first 100 chars): {request.code[:100] if request.code else 'EMPTY'}...")
    logger.info(f"Language: {request.language.value}")
    logger.info(f"Message: {request.message}")
    logger.info(f"Mode: {request.mode.value}")
    logger.info(f"Difficulty: {request.difficulty.value}")
    logger.info(f"NIM Service initialized: {nim_service is not None}")
    logger.info("=========================================")

    try:
        # For non-streaming response, collect the entire response
        response_chunks = []
        async for chunk in nim_service.get_coaching_response(
            problem=request.problem,
            code=request.code,
            language=request.language.value,
            message=request.message,
            mode=request.mode.value,
            difficulty=request.difficulty.value
        ):
            response_chunks.append(chunk)

        full_response = "".join(response_chunks)
        logger.info(f"=== COACH API RESPONSE ===")
        logger.info(f"Response length: {len(full_response)} characters")
        logger.info(f"Response (first 200 chars): {full_response[:200] if full_response else 'EMPTY'}...")
        logger.info("==========================")

        return CoachingResponse(
            response=full_response,
            mode=request.mode,
            language=request.language
        )

    except Exception as e:
        logger.error(f"=== COACH API ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Error args: {e.args}")
        logger.error("=======================")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating coaching response: {str(e)}"
        )

@router.post("/stream")
async def get_coaching_stream(
    request: CoachingRequest,
    nim_service: NIMService = Depends(get_nim_service)
):
    """
    Get streaming AI coaching response using Server-Sent Events.

    Returns a streaming response with Server-Sent Events format.
    Each chunk is sent as a separate SSE event.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # DEBUG: Log incoming request details for streaming endpoint
    logger.info("=== COACH API STREAM REQUEST ===")
    logger.info(f"Problem (first 100 chars): {request.problem[:100] if request.problem else 'EMPTY'}...")
    logger.info(f"Code (first 100 chars): {request.code[:100] if request.code else 'EMPTY'}...")
    logger.info(f"Language: {request.language.value}")
    logger.info(f"Message: {request.message}")
    logger.info(f"Mode: {request.mode.value}")
    logger.info(f"Difficulty: {request.difficulty.value}")
    logger.info(f"NIM Service initialized: {nim_service is not None}")
    logger.info("================================")

    async def generate_stream() -> AsyncIterator[str]:
        chunk_count = 0
        try:
            logger.info("Starting to stream chunks from NIM service...")
            async for chunk in nim_service.get_coaching_response(
                problem=request.problem,
                code=request.code,
                language=request.language.value,
                message=request.message,
                mode=request.mode.value,
                difficulty=request.difficulty.value
            ):
                chunk_count += 1
                # Format as SSE
                data = json.dumps({"chunk": chunk})
                yield f"data: {data}\n\n"

                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)

            logger.info(f"=== STREAM COMPLETE ===")
            logger.info(f"Total chunks sent: {chunk_count}")
            logger.info("=======================")
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"=== STREAM ERROR ===")
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
            "Access-Control-Allow-Origin": "*"
        }
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
            CoachingMode.FREEFORM.value: "Ask any question and get a natural response"
        }
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
            Language.TYPESCRIPT.value: "TypeScript"
        }
    }