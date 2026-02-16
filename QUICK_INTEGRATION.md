# 🎯 QUICK REFERENCE - Raspberry Pi Integration

## 📦 1. Transfer Package to Pi

```bash
# Copy package to Pi
scp pi-deployment-package.tar.gz pi@<PI_IP>:~/
```

## 🍓 2. Setup on Pi

```bash
# On Raspberry Pi
tar -xzf pi-deployment-package.tar.gz
cd pi-deployment-package
./setup_on_pi.sh

# Update PC IP
nano client/vision_service_example.py  # Line 43: pc_host="YOUR_PC_IP"
```

## ✅ 3. Test Connection

```bash
cd client
python3 test_connection.py 192.168.1.3  # Replace with your PC IP
```

## 🔥 4. READY-TO-USE PROMPTS

### A. Simple Quick Analysis (Fast)

```python
from client.vision_service_example import VisionAIService
from PIL import Image

service = VisionAIService(pc_host="192.168.1.3", pc_port=8080)
image = Image.open("frame.jpg")

result = service.analyze_simple(image)
print(result["description"])
```

**Use Cases:**
- Real-time monitoring
- Quick frame description
- Alert systems

**Latency:** ~2-3 seconds (CPU)

---

### B. Comprehensive Detailed Analysis (Recommended ⭐)

```python
from client.vision_service_example import VisionAIService
from PIL import Image

service = VisionAIService(pc_host="192.168.1.3", pc_port=8080)
image = Image.open("frame.jpg")

result = service.analyze_comprehensive(image)

print("Summary:", result["summary"])
print("\nPhases:")
for phase, content in result["phases"].items():
    print(f"  {phase}: {content}")
```

**Use Cases:**
- Detailed scene analysis
- Investigation/review
- Report generation

**Latency:** ~10-15 seconds (multiple turns)

---

### C. Integration with YOLO Detection

```python
from client.vision_service_example import VisionAIService
from PIL import Image

service = VisionAIService(pc_host="192.168.1.3", pc_port=8080)
image = Image.open("frame.jpg")

# Your YOLO detections
yolo_results = [
    {"label": "person", "confidence": 0.95, "bbox": [100, 150, 300, 450]},
    {"label": "car", "confidence": 0.88, "bbox": [400, 200, 700, 500]}
]

result = service.analyze_with_yolo(image, yolo_results)

print(f"VLM sees: {result['vlm_description']}")
print(f"Verification: {result['verification']}")
print(f"Confidence: {result['confidence']:.2%}")
```

**Use Cases:**
- Verify YOLO detections
- Cross-reference with VLM
- Improve detection confidence

---

### D. Custom Questions

```python
from client.vision_service_example import VisionAIService
from PIL import Image

service = VisionAIService(pc_host="192.168.1.3", pc_port=8080)
image = Image.open("frame.jpg")

# Ask specific questions
questions = [
    "Có bao nhiêu người trong ảnh?",
    "Người nào đang làm gì?",
    "Có hành vi bất thường không?",
    "Thời tiết như thế nào?"
]

for q in questions:
    result = service.analyze_simple(image, custom_prompt=q)
    print(f"Q: {q}")
    print(f"A: {result['description']}\n")
```

---

## 🌐 5. FastAPI Endpoints

### Add to your `backend/app/main.py`:

```python
from fastapi import FastAPI
from .api import vision_endpoints  # Copy fastapi_endpoints_example.py

app = FastAPI()
app.include_router(vision_endpoints.router)
```

### Available Endpoints:

```bash
# Health check
GET /api/vision/health

# Quick analysis
POST /api/vision/analyze/quick
  -F "file=@image.jpg"

# Detailed analysis
POST /api/vision/analyze/detailed
  -F "file=@image.jpg"

# With YOLO
POST /api/vision/analyze/with-yolo
  -F "file=@image.jpg"
  -F 'detections=[{"label":"person","confidence":0.95,"bbox":[100,150,300,450]}]'

# Custom prompt
POST /api/vision/analyze/custom
  -F "file=@image.jpg"
  -F "prompt=Có bao nhiêu người?"

# RTSP frame
POST /api/vision/analyze/rtsp-frame
  -d '{"camera_id":"cam1","frame_data":"base64_jpeg","include_detections":true}'
```

---

## 💡 6. BEST PROMPTS (Tiếng Việt)

### General Description
```python
"Mô tả chi tiết những gì bạn thấy trong ảnh."
"Bạn thấy gì trong ảnh này? Kể cả màu sắc, vật thể, vị trí."
```

### Object Counting
```python
"Có bao nhiêu người trong ảnh? Đếm cụ thể."
"Liệt kê tất cả các vật thể và số lượng từng loại."
```

