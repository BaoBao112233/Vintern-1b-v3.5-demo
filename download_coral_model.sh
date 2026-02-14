#!/bin/bash
# Quick download script for SSD MobileNet V2 model

set -e

echo "Downloading SSD MobileNet V2 model for Coral USB..."

mkdir -p models
cd models

# Model file
MODEL_FILE="ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
if [ ! -f "$MODEL_FILE" ]; then
    echo "Downloading $MODEL_FILE..."
    wget -q --show-progress \
        "https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite" \
        -O "$MODEL_FILE"
    echo "✅ Downloaded model"
else
    echo "✅ Model already exists"
fi

# Labels file
LABELS_FILE="coco_labels.txt"
if [ ! -f "$LABELS_FILE" ]; then
    echo "Downloading $LABELS_FILE..."
    wget -q --show-progress \
        "https://github.com/google-coral/test_data/raw/master/coco_labels.txt" \
        -O "$LABELS_FILE"
    echo "✅ Downloaded labels"
else
    echo "✅ Labels already exist"
fi

echo ""
echo "Model download complete!"
ls -lh
