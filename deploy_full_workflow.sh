#!/bin/bash

# Complete deployment: Convert on Raspberry Pi → Setup Orange Pi → Copy model → Start services
# This script handles the full workflow

set -e

ORANGEPI_IP="192.168.1.16"
ORANGEPI_USER="orangepi"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Deploy Vintern-1B to Orange Pi (2-Step Process)       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 WORKFLOW:"
echo "   Step 1: Convert model trên Raspberry Pi (~15 phút)"
echo "   Step 2: Setup llama.cpp trên Orange Pi (~10 phút)"
echo "   Step 3: Copy GGUF model sang Orange Pi (~2 phút)"
echo "   Step 4: Start services và test"
echo ""
echo "⏱️  Total time: ~30 phút"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# ============================================
# STEP 1: Convert model on Raspberry Pi
# ============================================
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  STEP 1: Convert Model on Raspberry Pi ║"
echo "╚════════════════════════════════════════╝"
echo ""

if [ -f "$HOME/models/vintern-1b-gguf/vintern-1b-q8_0.gguf" ]; then
    echo "✓ GGUF model already exists"
    MODEL_SIZE=$(du -h "$HOME/models/vintern-1b-gguf/vintern-1b-q8_0.gguf" | cut -f1)
    echo "   Size: $MODEL_SIZE"
    read -p "Skip conversion? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "⏩ Skipping conversion"
    else
        ./convert_model_rpi.sh || exit 1
    fi
else
    echo "Starting model conversion..."
    ./convert_model_rpi.sh || exit 1
fi

GGUF_FILE="$HOME/models/vintern-1b-gguf/vintern-1b-q8_0.gguf"
if [ ! -f "$GGUF_FILE" ]; then
    echo "❌ Conversion failed: GGUF file not found"
    exit 1
fi

echo ""
echo "✓ Model ready: $GGUF_FILE"
echo ""

# ============================================
# STEP 2: Setup Orange Pi
# ============================================
echo "╔════════════════════════════════════════╗"
echo "║  STEP 2: Setup llama.cpp on Orange Pi  ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Test SSH
echo "🔍 Testing SSH connection..."
if ! ping -c 1 $ORANGEPI_IP &>/dev/null; then
    echo "❌ Cannot reach Orange Pi at $ORANGEPI_IP"
    exit 1
fi

echo "✓ Orange Pi reachable"
echo ""

# Copy setup script
echo "📤 Copying setup script to Orange Pi..."
scp setup_orangepi_simple.sh "$ORANGEPI_USER@$ORANGEPI_IP:~/"

echo "✓ Script copied"
echo ""

# Run setup on Orange Pi
echo "🚀 Running setup on Orange Pi..."
ssh -t "$ORANGEPI_USER@$ORANGEPI_IP" "bash ~/setup_orangepi_simple.sh"

if [ $? -ne 0 ]; then
    echo "❌ Setup failed on Orange Pi"
    exit 1
fi

echo ""
echo "✓ Orange Pi setup complete"
echo ""

# ============================================
# STEP 3: Copy GGUF model to Orange Pi
# ============================================
echo "╔════════════════════════════════════════╗"
echo "║  STEP 3: Copy Model to Orange Pi       ║"
echo "╚════════════════════════════════════════╝"
echo ""

echo "📤 Copying GGUF model (~1.4GB)..."
echo "   This takes ~2-3 minutes..."

# Create directory on Orange Pi
ssh "$ORANGEPI_USER@$ORANGEPI_IP" "mkdir -p ~/models/vintern-1b-gguf"

# Copy GGUF file
scp "$GGUF_FILE" "$ORANGEPI_USER@$ORANGEPI_IP:~/models/vintern-1b-gguf/" || {
    echo "❌ Failed to copy model"
    exit 1
}

echo "✓ Model copied successfully"
echo ""

# ============================================
# STEP 4: Start services
# ============================================
echo "╔════════════════════════════════════════╗"
echo "║  STEP 4: Start Services on Orange Pi   ║"
echo "╚════════════════════════════════════════╝"
echo ""

echo "🚀 Starting services..."
ssh "$ORANGEPI_USER@$ORANGEPI_IP" << 'REMOTE'
# Stop old services if any
sudo systemctl stop vllm-service 2>/dev/null || true
sudo systemctl disable vllm-service 2>/dev/null || true

