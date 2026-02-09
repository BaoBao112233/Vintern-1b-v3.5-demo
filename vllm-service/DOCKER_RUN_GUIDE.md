# Docker Run Guide - VLLM Service

Hướng dẫn chạy VLLM Service bằng lệnh `docker run` trực tiếp (thay vì docker compose).

## Kiến trúc

Service này chạy trên Orange Pi RV 2 (RISC-V) và hoạt động như một **proxy** chuyển tiếp request đến backend GPU server:

```
[Orange Pi RISC-V] (port 8002) → forwards to → [GPU Server] (runs Vintern model)
```

## Bước 1: Build Docker Image

```bash
cd ~/Projects/Vintern-1b-v3.5-demo/vllm-service
sudo docker build -f Dockerfile.arm64 -t vllm-service:latest .
```

## Bước 2: Chạy Container

### Lệnh đầy đủ:

```bash
sudo docker run -d \
  --name vllm-service \
  -p 8002:8002 \
  -v "$(pwd)/app:/app/app" \
  -e PORT=8002 \
  -e HOST=0.0.0.0 \
  -e SERVICE_IP=192.168.100.20 \
  -e DETECTION_SERVICE_URL=http://192.168.100.10:8001 \
  -e MODEL_ID=5CD-AI/Vintern-1B-v3_5 \
  -e BACKEND_INFERENCE_URL=http://192.168.1.14:8000 \
  -e MAX_NEW_TOKENS=256 \
  -e TEMPERATURE=0.7 \
  -e TOP_P=0.9 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  vllm-service:latest
```

### Giải thích các tham số:

- `-d`: Chạy container ở chế độ detached (background)
- `--name vllm-service`: Đặt tên container
- `-p 8002:8002`: Map port 8002 của host với port 8002 của container
- `-v "$(pwd)/app:/app/app"`: Mount thư mục app để có thể cập nhật code mà không cần rebuild
- `-e`: Các biến môi trường:
  - `PORT`: Port mà service lắng nghe
  - `HOST`: Địa chỉ bind (0.0.0.0 = tất cả interfaces)
  - `SERVICE_IP`: IP của Orange Pi trong mạng
  - `DETECTION_SERVICE_URL`: URL của detection service
  - `MODEL_ID`: Model ID trên Hugging Face
  - `BACKEND_INFERENCE_URL`: **QUAN TRỌNG** - URL của GPU backend server
  - `MAX_NEW_TOKENS`: Số token tối đa để generate
  - `TEMPERATURE`: Temperature cho sampling
  - `TOP_P`: Top-p sampling parameter
  - `LOG_LEVEL`: Mức độ log (INFO, DEBUG, etc.)
- `--restart unless-stopped`: Tự động restart container khi reboot

## Bước 3: Cấu hình Backend URL

**QUAN TRỌNG**: Trước khi chạy, cập nhật `BACKEND_INFERENCE_URL` với địa chỉ IP thực tế của máy GPU backend:

```bash
# Ví dụ: nếu GPU server ở 192.168.1.100:8000
-e BACKEND_INFERENCE_URL=http://192.168.1.100:8000 \
```

## Quản lý Container

### Xem logs:
```bash
sudo docker logs -f vllm-service
```

### Kiểm tra trạng thái:
```bash
sudo docker ps | grep vllm-service
```

### Kiểm tra logs (100 dòng cuối):
```bash
sudo docker logs --tail 100 vllm-service
```

### Stop container:
```bash
sudo docker stop vllm-service
```

### Start container:
```bash
sudo docker start vllm-service
```

### Restart container:
```bash
sudo docker restart vllm-service
```

### Remove container:
```bash
sudo docker rm -f vllm-service
```

### Xem thông tin chi tiết:
```bash
sudo docker inspect vllm-service
```

## Test Service

### Test health endpoint (từ Orange Pi):
```bash
curl http://localhost:8002/health
```

### Test health endpoint (từ máy khác trong mạng):
```bash
curl http://192.168.100.20:8002/health
```

### Test API endpoints:
```bash
# Root endpoint
curl http://localhost:8002/

# Analysis endpoint
curl -X POST http://localhost:8002/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_description": "A red car on the street",
    "detected_objects": [{"label": "car", "confidence": 0.95}],
    "question": "What color is the car?"
  }'
```

