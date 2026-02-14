#!/bin/bash
# Setup script for Raspberry Pi 4 + Coral USB
# Run this script first before starting the services

set -e

echo "================================================"
echo "Raspberry Pi 4 + Coral USB - Setup Script"
echo "================================================"

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "⚠️  Warning: Not running on Raspberry Pi"
else
    cat /proc/device-tree/model
    echo ""
fi

# Step 1: Copy environment file
echo ""
echo "Step 1: Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.raspberrypi .env
    echo "✅ Created .env file from .env.raspberrypi"
    echo "⚠️  Please edit .env to set your camera IPs and passwords"
    read -p "Press Enter to edit .env now or Ctrl+C to cancel..."
    nano .env
else
    echo "✅ .env file already exists"
fi

# Step 2: Create models directory
echo ""
echo "Step 2: Creating models directory..."
mkdir -p models
echo "✅ Models directory created"

# Step 3: Download SSD MobileNet V2 model for Coral
echo ""
echo "Step 3: Downloading SSD MobileNet V2 model for Coral USB..."
cd models

MODEL_FILE="ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
LABELS_FILE="coco_labels.txt"

if [ -f "$MODEL_FILE" ]; then
    echo "✅ Model already exists: $MODEL_FILE"
else
    echo "⬇️  Downloading $MODEL_FILE..."
    wget -q --show-progress \
        "https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite" \
        -O "$MODEL_FILE"
    echo "✅ Downloaded: $MODEL_FILE"
fi

if [ -f "$LABELS_FILE" ]; then
    echo "✅ Labels already exist: $LABELS_FILE"
else
    echo "⬇️  Downloading $LABELS_FILE..."
    wget -q --show-progress \
        "https://github.com/google-coral/test_data/raw/master/coco_labels.txt" \
        -O "$LABELS_FILE"
    echo "✅ Downloaded: $LABELS_FILE"
fi

cd ..

# Step 4: Install Coral USB drivers (if needed)
echo ""
echo "Step 4: Checking Coral USB drivers..."
if ! lsusb | grep -q "Global Unichip Corp"; then
    echo "⚠️  Coral USB not detected"
    echo "Make sure Coral USB is plugged in"
    echo ""
    read -p "Do you want to install Coral USB drivers? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd detection-service
        bash install_coral.sh
        cd ..
        echo "✅ Coral drivers installed"
        echo "⚠️  You may need to reboot"
    fi
else
    echo "✅ Coral USB detected"
    lsusb | grep "Global Unichip Corp"
fi

# Step 5: Test cameras
echo ""
echo "Step 5: Testing camera connections..."
echo "Loading camera IPs from .env..."

. .env

echo ""
echo "Testing Camera 1: $CAMERA1_IP"
if ping -c 1 -W 2 "$CAMERA1_IP" > /dev/null 2>&1; then
    echo "✅ Camera 1 is reachable"
else
    echo "❌ Camera 1 is NOT reachable at $CAMERA1_IP"
fi

echo ""
echo "Testing Camera 2: $CAMERA2_IP"
if ping -c 1 -W 2 "$CAMERA2_IP" > /dev/null 2>&1; then
    echo "✅ Camera 2 is reachable"
else
    echo "❌ Camera 2 is NOT reachable at $CAMERA2_IP"
fi

# Step 6: Test VLLM service (Orange Pi)
echo ""
echo "Step 6: Testing VLLM service (Orange Pi)..."
VLLM_URL="${VLLM_SERVICE_URL:-http://192.168.1.16:8002}"
echo "VLLM URL: $VLLM_URL"

if curl -s -m 5 "$VLLM_URL/health" > /dev/null 2>&1; then
    echo "✅ VLLM service is reachable"
    curl -s "$VLLM_URL/health" | python3 -m json.tool 2>/dev/null || echo ""
else
    echo "❌ VLLM service is NOT reachable at $VLLM_URL"
    echo "⚠️  System will run in detection-only mode"
fi

# Step 7: Create logs directory
echo ""
echo "Step 7: Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory created"

# Summary
echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Make sure .env is configured correctly"
echo "2. Run: ./start_raspberrypi.sh"
echo "3. Access UI at: http://192.168.1.14:8000"
echo ""
echo "To download models manually:"
echo "  cd detection-service && bash download_model.sh"
echo ""
echo "To test cameras:"
echo "  python3 test_cameras.py"
echo ""
