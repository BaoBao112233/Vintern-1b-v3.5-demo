#!/bin/bash

# Deploy Vintern-1B inference to Orange Pi using llama.cpp
# Run this script ON Raspberry Pi

set -e

ORANGEPI_IP="192.168.1.16"
ORANGEPI_USER="orangepi"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Deploy Vintern-1B Inference lên Orange Pi RV2         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 OVERVIEW:"
echo "   • Orange Pi: RISC-V CPU → dùng llama.cpp (C++)"
echo "   • Model: Vintern-1B → convert sang GGUF Q8_0"
echo "   • API: Port 8003 (wrapper), 8002 (llama-server)"
echo "   • Không còn PROXY loop!"
echo ""

# Check SSH connectivity
echo "🔍 Checking SSH connection to Orange Pi..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "$ORANGEPI_USER@$ORANGEPI_IP" exit 2>/dev/null; then
    echo "⚠️  SSH key not set up. You'll need to enter password multiple times."
    echo ""
fi

# Load Hugging Face token from .env
HF_TOKEN=""
if [ -f "backend/.env" ]; then
    HF_TOKEN=$(grep "HUGGINGFACE_TOKEN=" backend/.env | cut -d'=' -f2)
fi
if [ -z "$HF_TOKEN" ] && [ -f ".env" ]; then
    HF_TOKEN=$(grep "HUGGINGFACE_TOKEN=" .env | cut -d'=' -f2)
fi

if [ -z "$HF_TOKEN" ]; then
    echo "⚠️  HUGGINGFACE_TOKEN not found in .env files"
    read -p "Enter Hugging Face token (hf_xxx): " HF_TOKEN
fi

echo "✓ Hugging Face token loaded"
echo ""

# Copy setup script to Orange Pi
echo "📤 Copying setup script to Orange Pi..."
scp setup_orangepi_llamacpp.sh "$ORANGEPI_USER@$ORANGEPI_IP:~/"

echo "✓ Script copied"
echo ""

# Execute setup on Orange Pi
echo "🚀 Running setup on Orange Pi..."
echo "   (This will take 15-30 minutes - building llama.cpp + convert model)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Run setup with token
ssh -t "$ORANGEPI_USER@$ORANGEPI_IP" "export HUGGINGFACE_TOKEN='$HF_TOKEN' && bash ~/setup_orangepi_llamacpp.sh"

if [ $? -ne 0 ]; then
    echo "❌ Setup failed on Orange Pi"
    exit 1
fi

echo ""
echo "✓ Setup completed on Orange Pi"
echo ""

# Start services on Orange Pi
echo "🚀 Starting services on Orange Pi..."
ssh "$ORANGEPI_USER@$ORANGEPI_IP" << 'REMOTE_COMMANDS'
sudo systemctl stop vllm-service 2>/dev/null || true
sudo systemctl disable vllm-service 2>/dev/null || true

sudo systemctl enable vintern-llamacpp
sudo systemctl start vintern-llamacpp
sleep 5
sudo systemctl enable vintern-wrapper
sudo systemctl start vintern-wrapper
sleep 3

echo ""
echo "📊 Service status:"
sudo systemctl status vintern-llamacpp --no-pager -l | head -20
echo ""
sudo systemctl status vintern-wrapper --no-pager -l | head -20
REMOTE_COMMANDS

echo ""
echo "✓ Services started on Orange Pi"
echo ""

# Test Orange Pi API
echo "🧪 Testing Orange Pi API..."
sleep 2

