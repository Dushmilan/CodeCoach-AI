@echo off
REM CodeCoach AI - Quick Start Script for Windows
REM This script helps you deploy the application locally

echo.
echo ====================================
echo   CodeCoach AI - Deployment Helper
echo ====================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)
echo [OK] Docker found

REM Check if Docker Compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not available
    echo Please install Docker Desktop which includes Docker Compose
    pause
    exit /b 1
)
echo [OK] Docker Compose found
echo.

REM Check for .env file
if not exist .env (
    echo [INFO] .env file not found. Creating from template...
    copy .env.example .env >nul
    echo [OK] Created .env file
    echo.
    echo [ACTION] Please edit .env and add your NVIDIA_API_KEY
    echo         Get your free key: https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct
    echo.
    pause
)

REM Check if NVIDIA_API_KEY is still default
findstr /C:"your_nvidia_nim_api_key_here" .env >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] NVIDIA_API_KEY is still set to default value
    echo [ACTION] Please edit .env and add your actual API key
    echo.
    set /p continue="Continue anyway? (Y/N): "
    if /i "%continue%"=="N" exit /b 1
)

echo.
echo [BUILD] Building and starting services...
echo.

REM Start services
docker compose up --build -d

if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo.
echo [OK] Services started!
echo.
echo [INFO] Waiting for services to initialize...
timeout /t 5 /nobreak >nul

echo.
echo [STATUS] Service Status:
docker compose ps

echo.
echo ====================================
echo   CodeCoach AI is running!
echo ====================================
echo.
echo Access points:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   Piston:    http://localhost:2000
echo.
echo Useful commands:
echo   View logs:     docker compose logs -f
echo   Stop:          docker compose down
echo   Restart:       docker compose restart
echo   Rebuild:       docker compose up --build
echo.

pause
