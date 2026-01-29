# Vintern-1B Distributed Architecture

**AI Vision System với 2 Services riêng biệt kết nối qua Ethernet LAN**

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Optional)                │
│                   ReactJS Web UI                     │
│                   Port: 3000                         │
└──────────────┬─────────────────┬────────────────────┘
               │                 │
               │                 │
     ┌─────────▼────────┐   ┌───▼──────────────┐
     │ Detection Service│   │  VLLM Service    │
     │ Raspberry Pi 4   │   │  Orange Pi RV 2  │
     │ + Coral USB TPU  │   │  4GB RAM         │
     │                  │   │                  │
     │ Port: 8001       │   │  Port: 8002      │
     │ IP: .100.10      │◄──┤  IP: .100.20     │
     └──────────────────┘   └──────────────────┘
              │                    ▲
              │                    │
              └────── Ethernet ────┘
                  192.168.100.0/24
```

## 🎯 Architecture Overview

### Service 1: Detection Service (Raspberry Pi 4)
**Hardware:**
- Raspberry Pi 4 (4GB RAM)
- Google Coral USB Accelerator (Edge TPU)
- USB Camera / Pi Camera Module
- Ethernet connection

**Software:**
- TensorFlow Lite
- MobileNet SSD v2 (Coral-optimized)
- FastAPI REST API
- WebSocket for streaming

**Responsibilities:**
- Real-time object detection
- Bounding box generation
- Object classification
- Camera frame processing

**Network:**
- Static IP: `192.168.100.10`
- Port: `8001`
- Endpoint: `http://192.168.100.10:8001`

---

### Service 2: VLLM Service (Orange Pi RV 2)
**Hardware:**
- Orange Pi RV 2 (4GB RAM)
- ARM64 CPU
- Ethernet connection

**Software:**
- PyTorch dengan INT8 quantization
- Vintern-1B-v3.5 (optimized)
- Transformers
- FastAPI REST API

**Responsibilities:**
- Vision-language understanding
- Context-aware Q&A
- Image analysis with detected objects
- Natural language responses

**Network:**
- Static IP: `192.168.100.20`
- Port: `8002`
- Endpoint: `http://192.168.100.20:8002`

---

## 🔄 Data Flow

```
1. Camera → Detection Service
   ↓
2. Detection Service: Object Detection (Coral TPU)
   → Output: Bounding boxes, labels, confidence
   ↓
3. Send to VLLM Service
   → Context: Detected objects + User question
   ↓
4. VLLM Service: Generate analysis
   → Output: Natural language response
   ↓
5. Return to Frontend
```

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 4 with Raspberry Pi OS 64-bit
- Orange Pi RV 2 with Ubuntu 22.04 ARM64
- Google Coral USB Accelerator
- Ethernet cable or switch
- Docker & Docker Compose on both devices

### 1. Network Setup

**Configure Ethernet LAN (192.168.100.0/24):**

```bash
# Raspberry Pi 4: 192.168.100.10
# Orange Pi RV 2: 192.168.100.20
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed network configuration.

### 2. Deploy Detection Service (Raspberry Pi)

```bash
cd detection-service
cp .env.template .env
docker-compose up --build -d
```

### 3. Deploy VLLM Service (Orange Pi)

```bash
cd vllm-service
python3 scripts/download_model.py
docker-compose up --build -d
```

### 4. Test Services

```bash
# Test detection
curl http://192.168.100.10:8001/health

# Test VLLM
curl http://192.168.100.20:8002/health
```

## 📡 API Endpoints

### Detection Service API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/detect` | POST | Detect objects (base64 image) |
| `/api/detect/upload` | POST | Detect from file upload |
| `/api/status` | GET | Detector status |
| `/ws/stream` | WebSocket | Real-time detection stream |

**Example:**
```bash
curl -X POST http://192.168.100.10:8001/api/detect/upload \
  -F "file=@image.jpg" \
  -F "draw_boxes=true"
```

