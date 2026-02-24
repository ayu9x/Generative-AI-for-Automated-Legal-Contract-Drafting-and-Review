@echo off
title Legal AI — Build Windows Installer
color 0B
echo.
echo  ======================================================
echo   Legal AI Contract System — Build Windows Installer
echo  ======================================================
echo.
echo  This script will:
echo    1. Build the frontend (npm run build)
echo    2. Bundle backend + frontend into a standalone .exe
echo    3. Create a Windows installer (.exe) using Inno Setup
echo.
echo  Prerequisites:
echo    - Python 3.11+ with pip
echo    - Node.js 18+ with npm
echo    - Inno Setup 6 (https://jrsoftware.org/isdl.php)
echo.
pause

echo.
echo [Step 1/3] Building standalone .exe with PyInstaller...
python build_exe.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo [Step 2/3] Creating Windows installer with Inno Setup...
where iscc >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Inno Setup Compiler (iscc) not found in PATH.
    echo          Please install from: https://jrsoftware.org/isdl.php
    echo          Then add to PATH or open installer\legal-ai-setup.iss manually.
    echo.
    echo  Standalone .exe is ready at: dist\LegalAI\LegalAI.exe
    echo  You can zip and distribute that folder.
    pause
    exit /b 0
)

iscc installer\legal-ai-setup.iss
if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup build failed!
    pause
    exit /b 1
)

echo.
echo [Step 3/3] Done!
echo.
echo  ======================================================
echo   BUILD COMPLETE!
echo  ======================================================
echo.
echo   Standalone .exe:  dist\LegalAI\LegalAI.exe
echo   Windows Installer: installer\Output\LegalAI-Setup-1.0.0.exe
echo.
echo   Distribution options:
echo     Option A: Zip dist\LegalAI\ and share the zip
echo     Option B: Share LegalAI-Setup-1.0.0.exe (proper installer)
echo  ======================================================
echo.
pause
