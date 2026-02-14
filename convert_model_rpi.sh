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

echo "🔨 Building llama.cpp on Raspberry Pi with CMake..."

# Install CMake if needed
if ! command -v cmake &> /dev/null; then
    echo "📦 Installing CMake..."
    sudo apt update && sudo apt install -y cmake
fi

# Build with CMake
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j$(nproc)
cd ..

# Check if built successfully
if [ ! -f "build/bin/llama-server" ] && [ ! -f "llama-server" ]; then
    echo "❌ Build failed"
    exit 1
fi

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
    
    # Find convert script (may be in root or examples/)
    CONVERT_SCRIPT=""
    if [ -f "$LLAMACPP_DIR/convert_hf_to_gguf.py" ]; then
        CONVERT_SCRIPT="$LLAMACPP_DIR/convert_hf_to_gguf.py"
    elif [ -f "$LLAMACPP_DIR/examples/convert_hf_to_gguf.py" ]; then
        CONVERT_SCRIPT="$LLAMACPP_DIR/examples/convert_hf_to_gguf.py"
    elif [ -f "$LLAMACPP_DIR/convert-hf-to-gguf.py" ]; then
        CONVERT_SCRIPT="$LLAMACPP_DIR/convert-hf-to-gguf.py"
    else
        echo "❌ Cannot find convert script"
        ls -la "$LLAMACPP_DIR"/*.py 2>/dev/null || echo "No .py files in root"
        exit 1
    fi
    
    echo "   Using convert script: $CONVERT_SCRIPT"
    
    # Convert to FP16
    python3 "$CONVERT_SCRIPT" \
        "$ACTUAL_MODEL_DIR" \
        --outfile "$MODEL_DIR/vintern-1b-f16.gguf" \
        --outtype f16
    
    # Find llama-quantize binary
    QUANTIZE_BIN=""
    if [ -f "$LLAMACPP_DIR/build/bin/llama-quantize" ]; then
        QUANTIZE_BIN="$LLAMACPP_DIR/build/bin/llama-quantize"
    elif [ -f "$LLAMACPP_DIR/llama-quantize" ]; then
        QUANTIZE_BIN="$LLAMACPP_DIR/llama-quantize"
    else
        echo "❌ Cannot find llama-quantize binary"
        exit 1
    fi
    
    echo "   Using quantize binary: $QUANTIZE_BIN"
    
    # Quantize to Q8_0
    "$QUANTIZE_BIN" \
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
