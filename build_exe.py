"""
Build Script — Create a standalone .exe for Legal AI Contract System
=====================================================================

This script:
1. Builds the frontend into static files
2. Copies them into the backend so FastAPI can serve them
3. Uses PyInstaller to bundle everything into a single .exe

Prerequisites (install once):
    pip install pyinstaller

Usage:
    python build_exe.py

Output:
    dist/LegalAI.exe  — standalone executable (double-click to run)
"""

import subprocess
import shutil
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
STATIC_DIR = os.path.join(BACKEND, "app", "static")
DIST_DIR = os.path.join(ROOT, "dist")


def run(cmd, cwd=None):
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or ROOT)
    if result.returncode != 0:
        print(f"  [ERROR] Command failed: {cmd}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("  Legal AI Contract System — Build Standalone .exe")
    print("=" * 60)
    print()

    # Step 1: Build frontend
    print("[1/4] Building Frontend...")
    run("npm install", cwd=FRONTEND)
    run("npm run build", cwd=FRONTEND)

    # Step 2: Copy built frontend to backend/app/static
    print("[2/4] Copying frontend build to backend...")
    if os.path.exists(STATIC_DIR):
        shutil.rmtree(STATIC_DIR)
    shutil.copytree(
        os.path.join(FRONTEND, "dist"),
        STATIC_DIR,
    )
    print(f"  Copied to {STATIC_DIR}")

    # Step 3: Install PyInstaller if needed
    print("[3/4] Checking PyInstaller...")
    try:
        import PyInstaller
        print(f"  Found PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  Installing PyInstaller...")
        run(f"{sys.executable} -m pip install pyinstaller")

    # Step 4: Build .exe with PyInstaller
    print("[4/4] Building .exe with PyInstaller...")
    
    # Create the PyInstaller entry point
    launcher_path = os.path.join(BACKEND, "launcher.py")
    with open(launcher_path, "w") as f:
        f.write('''"""
Legal AI Contract System — Desktop Launcher
Double-click this .exe to start the server and open your browser.
"""
import os
import sys
import time
import threading
import webbrowser

def open_browser():
    """Open browser after a short delay to let the server start."""
    time.sleep(3)
    webbrowser.open("http://localhost:8000")
    print()
    print("=" * 50)
    print("  Legal AI Contract System is running!")
    print("=" * 50)
    print()
    print("  Open: http://localhost:8000")
    print()
    print("  Login:")
    print("    Email:    admin@legalai.com")
    print("    Password: Admin@123456")
    print()
    print("  Close this window to stop the server.")
    print("=" * 50)

if __name__ == "__main__":
    # Set the working directory to the exe location
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    
    # Start browser opener in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start the FastAPI server
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
''')

    # Run PyInstaller
    pyinstaller_cmd = (
        f'{sys.executable} -m PyInstaller '
        f'--name "LegalAI" '
        f'--onedir '
        f'--console '
        f'--icon NONE '
        f'--add-data "app;app" '
        f'--hidden-import uvicorn.logging '
        f'--hidden-import uvicorn.loops '
        f'--hidden-import uvicorn.loops.auto '
        f'--hidden-import uvicorn.protocols '
        f'--hidden-import uvicorn.protocols.http '
        f'--hidden-import uvicorn.protocols.http.auto '
        f'--hidden-import uvicorn.protocols.websockets '
        f'--hidden-import uvicorn.protocols.websockets.auto '
        f'--hidden-import uvicorn.lifespan '
        f'--hidden-import uvicorn.lifespan.on '
        f'--hidden-import uvicorn.lifespan.off '
        f'--hidden-import passlib.handlers.bcrypt '
        f'--hidden-import jose '
        f'--hidden-import httpx '
        f'--hidden-import pydantic '
        f'--hidden-import pydantic_settings '
        f'--hidden-import structlog '
        f'--collect-all fastapi '
        f'--collect-all starlette '
        f'--collect-all pydantic '
        f'--noconfirm '
        f'launcher.py'
    )
    run(pyinstaller_cmd, cwd=BACKEND)

    # Move output to root dist
    src_dist = os.path.join(BACKEND, "dist", "LegalAI")
    dst_dist = os.path.join(DIST_DIR, "LegalAI")
    if os.path.exists(dst_dist):
        shutil.rmtree(dst_dist)
    shutil.move(src_dist, dst_dist)

    # Copy .env.example
    shutil.copy2(
        os.path.join(ROOT, ".env.example"),
        os.path.join(dst_dist, ".env"),
    )

    # Cleanup
    for cleanup_path in [
        os.path.join(BACKEND, "build"),
        os.path.join(BACKEND, "dist"),
        os.path.join(BACKEND, "LegalAI.spec"),
        launcher_path,
    ]:
        if os.path.isdir(cleanup_path):
            shutil.rmtree(cleanup_path)
        elif os.path.isfile(cleanup_path):
            os.remove(cleanup_path)

    exe_path = os.path.join(dst_dist, "LegalAI.exe")
    print()
    print("=" * 60)
    print("  BUILD COMPLETE!")
    print("=" * 60)
    print()
    print(f"  Output: {dst_dist}")
    print(f"  Run:    {exe_path}")
    print()
    print("  You can zip the 'dist/LegalAI' folder and distribute it.")
    print("  Users just unzip and double-click LegalAI.exe")
    print("=" * 60)


if __name__ == "__main__":
    main()
