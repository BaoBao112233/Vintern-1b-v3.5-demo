# 🌐 WEB UI - Hướng Dẫn Sử Dụng

Web UI hiển thị 2 camera + AI Analysis với Vintern-1B VLM

## 🚀 Khởi Động Hệ Thống

### 1. Khởi động Backend Service

```bash
cd /home/pi/Projects/Vintern-1b-v3.5-demo

# Start backend
HOST_IP=0.0.0.0 BACKEND_PORT=8005 python3 backend_service.py > /tmp/backend.log 2>&1 &

# Hoặc dùng script
./start_system.sh
```

### 2. Mở Web UI

Truy cập một trong các URL sau:

- **Trên Raspberry Pi**: http://localhost:8005/
- **Từ máy khác trong mạng**: http://192.168.1.14:8005/
- **File HTML trực tiếp**: Mở `web_ui/app.html` trong browser

## 🎯 Tính Năng Web UI

### 1. Hiển Thị 2 Cameras
- **Camera 1**: 192.168.1.4 (bên trái)
- **Camera 2**: 192.168.1.7 (bên phải)
- Real-time status indicator
- Timestamp trên mỗi frame

### 2. Controls Cho Mỗi Camera

#### 📸 Capture
- Chụp frame mới nhất từ camera
- Hiển thị ngay lập tức
- Không cần reload page

#### 🤖 Analyze
- Phân tích frame hiện tại với AI
- Sử dụng prompt tùy chỉnh
- Kết quả hiển thị trong Analysis Panel
- Latency: ~4-5 giây

#### 🔄 Auto Refresh
- Tự động refresh frames mỗi 3 giây
- Click lại để dừng
- Tiện cho monitoring liên tục

### 3. AI Analysis Panel

#### Custom Prompt
- Nhập prompt bằng tiếng Việt hoặc English
- Ví dụ:
  - "Mô tả chi tiết những gì bạn thấy trong ảnh"
  - "Có người không? Có xe không?"
  - "Describe everything you see in this image"

#### Quick Prompts
- 📝 Mô tả chung
- 👤 Phát hiện người
- 🚗 Phát hiện xe
- 🌐 English prompt

#### Analysis Results
- Hiển thị 10 kết quả gần nhất
- Thông tin: Camera ID, Latency, Timestamp
- Prompt đã sử dụng
- AI response đầy đủ

#### Statistics
- **Total Analyses**: Tổng số lần phân tích
- **Avg Latency**: Latency trung bình
- **Last Update**: Thời gian update cuối

## 🔧 Cấu Hình

### Backend API
- **URL**: `http://192.168.1.14:8005`
- **Cấu hình trong file**: `web_ui/app.html` (dòng 336)

```javascript
const API_BASE_URL = 'http://192.168.1.14:8005';
```

### VLLM Service
- **PC Inference Server**: http://192.168.1.3:8080
- **Cấu hình trong**: `.env` file

```bash
VLM_BACKEND=pc
VLLM_SERVICE_URL=http://192.168.1.3:8080
```

## 📋 Workflow Sử Dụng

### Scenario 1: Monitoring Cơ Bản
1. Mở Web UI
2. Click "Auto Refresh" trên cả 2 cameras
3. Quan sát live feeds (refresh mỗi 3s)
4. Click "Auto Refresh" lại để dừng

### Scenario 2: Phân Tích Đơn
1. Click "Capture" trên camera muốn phân tích
2. Điều chỉnh prompt nếu cần
3. Click "Analyze"
4. Đợi 4-5 giây
5. Xem kết quả trong Analysis Panel

### Scenario 3: So Sánh 2 Cameras
1. Capture từ Camera 1
2. Click "Analyze" Camera 1
3. Capture từ Camera 2
4. Click "Analyze" Camera 2
5. So sánh kết quả trong Analysis Panel

### Scenario 4: Phân Tích Chuyên Sâu
1. Capture frame
2. Dùng multiple quick prompts:
   - "Mô tả chung" → View overview
   - "Phát hiện người" → Human detection
   - "Phát hiện xe" → Vehicle detection
