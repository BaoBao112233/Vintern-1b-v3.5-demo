#!/bin/bash
# Quick test script for the detection service

echo "🧪 Testing Detection Service..."

# Check if model exists
if [ ! -f "/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite" ]; then
    echo "❌ Model not found! Run download_model.sh first"
    exit 1
fi

echo "✅ Model found"

# Check if Coral is connected
if lsusb | grep -q "Global Unichip"; then
    echo "✅ Coral USB Accelerator detected"
else
    echo "⚠️  Coral USB Accelerator not detected"
    echo "   Make sure Coral USB is connected"
fi

# Start detection service in test mode
cd "$(dirname "$0")"
echo "🚀 Starting detection service..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001
