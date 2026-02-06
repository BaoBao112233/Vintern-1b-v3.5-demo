#!/bin/bash
# Download SSD MobileNet V2 model for Coral Edge TPU

set -e

# Create models directory
MODELS_DIR="/models"
mkdir -p "$MODELS_DIR"

echo "📦 Downloading SSD MobileNet V2 (COCO) for Coral Edge TPU..."

# Download the Edge TPU compiled model
cd "$MODELS_DIR"

# SSD MobileNet V2 COCO (quantized, Edge TPU compiled)
MODEL_URL="https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
MODEL_NAME="ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"

if [ -f "$MODEL_NAME" ]; then
    echo "✅ Model already exists: $MODEL_NAME"
else
    echo "⬇️  Downloading $MODEL_NAME..."
    wget -q --show-progress "$MODEL_URL" -O "$MODEL_NAME"
    echo "✅ Downloaded: $MODEL_NAME"
fi

# Download labels
LABELS_URL="https://github.com/google-coral/test_data/raw/master/coco_labels.txt"
LABELS_NAME="coco_labels.txt"

if [ -f "$LABELS_NAME" ]; then
    echo "✅ Labels already exist: $LABELS_NAME"
else
    echo "⬇️  Downloading $LABELS_NAME..."
    wget -q --show-progress "$LABELS_URL" -O "$LABELS_NAME"
    echo "✅ Downloaded: $LABELS_NAME"
fi

echo "🎉 Model download complete!"
echo "📂 Model path: $MODELS_DIR/$MODEL_NAME"
echo "📂 Labels path: $MODELS_DIR/$LABELS_NAME"
