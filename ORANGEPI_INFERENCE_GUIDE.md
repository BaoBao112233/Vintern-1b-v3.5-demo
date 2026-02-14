# Chạy Vintern-1B trên Orange Pi RISC-V

## 🎯 Mục Tiêu

Chạy model Vintern-1B **native** trên Orange Pi RV2 (RISC-V) để phân tán tải, giải quyết vấn đề:
- ✅ Không làm quá tải Raspberry Pi 4
- ✅ Sử dụng computing power của Orange Pi
- ✅ Loại bỏ circular dependency của proxy mode
- ✅ AI inference chạy song song với camera streaming

## 🔧 Giải Pháp: llama.cpp

Orange Pi RV2 có CPU RISC-V không hỗ trợ PyTorch, nhưng có thể chạy **llama.cpp**:

### Tại sao llama.cpp?
- ✅ **Pure C++**: Compile được trên mọi kiến trúc (ARM, RISC-V, x86)
- ✅ **Hiệu quả cao**: Tối ưu cho CPU inference
- ✅ **GGUF format**: Model được quantize, tiết kiệm RAM
- ✅ **Vision support**: Hỗ trợ multimodal (text + image)
- ✅ **Active development**: Cộng đồng lớn, update thường xuyên

### Quantization
Model Vintern-1B (1.3GB) sẽ được convert sang **GGUF Q8_0**:
- Original FP16: ~2.6GB
- Q8_0: ~1.4GB (8-bit quantization)
- Q4_K_M: ~800MB (4-bit, nếu cần nhẹ hơn)
- Minimal loss trong accuracy với Q8_0

## 📦 Kiến Trúc Mới

```
┌─────────────────────────────────────────────────┐
│           Raspberry Pi 4 (ARM64)                │
│         192.168.1.14:8000                       │
│                                                 │
│  • FastAPI Backend                              │
│  • Camera streaming (2 cameras)                 │
│  • Object detection (Coral USB)                 │
│  • Web UI (HTML/JS)                             │
│                                                 │
└────────────────┬────────────────────────────────┘
                 │
                 │ HTTP Request
                 │ POST /analyze (image + prompt)
                 ↓
┌─────────────────────────────────────────────────┐
│          Orange Pi RV2 (RISC-V)                 │
│         192.168.1.16:8003                       │
│                                                 │
│  Port 8003: FastAPI Wrapper                     │
│    └─> /analyze → Format request                │
│    └─> /chat    → Forward to llama-server       │
│    └─> /health  → Status check                  │
│                                                 │
│  Port 8002: llama-server                        │
│    └─> Vintern-1B GGUF Q8_0                     │
│    └─> Native RISC-V inference                  │
│    └─> 2048 context, 256 max tokens             │
│                                                 │
└─────────────────────────────────────────────────┘
```

## 🚀 Deployment

### Option 1: Automatic (Khuyến nghị)

Chạy từ Raspberry Pi, script sẽ tự động SSH và setup Orange Pi:

```bash
cd /home/pi/Projects/Vintern-1b-v3.5-demo
./deploy_orangepi_inference.sh
```

Script này sẽ:
1. Copy `setup_orangepi_llamacpp.sh` sang Orange Pi
2. SSH vào Orange Pi và chạy setup (build llama.cpp + convert model)
3. Tạo systemd services trên Orange Pi
4. Start services
5. Test API
6. Update backend/.env trên Raspberry Pi
7. Restart backend Docker container

**Thời gian**: 20-30 phút (build llama.cpp + convert model)

### Option 2: Manual

#### Trên Orange Pi (192.168.1.16):

```bash
# Copy script từ Raspberry Pi
scp pi@192.168.1.14:~/Projects/Vintern-1b-v3.5-demo/setup_orangepi_llamacpp.sh ~/

# Run setup
bash ~/setup_orangepi_llamacpp.sh

# Start services
sudo systemctl enable vintern-llamacpp
sudo systemctl start vintern-llamacpp
sudo systemctl enable vintern-wrapper
sudo systemctl start vintern-wrapper

# Check status
sudo systemctl status vintern-llamacpp
sudo systemctl status vintern-wrapper

# Test API
curl http://localhost:8003/health
curl http://localhost:8003/model/info
```

#### Trên Raspberry Pi (192.168.1.14):

```bash
# Update backend/.env
echo "VLLM_SERVICE_URL=http://192.168.1.16:8003" >> backend/.env

# Restart backend
docker-compose restart backend

# Test
curl http://localhost:8000/api/health
```

## 📊 Services trên Orange Pi

### 1. vintern-llamacpp.service
- **Port**: 8002
- **Command**: `llama-server --model ~/models/vintern-1b-gguf/vintern-1b-q8_0.gguf`
- **Purpose**: Native inference engine
- **Logs**: `sudo journalctl -u vintern-llamacpp -f`

### 2. vintern-wrapper.service
- **Port**: 8003
- **Command**: `python3 llamacpp_wrapper.py`
- **Purpose**: API compatibility layer (FastAPI)
- **Logs**: `sudo journalctl -u vintern-wrapper -f`

### API Endpoints (port 8003):

```bash
# Health check
GET /health
→ {"status": "healthy", "model": "Vintern-1B-v3_5", "backend": "llama.cpp"}

# Model info
GET /model/info
→ {"model_id": "5CD-AI/Vintern-1B-v3_5", "mode": "native", "format": "GGUF Q8_0"}

# Analyze image
POST /analyze
{
  "image": "base64_encoded_image",
  "prompt": "Describe this image",
  "max_tokens": 256,
  "temperature": 0.7
}

# Chat (with optional image)
POST /chat
{
  "message": "What do you see?",
  "image": "base64_encoded_image",  # Optional
  "max_tokens": 256
}
```

