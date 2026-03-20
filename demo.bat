@echo off
echo ========================================
echo   CodeCoach AI - Demo Setup
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env file...
    echo NVIDIA_API_KEY=your_api_key_here > .env
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 >> .env
    echo NEXT_PUBLIC_WS_URL=ws://localhost:8000 >> .env
    echo.
    echo [!] Please edit .env file and add your NVIDIA_API_KEY
    echo.
)

echo Starting services...
echo.

REM Start backend
echo [1/3] Starting backend server...
cd backend
start "CodeCoach Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
cd ..
timeout /t 3 /nobreak >nul

REM Start piston (optional - for code execution)
echo [2/3] Piston code executor will be available at http://localhost:2000

REM Start frontend
echo [3/3] Starting frontend dev server...
cd frontend
start "CodeCoach Frontend" cmd /k "pnpm dev"
cd ..

echo.
echo ========================================
echo   Services Starting...
echo ========================================
echo.
echo   Backend API:  http://localhost:8000
echo   Frontend:     http://localhost:3000
echo   Piston:       http://localhost:2000
echo.
echo   Press any key to exit this window...
echo ========================================
pause >nul
