# 🚀 QUICK START - Raspberry Pi 4 + Coral USB

> **Hệ thống camera realtime với object detection sử dụng SSD MobileNet V2 + Coral USB**

## ⚡ Quick Start (5 phút)

### 1. Tải model (đã hoàn thành ✅)

```bash
./download_coral_model.sh
```

### 2. Cấu hình cameras

```bash
nano .env
```

Cập nhật IP cameras:
```env
CAMERA1_IP=192.168.1.11
CAMERA2_IP=192.168.1.13
CAMERA_USERNAME=admin
CAMERA_PASSWORD=abcd12345
VLLM_SERVICE_URL=http://192.168.1.16:8002
```

### 3. Start services

```bash
./start_raspberrypi.sh
```

### 4. Truy cập UI

🌐 **http://192.168.1.14:8000**

---

## 📋 System Overview

```
┌─────────────────────────────────────────┐
│         Raspberry Pi 4 (192.168.1.14)   │
│  ┌─────────────┐    ┌────────────────┐ │
│  │  Backend    │◄──►│   Detection    │ │
│  │  (8000)     │    │   Service      │ │
│  │  + UI       │    │   (8001)       │ │
│  └──────┬──────┘    │   + Coral USB  │ │
│         │           └────────────────┘ │
└─────────┼────────────────────────────────┘
          │
          ├──► 📹 Camera 1 (192.168.1.11)
          ├──► 📹 Camera 2 (192.168.1.13)
          └──► 🤖 VLLM (192.168.1.16:8002)
```

---

## 🔧 Services

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **UI** | 8000 | http://192.168.1.14:8000 | Frontend UI |
| **Backend API** | 8000 | http://192.168.1.14:8000/docs | FastAPI docs |
| **Detection** | 8001 | http://192.168.1.14:8001/docs | Detection API |
| **VLLM (Orange Pi)** | 8002 | http://192.168.1.16:8002/docs | VLM service |

---

## 📹 Camera URLs

```bash
# Camera 1
rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1

# Camera 2
rtsp://admin:abcd12345@192.168.1.13/cam/realmonitor?channel=1&subtype=1
```

### Test cameras

```bash
# Test với ffmpeg
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1" -t 10 -c copy test_cam1.mp4

# Test với Python
python3 test_cameras.py
```

---

## 🛠️ Management Commands

### Start/Stop

```bash
# Start
./start_raspberrypi.sh

# Stop
./stop_raspberrypi.sh

# Restart
sudo docker-compose -f docker-compose.raspberrypi.yml restart
```

### View Logs

```bash
# All logs
sudo docker-compose -f docker-compose.raspberrypi.yml logs -f

# Backend only
sudo docker-compose -f docker-compose.raspberrypi.yml logs -f backend

# Detection only
sudo docker-compose -f docker-compose.raspberrypi.yml logs -f detection-service
```

### Rebuild

```bash
sudo docker-compose -f docker-compose.raspberrypi.yml up -d --build
```

---

## 🔍 Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health | python3 -m json.tool

# Detection health
curl http://localhost:8001/health | python3 -m json.tool

# VLLM health (Orange Pi)
curl http://192.168.1.16:8002/health | python3 -m json.tool
```

---

## 🐛 Troubleshooting

### Coral USB không nhận diện

```bash
# Kiểm tra USB
lsusb | grep "Global Unichip Corp"

# Nếu không thấy, install drivers
cd detection-service && bash install_coral.sh
sudo reboot
```

### Camera không kết nối

```bash
# Test ping
ping 192.168.1.11

# Test RTSP
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1" -t 5 -c copy test.mp4

# Check .env
cat .env | grep CAMERA
```

### VLLM service không available

```bash
# Test connection
curl http://192.168.1.16:8002/health

# System sẽ chạy ở chế độ "detection only" nếu VLLM không available
```

### Docker out of memory

```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## 📊 Performance

- **Detection FPS**: ~30 FPS với Coral USB
- **Latency**: ~30ms per frame
- **Classes**: 80 COCO classes (person, car, dog, cat, etc.)
- **Model**: SSD MobileNet V2 (quantized for Edge TPU)

---

## 🎯 API Examples

### Detect objects

```bash
curl -X POST http://localhost:8001/detect \
  -F "file=@image.jpg" \
  | python3 -m json.tool
```

### Chat with vision

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What do you see?",
    "image_data": "data:image/jpeg;base64,...",
    "include_objects": true,
    "confidence_threshold": 0.5
  }' | python3 -m json.tool
```

### Get model status

```bash
curl http://localhost:8000/api/model-status | python3 -m json.tool
```

---

## 📚 Documentation

- **Full guide**: [README_RASPBERRY_PI.md](README_RASPBERRY_PI.md)
- **Docker deployment**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **Detection service**: [docs/detection-service.md](docs/detection-service.md)

---

## ✅ System Requirements

- Raspberry Pi 4 (4GB+ RAM recommended)
- Coral USB Accelerator
- 2x IP cameras with RTSP
- Docker & Docker Compose
- 32GB+ SD card

---

## 🎉 Features

✅ Realtime object detection với Coral USB  
✅ Multiple camera support (RTSP)  
✅ Web UI for monitoring  
✅ REST API  
✅ VLLM integration (Orange Pi)  
✅ 80 COCO classes detection  
✅ Bounding box visualization  
✅ Auto-restart on failure  

---

## 📝 Notes

- Hệ thống có thể chạy **detection-only** mode nếu VLLM service không available
- Coral USB tăng tốc detection lên **10-20x** so với CPU
- Sử dụng camera **substream** (subtype=1) để giảm bandwidth
- Model được load sẵn trong `models/` directory

---

## 🆘 Support

Nếu gặp vấn đề:

1. Check logs: `sudo docker-compose -f docker-compose.raspberrypi.yml logs`
2. Check health: `curl http://localhost:8000/api/health`
3. Restart services: `./stop_raspberrypi.sh && ./start_raspberrypi.sh`
4. Xem full documentation: `README_RASPBERRY_PI.md`
