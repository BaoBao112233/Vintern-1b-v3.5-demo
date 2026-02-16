# 🏗️ Kiến Trúc Hệ Thống Vision AI Phân Tán

## 📐 Sơ Đồ Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                        🌐 MẠNG LAN (1Gbps)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────┐    ┌────────────────────────────┐ │
│  │  📹 Camera Dahua (RTSP)       │    │  📹 Camera Dahua (RTSP)    │ │
│  │  192.168.1.4                  │    │  192.168.1.7               │ │
│  │  rtsp://admin:***@.../cam/... │    │  rtsp://admin:***@.../...  │ │
│  └──────────────┬────────────────┘    └──────────────┬─────────────┘ │
│                 │                                     │                │
│                 │                                     │                │
│                 └──────────────┬──────────────────────┘                │
│                                ▼                                       │
│     ┌─────────────────────────────────────────────────────┐           │
│     │  🍓 RASPBERRY PI 4 (Edge Node)                      │           │
│     │  IP: 192.168.1.50 (example)                         │           │
│     ├─────────────────────────────────────────────────────┤           │
│     │  ┌──────────────────────────────────────────────┐  │           │
│     │  │  1️⃣ RTSP Client Service                     │  │           │
│     │  │  - Nhận stream từ 2 cameras                 │  │           │
│     │  │  - Frame sampling (1-5 FPS)                 │  │           │
│     │  │  - Auto reconnect                           │  │           │
│     │  └──────────────────────────────────────────────┘  │           │
│     │                      ▼                              │           │
│     │  ┌──────────────────────────────────────────────┐  │           │
│     │  │  2️⃣ Detection Pipeline (Optional)           │  │           │
│     │  │  - YOLOv8n (lightweight)                     │  │           │
│     │  │  - Bounding boxes                            │  │           │
│     │  │  - Object tracking                           │  │           │
│     │  └──────────────────────────────────────────────┘  │           │
│     │                      ▼                              │           │
│     │  ┌──────────────────────────────────────────────┐  │           │
│     │  │  3️⃣ Backend API (FastAPI)                   │  │           │
│     │  │  - REST endpoints                            │  │           │
│     │  │  - WebSocket for realtime                    │  │           │
│     │  │  - Request queue management                  │  │           │
│     │  │  Port: 8001                                  │  │           │
│     │  └──────────────────────────────────────────────┘  │           │
│     │                      ▼                              │           │
│     │  ┌──────────────────────────────────────────────┐  │           │
│     │  │  4️⃣ Frontend UI (React)                     │  │           │
│     │  │  - Camera feeds display                      │  │           │
│     │  │  - Detection results                         │  │           │
│     │  │  - Chat interface                            │  │           │
│     │  │  Port: 3000                                  │  │           │
│     │  └──────────────────────────────────────────────┘  │           │
│     └─────────────────────┬───────────────────────────────┘           │
│                           │ HTTP Request                               │
│                           │ (Image + Prompt)                           │
│                           ▼                                            │
│     ┌─────────────────────────────────────────────────────┐           │
│     │  🖥 PC (Inference Node)                             │           │
│     │  IP: 192.168.1.100 (example)                        │           │
│     │  GPU: GTX 1050 Ti (4GB VRAM)                        │           │
│     ├─────────────────────────────────────────────────────┤           │
│     │  ┌──────────────────────────────────────────────┐  │           │
│     │  │  llama.cpp Inference Server                  │  │           │
│     │  │  Port: 8080                                  │  │           │
│     │  │  ┌────────────────────────────────────────┐ │  │           │
│     │  │  │  Model: Vintern-1B-v3.5 GGUF Q8_0     │ │  │           │
│     │  │  │  - Vision Encoder: 318MB               │ │  │           │
│     │  │  │  - Language Model: 644MB               │ │  │           │
│     │  │  │  - Total VRAM: ~1-1.5GB                │ │  │           │
│     │  │  └────────────────────────────────────────┘ │  │           │
│     │  │  API: OpenAI-compatible                      │  │           │
│     │  │  - /health                                   │  │           │
│     │  │  - /v1/chat/completions                      │  │           │
│     │  └──────────────────────────────────────────────┘  │           │
│     └─────────────────────┬───────────────────────────────┘           │
│                           │ Response (JSON)                            │
│                           │                                            │
└───────────────────────────┴────────────────────────────────────────────┘
```

## 🔄 Data Flow

```
Camera RTSP Stream (H.264)
    │
    ▼
[Pi] RTSP Client → Frame Extraction (640x480)
    │
    ▼
[Pi] Detection Pipeline (Optional)
    │ Objects detected
    ▼
[Pi] Backend API
    │ Prepare request:
    │ - Encode image to Base64
    │ - Add prompt
    │ - Add detected objects context
    ▼
[LAN] HTTP Request → PC Inference Server
    │
    ▼
[PC] llama.cpp Server
    │ - Vision encoder processes image
    │ - Language model generates response
    │ - Return JSON
    ▼
[LAN] HTTP Response ← PC
    │
    ▼
[Pi] Backend process response
    │
    ▼
