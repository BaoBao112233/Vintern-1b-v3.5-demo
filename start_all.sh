#!/bin/bash
# Start all services for Raspberry Pi deployment

set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo "🚀 Starting Vintern Multi-Camera System on Raspberry Pi 4..."

# Check Coral USB
echo "Checking Coral USB Accelerator..."
if lsusb | grep -q "Global Unichip"; then
    echo "✅ Coral USB Accelerator detected"
else
    echo "⚠️  Warning: Coral USB Accelerator not detected"
    echo "   Please connect Coral USB and restart"
fi

# Check model
if [ ! -f "/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite" ]; then
    echo "📦 Model not found, downloading..."
    cd detection-service
    sudo bash download_model.sh
    cd ..
fi

# Create logs directory
mkdir -p logs

# Kill existing services
echo "Stopping existing services..."
pkill -f "uvicorn app.main:app" || true
sleep 2

# Start Detection Service
echo "🎯 Starting Detection Service..."
cd detection-service
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > ../logs/detection.log 2>&1 &
DETECTION_PID=$!
echo "   Detection Service PID: $DETECTION_PID"
cd ..

# Wait for detection service
sleep 5

# Start Backend
echo "🔧 Starting Backend..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
cd ..

# Wait for backend
sleep 3

# Check if frontend build exists
if [ -d "frontend/build" ]; then
    echo "🌐 Starting Frontend..."
    cd frontend
    npx serve -s build -l 3000 > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
    cd ..
else
    echo "⚠️  Frontend build not found. Run 'npm run build' in frontend directory"
    FRONTEND_PID=""
fi

echo ""
echo "✅ All services started!"
echo ""
echo "Services:"
echo "  - Detection Service: http://localhost:8001 (PID: $DETECTION_PID)"
echo "  - Backend API: http://localhost:8000 (PID: $BACKEND_PID)"
if [ -n "$FRONTEND_PID" ]; then
    echo "  - Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
fi
echo ""
echo "To view logs:"
echo "  tail -f logs/detection.log"
echo "  tail -f logs/backend.log"
if [ -n "$FRONTEND_PID" ]; then
    echo "  tail -f logs/frontend.log"
fi
echo ""
echo "To stop all services:"
if [ -n "$FRONTEND_PID" ]; then
    echo "  kill $DETECTION_PID $BACKEND_PID $FRONTEND_PID"
else
    echo "  kill $DETECTION_PID $BACKEND_PID"
fi
echo ""

# Save PIDs to file
echo "$DETECTION_PID" > logs/detection.pid
echo "$BACKEND_PID" > logs/backend.pid
if [ -n "$FRONTEND_PID" ]; then
    echo "$FRONTEND_PID" > logs/frontend.pid
fi

# Wait for services
wait
