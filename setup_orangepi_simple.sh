#!/bin/bash

# Setup llama.cpp on Orange Pi RV2 (SIMPLIFIED - No PyTorch needed)
# Model will be copied from Raspberry Pi after conversion

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Setup llama.cpp trên Orange Pi RV2 (RISC-V)            ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check RISC-V
ARCH=$(uname -m)
if [ "$ARCH" != "riscv64" ]; then
    echo "⚠️  WARNING: Expected riscv64, got $ARCH"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ Architecture: $ARCH"
echo ""

# Install dependencies (NO PyTorch!)
echo "📦 Installing dependencies..."
sudo apt update
sudo apt install -y build-essential git cmake wget curl

echo "✓ System dependencies installed"
echo ""

# Install minimal Python packages for wrapper (API only)
echo "📦 Installing Python packages for API wrapper..."
pip3 install --break-system-packages fastapi uvicorn requests pillow

echo "✓ API wrapper dependencies installed"
echo ""

# Clone and build llama.cpp
LLAMACPP_DIR="$HOME/llama.cpp"
if [ ! -d "$LLAMACPP_DIR" ]; then
    echo "📥 Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMACPP_DIR"
else
    echo "✓ llama.cpp exists, updating..."
    cd "$LLAMACPP_DIR"
    git pull
fi

cd "$LLAMACPP_DIR"

echo "🔨 Building llama.cpp for RISC-V..."
echo "   (This takes 10-15 minutes on Orange Pi RV2)"
make clean
make -j$(nproc)

if [ ! -f "llama-server" ]; then
    echo "❌ Build failed: llama-server not found"
    exit 1
fi

echo "✓ llama.cpp built successfully"
echo ""

# Create model directory
MODEL_DIR="$HOME/models/vintern-1b-gguf"
mkdir -p "$MODEL_DIR"

echo "📁 Model directory created: $MODEL_DIR"
echo ""

# Create systemd service for llama-server
echo "📝 Creating llama-server systemd service..."
sudo tee /etc/systemd/system/vintern-llamacpp.service > /dev/null <<EOF
[Unit]
Description=Vintern-1B llama.cpp Server
After=network.target

[Service]
Type=simple
User=orangepi
WorkingDirectory=$HOME/llama.cpp
ExecStart=$HOME/llama.cpp/llama-server \\
    --model $MODEL_DIR/vintern-1b-q8_0.gguf \\
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

echo "✓ llama-server service created"
echo ""

# Create API wrapper
VLLM_SERVICE_DIR="$HOME/Projects/Vintern-1b-v3.5-demo/vllm-service"
mkdir -p "$VLLM_SERVICE_DIR"

echo "📝 Creating API wrapper..."
cat > "$VLLM_SERVICE_DIR/llamacpp_wrapper.py" <<'PYTHON'
"""
API wrapper for llama.cpp server
Makes llama.cpp compatible with existing VLLM API
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import uvicorn
from typing import Optional

app = FastAPI(title="Vintern-1B llama.cpp Wrapper")

LLAMACPP_URL = "http://localhost:8002"

class AnalyzeRequest(BaseModel):
    image: str  # base64
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
    try:
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
    if request.image:
        return await analyze(AnalyzeRequest(
            image=request.image,
            prompt=request.message,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        ))
    else:
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
        "mode": "native"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
PYTHON

chmod +x "$VLLM_SERVICE_DIR/llamacpp_wrapper.py"
echo "✓ API wrapper created"
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
echo "║              ✓ SETUP HOÀN TẤT (STEP 1/2)               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 SERVICES CREATED:"
echo "   1. vintern-llamacpp.service  → llama-server (port 8002)"
echo "   2. vintern-wrapper.service   → API wrapper (port 8003)"
echo ""
echo "⚠️  CHƯA CÓ MODEL! Next steps:"
echo ""
echo "1. Trên Raspberry Pi, convert model:"
echo "   cd /home/pi/Projects/Vintern-1b-v3.5-demo"
echo "   ./convert_model_rpi.sh"
echo ""
echo "2. Copy GGUF sang Orange Pi:"
echo "   scp ~/models/vintern-1b-gguf/vintern-1b-q8_0.gguf \\"
echo "       orangepi@192.168.1.16:~/models/vintern-1b-gguf/"
echo ""
echo "3. Start services trên Orange Pi:"
echo "   sudo systemctl enable vintern-llamacpp"
echo "   sudo systemctl start vintern-llamacpp"
echo "   sudo systemctl enable vintern-wrapper"
echo "   sudo systemctl start vintern-wrapper"
echo ""
echo "4. Test:"
echo "   curl http://localhost:8003/health"
echo ""
