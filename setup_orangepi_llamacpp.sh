#!/bin/bash

# Setup llama.cpp on Orange Pi RV2 for Vintern-1B inference
# This script will be run ON Orange Pi (192.168.1.16)

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Setup llama.cpp trên Orange Pi RV2 cho Vintern-1B      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if running on RISC-V
ARCH=$(uname -m)
if [ "$ARCH" != "riscv64" ]; then
    echo "⚠️  WARNING: This script is designed for RISC-V (riscv64)"
    echo "   Current architecture: $ARCH"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ Detected RISC-V architecture: $ARCH"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt update
sudo apt install -y build-essential git cmake python3 python3-pip

# Install Python packages for model conversion
echo "📦 Installing Python packages..."
pip3 install transformers torch sentencepiece protobuf huggingface-hub

# Clone llama.cpp
LLAMACPP_DIR="$HOME/llama.cpp"
if [ -d "$LLAMACPP_DIR" ]; then
    echo "✓ llama.cpp already exists at $LLAMACPP_DIR"
    cd "$LLAMACPP_DIR"
    git pull
else
    echo "📥 Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMACPP_DIR"
    cd "$LLAMACPP_DIR"
fi

# Build llama.cpp for RISC-V
echo "🔨 Building llama.cpp for RISC-V..."
echo "   (This may take 10-15 minutes on Orange Pi RV2)"
make clean
make -j$(nproc)

if [ ! -f "llama-server" ]; then
    echo "❌ Build failed: llama-server not found"
    exit 1
fi

echo "✓ llama.cpp built successfully"
echo ""

# Download and convert Vintern-1B model
MODEL_DIR="$HOME/models/vintern-1b-gguf"
mkdir -p "$MODEL_DIR"

echo "📥 Downloading Vintern-1B model..."
echo "   Model: 5CD-AI/Vintern-1B-v3_5"
echo ""

# Check if model already downloaded
HF_MODEL_DIR="$HOME/.cache/huggingface/hub/models--5CD-AI--Vintern-1B-v3_5"
if [ ! -d "$HF_MODEL_DIR" ]; then
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
    echo "✓ Model already downloaded in cache"
fi

# Convert model to GGUF format
echo ""
echo "🔄 Converting model to GGUF format..."
GGUF_FILE="$MODEL_DIR/vintern-1b-q8_0.gguf"

