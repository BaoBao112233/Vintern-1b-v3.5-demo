#!/bin/bash
# Stop all services

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo "🛑 Stopping all services..."

# Read PIDs from files if they exist
if [ -f "logs/detection.pid" ]; then
    DETECTION_PID=$(cat logs/detection.pid)
    echo "Stopping Detection Service (PID: $DETECTION_PID)..."
    kill $DETECTION_PID 2>/dev/null || true
    rm logs/detection.pid
fi

if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    echo "Stopping Backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm logs/backend.pid
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    echo "Stopping Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm logs/frontend.pid
fi

# Also kill by process name as backup
pkill -f "uvicorn app.main:app" || true
pkill -f "serve -s build" || true

echo "✅ All services stopped"