### VLLM Service API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with memory info |
| `/api/analyze` | POST | Analyze image with context |
| `/api/chat` | POST | Chat about image |
| `/api/model-info` | GET | Model information |

**Example:**
```bash
curl -X POST http://192.168.100.20:8002/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_description": "Ảnh từ camera",
    "detected_objects": [
      {"name": "person", "confidence": 0.95},
      {"name": "car", "confidence": 0.87}
    ],
    "question": "Có những gì trong ảnh?"
  }'
```

## 🔧 Configuration

### Detection Service `.env`
```bash
PORT=8001
SERVICE_IP=192.168.100.10
VLLM_SERVICE_URL=http://192.168.100.20:8002
MODEL_PATH=models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
CONFIDENCE_THRESHOLD=0.5
```

### VLLM Service `.env`
```bash
PORT=8002
SERVICE_IP=192.168.100.20
DETECTION_SERVICE_URL=http://192.168.100.10:8001
USE_QUANTIZATION=true
QUANTIZATION_BITS=8
MAX_NEW_TOKENS=256
```

## 📊 Performance

### Detection Service
- **Latency**: 30-50ms per frame (with Coral TPU)
- **FPS**: 20-30 fps
- **Memory**: ~500MB
- **CPU**: Low (TPU offloading)

### VLLM Service
- **Latency**: 2-5s per response (INT8 quantized)
- **Memory**: 2.5-3GB (with 8-bit quantization)
- **CPU**: High during inference
- **Optimization**: Batch size=1, low memory mode

## 🔍 Monitoring

### Check Service Status
```bash
# Detection Service
curl http://192.168.100.10:8001/health | jq

# VLLM Service
curl http://192.168.100.20:8002/health | jq
```

### Monitor Resources
```bash
# On each device
htop
free -h
docker stats
```

## 🛠️ Troubleshooting

### Common Issues

**1. Coral USB not detected**
```bash
lsusb | grep "Google"
sudo apt-get install --reinstall libedgetpu1-std python3-pycoral
```

**2. VLLM Out of Memory**
```bash
# Change to 4-bit quantization in .env
QUANTIZATION_BITS=4
docker-compose restart
```

**3. Network connectivity issues**
```bash
ping 192.168.100.10  # From Orange Pi
ping 192.168.100.20  # From Raspberry Pi
```

**4. Service not responding**
```bash
docker-compose logs -f
docker-compose restart
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive troubleshooting guide.

## 📁 Project Structure

```
Vintern-1b-v3.5-demo/
├── detection-service/          # Raspberry Pi 4 service
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── models/            # Coral TPU detector
│   │   └── main.py
│   ├── Dockerfile.arm
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── vllm-service/              # Orange Pi RV 2 service
│   ├── app/
│   │   ├── api/               # Analysis endpoints
│   │   ├── models/            # Optimized VLLM
│   │   └── main.py
│   ├── scripts/
│   │   └── download_model.py
│   ├── Dockerfile.arm64
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── DEPLOYMENT.md              # Deployment guide
└── README_DISTRIBUTED.md      # This file
```

## 🔐 Security

- Use static IPs on private subnet (192.168.100.0/24)
- Enable firewall on both devices
- Restrict service access to LAN only
- Use SSH keys for remote access
- Regular security updates

## 📚 Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Full deployment guide
- [detection-service/README.md](./detection-service/README.md) - Detection Service docs
- [vllm-service/README.md](./vllm-service/README.md) - VLLM Service docs

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Test on actual hardware
4. Submit pull request

## 📄 License

See LICENSE file.

## 🙏 Credits

- [5CD-AI/Vintern-1B-v3.5](https://huggingface.co/5CD-AI/Vintern-1B-v3_5) - Vision Language Model
- [Google Coral](https://coral.ai/) - Edge TPU
- [FastAPI](https://fastapi.tiangolo.com/) - API Framework
- [PyTorch](https://pytorch.org/) - Deep Learning
