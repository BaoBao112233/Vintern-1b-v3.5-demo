#!/bin/bash
# Start script for Raspberry Pi 4 + Coral USB

set -e

echo "================================================"
echo "Starting Raspberry Pi 4 Camera System"
echo "================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Run ./setup_raspberrypi.sh first"
    exit 1
fi

# Load environment
. .env

# Check if models exist
if [ ! -f models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite ]; then
    echo "❌ Model not found!"
    echo "Run ./setup_raspberrypi.sh first"
    exit 1
fi

# Stop any existing containers
echo ""
echo "Stopping existing containers..."
sudo docker-compose -f docker-compose.raspberrypi.yml down 2>/dev/null || true

# Build and start services
echo ""
echo "Building and starting services..."
sudo docker-compose -f docker-compose.raspberrypi.yml up -d --build

# Wait for services to start
echo ""
echo "Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

echo ""
echo "Detection Service:"
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Detection service is running"
    curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo ""
else
    echo "❌ Detection service is not responding"
fi

echo ""
echo "Backend Service:"
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend service is running"
    curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || echo ""
else
    echo "❌ Backend service is not responding"
fi

# Summary
echo ""
echo "================================================"
echo "System Started!"
echo "================================================"
echo ""
echo "Access URLs:"
echo "  UI:              http://$HOST_IP:8000"
echo "  API Docs:        http://$HOST_IP:8000/docs"
echo "  Detection API:   http://$HOST_IP:8001/docs"
echo ""
echo "Camera URLs:"
echo "  Camera 1: rtsp://$CAMERA_USERNAME:$CAMERA_PASSWORD@$CAMERA1_IP/cam/realmonitor?channel=1&subtype=1"
echo "  Camera 2: rtsp://$CAMERA_USERNAME:$CAMERA_PASSWORD@$CAMERA2_IP/cam/realmonitor?channel=1&subtype=1"
echo ""
echo "VLLM Service: $VLLM_SERVICE_URL"
echo ""
echo "View logs:"
echo "  All:          sudo docker-compose -f docker-compose.raspberrypi.yml logs -f"
echo "  Backend:      sudo docker-compose -f docker-compose.raspberrypi.yml logs -f backend"
echo "  Detection:    sudo docker-compose -f docker-compose.raspberrypi.yml logs -f detection-service"
echo ""
echo "Stop services:"
echo "  ./stop_raspberrypi.sh"
echo ""