[Pi] Frontend display results
```

## ⚙️ Cấu Hình Chi Tiết

### 🖥 PC (Inference Node)

| Component | Specification |
|-----------|--------------|
| CPU | Intel Core i3-10105F @ 3.70GHz (4C/8T) |
| RAM | 16GB |
| GPU | GTX 1050 Ti 4GB VRAM |
| Driver | NVIDIA 580.126.09 |
| CUDA | 13.0 (driver-only) |
| OS | Ubuntu 22.04 |

**Chạy:**
- llama.cpp inference server
- Model: Vintern-1B-v3.5 GGUF Q8_0
- Mode: CPU-only (có thể upgrade lên GPU)
- Port: 8080
- API: OpenAI-compatible

**VRAM Budget:**
```
Model weights:     ~1000 MB
KV Cache (2048):    ~200 MB
Activations:        ~100 MB
─────────────────────────────
Total:             ~1300 MB / 4096 MB ✅
Còn dư:            ~2700 MB
```

### 🍓 Raspberry Pi 4 (Edge Node)

| Component | Requirements |
|-----------|--------------|
| RAM | 4GB+ (recommended 8GB) |
| OS | Ubuntu 22.04 ARM64 hoặc Raspberry Pi OS 64-bit |
| Python | 3.8+ |
| Storage | SD Card Class 10 UHS-I (16GB+) |

**Chạy:**
- RTSP client (2 cameras)
- Detection pipeline (YOLOv8n)
- Backend API (FastAPI)
- Frontend UI (React)

**RAM Budget:**
```
RTSP streams:       ~200 MB
YOLOv8n model:      ~50 MB
Backend API:        ~100 MB
Frontend:           ~50 MB
Frame buffers:      ~100 MB
─────────────────────────────
Total:             ~500 MB / 4GB ✅
Safe zone:          ~1GB usage
```

### 📡 Network Requirements

| Parameter | Requirement |
|-----------|-------------|
| LAN Speed | 100Mbps+ (1Gbps recommended) |
| Latency | <5ms (local network) |
| Static IP | Recommended cho cả PC và Pi |
| Ports | 8080 (PC), 8001 (Pi Backend), 3000 (Pi Frontend) |

**Bandwidth Estimate:**
```
1 camera stream (640x480 @ 5 FPS):
- Image size: ~50 KB/frame  
- Base64 encoded: ~70 KB/frame
- 5 FPS → 350 KB/s → 2.8 Mbps
- 2 cameras → ~6 Mbps

Total with overhead: ~10 Mbps
100Mbps LAN: ✅ OK
```

## 🚀 Performance Estimates

### Current (CPU-only)

| Metric | Value |
|--------|-------|
| Inference Time | 2-3 seconds |
| Throughput | ~20-30 requests/min |
| GPU VRAM | 0 MB (CPU-only) |
| CPU Usage | ~100% (4 cores) |
| Power | ~65W |

### Với GPU CUDA (Future)

| Metric | Value |
|--------|-------|
| Inference Time | 0.3-0.5 seconds |
| Throughput | ~120-200 requests/min |
| GPU VRAM | ~1.3 GB / 4 GB |
| CPU Usage | ~20% |
| Power | ~120W |

## 🎯 API Specification

### PC Inference Server

**Base URL:** `http://<PC_IP>:8080`

**Endpoints:**

1. **Health Check**
   ```
   GET /health
   Response: {"status": "ok"}
   ```

2. **Chat Completions** (OpenAI-compatible)
   ```
   POST /v1/chat/completions
   Content-Type: application/json
   
   {
     "messages": [
       {
         "role": "user",
         "content": [
           {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
           {"type": "text", "text": "Describe this image"}
         ]
       }
     ],
     "max_tokens": 200,
     "temperature": 0.1
   }
   ```

### Pi Backend API

**Base URL:** `http://<Pi_IP>:8001`

**Endpoints:**

1. **System Health**
   ```
   GET /health
   ```

2. **Camera Status**
   ```
   GET /stream-status
   ```

3. **Detection**
   ```
   POST /detect
   ```

4. **Ask VLM**
   ```
   POST /ask-llm
   Body: {
     "camera_id": 1,
     "prompt": "What do you see?",
     "include_detections": true
   }
   ```

5. **System Info**
   ```
   GET /system-info
   ```

## 🔒 Security Considerations

1. **Network Isolation**
   - Chạy trên LAN nội bộ, không expose ra internet
   - Firewall chặn ports từ WAN

2. **Camera Authentication**
   - RTSP URLs có username/password
   - Lưu trong `.env`, không commit

3. **Access Control**
   - Frontend chỉ truy cập từ LAN
   - API không có public endpoints

## 📊 Monitoring

### PC
```bash
# GPU monitoring (nếu có CUDA)
watch -n 1 nvidia-smi

# CPU/RAM
htop

# Server logs
tail -f /home/baobao/Projects/Vintern-1b-v3.5-demo/pc-inference-server/logs/server_*.log
```

### Pi
```bash
# CPU temperature
vcgencmd measure_temp

# Memory
free -h

# Processes
htop
```

## 🐛 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Pi không connect được PC | Firewall/Network | Check firewall, ping test |
| Inference quá chậm | CPU-only | Rebuild llama.cpp với CUDA |
| RTSP timeout | Camera offline | Check camera connection, auto-reconnect |
| RAM overflow Pi | Leak/buffer | Implement frame buffer limits |
| GPU OOM | VRAM full | Giảm batch_size, ctx_size |

## 🎓 Next Steps

1. ✅ **PC Setup Complete** - Inference server ready
2. ⏭️ **Pi Setup** - Install dependencies, RTSP client
3. ⏭️ **Backend API** - Create FastAPI endpoints
4. ⏭️ **Frontend** - Build React UI
5. ⏭️ **Integration Test** - Full pipeline test
6. ⏭️ **Optimization** - GPU support, caching, etc.

---

**Xác nhận để tiếp tục setup Raspberry Pi!**
