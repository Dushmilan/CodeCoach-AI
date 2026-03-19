from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file with explicit path
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from app.api import coach, run, questions, health, debug

app = FastAPI(
    title="CodeCoach AI Backend",
    description="AI-powered coding interview practice platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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

@app.get("/")
async def root():
    return {"message": "CodeCoach AI Backend is running"}

@app.get("/docs")
async def docs():
    return {"message": "API documentation available at /docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)