## Troubleshooting

### Container không start:
```bash
# Xem logs để tìm lỗi
sudo docker logs vllm-service

# Kiểm tra xem port 8002 có bị chiếm không
sudo netstat -tulpn | grep 8002
```

### Không kết nối được với backend:
```bash
# Test kết nối đến backend từ Orange Pi
curl http://192.168.1.14:8000/health

# Kiểm tra network
ping 192.168.1.14
```

### Container bị crash liên tục:
```bash
# Xem logs chi tiết
sudo docker logs --tail 200 vllm-service

# Chạy container không detached để xem lỗi real-time
sudo docker run --rm \
  --name vllm-service-test \
  -p 8002:8002 \
  -v "$(pwd)/app:/app/app" \
  -e PORT=8002 \
  -e HOST=0.0.0.0 \
  -e BACKEND_INFERENCE_URL=http://192.168.1.14:8000 \
  vllm-service:latest
```

### Rebuild image sau khi thay đổi code:
```bash
# Stop và remove container cũ
sudo docker rm -f vllm-service

# Rebuild image
sudo docker build -f Dockerfile.arm64 -t vllm-service:latest .

# Chạy lại container mới
sudo docker run -d \
  --name vllm-service \
  -p 8002:8002 \
  -v "$(pwd)/app:/app/app" \
  -e PORT=8002 \
  -e HOST=0.0.0.0 \
  -e SERVICE_IP=192.168.100.20 \
  -e DETECTION_SERVICE_URL=http://192.168.100.10:8001 \
  -e MODEL_ID=5CD-AI/Vintern-1B-v3_5 \
  -e BACKEND_INFERENCE_URL=http://192.168.1.14:8000 \
  -e MAX_NEW_TOKENS=256 \
  -e TEMPERATURE=0.7 \
  -e TOP_P=0.9 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  vllm-service:latest
```

## Script tự động

Tạo script để dễ quản lý:

### start_vllm.sh
```bash
#!/bin/bash
cd ~/Projects/Vintern-1b-v3.5-demo/vllm-service

sudo docker run -d \
  --name vllm-service \
  -p 8002:8002 \
  -v "$(pwd)/app:/app/app" \
  -e PORT=8002 \
  -e HOST=0.0.0.0 \
  -e SERVICE_IP=192.168.100.20 \
  -e DETECTION_SERVICE_URL=http://192.168.100.10:8001 \
  -e MODEL_ID=5CD-AI/Vintern-1B-v3_5 \
  -e BACKEND_INFERENCE_URL=http://192.168.1.14:8000 \
  -e MAX_NEW_TOKENS=256 \
  -e TEMPERATURE=0.7 \
  -e TOP_P=0.9 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  vllm-service:latest

echo "VLLM Service started!"
echo "Check logs with: sudo docker logs -f vllm-service"
```

### stop_vllm.sh
```bash
#!/bin/bash
sudo docker stop vllm-service
sudo docker rm vllm-service
echo "VLLM Service stopped!"
```

### Sử dụng scripts:
```bash
# Tạo scripts
cd ~/Projects/Vintern-1b-v3.5-demo/vllm-service
nano start_vllm.sh  # paste nội dung
nano stop_vllm.sh   # paste nội dung

# Chmod executable
chmod +x start_vllm.sh stop_vllm.sh

# Chạy
./start_vllm.sh
./stop_vllm.sh
```

## Network Configuration

Đảm bảo các service có thể giao tiếp với nhau:

- **VLLM Service (Orange Pi RV 2)**: `192.168.100.20:8002`
- **Detection Service**: `192.168.100.10:8001`
- **Backend GPU Server**: `192.168.1.14:8000` (cập nhật theo máy của bạn)

## Notes

1. Service này **chỉ là proxy**, không chạy model trực tiếp
2. Cần có backend GPU server chạy model Vintern thực sự
3. Orange Pi RV 2 (RISC-V) không thể chạy PyTorch nên phải dùng kiến trúc proxy
4. Lightweight dependencies được sử dụng (không có PyTorch, transformers)
