#!/bin/bash

# Convert Vintern-1B to GGUF on Raspberry Pi
# Then copy to Orange Pi

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Convert Vintern-1B to GGUF trên Raspberry Pi           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Load HF token
HF_TOKEN=$(grep "HUGGINGFACE_TOKEN=" backend/.env | cut -d'=' -f2)
if [ -z "$HF_TOKEN" ]; then
    echo "❌ HUGGINGFACE_TOKEN not found in backend/.env"
    exit 1
fi

echo "✓ Hugging Face token loaded"
echo ""

# Setup llama.cpp on Raspberry Pi
LLAMACPP_DIR="$HOME/llama.cpp"
if [ ! -d "$LLAMACPP_DIR" ]; then
    echo "📥 Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMACPP_DIR"
fi

cd "$LLAMACPP_DIR"
git pull

echo "🔨 Building llama.cpp on Raspberry Pi..."
make clean
make -j$(nproc)

echo "✓ llama.cpp built"
echo ""

# Create venv for model download
VENV_DIR="$HOME/.venv-model-convert"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install transformers torch sentencepiece protobuf huggingface-hub numpy

echo "✓ Dependencies installed"
echo ""

# Download model
MODEL_DIR="$HOME/models/vintern-1b-gguf"
mkdir -p "$MODEL_DIR"

HF_MODEL_DIR="$HOME/.cache/huggingface/hub/models--5CD-AI--Vintern-1B-v3_5"
if [ ! -d "$HF_MODEL_DIR" ]; then
    echo "📥 Downloading Vintern-1B model..."
    export HUGGINGFACE_TOKEN="$HF_TOKEN"
    
    python3 - <<'PYTHON'
from huggingface_hub import snapshot_download
import os

token = os.getenv("HUGGINGFACE_TOKEN", "")
model_id = "5CD-AI/Vintern-1B-v3_5"

print(f"Downloading {model_id}...")
snapshot_download(
    repo_id=model_id,
    token=token,
    local_dir=os.path.expanduser("~/.cache/huggingface/hub/models--5CD-AI--Vintern-1B-v3_5/snapshots/main"),
    local_dir_use_symlinks=False
)
print("✓ Download complete")
PYTHON
else
    echo "✓ Model already downloaded"
fi

echo ""

# Convert to GGUF
GGUF_FILE="$MODEL_DIR/vintern-1b-q8_0.gguf"
if [ ! -f "$GGUF_FILE" ]; then
    echo "🔄 Converting model to GGUF format..."
    
    # Find model directory
    SNAPSHOT_DIR=$(find "$HF_MODEL_DIR" -type d -name "snapshots" | head -1)
    ACTUAL_MODEL_DIR=$(find "$SNAPSHOT_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
    
    if [ ! -d "$ACTUAL_MODEL_DIR" ]; then
        echo "❌ Cannot find model directory"
        exit 1
    fi
    
    echo "   Model directory: $ACTUAL_MODEL_DIR"
    
    # Convert to FP16
    python3 "$LLAMACPP_DIR/convert_hf_to_gguf.py" \
        "$ACTUAL_MODEL_DIR" \
        --outfile "$MODEL_DIR/vintern-1b-f16.gguf" \
        --outtype f16
    
    # Quantize to Q8_0
    "$LLAMACPP_DIR/llama-quantize" \
        "$MODEL_DIR/vintern-1b-f16.gguf" \
        "$GGUF_FILE" \
        Q8_0
    
    # Remove intermediate file
    rm -f "$MODEL_DIR/vintern-1b-f16.gguf"
    
    echo "✓ Model converted to GGUF Q8_0"
else
    echo "✓ GGUF model already exists"
fi

deactivate

echo ""
echo "Model size:"
du -h "$GGUF_FILE"
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║            ✓ CONVERSION HOÀN TẤT                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📁 GGUF Model: $GGUF_FILE"
echo ""
echo "🚀 NEXT STEP: Copy to Orange Pi"
echo "   scp $GGUF_FILE orangepi@192.168.1.16:~/models/vintern-1b-gguf/"
echo ""
