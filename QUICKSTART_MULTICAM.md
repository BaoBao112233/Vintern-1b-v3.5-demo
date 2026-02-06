# Vintern Multi-Camera Detection System - Quick Start

## 🎯 Giới thiệu
Hệ thống object detection đa camera sử dụng:
- **Hardware**: Raspberry Pi 4 + Coral USB Accelerator
- **Model**: SSD MobileNet V2 (COCO dataset, 80 classes)
- **Cameras**: 2 IP cameras với RTSP streams
- **Performance**: ~30-40 FPS per camera trên Coral TPU

## 📋 Yêu cầu
- Raspberry Pi 4 (4GB RAM+)
- Coral USB Accelerator
- 2 Camera IP hỗ trợ RTSP
- Python 3.7+
- Node.js 14+ (cho frontend)

## 🚀 Cài đặt nhanh

### Bước 1: Cài đặt Coral TPU Runtime

```bash
cd detection-service
sudo bash install_coral.sh
```

Script này sẽ:
- Cài đặt libedgetpu runtime
- Cài đặt PyCoral library  
- Kiểm tra Coral USB connection

### Bước 2: Download Model

```bash
# Model đã được tải tự động, nhưng có thể chạy lại nếu cần:
sudo bash download_model.sh
```

### Bước 3: Cấu hình Cameras

Tạo file `.env` trong thư mục `backend`:

```bash
cd ../backend
cp .env.example .env
nano .env
```

Cập nhật thông tin cameras:
```env
CAMERA1_IP=192.168.1.11
CAMERA2_IP=192.168.1.13
CAMERA_USERNAME=admin
CAMERA_PASSWORD=abcd12345
```

### Bước 4: Cài đặt Dependencies

```bash
# Backend
cd backend
pip3 install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build
```

### Bước 5: Chạy hệ thống

```bash
# Từ thư mục gốc
./start_all.sh
```

Hoặc chạy thủ công từng service:

```bash
# Terminal 1: Detection Service
cd detection-service
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Backend
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 3: Frontend
cd frontend
npm start
```

## 🌐 Truy cập

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Detection Service**: http://localhost:8001/docs

## 📱 Sử dụng

1. Mở browser tại http://localhost:3000
2. Click nút **"Multi-Camera View"**
3. Click **"Initialize Cameras"** để kết nối cameras
4. Hệ thống sẽ tự động:
   - Stream video từ 2 cameras
   - Detect objects real-time
   - Hiển thị bounding boxes và labels

## 🎛️ Điều chỉnh

### Thay đổi FPS/Resolution

File: `backend/app/services/camera_manager.py`

```python
CameraConfig(
    width=640,  # Thay đổi độ phân giải
    height=480,
    fps=5       # Thay đổi frame rate
)
```

### Thay đổi Confidence Threshold

File: `detection-service/.env`

```env
CONFIDENCE_THRESHOLD=0.5  # 0.0 - 1.0
```

### Refresh Interval (Frontend)

Trong Multi-Camera View, chọn refresh interval từ dropdown:
- 0.5s (nhanh nhất)
- 1s (khuyến nghị)
- 2s
- 5s (tiết kiệm tài nguyên)

## 🔍 Kiểm tra

### Test Coral TPU

```bash
python3 -c "from pycoral.utils import edgetpu; print(edgetpu.list_edge_tpus())"
```

Kết quả mong đợi: `[{'type': 'usb', 'path': '/dev/bus/usb/...'}]`

### Test RTSP Stream

```bash
# Test Camera 1
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.11/cam/realmonitor?channel=1&subtype=1" -t 5 -c copy test1.mp4

# Test Camera 2
ffmpeg -rtsp_transport tcp -i "rtsp://admin:abcd12345@192.168.1.13/cam/realmonitor?channel=1&subtype=1" -t 5 -c copy test2.mp4
```

### Check Services

```bash
# Detection service
curl http://localhost:8001/health

# Backend
curl http://localhost:8000/api/health

# Camera status
curl http://localhost:8000/api/cameras/status
```

## ⚠️ Troubleshooting

### Coral không nhận diện

```bash
# Check USB
lsusb | grep "Global Unichip"

# Nếu không thấy, thử:
# 1. Rút và cắm lại Coral USB
# 2. Thử cổng USB khác (ưu tiên USB 3.0)
# 3. Reboot Raspberry Pi
sudo reboot
```

### Camera không kết nối

```bash
# Test kết nối
ping 192.168.1.11
ping 192.168.1.13

# Kiểm tra credentials
curl -u admin:abcd12345 rtsp://192.168.1.11/

# Xem logs
tail -f logs/backend.log
```

### Service lỗi

```bash
# Xem logs
tail -f logs/detection.log
tail -f logs/backend.log

# Restart services
./stop_all.sh
./start_all.sh
```

### Memory/Performance issues

```bash
# Tăng swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Giảm resolution/FPS trong code
# Đóng các ứng dụng khác
```

## 🛑 Dừng hệ thống

```bash
./stop_all.sh
```

## 📊 Performance

- **Detection Speed**: 30-40 FPS/camera trên Coral TPU
- **Latency**: ~20-30ms per frame
- **Memory**: ~1-2GB RAM (2 cameras + detection)
- **CPU**: ~30-50% (chủ yếu cho video decoding)

## 📚 Tài liệu chi tiết

Xem file `SETUP_RASPBERRY_PI.md` để biết thêm:
- Cấu hình systemd auto-start
- Monitoring và logging
- Advanced configuration
- Performance tuning

## 🆘 Hỗ trợ

### Check logs:
```bash
tail -f logs/*.log
```

### API Documentation:
- Backend: http://localhost:8000/docs
- Detection: http://localhost:8001/docs

### Các object classes được hỗ trợ:
80 classes từ COCO dataset bao gồm:
- person, car, motorcycle, bicycle
- dog, cat, bird
- bottle, cup, chair, laptop
- và nhiều objects khác...

Xem đầy đủ trong file `/models/coco_labels.txt`
