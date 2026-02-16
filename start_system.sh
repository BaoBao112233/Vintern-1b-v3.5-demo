#!/bin/bash
# Quick Start Script - Khởi động hệ thống Camera + VLLM

echo "=========================================="
echo "🚀 KHỞI ĐỘNG HỆ THỐNG CAMERA + VLLM"
echo "=========================================="
echo ""

# Change to project directory
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Check if backend is already running
if lsof -Pi :8005 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Backend đã chạy trên port 8005"
    echo ""
    read -p "Khởi động lại backend? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Dừng backend cũ..."
        pkill -f "backend_service.py" || true
        sleep 2
    else
        echo "✅ Sử dụng backend hiện có"
        echo ""
        echo "API URL: http://192.168.1.14:8005"
        echo "API Docs: http://192.168.1.14:8005/docs"
        exit 0
    fi
fi

# Start backend service
echo "🚀 Khởi động Backend Service..."
echo ""

HOST_IP=0.0.0.0 BACKEND_PORT=8005 python3 backend_service.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Log file: /tmp/backend.log"
echo ""

# Wait for backend to start
echo "⏳ Đợi backend khởi động (5 giây)..."
sleep 5

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "❌ Backend không khởi động được!"
    echo ""
    echo "Chi tiết lỗi:"
    tail -20 /tmp/backend.log
    exit 1
fi

# Test health endpoint
echo "🏥 Kiểm tra health endpoint..."
HEALTH_CHECK=$(curl -s http://localhost:8005/health 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Backend đang hoạt động!"
    echo ""
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
    echo ""
else
    echo "⚠️  Không thể kết nối đến backend"
    echo "Kiểm tra log: tail -f /tmp/backend.log"
    exit 1
fi

# Display info
echo ""
echo "=========================================="
echo "✅ HỆ THỐNG ĐÃ SẴN SÀNG"
echo "=========================================="
echo ""
echo "📡 Backend API:"
echo "   URL: http://192.168.1.14:8005"
echo "   Docs: http://192.168.1.14:8005/docs"
echo ""
echo "📹 Cameras:"
echo "   Camera 1: 192.168.1.4"
echo "   Camera 2: 192.168.1.7"
echo ""
echo "🎯 Quick Commands:"
echo ""
echo "   # Chụp frame từ camera 1"
echo "   curl http://localhost:8005/api/capture/1 -o camera1.jpg"
echo ""
echo "   # Test API"
echo "   python3 test_backend_api.py --test capture --camera 1"
echo ""
echo "   # Monitor camera liên tục"
echo "   python3 analyze_camera.py --camera 1 --interval 5"
echo ""
echo "   # Xem log"
echo "   tail -f /tmp/backend.log"
echo ""
echo "   # Dừng backend"
echo "   pkill -f backend_service.py"
echo ""
echo "=========================================="
echo ""

# Optional: Run test
read -p "Chạy test ngay bây giờ? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧪 Chạy test..."
    echo ""
    python3 test_backend_api.py --test capture --camera 1
fi

echo ""
echo "✅ Hoàn tất!"
echo ""
