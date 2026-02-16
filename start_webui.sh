#!/bin/bash
# Start Web UI System - Full stack với Web interface

echo "=========================================="
echo "🌐 KHỞI ĐỘNG WEB UI SYSTEM"
echo "=========================================="
echo ""

cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

# Stop old backend if running
if lsof -Pi :8005 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "🛑 Dừng backend cũ..."
    pkill -f backend_service.py || true
    sleep 2
fi

# Check PC VLLM service
echo "🔍 Kiểm tra PC VLLM service (192.168.1.3:8080)..."
if curl -s -m 3 http://192.168.1.3:8080/health > /dev/null 2>&1; then
    echo "✅ PC VLLM service: OK"
else
    echo "❌ PC VLLM service: KHÔNG KẾT NỐI ĐƯỢC"
    echo ""
    echo "Vui lòng kiểm tra:"
    echo "  1. PC có đang chạy không?"
    echo "  2. llama-server có đang chạy trên port 8080?"
    echo "  3. Firewall có block không?"
    echo ""
    read -p "Tiếp tục không? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Check cameras
echo "🔍 Kiểm tra cameras..."
for cam_id in 1 2; do
    if [ $cam_id -eq 1 ]; then
        cam_ip="192.168.1.4"
    else
        cam_ip="192.168.1.7"
    fi
    
    # Quick ping test
    if ping -c 1 -W 1 $cam_ip > /dev/null 2>&1; then
        echo "✅ Camera $cam_id ($cam_ip): Reachable"
    else
        echo "⚠️  Camera $cam_id ($cam_ip): Không ping được"
    fi
done

echo ""

# Start backend
echo "🚀 Khởi động Backend Service..."
HOST_IP=0.0.0.0 BACKEND_PORT=8005 python3 backend_service.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo ""

# Wait for backend
echo "⏳ Đợi backend khởi động (5 giây)..."
sleep 5

# Check backend
if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "❌ Backend không khởi động được!"
    echo ""
    echo "Chi tiết lỗi:"
    tail -20 /tmp/backend.log
    exit 1
fi

# Test health
echo "🏥 Kiểm tra backend health..."
HEALTH=$(curl -s http://localhost:8005/health 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Backend đang hoạt động!"
    echo ""
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "❌ Không thể kết nối đến backend"
    echo "Xem log: tail -f /tmp/backend.log"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ HỆ THỐNG ĐÃ SẴN SÀNG"
echo "=========================================="
echo ""
echo "🌐 WEB UI:"
echo "   - Trên Pi: http://localhost:8005/"
echo "   - Từ máy khác: http://192.168.1.14:8005/"
echo ""
echo "📡 Backend API:"
echo "   - Health: http://192.168.1.14:8005/health"
echo "   - Docs: http://192.168.1.14:8005/docs"
echo ""
echo "📹 Cameras:"
echo "   - Camera 1: 192.168.1.4"
echo "   - Camera 2: 192.168.1.7"
echo ""
echo "🤖 VLLM:"
echo "   - PC Service: http://192.168.1.3:8080"
echo ""
echo "📝 Logs:"
echo "   - Backend: tail -f /tmp/backend.log"
echo ""
echo "🛑 Dừng hệ thống:"
echo "   pkill -f backend_service.py"
echo ""
echo "=========================================="
echo ""

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "🌐 MỞ TRÌNH DUYỆT:"
echo ""
echo "   http://$LOCAL_IP:8005/"
echo ""
echo "   hoặc"
echo ""
echo "   http://192.168.1.14:8005/"
echo ""
echo "=========================================="
echo ""

# Optional: Open browser if on desktop
if [ -n "$DISPLAY" ] && command -v xdg-open > /dev/null 2>&1; then
    read -p "Mở browser ngay bây giờ? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open "http://localhost:8005/" 2>/dev/null &
    fi
fi

echo "✅ Hoàn tất!"
echo ""
