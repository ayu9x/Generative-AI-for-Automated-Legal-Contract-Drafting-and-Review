@echo off
title Legal AI Contract System
color 0B
echo.
echo  ======================================================
echo   Legal AI Contract System - Starting...
echo  ======================================================
echo.

:: Check if installed
if not exist "backend\venv" (
    echo [ERROR] Not installed yet. Run install.bat first!
    pause
    exit /b 1
)

echo  Starting Backend server...
start "Legal AI - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo  Starting Frontend server...
start "Legal AI - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait for servers to start
echo.
echo  Waiting for servers to initialize...
timeout /t 5 /nobreak >nul

echo.
echo  ======================================================
echo   Application is running!
echo  ======================================================
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Login with:
echo     Email:    admin@legalai.com
echo     Password: Admin@123456
echo.
echo   Opening browser...
echo  ======================================================

:: Open browser
start http://localhost:5173

echo.
echo  Press any key to stop both servers...
pause >nul

:: Kill servers
taskkill /FI "WINDOWTITLE eq Legal AI - Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Legal AI - Frontend*" /F >nul 2>&1
echo  Servers stopped.