## 🧪 Testing

### Test Orange Pi API trực tiếp:

```bash
# From Raspberry Pi
curl http://192.168.1.16:8003/health

# Health check with details
curl -s http://192.168.1.16:8003/health | jq .

# Model info
curl -s http://192.168.1.16:8003/model/info | jq .
```

### Test với image:

```bash
# Capture frame from camera
curl -s http://localhost:8000/api/cameras/1/frame | jq -r '.image_base64' > /tmp/frame.b64

# Send to Orange Pi for analysis
curl -X POST http://192.168.1.16:8003/analyze \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"$(cat /tmp/frame.b64)\", \"prompt\": \"Mô tả chi tiết những gì bạn thấy trong hình\"}"
```

### Test từ Web UI:

1. Mở http://192.168.1.14:8000/
2. Kiểm tra VLLM status trong status bar (phải là "Ready")
3. Click "Analyze with AI" trên camera 1 hoặc 2
4. Hoặc enable "Continuous AI Analysis"
5. Xem kết quả trong AI analysis box

## 📈 Performance

### Orange Pi RV2 Specs:
- **CPU**: Ky X1 (RISC-V), 2 cores @ 1.5GHz
- **RAM**: 2GB hoặc 4GB
- **Expected inference**: 2-5 tokens/second (text), 10-20s per image

### Model Size:
- **Original**: ~2.6GB (FP16)
- **GGUF Q8_0**: ~1.4GB
- **GGUF Q4_K_M**: ~800MB (optional, faster but less accurate)

### Resource Usage:
- **RAM**: ~1.5GB cho model + ~500MB cho runtime
- **CPU**: ~80-100% during inference
- **Idle**: ~2-5% CPU

## 🛠️ Troubleshooting

### Service không start

```bash
# Check logs
sudo journalctl -u vintern-llamacpp -n 50
sudo journalctl -u vintern-wrapper -n 50

# Check if llama-server is running
ps aux | grep llama-server

# Check port
sudo netstat -tlnp | grep :8002
sudo netstat -tlnp | grep :8003
```

### Model không load

```bash
# Check model file exists
ls -lh ~/models/vintern-1b-gguf/vintern-1b-q8_0.gguf

# Check RAM
free -h

# Try loading manually
~/llama.cpp/llama-server \
  --model ~/models/vintern-1b-gguf/vintern-1b-q8_0.gguf \
  --host 127.0.0.1 \
  --port 8002 \
  --ctx-size 2048 \
  --threads 2
```

### Build llama.cpp failed

```bash
# Install build dependencies
sudo apt update
sudo apt install -y build-essential git cmake

# Clean and rebuild
cd ~/llama.cpp
make clean
make -j2  # Use 2 threads to avoid OOM
```

### API không response

```bash
# Check if wrapper can reach llama-server
curl http://localhost:8002/health

# Check Python wrapper
ps aux | grep llamacpp_wrapper

# Restart services
sudo systemctl restart vintern-llamacpp
sleep 5
sudo systemctl restart vintern-wrapper
```

### Backend không connect được Orange Pi

```bash
# From Raspberry Pi, test connectivity
ping 192.168.1.16
curl http://192.168.1.16:8003/health

# Check backend .env
cat backend/.env | grep VLLM_SERVICE_URL

# Should be: VLLM_SERVICE_URL=http://192.168.1.16:8003
```

## 🔄 Update Model

Để update model hoặc thử quantization khác:

```bash
# On Orange Pi
cd ~/llama.cpp

# List available quantizations
./llama-quantize

# Convert to Q4_K_M (faster, smaller, nhưng kém accuracy hơn)
./llama-quantize \
  ~/models/vintern-1b-gguf/vintern-1b-f16.gguf \
  ~/models/vintern-1b-gguf/vintern-1b-q4_k_m.gguf \
  Q4_K_M

# Update service to use new model
sudo systemctl edit vintern-llamacpp

# Change --model path, save, then:
sudo systemctl daemon-reload
sudo systemctl restart vintern-llamacpp
```

## 📚 References

- llama.cpp: https://github.com/ggerganov/llama.cpp
- GGUF format: https://github.com/ggerganov/ggml/blob/master/docs/gguf.md
- Quantization guide: https://github.com/ggerganov/llama.cpp/blob/master/examples/quantize/README.md
- Vision model support: https://github.com/ggerganov/llama.cpp/blob/master/examples/llava/README.md

## ✅ Checklist

Sau khi deploy, verify:

- [ ] Orange Pi: `systemctl status vintern-llamacpp` → active (running)
- [ ] Orange Pi: `systemctl status vintern-wrapper` → active (running)
- [ ] Orange Pi: `curl http://localhost:8003/health` → {"status": "healthy"}
- [ ] Raspberry Pi: `cat backend/.env | grep VLLM` → http://192.168.1.16:8003
- [ ] Raspberry Pi: `docker ps | grep backend` → Up
- [ ] Web UI: http://192.168.1.14:8000/ → cameras streaming
- [ ] Web UI: Status bar → "VLLM: Ready"
- [ ] Web UI: Click "Analyze with AI" → Nhận được response từ Orange Pi

Nếu tất cả ✅, hệ thống đã sẵn sàng!
