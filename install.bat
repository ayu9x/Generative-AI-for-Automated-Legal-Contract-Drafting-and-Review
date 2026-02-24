@echo off
title Legal AI Contract System - Installer
color 0B
echo.
echo  ======================================================
echo   Legal AI Contract System - One-Click Installer
echo   Supports: Windows 10/11
echo  ======================================================
echo.

:: ── Check Python ──────────────────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Download from: https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYTHON_VER=%%v
echo         Found Python %PYTHON_VER%

:: ── Check Node.js ─────────────────────────────────────────
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo         Download from: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1 delims= " %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo         Found Node.js %NODE_VER%

:: ── Setup Backend ─────────────────────────────────────────
echo [3/6] Setting up Backend (Python virtual environment)...
if not exist "backend\venv" (
    python -m venv backend\venv
)
call backend\venv\Scripts\activate.bat

echo [4/6] Installing Backend dependencies...
pip install -r backend\requirements.txt --quiet 2>nul
pip install bcrypt==4.0.1 --quiet 2>nul
pip install httpx --quiet 2>nul

:: ── Setup Frontend ────────────────────────────────────────
echo [5/6] Installing Frontend dependencies...
cd frontend
call npm install --silent 2>nul
cd ..

:: ── Setup Environment ─────────────────────────────────────
echo [6/6] Configuring environment...
if not exist ".env" (
    copy .env.example .env >nul 2>&1
    echo         Created .env from template
) else (
    echo         .env already exists
)

echo.
echo  ======================================================
echo   Installation Complete!
echo  ======================================================
echo.
echo   To start the application, run:
echo     start.bat
echo.
echo   Or start manually:
echo     Backend:  cd backend ^& venv\Scripts\activate ^& uvicorn app.main:app --reload --port 8000
echo     Frontend: cd frontend ^& npm run dev
echo.
echo   Default Login:
echo     Email:    admin@legalai.com
echo     Password: Admin@123456
echo.
echo   URLs:
echo     Frontend: http://localhost:5173
echo     Backend:  http://localhost:8000
echo     API Docs: http://localhost:8000/docs
echo  ======================================================
echo.
pause
