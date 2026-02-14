# Raspberry Pi 4 + Coral USB Setup Guide

Hướng dẫn chạy hệ thống camera với object detection trên Raspberry Pi 4 + Coral USB Accelerator.

## Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4                            │
│  ┌────────────────────┐        ┌──────────────────────┐    │
│  │  Backend (8000)    │◄──────►│  Detection Service   │    │
│  │  - UI              │        │  (8001)              │    │
│  │  - Camera feeds    │        │  - Coral USB         │    │
│  │  - API endpoints   │        │  - SSD MobileNet V2  │    │
│  └─────────┬──────────┘        └──────────────────────┘    │
│            │                                                 │
└────────────┼─────────────────────────────────────────────────┘
             │
             ├──────► Camera 1 (192.168.1.11)
             ├──────► Camera 2 (192.168.1.13)
             └──────► VLLM Service on Orange Pi (192.168.1.16:8002)
```

## Hardware Requirements

- **Raspberry Pi 4** (4GB RAM recommended)
- **Coral USB Accelerator**
- **2x IP Cameras** with RTSP support
- **MicroSD Card** (32GB+ recommended)

## Software Requirements

- Raspberry Pi OS (64-bit recommended)
- Docker & Docker Compose
- Git

## Quick Start

### 1. Clone repository

```bash
cd ~/Projects
git clone <repository-url> Vintern-1b-v3.5-demo
cd Vintern-1b-v3.5-demo
```

### 2. Run setup script

```bash
chmod +x setup_raspberrypi.sh start_raspberrypi.sh stop_raspberrypi.sh
./setup_raspberrypi.sh
```

Script sẽ:
- Tạo file `.env` từ template
- Tải model SSD MobileNet V2 cho Coral
- Kiểm tra Coral USB
- Test kết nối cameras
- Test kết nối VLLM service

### 3. Configure `.env` file

Edit `.env` với thông tin cameras của bạn:

```bash
nano .env
```

```env
# Host configuration
HOST_IP=192.168.1.14

# Camera configuration
CAMERA1_IP=192.168.1.11
CAMERA2_IP=192.168.1.13
CAMERA_USERNAME=admin
CAMERA_PASSWORD=abcd12345

# VLLM service (Orange Pi)
VLLM_SERVICE_URL=http://192.168.1.16:8002

# Detection settings
MOCK_MODE=false
CONFIDENCE_THRESHOLD=0.5
```

### 4. Start services

```bash
./start_raspberrypi.sh
```

### 5. Access UI

- **Main UI**: http://192.168.1.14:8000
- **API Docs**: http://192.168.1.14:8000/docs
- **Detection API**: http://192.168.1.14:8001/docs

## Camera Configuration

### RTSP URL Format

```
rtsp://<username>:<password>@<camera_ip>/cam/realmonitor?channel=1&subtype=1
```

Example:
```
rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1
```

### Test Camera Feeds

```bash
# Test Camera 1
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1" -t 10 -c copy test_cam1.mp4

# Test Camera 2
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.13/cam/realmonitor?channel=1&subtype=1" -t 10 -c copy test_cam2.mp4
```

Or use the test script:
```bash
python3 test_cameras.py
```

## Coral USB Setup

### Install drivers

```bash
cd detection-service
bash install_coral.sh
```

### Verify Coral USB

```bash
lsusb | grep "Global Unichip Corp"
```

Should show:
```
Bus 001 Device 004: ID 1a6e:089a Global Unichip Corp.
```

### Test Coral

```bash
cd detection-service
bash test_service.sh
```

## Docker Management

### View logs

```bash
# All services
sudo docker-compose -f docker-compose.raspberrypi.yml logs -f

# Backend only
sudo docker-compose -f docker-compose.raspberrypi.yml logs -f backend

