@echo off
title FinAccess — Starting Services

echo.
echo =========================================================
echo   FinAccess — Starting Backend + Frontend
echo =========================================================
echo.

:: ── 1. Install backend dependencies ──────────────────────────
echo [1/4] Installing backend dependencies...
pip install fastapi uvicorn sqlalchemy aiosqlite python-multipart --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)
echo       Done.

:: ── 2. Install frontend dependencies ─────────────────────────
echo [2/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install --silent
if %errorlevel% neq 0 (
    echo ERROR: npm install failed. Make sure Node.js is installed.
    pause
    exit /b 1
)
echo       Done.

:: ── 3. Start backend in a new window ─────────────────────────
echo [3/4] Starting backend on http://localhost:8000 ...
cd /d "%~dp0backend"
start "FinAccess Backend" cmd /k "python server.py"
timeout /t 3 /nobreak >nul

:: ── 4. Start frontend in a new window ────────────────────────
echo [4/4] Starting frontend on http://localhost:5173 ...
cd /d "%~dp0frontend"
start "FinAccess Frontend" cmd /k "npm run dev"

echo.
echo =========================================================
echo   Both services started in separate windows!
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Demo accounts (pre-seeded):
echo     Admin:     admin@finaccess.com  /  admin123
echo     Applicant: applicant@finaccess.com  /  pass1234
echo.
echo   You can also CREATE NEW ACCOUNTS from the login page.
echo =========================================================
echo.
pause
