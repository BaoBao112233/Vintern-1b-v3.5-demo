# PC Inference Server - Vintern 1B

Server inference chạy trên PC (GTX 1050Ti) để Raspberry Pi gửi request qua LAN.

## 📊 Cấu Hình Hiện Tại

### Hardware
- **CPU**: Intel Core i3-10105F @ 3.70GHz (4C/8T)
- **RAM**: 16GB
- **GPU**: GTX 1050 Ti 4GB VRAM
- **Driver**: NVIDIA 580.126.09
- **CUDA**: 13.0 (driver-only)

### Software
- **Model**: Vintern-1B-v3.5 GGUF Q8_0 (~1GB total)
  - LLM: 644MB
  - Vision Encoder: 318MB
- **Engine**: llama.cpp (build 8067)
- **Mode**: **CPU-only** (chưa có CUDA Toolkit)
- **API**: OpenAI-compatible endpoints

## 🚀 Cách Sử Dụng

### 1. Khởi động server

```bash
cd /home/baobao/Projects/Vintern-1b-v3.5-demo/pc-inference-server
chmod +x start_server.sh
./start_server.sh
```

Server sẽ:
- Listen trên `0.0.0.0:8080` (tất cả interfaces)  
- Cho phép Raspberry Pi connect qua LAN
- Log output vào `logs/server_*.log`

### 2. Test server

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test inference với Python script
chmod +x test_server.py
python3 test_server.py path/to/image.jpg "Mô tả ảnh này"
```

### 3. Dừng server

```bash
chmod +x stop_server.sh
./stop_server.sh
```

## 📡 API Endpoints

### Health Check
```bash
GET http://<PC_IP>:8080/health
```

Response:
```json
{"status":"ok"}
```

### Chat Completions (OpenAI-compatible)
```bash
POST http://<PC_IP>:8080/v1/chat/completions
Content-Type: application/json
```

Request body:
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,<BASE64_IMAGE>"
          }
        },
        {
          "type": "text",
          "text": "Mô tả ảnh này"
        }
      ]
    }
  ],
  "max_tokens": 200,
  "temperature": 0.1
}
```

## 🔧 Tối Ưu Performance

### Hiện tại: CPU-only
- ✅ Đơn giản, stable
- ⚠️ Chậm hơn GPU (~2-3s per inference)

### Upgrade lên GPU (nếu cần):

1. **Cài CUDA Toolkit**:
```bash
sudo apt install nvidia-cuda-toolkit
```

2. **Rebuild llama.cpp với CUDA**:
```bash
cd /home/baobao/Projects/llama.cpp-vintern
rm -rf build
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=61
cmake --build build --config Release --target llama-server -j4
```

3. **Edit `start_server.sh`**: Thêm flag `-ngl 99` để offload layers lên GPU

4. **Restart server**

Performance với GPU:
- ✅ Nhanh hơn 5-10x (~0.3-0.5s per inference)
- ✅ Fit vào 4GB VRAM (model chỉ ~1GB)
- ✅ Giảm CPU usage

## 🌐 Network Configuration

### Static IP (khuyến nghị)
Để Pi dễ dàng connect, nên set static IP cho PC:

```bash
# Check current IP
ip addr show

# Example: PC = 192.168.1.100, Pi will use this IP
```

### Firewall  
Mở port 8080 nếu firewall đang bật:
```bash
sudo ufw allow 8080/tcp
# hoặc
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

### Test từ Pi
```bash
# Từ Raspberry Pi
curl http://<PC_IP>:8080/health
```

## 📊 Monitoring

### Check GPU usage (nếu có CUDA):
```bash
watch -n 1 nvidia-smi
```

### Check CPU usage:
```bash
htop
```

### Check server logs:
```bash
tail -f logs/server_*.log
```

## 🔥 Troubleshooting

### Server không start
- Kiểm tra llama-server binary tồn tại
- Kiểm tra model files đã download
- Check port 8080 có bị chiếm không: `lsof -i :8080`

### Pi không connect được
- Ping từ Pi sang PC: `ping <PC_IP>`
- Check firewall PC
- Verify server đang listen: `netstat -tlnp | grep 8080`

### Inference quá chậm
- CPU-only: bình thường, chờ 2-5s
- Cần nhanh hơn → rebuild với CUDA (xem phần Upgrade)

### Out of memory
- Model 1GB fit OK trong 4GB VRAM
- Nếu crash → giảm `ctx_size` trong `start_server.sh`  
- Hoặc dùng Q4 quantization (nhẹ hơn)

## 📝 Next Steps

1. ✅ **Server đang chạy** - test thử inference
2. ⏭️ **Setup Raspberry Pi** - cấu hình Pi gửi request qua LAN
3. ⏭️ **Integrate camera RTSP** - Pi nhận camera feed
4. ⏭️ **Full pipeline** - Camera → Detection → VLM inference → Response

## 🎯 Performance Benchmark

| Config | Inference Time | GPU VRAM | CPU Usage |
|--------|---------------|----------|-----------|
| CPU-only (current) | ~2-3s | 0 MB | ~100% (4 cores) |
| GPU CUDA (todo) | ~0.3-0.5s | ~1.2 GB | ~20% |

---

**Liên hệ**: Đang test, sẽ update khi có vấn đề!
