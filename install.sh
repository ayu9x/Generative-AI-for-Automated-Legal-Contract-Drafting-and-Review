#!/usr/bin/env bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}======================================================"
echo "  Legal AI Contract System — One-Click Installer"
echo "  Supports: macOS, Ubuntu/Debian, Fedora, Arch"
echo -e "======================================================${NC}"
echo ""

# ── Check Python ──────────────────────────────────────────
echo -e "${YELLOW}[1/6]${NC} Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Python3 is not installed."
    echo "  macOS:   brew install python@3.11"
    echo "  Ubuntu:  sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora:  sudo dnf install python3 python3-pip"
    exit 1
fi
PYTHON_VER=$(python3 --version 2>&1)
echo "         Found $PYTHON_VER"

# ── Check Node.js ─────────────────────────────────────────
echo -e "${YELLOW}[2/6]${NC} Checking Node.js..."
if ! command -v node &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Node.js is not installed."
    echo "  macOS:   brew install node"
    echo "  Ubuntu:  sudo apt install nodejs npm"
    echo "  Or use:  https://nodejs.org/"
    exit 1
fi
NODE_VER=$(node --version 2>&1)
echo "         Found Node.js $NODE_VER"

# ── Setup Backend ─────────────────────────────────────────
echo -e "${YELLOW}[3/6]${NC} Setting up Backend (Python virtual environment)..."
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
fi
source backend/venv/bin/activate

echo -e "${YELLOW}[4/6]${NC} Installing Backend dependencies..."
pip install -r backend/requirements.txt --quiet 2>/dev/null
pip install bcrypt==4.0.1 --quiet 2>/dev/null
pip install httpx --quiet 2>/dev/null

# ── Setup Frontend ────────────────────────────────────────
echo -e "${YELLOW}[5/6]${NC} Installing Frontend dependencies..."
cd frontend
npm install --silent 2>/dev/null
cd ..

# ── Setup Environment ─────────────────────────────────────
echo -e "${YELLOW}[6/6]${NC} Configuring environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "         Created .env from template"
else
    echo "         .env already exists"
fi

echo ""
echo -e "${GREEN}======================================================"
echo "  Installation Complete!"
echo "======================================================"
echo ""
echo "  To start the application, run:"
echo "    ./start.sh"
echo ""
echo "  Or start manually:"
echo "    Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "    Frontend: cd frontend && npm run dev"
echo ""
echo "  Default Login:"
echo "    Email:    admin@legalai.com"
echo "    Password: Admin@123456"
echo ""
echo "  URLs:"
echo "    Frontend: http://localhost:5173"
echo "    Backend:  http://localhost:8000"
echo "    API Docs: http://localhost:8000/docs"
echo -e "======================================================${NC}"
echo ""
