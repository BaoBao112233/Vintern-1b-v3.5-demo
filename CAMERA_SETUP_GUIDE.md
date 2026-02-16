# 🎥 Hướng Dẫn Sử Dụng Hệ Thống Camera + VLLM

Hệ thống đã được cấu hình để kết nối camera Dahua với backend API tích hợp VLLM.

## 📋 Thông Tin Cấu Hình

### Camera
- **Camera 1**: 192.168.1.4 
- **Camera 2**: 192.168.1.7
- **Username**: admin
- **Password**: abcd12345
- **RTSP URL**: `rtsp://admin:abcd12345@192.168.1.{4|7}/cam/realmonitor?channel=1&subtype=1`

### Backend API
- **Host**: 192.168.1.14 (Raspberry Pi)
- **Port**: 8005
- **URL**: http://192.168.1.14:8005
- **Documentation**: http://192.168.1.14:8005/docs

### VLLM Service
- **Backend hiện tại**: HuggingFace API
- **Model**: 5CD-AI/Vintern-1B-v3_5
- **Token**: Đã cấu hình trong .env

## 🚀 Khởi Động Hệ Thống

### 1. Khởi động Backend Service

```bash
cd /home/pi/Projects/Vintern-1b-v3.5-demo

# Chạy backend trên port 8005
HOST_IP=0.0.0.0 BACKEND_PORT=8005 python3 backend_service.py > /tmp/backend.log 2>&1 &

# Kiểm tra log
tail -f /tmp/backend.log
```

### 2. Kiểm Tra Trạng Thái

```bash
# Health check
curl http://localhost:8005/health | python3 -m json.tool

# Danh sách cameras
curl http://localhost:8005/api/cameras | python3 -m json.tool
```

## 🎯 Sử Dụng API

### 1. Chụp Frame Từ Camera

```bash
# Camera 1
curl http://localhost:8005/api/capture/1 -o camera1.jpg

# Camera 2
curl http://localhost:8005/api/capture/2 -o camera2.jpg
```

### 2. Phân Tích Frame với VLLM

#### Sử dụng curl:
```bash
curl -X POST http://localhost:8005/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 1,
    "prompt": "Mô tả những gì bạn thấy trong ảnh. Có người không? Có xe không?",
    "save_frame": true
  }' | python3 -m json.tool
```

#### Sử dụng Python:
```python
import requests
import json

# Phân tích camera 1
response = requests.post(
    "http://localhost:8005/api/analyze",
    json={
        "camera_id": 1,
        "prompt": "Describe what you see. Any people or vehicles?",
        "save_frame": True
    }
)

result = response.json()
if result['success']:
    print(f"Analysis: {result['response']}")
    print(f"Latency: {result['latency_ms']:.1f}ms")
else:
    print(f"Error: {result['error']}")
```

### 3. Monitor Liên Tục (Server-Sent Events)

```bash
# Monitor camera 1, 5 giây/lần, tối đa 10 lần
curl -N http://localhost:8005/api/monitor/1?interval=5&max_iterations=10
```

## 🛠️ Scripts Tiện Ích

### 1. Test Backend API

```bash
cd /home/pi/Projects/Vintern-1b-v3.5-demo

# Test tất cả
python3 test_backend_api.py

# Test chỉ capture
python3 test_backend_api.py --test capture --camera 1

# Test phân tích
python3 test_backend_api.py --test analyze --camera 1
```

### 2. Analyze Camera (Standalone)

```bash
# Phân tích camera 1, 5 giây/lần, tối đa 3 lần
python3 analyze_camera.py --camera 1 --interval 5 --max-iterations 3 --save-frames

# Chạy liên tục (Ctrl+C để dừng)
python3 analyze_camera.py --camera 2 --interval 10 --save-frames
```

## 📊 API Endpoints

