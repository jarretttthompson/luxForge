#!/usr/bin/env bash
# Start both the Python backend (simulator mode) and the Vite frontend dev server.
# Press Ctrl+C to stop both.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "Done."
}

trap cleanup EXIT INT TERM

# Start backend in simulator mode
echo "Starting backend (simulator mode)..."
source .venv/bin/activate
python -m src.main --simulator &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 2

# Start frontend dev server
echo "Starting frontend dev server..."
cd ui
npm run dev &
FRONTEND_PID=$!

cd "$PROJECT_DIR"

echo ""
echo "==================================="
echo "  LuxForge dev environment running"
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:5173"
echo "  Press Ctrl+C to stop"
echo "==================================="
echo ""

# Wait for either process to exit
wait
