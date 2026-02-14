# Hướng dẫn Fix VLLM Service (Orange Pi)

## Vấn đề hiện tại
VLLM service đang chạy ở chế độ **proxy mode** và gây ra circular dependency:
```
Backend (192.168.1.14:8000) → VLLM (192.168.1.16:8002) → Backend (192.168.1.14:8000) ❌
```

Response từ VLLM:
```json
{
  "success": true,
  "response": "Backend service unavailable. Please ensure the inference service is running at http://192.168.1.14:8000"
}
```

## Giải pháp

### Bước 1: SSH vào Orange Pi
```bash
ssh orangepi@192.168.1.16
# Nhập password của orangepi user
```

### Bước 2: Tìm VLLM service
```bash
# Tìm thư mục VLLM service
find ~/ -name "vllm-service" -type d 2>/dev/null
ls -la ~/vllm-service/ || ls -la ~/Projects/ | grep vllm

# Kiểm tra process đang chạy
ps aux | grep -E "python.*8002|uvicorn.*8002" | grep -v grep
```

### Bước 3: Kiểm tra cấu hình hiện tại
```bash
cd ~/vllm-service  # hoặc đường dẫn bạn tìm được

# Xem file cấu hình
cat .env
cat app/main.py | grep -A10 "mode\|proxy\|backend"
```

### Bước 4: Sửa cấu hình
Tìm và sửa file `.env` hoặc file cấu hình chính:

**TÌM:**
```bash
MODE=proxy
BACKEND_URL=http://192.168.1.14:8000
```

**ĐỔI THÀNH:**
```bash
MODE=vllm  # hoặc MODE=direct
# Comment hoặc xóa dòng BACKEND_URL
# BACKEND_URL=http://192.168.1.14:8000
```

### Bước 5: Đảm bảo model được load
```bash
# Kiểm tra model path
echo $MODEL_PATH
ls -la models/ || ls -la ~/.cache/huggingface/hub/

# Nếu chưa có model, download:
python3 download_model.py  # nếu có script
# hoặc
huggingface-cli download 5CD-AI/Vintern-1B-v3_5
```

### Bước 6: Restart VLLM service
```bash
# Stop service
pkill -f "uvicorn.*8002" || pkill -f "python.*8002"

# Start lại
cd ~/vllm-service
source venv/bin/activate  # nếu dùng virtualenv
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Hoặc nếu có script startup:
./start.sh
```

### Bước 7: Kiểm tra từ Raspberry Pi
```bash
# Từ Raspberry Pi, test VLLM service
curl -s http://192.168.1.16:8002/health | python3 -m json.tool

# Test analyze endpoint
curl -s -X POST http://192.168.1.16:8002/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_description":"Test camera",
    "detected_objects":[{"label":"person","confidence":0.9}],
    "question":"What do you see?"
  }' | python3 -m json.tool
```

Kết quả mong đợi:
```json
{
  "success": true,
  "response": "I can see a person in the image...",  // ← Phản hồi thực từ model
  "model_info": {
    "mode": "vllm",  // ← Không còn "proxy"
    "is_loaded": true
  }
}
```

## Alternative: Nếu không thể SSH

### Option A: Restart từ xa (nếu có systemd)
```bash
# Từ Raspberry Pi
ssh orangepi@192.168.1.16 "systemctl --user restart vllm-service"
```

### Option B: Tạm thời disable VLLM và dùng detection only
Trong file `.env` của Raspberry Pi:
```bash
# Comment out VLLM service
# VLLM_SERVICE_URL=http://192.168.1.16:8002
```

Restart backend:
```bash
sudo systemctl restart vintern-backend
# hoặc
pkill -f "uvicorn.*8000"
cd ~/Projects/Vintern-1b-v3.5-demo/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Kiểm tra sau khi fix

1. **Health check:**
```bash
curl http://localhost:8000/api/health | python3 -m json.tool
```

Kỳ vọng thấy:
```json
{
  "vllm_ready": true,
  "vllm_info": {
    "vllm_url": "http://192.168.1.16:8002",
    "available": true,
    "status": "ready"
  }
}
```

2. **Test qua web interface:**
- Mở http://192.168.1.14:8000/
- Hard refresh (Ctrl+Shift+R)
- Bật "🤖 Continuous AI Analysis"
- Kiểm tra status bar: "VLLM AI" phải hiện màu xanh ✅
- Click "Analyze with AI" trên mỗi camera
- Xem response trong phần "AI Analysis"

## Troubleshooting

### VLLM không start được
```bash
# Kiểm tra logs
journalctl -u vllm-service -f  # nếu dùng systemd
# hoặc
tail -f ~/vllm-service/logs/*.log
```

### Out of memory
```bash
# Kiểm tra RAM
free -h
# Nếu thiếu RAM, dùng quantized model hoặc giảm context length
```

### Model không load được
```bash
# Verify model files
ls -lh ~/.cache/huggingface/hub/models--5CD-AI--Vintern-1B-v3_5/

# Re-download nếu cần
rm -rf ~/.cache/huggingface/hub/models--5CD-AI--Vintern-1B-v3_5/
huggingface-cli download 5CD-AI/Vintern-1B-v3_5
```

## Liên hệ
Nếu vẫn gặp vấn đề, cần thông tin sau để debug:
1. Output của `ps aux | grep 8002`
2. Nội dung file `.env` của VLLM service
3. Logs từ VLLM service
4. Hardware info: `free -h && df -h`
