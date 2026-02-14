#!/bin/bash
# Setup Local Inference trên Raspberry Pi + Orange Pi VLLM Proxy
# Script này sẽ cấu hình architecture phân tán đúng cách

set -e  # Exit on error

echo "=================================================="
echo "🚀 SETUP RASPBERRY PI + ORANGE PI INFERENCE"
echo "=================================================="
echo ""
echo "Architecture:"
echo "  📹 Raspberry Pi (192.168.1.14:8000)"
echo "     ├─ Backend API (camera, detection, chat)"
echo "     └─ Inference Engine (/api/generate)"
echo ""
echo "  🤖 Orange Pi (192.168.1.16:8002)"
echo "     └─ VLLM Proxy → Raspberry Pi /api/generate"
echo ""

# Raspberry Pi IP
RPI_HOST="192.168.1.14"
RPI_BACKEND_PORT="8000"

# Orange Pi IP
ORANGE_PI_HOST="192.168.1.16"
ORANGE_PI_PORT="8002"

# Paths
BACKEND_DIR="/home/pi/Projects/Vintern-1b-v3.5-demo/backend"
ENV_FILE="$BACKEND_DIR/.env"

# ==================================================
# STEP 1: Kiểm tra model đã download chưa
# ==================================================
echo "=================================================="
echo "📦 BƯỚC 1: KIỂM TRA MODEL"
echo "=================================================="
echo ""

MODEL_PATH="$BACKEND_DIR/models/Vintern-1B-v3_5"

if [ ! -d "$MODEL_PATH" ]; then
    echo "❌ Model chưa được download!"
    echo ""
    read -p "Bạn có muốn download model ngay bây giờ? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd /home/pi/Projects/Vintern-1b-v3.5-demo
        ./download_vintern_model.sh
    else
        echo "⚠️  Vui lòng chạy: ./download_vintern_model.sh trước"
        exit 1
    fi
fi

echo "✅ Model đã tồn tại: $MODEL_PATH"
echo ""

# ==================================================
# STEP 2: Config Raspberry Pi Backend
# ==================================================
echo "=================================================="
echo "🔧 BƯỚC 2: CẤU HÌNH RASPBERRY PI BACKEND"
echo "=================================================="
echo ""

# Backup .env if exists
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Đã backup .env"
fi

# Update or create .env
cat > "$ENV_FILE" << EOL
# ================================
# Raspberry Pi Backend Configuration
# ================================

# Model Mode - ENABLE LOCAL INFERENCE
MODEL_MODE=local
USE_LOCAL_MODEL=true
LOCAL_MODEL_PATH=$MODEL_PATH

# VLLM Service - Orange Pi
# Backend sẽ gọi Orange Pi VLLM, Orange Pi sẽ proxy về /api/generate
VLLM_SERVICE_URL=http://$ORANGE_PI_HOST:$ORANGE_PI_PORT

# Detection Service
DETECTION_SERVICE_URL=http://192.168.1.14:8001
USE_DETECTION_SERVICE=true
MOCK_MODE=false

# Camera Configuration
CAMERA_IDS=cam1,cam2
CAMERA_RTSP_URLS=rtsp://192.168.1.4:554/stream1,rtsp://192.168.1.7:554/stream1

# API Configuration
HOST=0.0.0.0
PORT=$RPI_BACKEND_PORT
LOG_LEVEL=INFO

# HuggingFace (optional, for logging)
HF_TOKEN=your_token_here
EOL

echo "✅ Đã tạo $ENV_FILE"
echo ""

# ==================================================
# STEP 3: Config Orange Pi VLLM Proxy
# ==================================================
echo "=================================================="
echo "🔧 BƯỚC 3: CẤU HÌNH ORANGE PI VLLM PROXY"
echo "=================================================="
echo ""

echo "Đang kết nối Orange Pi qua SSH..."
echo ""

# Create .env for Orange Pi VLLM service
ORANGE_PI_ENV_CONTENT="# ================================
# Orange Pi VLLM Proxy Configuration
# ================================

# Proxy Mode - Forward to Raspberry Pi Inference
USE_PROXY_MODE=true
BACKEND_INFERENCE_URL=http://$RPI_HOST:$RPI_BACKEND_PORT/api/generate

# Model Info (for display only)
MODEL_ID=5CD-AI/Vintern-1B-v3_5

# Server Configuration
HOST=0.0.0.0
PORT=$ORANGE_PI_PORT
LOG_LEVEL=INFO"