### Behavior Analysis
```python
"Người trong ảnh đang làm gì?"
"Có hành vi bất thường hoặc đáng ngờ nào không?"
"Mọi người đang tương tác như thế nào?"
```

### Safety & Security
```python
"Có dấu hiệu nguy hiểm nào trong ảnh không?"
"Môi trường có an toàn không? Giải thích."
"Phát hiện điểm bất thường về an ninh."
```

### Vehicle Analysis
```python
"Có phương tiện gì trong ảnh? Màu gì? Loại gì?"
"Biển số xe có thể đọc được không?"
"Xe đang ở vị trí nào?"
```

### Environment
```python
"Đây là môi trường gì? Trong nhà hay ngoài trời?"
"Thời tiết như thế nào?"
"Ánh sáng ban ngày hay ban đêm?"
```

### Multi-Phase Questions (Best Results ⭐)
```python
questions = {
    "overview": "Mô tả tổng quan bức ảnh.",
    "people": "Có người không? Họ đang làm gì?",
    "objects": "Có vật thể gì đáng chú ý?",
    "safety": "Có điểm bất thường về an ninh không?",
    "details": "Chi tiết quan trọng khác?"
}
```

---

## 📊 7. Performance Expectations

| Analysis Type | Latency (CPU) | Tokens | Quality |
|--------------|---------------|--------|---------|
| Quick | ~2-3s | ~340 | ⭐⭐⭐ |
| Detailed | ~10-15s | ~1000+ | ⭐⭐⭐⭐⭐ |
| YOLO+VLM | ~3-5s | ~400 | ⭐⭐⭐⭐ |
| Custom | ~2-3s | ~340 | ⭐⭐⭐ |

**Note:** With GPU (rebuild with CUDA) → 5-10x faster!

---

## 🔧 8. Integration Examples

### A. RTSP Camera Stream

```python
import cv2
from client.vision_service_example import VisionAIService
from PIL import Image

service = VisionAIService(pc_host="192.168.1.3")

# Open RTSP stream
cap = cv2.VideoCapture("rtsp://admin:pass@192.168.1.4/stream")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Analyze every 30 frames (1 second at 30fps)
    if frame_count % 30 == 0:
        # Convert to PIL
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Quick analysis
        result = service.analyze_simple(image)
        
        print(f"Frame {frame_count}: {result['description']}")
    
    frame_count += 1
```

### B. Motion-Triggered Analysis

```python
from client.vision_service_example import VisionAIService
import time

service = VisionAIService(pc_host="192.168.1.3")

def on_motion_detected(frame):
    """Callback khi phát hiện chuyển động"""
    
    # Detailed analysis
    result = service.analyze_comprehensive(frame)
    
    if "người" in result["summary"].lower():
        # Alert: có người
        send_alert(result["summary"])
    
    # Log
    save_to_database(result)
```

### C. Scheduled Monitoring

```python
from client.vision_service_example import VisionAIService
import schedule
import time

service = VisionAIService(pc_host="192.168.1.3")

def analyze_camera():
    """Chạy định kỳ mỗi 5 phút"""
    frame = capture_frame_from_camera()
    result = service.analyze_simple(frame)
    
    print(f"[{time.strftime('%H:%M:%S')}] {result['description']}")

# Schedule
schedule.every(5).minutes.do(analyze_camera)

while True:
    schedule.run_pending()
    time.sleep(1)
```

---

## 🚨 9. Error Handling

```python
from client.vision_service_example import VisionAIService

service = VisionAIService(pc_host="192.168.1.3", max_retries=2)

try:
    result = service.analyze_simple(image)
    
    if not result["success"]:
        print(f"Analysis failed: {result.get('error')}")
        # Fallback logic
        
except ConnectionError:
    print("PC server not reachable")
    # Use cached results or skip
    
except TimeoutError:
    print("Request timeout")
    # Retry later
```

---

## 📚 10. Full Documentation

- **PI_INTEGRATION_GUIDE.md** - Complete integration guide
- **OUTPUT_LIMITATION.md** - Why model outputs are short
- **client/README.md** - Client API reference
- **ARCHITECTURE.md** - System architecture

---

## ✅ Checklist

- [ ] Package transferred to Pi
- [ ] Dependencies installed (`./setup_on_pi.sh`)
- [ ] PC IP configured in scripts
- [ ] Connection tested (`test_connection.py`)
- [ ] Quick analysis works
- [ ] Integrated into backend
- [ ] RTSP cameras connected
- [ ] Production deployment

---

**🎯 Everything you need is ready! Start integrating now!**

File locations:
- Package: `/home/baobao/Projects/Vintern-1b-v3.5-demo/pi-deployment-package.tar.gz`
- Guide: `PI_INTEGRATION_GUIDE.md`
- Examples: `client/vision_service_example.py`
- Endpoints: `client/fastapi_endpoints_example.py`