# Detection service only
sudo docker-compose -f docker-compose.raspberrypi.yml logs -f detection-service
```

### Restart services

```bash
sudo docker-compose -f docker-compose.raspberrypi.yml restart
```

### Stop services

```bash
./stop_raspberrypi.sh
```

### Rebuild after code changes

```bash
sudo docker-compose -f docker-compose.raspberrypi.yml up -d --build
```

## API Endpoints

### Backend (Port 8000)

- `GET /` - UI Homepage
- `GET /api/health` - Health check
- `GET /api/cameras` - List cameras
- `GET /api/cameras/{camera_id}/stream` - Camera stream
- `POST /api/chat` - Chat with vision & detection
- `POST /api/analyze-image` - Analyze image
- `GET /api/model-status` - Model status

### Detection Service (Port 8001)

- `GET /health` - Health check
- `POST /detect` - Object detection
- `GET /status` - Service status

## VLLM Service (Orange Pi)

Backend tự động kết nối đến VLLM service trên Orange Pi:

```env
VLLM_SERVICE_URL=http://192.168.1.16:8002
```

Nếu không kết nối được VLLM service, hệ thống vẫn chạy ở chế độ "detection only".

## Troubleshooting

### Coral USB not detected

```bash
# Check USB devices
lsusb

# Reinstall drivers
cd detection-service
bash install_coral.sh

# Reboot
sudo reboot
```

### Camera not connecting

```bash
# Ping camera
ping 192.168.1.11

# Test RTSP stream
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1" -t 5 -c copy test.mp4

# Check camera credentials in .env
cat .env | grep CAMERA
```

### VLLM service not available

```bash
# Test connection to Orange Pi
curl http://192.168.1.16:8002/health

# Check if Orange Pi is running
ping 192.168.1.16

# System will work in detection-only mode without VLLM
```

### Docker out of memory

```bash
# Check memory
free -h

# Add swap space (if needed)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Detection service slow

```bash
# Check if Coral is being used (should show TPU device)
sudo docker-compose -f docker-compose.raspberrypi.yml logs detection-service | grep -i coral

# If not, check USB connection
lsusb | grep "Global Unichip"

# Restart detection service
sudo docker-compose -f docker-compose.raspberrypi.yml restart detection-service
```

## Performance Tips

1. **Use Coral USB**: Detection is 10-20x faster with Coral compared to CPU
2. **Lower camera resolution**: Use subtype=1 (substream) instead of subtype=0 (mainstream)
3. **Adjust confidence threshold**: Lower threshold = more detections but more false positives
4. **Limit FPS**: Process fewer frames per second to reduce load

## Model Information

**SSD MobileNet V2 COCO**
- Input: 300x300 RGB
- Classes: 80 COCO classes (person, car, dog, etc.)
- Quantized for Edge TPU
- Speed: ~30ms per frame on Coral USB

## File Structure

```
.
├── docker-compose.raspberrypi.yml  # Docker compose for RPi4
├── .env.raspberrypi                # Environment template
├── setup_raspberrypi.sh            # Setup script
├── start_raspberrypi.sh            # Start script
├── stop_raspberrypi.sh             # Stop script
├── models/                         # Model files
│   └── ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
├── backend/                        # Backend service
│   ├── app/
│   │   ├── services/
│   │   │   ├── vllm_client.py     # VLLM client (Orange Pi)
│   │   │   ├── camera_manager.py  # Camera management
│   │   │   └── detection_client.py # Detection client
│   │   └── api/
│   │       └── chat.py            # Chat API
│   └── static/                    # Frontend UI
└── detection-service/              # Detection service
    ├── Dockerfile.arm             # ARM Dockerfile
    ├── app/models/detector.py     # Coral detector
    └── install_coral.sh           # Coral setup
```

## System Requirements

- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 8GB minimum for OS + Docker images
- **Network**: Gigabit Ethernet recommended for multiple camera streams
- **USB**: USB 3.0 port for Coral Accelerator

## Production Tips

1. **Auto-start on boot**:
   ```bash
   # Add to crontab
   @reboot sleep 60 && cd /home/pi/Projects/Vintern-1b-v3.5-demo && ./start_raspberrypi.sh
   ```

2. **Monitor logs**:
   ```bash
   # Setup log rotation
   sudo nano /etc/docker/daemon.json
   ```
   ```json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   ```

3. **Backup configuration**:
   ```bash
   cp .env .env.backup
   ```

## Support

For issues or questions, check:
- Detection service logs: `sudo docker logs detection-service`
- Backend logs: `sudo docker logs backend`
- System logs: `journalctl -u docker`