| Method | Endpoint | Mô Tả |
|--------|----------|-------|
| GET | `/health` | Kiểm tra trạng thái service |
| GET | `/api/cameras` | Danh sách cameras |
| GET | `/api/capture/{camera_id}` | Chụp frame từ camera |
| POST | `/api/analyze` | Phân tích frame với VLLM |
| GET | `/api/monitor/{camera_id}` | Monitor liên tục (SSE) |

## 🔧 Cấu Hình VLLM Backend

Hệ thống hỗ trợ 3 loại backend:

### 1. HuggingFace API (Hiện tại)
```bash
# Trong .env
VLM_BACKEND=hf
HUGGINGFACE_TOKEN=your_token_here
```

**Lưu ý**: HuggingFace Inference API có thể không ổn định hoặc model không khả dụng.

### 2. Local VLLM Service
```bash
# Trong .env
VLM_BACKEND=vllm
VLLM_SERVICE_URL=http://192.168.1.16:8003
```

**Yêu cầu**: Cần có VLLM service (llama.cpp) chạy trên máy khác trong mạng LAN.

### 3. PC Inference Server
```bash
# Trong .env
VLM_BACKEND=pc
VLLM_SERVICE_URL=http://192.168.1.100:8080
```

**Yêu cầu**: Cần setup PC theo hướng dẫn trong `pc-inference-server/README.md`

## 🔍 Troubleshooting

### Camera không kết nối được

```bash
# Test RTSP trực tiếp với ffmpeg
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.4/cam/realmonitor?channel=1&subtype=1" -frames:v 1 test.jpg
```

### Backend service không khởi động

```bash
# Kiểm tra process
ps aux | grep backend_service

# Kiểm tra log
tail -50 /tmp/backend.log

# Kiểm tra port
lsof -i :8005
```

### VLLM phân tích lỗi

1. **HuggingFace API không khả dụng**: 
   - Model có thể không hỗ trợ Inference API
   - Chuyển sang sử dụng PC inference server

2. **Local VLLM không kết nối được**:
   ```bash
   # Kiểm tra connection
   curl http://192.168.1.16:8003/health
   ```

## 📝 Ví Dụ Tích Hợp

### Backend FastAPI Service

```python
from app.services.rtsp_camera import RTSPCamera
from app.services.vintern_client import VinternClient

# Khởi tạo
camera = RTSPCamera(
    "rtsp://admin:password@192.168.1.4/cam/realmonitor?channel=1&subtype=1",
    "Camera_1"
)

vlm = VinternClient(
    hf_token="your_token",
    vllm_url="http://192.168.1.16:8003",
    backend="vllm"  # hoặc "hf" hoặc "pc"
)

# Capture và phân tích
result = camera.capture_frame()
if result:
    _, frame_bytes = result
    analysis = vlm.analyze_image(
        frame_bytes,
        "Describe what you see"
    )
    print(analysis['response'])
```

### Smart Analysis (nhiều câu hỏi)

Tham khảo `smart_analyze.py` để phân tích chi tiết bằng nhiều câu hỏi liên tiếp:

```bash
# Chụp frame trước
curl http://localhost:8005/api/capture/1 -o test.jpg

# Phân tích smart
python3 smart_analyze.py test.jpg
```

**Lưu ý**: `smart_analyze.py` hiện chỉ hoạt động khi có PC inference server hoặc local VLLM đang chạy.

## 🎯 Next Steps

1. **Setup PC Inference Server** (khuyến nghị):
   - Xem `pc-inference-server/README.md`
   - Download model Vintern-1B-v3.5 GGUF
   - Chạy llama-server trên PC

2. **Tích hợp Detection Service**:
   - Sử dụng Coral USB accelerator (nếu có)
   - Object detection trước khi gửi VLLM

3. **Setup Frontend**:
   - React app để hiển thị camera feeds
   - Real-time analysis results
   - Chat interface

## 📞 Liên Hệ / Support

- Xem thêm: `ARCHITECTURE.md`, `PI_INTEGRATION_GUIDE.md`
- API Docs: http://192.168.1.14:8005/docs
