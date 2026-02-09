# Setup Guide: Raspberry Pi 4 + Coral USB + Multi-Camera Detection

## Tổng quan
Hệ thống này chạy object detection trên Raspberry Pi 4 với Coral USB Accelerator, xử lý 2 camera IP streams sử dụng SSD MobileNet V2.

## Yêu cầu phần cứng
- Raspberry Pi 4 (4GB RAM trở lên khuyến nghị)
- Coral USB Accelerator
- 2 Camera IP với RTSP stream support
- Kết nối mạng ổn định

## Cài đặt

### 1. Cài đặt Edge TPU Runtime

```bash
# Add Coral repository
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

# Update and install
sudo apt-get update
sudo apt-get install libedgetpu1-std
sudo apt-get install python3-pycoral
```

### 2. Cài đặt dependencies cho Detection Service

```bash
cd detection-service

# Cài đặt Python packages
pip3 install -r requirements.txt

# Download model (nếu chưa có)
sudo bash download_model.sh
```

### 3. Cài đặt Backend

```bash
cd ../backend

# Cài đặt Python packages
pip3 install -r requirements.txt

# Copy và cấu hình .env
cp .env.example .env
nano .env  # Điều chỉnh IP cameras và credentials
```

### 4. Cài đặt Frontend

```bash
cd ../frontend

# Cài đặt Node packages
npm install

# Build production
npm run build
```

## Cấu hình Camera

### Cập nhật Backend .env

```env
CAMERA1_IP=192.168.1.11
CAMERA2_IP=192.168.1.13
CAMERA_USERNAME=admin
CAMERA_PASSWORD=abcd12345
```

### Test RTSP Streams

```bash
# Test Camera 1
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1" -t 5 -c copy test_cam1.mp4

# Test Camera 2
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.13/cam/realmonitor?channel=1&subtype=1" -t 5 -c copy test_cam2.mp4
```

## Chạy hệ thống

### Option 1: Chạy thủ công (Development)

#### Terminal 1: Detection Service
```bash
cd detection-service
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 2: Backend
```bash
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 3: Frontend
```bash
cd frontend
npm start
```

### Option 2: Sử dụng script tự động

```bash
# Tạo script start_all.sh
cat > start_all.sh << 'EOF'
#!/bin/bash

# Start detection service
cd detection-service
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 &
DETECTION_PID=$!

# Wait for detection service to start
sleep 5

# Start backend
cd ../backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend (production mode)
cd ../frontend
npx serve -s build -l 3000 &
FRONTEND_PID=$!

echo "Services started:"
echo "  Detection Service PID: $DETECTION_PID"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop all services, run: kill $DETECTION_PID $BACKEND_PID $FRONTEND_PID"

wait
EOF

chmod +x start_all.sh
./start_all.sh
```

## Truy cập

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Detection Service API: http://localhost:8001/docs

## Sử dụng

1. Mở trình duyệt tại `http://localhost:3000`
2. Chọn tab "Multi-Camera View"
3. Click "Initialize Cameras" để khởi động camera streams
4. Hệ thống sẽ tự động hiển thị detection results từ cả 2 cameras

## Các endpoints API chính

### Backend
- `GET /api/health` - Health check
- `GET /api/cameras/status` - Camera status
- `POST /api/cameras/initialize` - Initialize cameras
- `GET /api/cameras/all/frames` - Get frames from all cameras
- `GET /api/cameras/{camera_id}/frame` - Get frame from specific camera

### Detection Service
- `GET /health` - Health check
- `POST /api/detect` - Detect objects in image

## Troubleshooting

### Coral TPU không nhận diện

```bash
# Check USB devices
lsusb | grep "Global Unichip"

# Should see: Bus XXX Device XXX: ID 1a6e:089a Global Unichip Corp.

# If not detected, try:
sudo modprobe apex
```

### Camera không kết nối

```bash
# Test RTSP stream
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@IP_ADDRESS/cam/realmonitor?channel=1&subtype=1" -t 5 test.mp4

# Check network connectivity
ping IP_ADDRESS

# Check camera credentials
curl -u admin:abcd12345 rtsp://IP_ADDRESS/
```

### Detection chậm

1. Giảm resolution camera (trong code: width=320, height=240)
2. Giảm FPS (trong frontend: refreshInterval)
3. Tăng CONFIDENCE_THRESHOLD để giảm số detection

### Memory issues

```bash
# Increase swap space
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Performance tuning

### Optimize camera stream settings

Trong `backend/app/services/camera_manager.py`, điều chỉnh:

```python
config = CameraConfig(
    width=320,  # Giảm từ 640
    height=240,  # Giảm từ 480
    fps=3       # Giảm từ 5
)
```

### Optimize detection frequency

Trong frontend, tăng `refreshInterval`:

```javascript
refreshInterval: 2000  // 2 seconds thay vì 1 second
```

## Logs

```bash
# View detection service logs
tail -f detection-service/logs/detection.log

# View backend logs
tail -f backend/logs/backend.log

# View system logs
journalctl -u detection-service -f
```

## Auto-start on boot (Systemd)

### Detection Service

```bash
sudo nano /etc/systemd/system/detection-service.service
```

```ini
[Unit]
Description=Object Detection Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/Vintern-1b-v3.5-demo/detection-service
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

### Backend Service

```bash
sudo nano /etc/systemd/system/vintern-backend.service
```

```ini
[Unit]
Description=Vintern Backend Service
After=network.target detection-service.service
Requires=detection-service.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/Vintern-1b-v3.5-demo/backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Enable services

```bash
sudo systemctl daemon-reload
sudo systemctl enable detection-service
sudo systemctl enable vintern-backend
sudo systemctl start detection-service
sudo systemctl start vintern-backend

# Check status
sudo systemctl status detection-service
sudo systemctl status vintern-backend
```

## Monitoring

```bash
# CPU and Memory usage
htop

# GPU (Coral) temperature
cat /sys/class/thermal/thermal_zone*/temp

# Network bandwidth
iftop
```

## Notes

- SSD MobileNet V2 chạy ~30-40 FPS trên Coral TPU
- Latency khoảng 20-30ms per frame
- Hỗ trợ 80 object classes từ COCO dataset
- Confidence threshold mặc định: 0.5
