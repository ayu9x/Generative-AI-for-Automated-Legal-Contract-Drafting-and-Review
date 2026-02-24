#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if installed
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    echo "[ERROR] Not installed yet. Run ./install.sh first!"
    exit 1
fi

echo ""
echo -e "${BLUE}  Starting Legal AI Contract System...${NC}"
echo ""

# Start backend
echo "  Starting Backend on port 8000..."
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "  Starting Frontend on port 5173..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

sleep 3

echo ""
echo -e "${GREEN}======================================================"
echo "  Application is running!"
echo "======================================================"
echo ""
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  Login with:"
echo "    Email:    admin@legalai.com"
echo "    Password: Admin@123456"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo -e "======================================================${NC}"

# Open browser
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5173 2>/dev/null &
elif command -v open &>/dev/null; then
    open http://localhost:5173 2>/dev/null &
fi

# Cleanup on exit
cleanup() {
    echo ""
    echo "  Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "  Servers stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