if [ ! -f "$GGUF_FILE" ]; then
    # Find the actual model directory
    SNAPSHOT_DIR=$(find "$HF_MODEL_DIR" -type d -name "snapshots" | head -1)
    if [ -z "$SNAPSHOT_DIR" ]; then
        echo "❌ Cannot find model snapshots directory"
        exit 1
    fi
    
    ACTUAL_MODEL_DIR=$(find "$SNAPSHOT_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
    
    if [ ! -d "$ACTUAL_MODEL_DIR" ]; then
        echo "❌ Cannot find actual model directory"
        exit 1
    fi
    
    echo "   Model directory: $ACTUAL_MODEL_DIR"
    
    # Convert to FP16 first, then quantize
    python3 "$LLAMACPP_DIR/convert_hf_to_gguf.py" \
        "$ACTUAL_MODEL_DIR" \
        --outfile "$MODEL_DIR/vintern-1b-f16.gguf" \
        --outtype f16
    
    # Quantize to Q8_0 for good balance of speed and quality
    "$LLAMACPP_DIR/llama-quantize" \
        "$MODEL_DIR/vintern-1b-f16.gguf" \
        "$GGUF_FILE" \
        Q8_0
    
    # Remove intermediate file
    rm -f "$MODEL_DIR/vintern-1b-f16.gguf"
    
    echo "✓ Model converted to GGUF Q8_0 format"
else
    echo "✓ GGUF model already exists"
fi

echo ""
echo "Model size:"
du -h "$GGUF_FILE"
echo ""

# Create systemd service
echo "📝 Creating systemd service..."
sudo tee /etc/systemd/system/vintern-llamacpp.service > /dev/null <<EOF
[Unit]
Description=Vintern-1B llama.cpp Server
After=network.target

[Service]
Type=simple
User=orangepi
WorkingDirectory=$HOME/llama.cpp
ExecStart=$HOME/llama.cpp/llama-server \\
    --model $GGUF_FILE \\
    --host 0.0.0.0 \\
    --port 8002 \\
    --ctx-size 2048 \\
    --n-predict 256 \\
    --threads $(nproc) \\
    --batch-size 512 \\
    --log-disable
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service created"
echo ""

# Create API wrapper for compatibility
VLLM_SERVICE_DIR="$HOME/Projects/Vintern-1b-v3.5-demo/vllm-service"
echo "📝 Creating API wrapper..."

cat > "$VLLM_SERVICE_DIR/llamacpp_wrapper.py" <<'PYTHON'
"""
API wrapper to make llama.cpp server compatible with existing VLLM API
Runs on port 8003 and forwards to llama-server on port 8002
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import uvicorn
import base64
from typing import Optional

app = FastAPI(title="Vintern-1B llama.cpp Wrapper")

LLAMACPP_URL = "http://localhost:8002"

class AnalyzeRequest(BaseModel):
    image: str  # base64 encoded
    prompt: Optional[str] = "Describe this image in detail."
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7

class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7

@app.get("/health")
async def health():
    try:
        response = requests.get(f"{LLAMACPP_URL}/health", timeout=2)
        return {
            "status": "healthy",
            "model": "Vintern-1B-v3_5",
            "backend": "llama.cpp",
            "architecture": "riscv64"
        }
    except:
        raise HTTPException(status_code=503, detail="llama-server not available")

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """Analyze image with vision model"""
    try:
        # llama.cpp format for vision models
        payload = {
            "prompt": request.prompt,
            "image_data": [{
                "data": request.image,
                "id": 1
            }],
            "n_predict": request.max_tokens,
            "temperature": request.temperature,
            "stop": ["</s>", "<|im_end|>", "<|endoftext|>"]
        }
        
        response = requests.post(
            f"{LLAMACPP_URL}/completion",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        result = response.json()
        return {
            "response": result.get("content", ""),
            "model": "Vintern-1B-v3_5",
            "backend": "llama.cpp"
        }
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with optional image"""
    if request.image:
        return await analyze(AnalyzeRequest(
            image=request.image,
            prompt=request.message,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        ))
    else:
        # Text-only chat
        payload = {
            "prompt": request.message,
            "n_predict": request.max_tokens,
            "temperature": request.temperature,
            "stop": ["</s>", "<|im_end|>", "<|endoftext|>"]
        }
        
        response = requests.post(f"{LLAMACPP_URL}/completion", json=payload, timeout=30)
        result = response.json()
        
        return {
            "response": result.get("content", ""),
            "model": "Vintern-1B-v3_5",
            "backend": "llama.cpp"
        }

@app.get("/model/info")
async def model_info():
    return {
        "model_id": "5CD-AI/Vintern-1B-v3_5",
        "backend": "llama.cpp",
        "format": "GGUF Q8_0",
        "architecture": "riscv64",
        "mode": "native"  # Not proxy anymore!
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
PYTHON

chmod +x "$VLLM_SERVICE_DIR/llamacpp_wrapper.py"
echo "✓ API wrapper created at port 8003"
echo ""

# Create wrapper service
sudo tee /etc/systemd/system/vintern-wrapper.service > /dev/null <<EOF
[Unit]
Description=Vintern-1B API Wrapper
After=vintern-llamacpp.service
Requires=vintern-llamacpp.service

[Service]
Type=simple
User=orangepi
WorkingDirectory=$VLLM_SERVICE_DIR
ExecStart=/usr/bin/python3 $VLLM_SERVICE_DIR/llamacpp_wrapper.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Wrapper service created"
echo ""

# Reload systemd
sudo systemctl daemon-reload

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  ✓ SETUP HOÀN TẤT                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 SERVICES ĐƯỢC TẠO:"
echo "   1. vintern-llamacpp.service  → llama-server (port 8002)"
echo "   2. vintern-wrapper.service   → API wrapper (port 8003)"
echo ""
echo "🚀 KHỞI ĐỘNG SERVICES:"
echo "   sudo systemctl enable vintern-llamacpp"
echo "   sudo systemctl start vintern-llamacpp"
echo "   sudo systemctl enable vintern-wrapper"
echo "   sudo systemctl start vintern-wrapper"
echo ""
echo "📊 KIỂM TRA STATUS:"
echo "   sudo systemctl status vintern-llamacpp"
echo "   sudo systemctl status vintern-wrapper"
echo ""
echo "🧪 TEST API:"
echo "   curl http://localhost:8003/health"
echo "   curl http://localhost:8003/model/info"
echo ""
echo "⚙️  CẬP NHẬT RASPBERRY PI BACKEND:"
echo "   Thay đổi VLLM_SERVICE_URL=http://192.168.1.16:8003"
echo "   (port 8003, không phải 8002)"
echo ""
