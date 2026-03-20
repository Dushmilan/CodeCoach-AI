from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file with explicit path
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from app.api import coach, run, questions, health, debug, validation, question_validation

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
    logger.error(f"=== VALIDATION ERROR ===")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Validation errors: {exc.errors()}")
    logger.error(f"Request body: {await request.body()}")
    logger.error("========================")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://codecoach-ai-frontend.vercel.app",
    ], # Configure properly for production
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
app.include_router(validation.router, prefix="/api/validate", tags=["validation"])
app.include_router(question_validation.router, prefix="/api/question-validation", tags=["question-validation"])

@app.get("/")
async def root():
    return {"message": "CodeCoach AI Backend is running"}

@app.get("/docs")
async def docs():
    return {"message": "API documentation available at /docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)