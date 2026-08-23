from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv, find_dotenv
import logging
import os
import sys

logger = logging.getLogger(__name__)


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


load_dotenv(find_dotenv())

setup_logging()

from app.api import (  # noqa: E402
    coach,
    run,
    questions,
    submit,
    health,
    debug,
    question_validation,
    auth,
    courses,
    progress,
    admin,
    daily_limits,
    skills,
    submissions,
    rescue,
)
from app.core.config import get_settings, is_production  # noqa: E402
from app.middleware.rate_limit import (  # noqa: E402
    limiter,
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)
from app.middleware.security_headers import SecurityHeadersMiddleware  # noqa: E402
from app.services.redis_service import RedisCache  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await _log_migration_requirement()

    if settings.REDIS_ENABLED:
        try:
            _app.state.redis_cache = RedisCache(settings.REDIS_URL)
            logger.info("Redis cache initialized at %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning(
                "Redis cache initialization failed: %s — caching disabled", e
            )
            _app.state.redis_cache = None
    else:
        _app.state.redis_cache = None
        logger.info("Redis caching disabled via config")

    yield

    if hasattr(_app.state, "redis_cache") and _app.state.redis_cache:
        await _app.state.redis_cache.close()
        logger.info("Redis cache connection closed")


settings = get_settings()

_production = is_production()


async def _log_migration_requirement() -> None:
    """Log whether migrations have been applied — never create schema at startup.

    Schema is owned exclusively by Alembic migrations (`alembic upgrade head`).
    Running `Base.metadata.create_all` at startup would hide missing
    migrations and drift silently from the migration chain, so the app only
    verifies connectivity and surfaces the migration status in logs.
    """
    try:
        from sqlalchemy import text

        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            migrated = (
                await session.execute(
                    text("SELECT to_regclass('alembic_version') IS NOT NULL AS applied")
                )
            ).scalar_one()
        if migrated:
            logger.info("Database reachable; Alembic migration state present")
        else:
            logger.warning(
                "Database reachable but Alembic is not applied. "
                "Run `alembic upgrade head` before serving traffic."
            )
    except Exception as exc:  # noqa: BLE001 - startup must not fail hard
        logger.error(
            "Database connectivity/migration check failed at startup (%s). "
            "Verify DATABASE_URL and run `alembic upgrade head`.",
            exc,
        )


app = FastAPI(
    title="CodeCoach AI Backend",
    description="AI-powered coding interview practice platform backend",
    version="1.0.0",
    docs_url="/docs" if not _production else None,
    redoc_url="/redoc" if not _production else None,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)


# Add validation error handler for detailed error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = _sanitize_errors(exc.errors())
    logger.error(
        "Validation error on %s %s: %s", request.method, request.url.path, errors
    )
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


def _sanitize_errors(error_data):
    """Recursively make error structures JSON-serializable.

    Handles bytes (decode), Pydantic ``ValueError`` instances in ``ctx``
    (stringify) and any other non-serializable objects.
    """
    if isinstance(error_data, bytes):
        return error_data.decode("utf-8", errors="replace")
    if isinstance(error_data, dict):
        return {k: _sanitize_errors(v) for k, v in error_data.items()}
    if isinstance(error_data, list):
        return [_sanitize_errors(e) for e in error_data]
    if isinstance(error_data, (str, int, float, bool)) or error_data is None:
        return error_data
    return str(error_data)


# Configure CORS
# Production: set CORS_ORIGINS to the real frontend origin(s), e.g.
# "https://codecoach.app,https://app.codecoach.ai". The workers.dev URL below
# is only a placeholder (real URLs are account-scoped).
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://codecoach-ai-frontend.vercel.app,"
    "https://codecoach-ai.workers.dev",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(coach.router, prefix="/api/coach", tags=["coach"])
app.include_router(run.router, prefix="/api/run", tags=["run"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(debug.router, prefix="/debug", tags=["debug"])
app.include_router(submit.router, prefix="/api/submit", tags=["submit"])
app.include_router(
    question_validation.router,
    prefix="/api/question-validation",
    tags=["question-validation"],
)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(daily_limits.router, prefix="/api/usage", tags=["usage"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["submissions"])
app.include_router(rescue.router, prefix="/api/rescue", tags=["rescue"])


@app.get("/")
async def root():
    return {"message": "CodeCoach AI Backend is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
