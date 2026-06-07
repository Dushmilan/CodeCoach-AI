from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
import logging
import os
import sys
from pathlib import Path

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


# Load environment variables from .env file with explicit path
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

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
)
from app.core.config import get_settings  # noqa: E402
from app.core.database import init_db  # noqa: E402

settings = get_settings()

app = FastAPI(
    title="CodeCoach AI Backend",
    description="AI-powered coding interview practice platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Add validation error handler for detailed error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = _sanitize_errors(exc.errors())
    logger.error("Validation error on %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


def _sanitize_errors(errors):
    """Recursively convert bytes to strings in error structures."""
    if isinstance(errors, bytes):
        return errors.decode("utf-8", errors="replace")
    if isinstance(errors, list):
        return [_sanitize_errors(e) for e in errors]
    if isinstance(errors, dict):
        return {k: _sanitize_errors(v) for k, v in errors.items()}
    return errors


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://codecoach-ai-frontend.vercel.app",
    ],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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


@app.on_event("startup")
async def on_startup():
    if settings.USE_DATABASE:
        await init_db()
        logger.info("Database tables created/verified")


@app.get("/")
async def root():
    return {"message": "CodeCoach AI Backend is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