3. Xem tất cả kết quả cùng lúc

## 🎨 Giao Diện

### Layout
```
┌─────────────────────────────────────────────┐
│           Header + System Status            │
├──────────────────┬──────────────────────────┤
│   Camera 1       │      Camera 2            │
│   - Feed         │      - Feed              │
│   - Controls     │      - Controls          │
├──────────────────┴──────────────────────────┤
│         AI Analysis Panel                   │
│   - Custom Prompt                           │
│   - Quick Prompts                           │
│   - Results (10 latest)                     │
│   - Statistics                              │
└─────────────────────────────────────────────┘
```

### Responsive Design
- **Desktop**: 2 columns (2 cameras side by side)
- **Mobile/Tablet**: 1 column (cameras stack vertically)

## 🚨 Troubleshooting

### Web UI không load được
```bash
# Kiểm tra backend
curl http://localhost:8005/health

# Kiểm tra log
tail -f /tmp/backend.log

# Restart backend
pkill -f backend_service.py
./start_system.sh
```

### Camera không hiển thị
```bash
# Test camera RTSP trực tiếp
ffmpeg -rtsp_transport tcp \
  -i "rtsp://admin:abcd12345@192.168.1.4/cam/realmonitor?channel=1&subtype=1" \
  -frames:v 1 test.jpg

# Test capture API
curl http://localhost:8005/api/capture/1 -o test.jpg
```

### Analyze không hoạt động
```bash
# Kiểm tra PC VLLM service
curl http://192.168.1.3:8080/health

# Kiểm tra config
cat .env | grep VLM

# Test analyze API
python3 quick_test_vllm.py
```

### CORS errors trong browser
- Backend đã config CORS allow all
- Nếu vẫn lỗi, mở Web UI từ cùng domain: http://192.168.1.14:8005/

## 📊 Performance

### Typical Latencies
- **Capture Frame**: 1-2 giây
- **AI Analysis**: 4-5 giây
- **Auto Refresh**: 3 giây/frame

### Bandwidth
- Frame size: ~40-80 KB/frame
- Analysis request: ~50-100 KB
- Analysis response: ~1-2 KB
- Total: ~150 KB/analysis

### Recommendations
- Không auto refresh quá nhanh (< 3s)
- Không analyze quá nhiều frames liên tục
- Clear analysis results định kỳ để giảm RAM

## 🔐 Security Notes

- ⚠️ **Camera credentials hardcoded** trong code
- ⚠️ **No authentication** cho Web UI
- ⚠️ **CORS allow all** để dễ test
- Chỉ dùng trong mạng LAN tin cậy
- Không expose ra Internet

## 📱 Mobile Support

Web UI đã optimize cho mobile:
- Responsive layout
- Touch-friendly buttons
- Auto-fit camera feeds
- Swipe để scroll results

## 🎯 Next Features (TODO)

- [ ] Real-time video streaming thay vì periodic refresh
- [ ] WebSocket cho real-time analysis results
- [ ] User authentication
- [ ] Multi-language support
- [ ] Export analysis history
- [ ] Object detection overlay trên frames
- [ ] Alert system khi detect người/xe
- [ ] Recording video clips
- [ ] PTZ camera control (nếu camera hỗ trợ)

## 📞 Support

- Backend logs: `tail -f /tmp/backend.log`
- Browser console: F12 → Console tab
- Test API: `python3 test_backend_api.py`
- Full system test: `python3 quick_test_vllm.py`

## ✅ Quick Check

```bash
# 1. Backend running?
curl http://localhost:8005/health

# 2. PC VLLM available?
curl http://192.168.1.3:8080/health

# 3. Camera 1 working?
curl http://localhost:8005/api/capture/1 -o cam1.jpg

# 4. Camera 2 working?
curl http://localhost:8005/api/capture/2 -o cam2.jpg

# 5. Analyze working?
python3 quick_test_vllm.py
```

Nếu tất cả OK → Mở browser: **http://192.168.1.14:8005/**

---

Enjoy your Camera + AI Analysis System! 🎉