# Try to update Orange Pi via SSH
read -p "Nhập mật khẩu Orange Pi (orangepi@$ORANGE_PI_HOST): " -s ORANGE_PASSWORD
echo ""

# Update Orange Pi .env via SSH
echo "$ORANGE_PI_ENV_CONTENT" | ssh orangepi@$ORANGE_PI_HOST "cat > ~/Projects/Vintern-1b-v3.5-demo/vllm-service/.env"

if [ $? -eq 0 ]; then
    echo "✅ Đã cập nhật Orange Pi .env"
else
    echo "❌ Không thể cập nhật Orange Pi qua SSH"
    echo "Vui lòng tự cập nhật file .env trên Orange Pi:"
    echo ""
    echo "$ORANGE_PI_ENV_CONTENT"
    echo ""
    read -p "Nhấn Enter khi đã cập nhật xong..."
fi

echo ""

# ==================================================
# STEP 4: Restart Services
# ==================================================
echo "=================================================="
echo "🔄 BƯỚC 4: KHỞI ĐỘNG LẠI SERVICES"
echo "=================================================="
echo ""

# Restart Raspberry Pi backend (Docker)
echo "🔄 Khởi động lại Raspberry Pi backend..."
cd /home/pi/Projects/Vintern-1b-v3.5-demo
docker compose down
docker compose up -d --build

echo "✅ Backend đã khởi động"
echo ""

# Restart Orange Pi VLLM service
echo "🔄 Khởi động lại Orange Pi VLLM service..."
ssh orangepi@$ORANGE_PI_HOST "cd ~/Projects/Vintern-1b-v3.5-demo/vllm-service && docker compose down && docker compose up -d"

if [ $? -eq 0 ]; then
    echo "✅ Orange Pi VLLM service đã khởi động"
else
    echo "⚠️  Không thể khởi động Orange Pi service tự động"
    echo "Vui lòng chạy trên Orange Pi:"
    echo "  cd ~/Projects/Vintern-1b-v3.5-demo/vllm-service"
    echo "  docker compose up -d"
fi

echo ""

# ==================================================
# STEP 5: Test Services
# ==================================================
echo "=================================================="
echo "🧪 BƯỚC 5: KIỂM TRA SERVICES"
echo "=================================================="
echo ""

# Wait for services to start
echo "Đợi services khởi động (30 giây)..."
sleep 30

# Test Raspberry Pi backend
echo "🔍 Test Raspberry Pi backend..."
BACKEND_HEALTH=$(curl -s http://$RPI_HOST:$RPI_BACKEND_PORT/api/health)
echo "Response: $BACKEND_HEALTH"
echo ""

# Test Raspberry Pi inference endpoint
echo "🔍 Test Raspberry Pi inference endpoint..."
INFERENCE_TEST=$(curl -s -X POST http://$RPI_HOST:$RPI_BACKEND_PORT/api/model-info)
echo "Response: $INFERENCE_TEST"
echo ""

# Test Orange Pi VLLM
echo "🔍 Test Orange Pi VLLM..."
VLLM_HEALTH=$(curl -s http://$ORANGE_PI_HOST:$ORANGE_PI_PORT/)
echo "Response: $VLLM_HEALTH"
echo ""

# ==================================================
# DONE!
# ==================================================
echo "=================================================="
echo "✅ HOÀN TẤT SETUP!"
echo "=================================================="
echo ""
echo "📊 Services:"
echo "  ✅ Raspberry Pi Backend:    http://$RPI_HOST:$RPI_BACKEND_PORT"
echo "  ✅ Raspberry Pi Inference:  http://$RPI_HOST:$RPI_BACKEND_PORT/api/generate"
echo "  ✅ Orange Pi VLLM Proxy:    http://$ORANGE_PI_HOST:$ORANGE_PI_PORT"
echo ""
echo "🌐 Web UI:"
echo "  👉 http://$RPI_HOST:$RPI_BACKEND_PORT/"
echo ""
echo "📝 Test AI Analysis:"
echo "  1. Mở web UI"
echo "  2. Bật 'Continuous AI Analysis'"
echo "  3. Xem kết quả phân tích tự động"
echo ""
echo "🔍 Kiểm tra logs:"
echo "  docker logs -f backend        # Raspberry Pi"
echo "  ssh orangepi@$ORANGE_PI_HOST 'docker logs -f vllm-service'"
echo ""
