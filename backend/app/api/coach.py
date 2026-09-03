from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from typing import AsyncIterator, Optional
import asyncio
import json
import logging
import os
import time

from app.models.schemas import (
    CoachingRequest,
    CoachingResponse,
    CoachingMode,
    Language,
    AnimateRequest,
    AnimateResponse,
)
from app.ports.coaching_provider import CoachingProvider
from app.ports.code_executor import CodeExecutor
from app.services.groq_service import GroqService
from app.services.redis_service import RedisCache
from app.services.usage_service import UsageService, check_caps, usage_headers
from app.services.solution_animation_service import SolutionAnimationService
from app.api.auth_deps import get_current_user
from app.api.daily_limits import enforce_daily_request_cap
from app.api.dependencies import (
    get_learner_context_service_dependency,
    get_redis_cache,
    get_usage_service,
    get_executor,
)
from app.models.auth_schemas import UserResponse
from app.middleware.rate_limit import limiter, COACH_RATE_LIMIT
from app.services.learner_context_service import LearnerContextService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_coaching_provider(
    cache: Optional[RedisCache] = Depends(get_redis_cache),
    user: UserResponse = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service),
) -> CoachingProvider:
    # Platform-owned key: clients never supply their own. The key is used
    # server-side to call Groq; per-user token usage is metered via the
    # injected UsageService.
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Groq API key not configured")
    return GroqService(
        api_key=api_key,
        cache=cache,
        usage_recorder=usage_service,
        user_id=user.id,
    )


async def check_daily_token_cap(
    request: Request,
    user: UserResponse = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service),
) -> None:
    """Enforce daily per-user input/output token caps; set X-Usage-* headers."""
    daily = await usage_service.get_daily_usage(user.id)
    input_cap = int(os.getenv("DAILY_TOKEN_INPUT_CAP", "250000"))
    output_cap = int(os.getenv("DAILY_TOKEN_OUTPUT_CAP", "125000"))
    allowed, _, _ = check_caps(daily, input_cap, output_cap)
    headers = usage_headers(daily, input_cap, output_cap)
    request.state.usage_headers = headers
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Daily token limit reached",
            headers=headers,
        )