# Enable and start new services
sudo systemctl enable vintern-llamacpp
sudo systemctl start vintern-llamacpp

echo "⏳ Waiting for llama-server to start..."
sleep 10

sudo systemctl enable vintern-wrapper
sudo systemctl start vintern-wrapper

sleep 3

echo ""
echo "📊 Service status:"
sudo systemctl status vintern-llamacpp --no-pager | head -15
echo ""
sudo systemctl status vintern-wrapper --no-pager | head -15
REMOTE

echo ""
echo "✓ Services started"
echo ""

# ============================================
# STEP 5: Test system
# ============================================
echo "╔════════════════════════════════════════╗"
echo "║  STEP 5: Test System                    ║"
echo "╚════════════════════════════════════════╝"
echo ""

echo "🧪 Testing Orange Pi API..."
sleep 2

HEALTH=$(curl -s http://$ORANGEPI_IP:8003/health 2>&1 || echo "FAILED")
if [[ "$HEALTH" == *"healthy"* ]]; then
    echo "✓ API is healthy!"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "⚠️  API not responding yet"
    echo "   Response: $HEALTH"
    echo ""
    echo "   Wait a few minutes for model loading..."
    echo "   Check logs: ssh orangepi@$ORANGEPI_IP 'sudo journalctl -u vintern-llamacpp -f'"
fi

echo ""

# ============================================
# STEP 6: Update Raspberry Pi backend
# ============================================
echo "╔════════════════════════════════════════╗"
echo "║  STEP 6: Update Raspberry Pi Backend   ║"
echo "╚════════════════════════════════════════╝"
echo ""

BACKEND_ENV="backend/.env"
if [ -f "$BACKEND_ENV" ]; then
    # Backup
    cp "$BACKEND_ENV" "$BACKEND_ENV.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Update or add VLLM_SERVICE_URL
    if grep -q "VLLM_SERVICE_URL" "$BACKEND_ENV"; then
        sed -i 's|^VLLM_SERVICE_URL=.*|VLLM_SERVICE_URL=http://192.168.1.16:8003|' "$BACKEND_ENV"
        sed -i 's|^#VLLM_SERVICE_URL=.*|VLLM_SERVICE_URL=http://192.168.1.16:8003|' "$BACKEND_ENV"
        echo "✓ Updated VLLM_SERVICE_URL in backend/.env"
    else
        echo "" >> "$BACKEND_ENV"
        echo "# VLLM Service on Orange Pi (llama.cpp)" >> "$BACKEND_ENV"
        echo "VLLM_SERVICE_URL=http://192.168.1.16:8003" >> "$BACKEND_ENV"
        echo "✓ Added VLLM_SERVICE_URL to backend/.env"
    fi
fi

echo ""
echo "🔄 Restarting backend..."
docker-compose restart backend

echo "⏳ Waiting for backend..."
sleep 5

echo ""
echo "🧪 Testing backend health..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/api/health)
echo "$BACKEND_HEALTH" | python3 -m json.tool 2>/dev/null || echo "$BACKEND_HEALTH"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              ✓ DEPLOYMENT COMPLETE!                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 ARCHITECTURE:"
echo ""
echo "   ┌─────────────────────┐"
echo "   │  Raspberry Pi 4     │  Backend + Cameras"
echo "   │  192.168.1.14:8000  │"
echo "   └──────────┬──────────┘"
echo "              │"
echo "              │ VLLM API (port 8003)"
echo "              ↓"
echo "   ┌─────────────────────┐"
echo "   │  Orange Pi RV2      │  Vintern-1B Inference"
echo "   │  192.168.1.16:8003  │  llama.cpp (native)"
echo "   └─────────────────────┘"
echo ""
echo "🌐 WEB UI: http://192.168.1.14:8000"
echo "   • Hard refresh: Ctrl + Shift + R"
echo "   • Click 'Analyze with AI' to test"
echo ""
echo "📊 MONITOR:"
echo "   Orange Pi logs:"
echo "     ssh orangepi@192.168.1.16"
echo "     sudo journalctl -u vintern-llamacpp -f"
echo "     sudo journalctl -u vintern-wrapper -f"
echo ""
echo "   Backend logs:"
echo "     docker logs -f backend"
echo ""