HEALTH_RESPONSE=$(curl -s http://$ORANGEPI_IP:8003/health || echo "FAILED")
if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "✓ Orange Pi API is healthy!"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "⚠️  Orange Pi API not ready yet"
    echo "   Wait a few minutes and check: curl http://$ORANGEPI_IP:8003/health"
fi

echo ""

# Update Raspberry Pi backend configuration
echo "⚙️  Updating Raspberry Pi backend configuration..."
echo ""

BACKEND_ENV="/home/pi/Projects/Vintern-1b-v3.5-demo/backend/.env"

if [ -f "$BACKEND_ENV" ]; then
    # Backup
    cp "$BACKEND_ENV" "$BACKEND_ENV.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Update VLLM_SERVICE_URL to point to wrapper (port 8003)
    if grep -q "VLLM_SERVICE_URL" "$BACKEND_ENV"; then
        sed -i 's|^VLLM_SERVICE_URL=.*|VLLM_SERVICE_URL=http://192.168.1.16:8003|' "$BACKEND_ENV"
        echo "✓ Updated VLLM_SERVICE_URL in backend/.env"
    else
        echo "VLLM_SERVICE_URL=http://192.168.1.16:8003" >> "$BACKEND_ENV"
        echo "✓ Added VLLM_SERVICE_URL to backend/.env"
    fi
    
    # Comment out old proxy settings if exists
    sed -i 's|^BACKEND_INFERENCE_URL=|#BACKEND_INFERENCE_URL=|' "$BACKEND_ENV" 2>/dev/null || true
else
    echo "⚠️  backend/.env not found, creating..."
    cat > "$BACKEND_ENV" <<EOF
# VLLM Service on Orange Pi (llama.cpp)
VLLM_SERVICE_URL=http://192.168.1.16:8003

# Camera Configuration
CAMERA1_URL=rtsp://admin:@192.168.1.4:554/stream1
CAMERA2_URL=rtsp://admin:@192.168.1.7:554/stream1

# Detection Service
DETECTION_SERVICE_URL=http://localhost:8001
MOCK_MODE=true
EOF
    echo "✓ Created backend/.env"
fi

echo ""

# Restart backend to apply changes
echo "🔄 Restarting backend Docker container..."
cd /home/pi/Projects/Vintern-1b-v3.5-demo
docker-compose restart backend

echo ""
echo "⏳ Waiting for backend to restart..."
sleep 5

# Test full system
echo ""
echo "🧪 Testing complete system..."
echo ""

BACKEND_HEALTH=$(curl -s http://localhost:8000/api/health)
echo "Backend health:"
echo "$BACKEND_HEALTH" | python3 -m json.tool 2>/dev/null || echo "$BACKEND_HEALTH"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              ✓ DEPLOYMENT HOÀN TẤT!                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 KIẾN TRÚC MỚI:"
echo ""
echo "   ┌─────────────────────┐"
echo "   │  Raspberry Pi 4     │  ← Web UI + Backend"
echo "   │  192.168.1.14:8000  │"
echo "   └──────────┬──────────┘"
echo "              │"
echo "              │ VLLM requests"
echo "              ↓"
echo "   ┌─────────────────────┐"
echo "   │  Orange Pi RV2      │  ← Inference Engine"
echo "   │  192.168.1.16:8003  │     (llama.cpp)"
echo "   └─────────────────────┘"
echo ""
echo "✓ Không còn circular dependency!"
echo "✓ Vintern-1B chạy native trên Orange Pi RISC-V"
echo "✓ API wrapper tương thích với backend"
echo ""
echo "🌐 TEST HỆ THỐNG:"
echo "   1. Web UI: http://192.168.1.14:8000"
echo "   2. Click 'Analyze with AI' trên camera bất kỳ"
echo "   3. Hoặc enable 'Continuous Analysis'"
echo ""
echo "📊 MONITOR LOGS:"
echo "   Orange Pi:"
echo "     ssh orangepi@192.168.1.16"
echo "     sudo journalctl -u vintern-llamacpp -f"
echo "     sudo journalctl -u vintern-wrapper -f"
echo ""
echo "   Raspberry Pi:"
echo "     docker logs -f backend"
echo ""
echo "⚡ PERFORMANCE:"
echo "   • Orange Pi RV2 xử lý AI inference"
echo "   • Raspberry Pi 4 xử lý cameras + web"
echo "   • Model GGUF Q8_0 tối ưu cho CPU"
echo ""