async def enforce_user_rate_limit(
    user: UserResponse = Depends(get_current_user),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
) -> None:
    """Per-user requests-per-minute gate backed by Redis (degrades open)."""
    limit = int(os.getenv("USER_RATE_LIMIT_PER_MINUTE", "60"))
    if cache is None:
        return
    minute = int(time.time() // 60)
    key = RedisCache.key("rl", "user", user.id, str(minute))
    count = await cache.incr(key, ttl=60)
    if count is not None and count > limit:
        raise HTTPException(status_code=429, detail="User request rate limit exceeded")


@router.post("/", response_model=CoachingResponse)
@limiter.limit(COACH_RATE_LIMIT)
async def get_coaching(
    request: Request,
    response: Response,
    coaching_request: CoachingRequest,
    provider: CoachingProvider = Depends(get_coaching_provider),
    user: UserResponse = Depends(get_current_user),
    _usage_guard: None = Depends(check_daily_token_cap),
    _rate_guard: None = Depends(enforce_user_rate_limit),
    _daily_guard: None = Depends(enforce_daily_request_cap),
    learner_context: LearnerContextService = Depends(
        get_learner_context_service_dependency
    ),
):
    """
    Get AI coaching response for coding problems.

    This endpoint provides structured AI coaching using Groq.
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
    logger.debug("=========================================")

    try:
        chat_history_list = (
            [m.model_dump() for m in coaching_request.chat_history]
            if coaching_request.chat_history
            else []
        )

        # Learner context (cached skill graph + recent submissions) — only for
        # the questions surface. The learn surface is graph-free by design:
        # skipping the fetch saves Redis + DB roundtrips and prompt tokens.
        surface = coaching_request.surface
        learner_ctx: dict = {"skill_block": "", "submission_block": ""}
        if surface == "questions":
            try:
                learner_ctx = await learner_context.get_context(user.id)
                if learner_ctx.get("skill_block"):
                    logger.debug(
                        "Coach learner skills: %s", learner_ctx["skill_block"][:200]
                    )
                if learner_ctx.get("submission_block"):
                    logger.debug(
                        "Coach submissions: %s", learner_ctx["submission_block"][:200]
                    )
            except Exception as e:  # pragma: no cover - degrade open
                logger.debug("Learner context fetch failed: %s", e)

        structured_data = await provider.get_structured(
            problem=coaching_request.problem,
            code=coaching_request.code,
            language=coaching_request.language.value,
            message=coaching_request.message,
            mode=coaching_request.mode.value,
            difficulty=coaching_request.difficulty.value,
            lesson_context=coaching_request.lesson_context,
            chat_history=chat_history_list,
            initial_code=coaching_request.initial_code,
            learner_context=learner_ctx.get("skill_block") or None,
            submission_context=learner_ctx.get("submission_block") or None,
            surface=surface,
        )

        raw_response = _format_structured_as_text(structured_data)

        logger.debug("=== COACH API RESPONSE ===")
        logger.debug(f"Structured response keys: {list(structured_data.keys())}")
        logger.debug(f"Summary: {structured_data.get('summary', 'N/A')[:100]}...")
        logger.debug("==========================")

        response.headers.update(getattr(request.state, "usage_headers", {}))
        response.headers.update(getattr(request.state, "daily_limit_headers", {}))
        response.headers["X-Surface"] = surface

        return CoachingResponse(
            response=raw_response,
            structured=structured_data,
            mode=coaching_request.mode,
            language=coaching_request.language,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("=== COACH API ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Error args: {e.args}")
        logger.error("=======================")
        raise HTTPException(
            status_code=500, detail="Error generating coaching response"
        )


@router.post("/animate", response_model=AnimateResponse)
@limiter.limit(COACH_RATE_LIMIT)
async def get_animation(
    request: Request,
    response: Response,
    animate_request: AnimateRequest,
    provider: CoachingProvider = Depends(get_coaching_provider),
    executor: CodeExecutor = Depends(get_executor),
    user: UserResponse = Depends(get_current_user),
    _usage_guard: None = Depends(check_daily_token_cap),
    _rate_guard: None = Depends(enforce_user_rate_limit),
    _daily_guard: None = Depends(enforce_daily_request_cap),
):
    """
    Generate a visual algorithm animation for the standalone Animate viewer.

    Unlike /api/coach/, this endpoint returns only a validated animation
    script — never a chat response. The animation is generated from the
    canonical optimal solution for the question (executed against the first
    public example), never from the user's typed code. The frontend plays it
    back as a Motion Canvas animation in a dedicated window, completely
    separate from the AI Coach chat panel.
    """
    try:
        # Preferred path: execute the question's canonical optimal solution
        # against examples[0].input and compile its trace into the animation.
        # The user's code is never used here.
        animation = None
        if animate_request.question is not None:
            try:
                animation = await SolutionAnimationService(
                    executor=executor
                ).build_animation(
                    question=animate_request.question.model_dump(),
                )
            except Exception as e:  # defensive: trace path must never 500
                logger.warning("Trace animation failed, using fallback: %s", e)

        # Fallback for questions without a curated canonical solution.
        if animation is None:
            animation = await provider.get_animation_script(
                problem=animate_request.problem,
                code=animate_request.code,
                language=animate_request.language.value,
                difficulty=animate_request.difficulty.value,
                lesson_context=animate_request.lesson_context,
                initial_code=animate_request.initial_code,
                question=(
                    animate_request.question.model_dump()
                    if animate_request.question
                    else None
                ),
            )
        if not animation:
            raise HTTPException(
                status_code=502,
                detail="Failed to generate a valid animation for this problem.",
            )

        response.headers.update(getattr(request.state, "usage_headers", {}))
        response.headers.update(getattr(request.state, "daily_limit_headers", {}))

        try:
            return AnimateResponse(animation=animation)
        except ValidationError as exc:
            # A scene that passed structural checks but fails the response
            # schema is not renderable — treat it like any other failed
            # generation (502) instead of surfacing a 500 with schema
            # internals.
            logger.warning("Animation failed response validation: %s", exc)
            raise HTTPException(
                status_code=502,
                detail="Failed to generate a valid animation for this problem.",
            ) from exc
    except HTTPException:
        raise
    except Exception as e:
        logger.error("=== COACH ANIMATE API ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("===============================")
        raise HTTPException(status_code=500, detail="Error generating animation")


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
    provider: CoachingProvider = Depends(get_coaching_provider),
    user: UserResponse = Depends(get_current_user),
    _usage_guard: None = Depends(check_daily_token_cap),
    _rate_guard: None = Depends(enforce_user_rate_limit),
    _daily_guard: None = Depends(enforce_daily_request_cap),
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
    logger.debug("================================")

    async def generate_stream() -> AsyncIterator[str]:
        chunk_count = 0
        try:
            logger.debug("Starting to stream chunks from coaching provider...")
            chat_history_list = (
                [m.model_dump() for m in coaching_request.chat_history]
                if coaching_request.chat_history
                else []
            )

            async for chunk in provider.stream(
                problem=coaching_request.problem,
                code=coaching_request.code,
                language=coaching_request.language.value,
                message=coaching_request.message,
                mode=coaching_request.mode.value,
                difficulty=coaching_request.difficulty.value,
                lesson_context=coaching_request.lesson_context,
                chat_history=chat_history_list,
                initial_code=coaching_request.initial_code,
                surface=coaching_request.surface,
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
            error_data = json.dumps({"error": "Stream interrupted"})
            yield f"data: {error_data}\n\n"

    stream_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    stream_headers.update(getattr(request.state, "usage_headers", {}))
    stream_headers.update(getattr(request.state, "daily_limit_headers", {}))

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers=stream_headers,
    )


@router.get("/modes")
async def get_coaching_modes(
    user: UserResponse = Depends(get_current_user),
):
    """Get available coaching modes."""
    return {
        "modes": [mode.value for mode in CoachingMode],
        "descriptions": {
            CoachingMode.HINT.value: "Get gentle hints to guide your thinking",
            CoachingMode.REVIEW.value: "Get code review and feedback",
            CoachingMode.EXPLAIN.value: "Get explanations of concepts or approaches",
            CoachingMode.DEBUG.value: "Get help debugging your code",
            CoachingMode.FREEFORM.value: "Ask any question and get a natural response",
            CoachingMode.ANIMATE.value: "Animate the optimal solution for the problem",
        },
    }


@router.get("/languages")
async def get_supported_languages(
    user: UserResponse = Depends(get_current_user),
):
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
