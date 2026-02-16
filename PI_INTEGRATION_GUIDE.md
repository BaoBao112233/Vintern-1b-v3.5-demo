# 🍓 Raspberry Pi Integration Guide

Hướng dẫn tích hợp Vision AI inference từ PC vào Raspberry Pi 4 với backend FastAPI.

## 📋 Prerequisites

### Trên PC (đã setup):
- ✅ llama-server đang chạy port 8080
- ✅ Context size: 4096 tokens
- ✅ PC IP: `192.168.1.3` (hoặc IP thực của bạn)

### Trên Raspberry Pi 4:
- Python 3.8+
- Network kết nối được với PC
- Backend FastAPI hiện có

## 🚀 Quick Start (5 phút)

### Bước 1: Transfer Files Sang Pi

```bash
# Trên PC, compress client code
cd /home/baobao/Projects/Vintern-1b-v3.5-demo
tar -czf pi-client.tar.gz client/ smart_analyze.py OUTPUT_LIMITATION.md

# Copy sang Pi (thay PI_IP bằng IP thực của Pi)
scp pi-client.tar.gz pi@<PI_IP>:~/

# Hoặc dùng USB nếu không có SSH
```

### Bước 2: Setup Trên Pi

```bash
# SSH vào Pi
ssh pi@<PI_IP>

# Extract files
cd ~
tar -xzf pi-client.tar.gz

# Install dependencies
pip3 install requests pillow

# Test connection
cd client
python3 test_connection.py 192.168.1.3
```

Kết quả mong đợi:
```
✅ PC Inference Server: AVAILABLE
🌐 Network: OK (latency: 2.3ms)
🖼️ Vision Model: Vintern-1B-v3.5
```

### Bước 3: Tích Hợp Vào Backend

Xem phần [Backend Integration Examples](#-backend-integration-examples) bên dưới.

---

## 🎯 Backend Integration Examples

### Example 1: Simple Analysis (Fast)

**Use case:** Mô tả nhanh một frame từ camera

```python
# backend/app/services/vision_service.py

from client.pc_inference_client import PCInferenceClient
from PIL import Image
import io

class VisionService:
    def __init__(self):
        self.client = PCInferenceClient(
            host="192.168.1.3",  # PC IP
            port=8080,
            timeout=30
        )
    
    def analyze_frame(self, image_data: bytes) -> dict:
        """
        Phân tích nhanh một frame
        
        Args:
            image_data: JPEG image bytes
            
        Returns:
            {"description": str, "tokens": int, "latency_ms": float}
        """
        import time
        
        start = time.time()
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Simple question
        result = self.client.chat_completion(
            image=image,
            prompt="Mô tả ngắn gọn những gì bạn thấy trong ảnh."
        )
        
        latency = (time.time() - start) * 1000
        
        return {
            "description": result.get("content", ""),
            "tokens": result.get("tokens", 0),
            "latency_ms": round(latency, 2)
        }
```

### Example 2: Detailed Analysis (Recommended ⭐)

**Use case:** Phân tích chi tiết cho object detection + description

```python
# backend/app/services/vision_detailed_service.py

from client.pc_inference_client import PCInferenceClient
from PIL import Image
import io

class DetailedVisionService:
    def __init__(self):
        self.client = PCInferenceClient(
            host="192.168.1.3",
            port=8080,
            timeout=60
        )
        
        # Multi-phase questions (giống smart_analyze)
        self.analysis_phases = {
            "overview": [
                "Bạn thấy gì trong ảnh này? Mô tả ngắn gọn."
            ],
            "objects": [
                "Có những loại vật thể gì? Liệt kê cụ thể.",
                "Có bao nhiêu vật thể? Đếm từng loại.",
            ],
            "colors": [
                "Màu sắc của từng vật thể như thế nào?"
            ],
            "layout": [
                "Vật thể được sắp xếp như thế nào?",
                "Vị trí tương đối của các vật thể ra sao?"
            ],
            "environment": [
                "Nền của ảnh là gì? Màu gì?",
                "Có yếu tố nào khác đáng chú ý không?"
            ]
        }
    
    def analyze_comprehensive(self, image_data: bytes) -> dict:
        """
        Phân tích toàn diện với multi-turn conversation
        
        Returns:
            {
                "summary": str,              # Tổng hợp tất cả
                "phases": {...},             # Chi tiết từng phase
                "total_tokens": int,
                "total_time_ms": float
            }
        """
        import time
        
        start_time = time.time()
        image = Image.open(io.BytesIO(image_data))
        
        results = {}
        total_tokens = 0
        conversation_context = []
        
        for phase_name, questions in self.analysis_phases.items():
            phase_answers = []
            
            for i, question in enumerate(questions):
                # First question of first phase includes image
                if phase_name == "overview" and i == 0:
                    result = self.client.chat_completion(
                        image=image,
                        prompt=question,
                        context=conversation_context
                    )
                else:
                    # Subsequent questions use context (multi-turn)
                    result = self.client.chat_completion(
                        image=None,  # No image for follow-up
                        prompt=question,
                        context=conversation_context
                    )
                
                answer = result.get("content", "")
                phase_answers.append(answer)
                total_tokens += result.get("tokens", 0)
                
                # Update context for next question
                conversation_context = result.get("context", [])
            
            results[phase_name] = " ".join(phase_answers)
        
        # Generate comprehensive summary
        summary = " ".join(results.values())
        summary = " ".join(summary.split())  # Clean whitespace
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "summary": summary,
            "phases": results,
            "total_tokens": total_tokens,
            "total_time_ms": round(total_time, 2)
        }
```

### Example 3: With YOLO Detection Integration

**Use case:** Combine YOLO detection + VLM description

```python
# backend/app/services/integrated_vision_service.py

from client.pc_inference_client import PCInferenceClient
from .object_detection import YOLODetector  # Your existing YOLO
from PIL import Image
import io

class IntegratedVisionService:
    def __init__(self):
        self.vlm_client = PCInferenceClient(host="192.168.1.3", port=8080)
        self.yolo = YOLODetector()  # Your existing detector
    
    def analyze_with_detection(self, image_data: bytes) -> dict:
        """
        1. YOLO detect objects
        2. VLM verify và describe
        
        Returns:
            {
                "detections": [...],        # YOLO boxes
                "vlm_verification": str,    # VLM confirms what it sees
                "detailed_desc": str,       # Full description
                "confidence": float
            }
        """
        image = Image.open(io.BytesIO(image_data))
        
        # Step 1: YOLO detection
        detections = self.yolo.detect(image)
        
        # Step 2: Build smart prompt based on detections
        detected_labels = [d['label'] for d in detections]
        
        if detected_labels:
            # Ask VLM to verify YOLO results
            verify_prompt = (
                f"YOLO phát hiện: {', '.join(detected_labels)}. "
                f"Bạn có thấy những vật thể này không? Xác nhận và mô tả chi tiết."
            )
        else:
            verify_prompt = "Mô tả chi tiết những gì bạn thấy trong ảnh."
        
        # Step 3: Get VLM response
        result = self.vlm_client.chat_completion(
            image=image,
            prompt=verify_prompt
        )
        
        vlm_response = result.get("content", "")
        
        # Step 4: Calculate confidence (simple heuristic)
        confidence = self._calculate_confidence(detected_labels, vlm_response)
        
        return {
            "detections": detections,
            "vlm_verification": vlm_response,
            "confidence": confidence,
            "tokens": result.get("tokens", 0)
        }
    
    def _calculate_confidence(self, yolo_labels, vlm_text):
        """Simple matching between YOLO and VLM"""
        if not yolo_labels:
            return 0.5
        
        vlm_lower = vlm_text.lower()
        matches = sum(1 for label in yolo_labels if label.lower() in vlm_lower)
        
        return min(0.5 + (matches / len(yolo_labels)) * 0.5, 1.0)
```

---

## 🔌 FastAPI Endpoints

### Thêm vào `backend/app/api/vision.py`:

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.vision_detailed_service import DetailedVisionService

router = APIRouter(prefix="/api/vision", tags=["vision"])

# Initialize service (singleton)
vision_service = DetailedVisionService()

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Phân tích chi tiết một ảnh
    
    POST /api/vision/analyze
    Body: multipart/form-data with 'file' field
    
    Returns:
        {
            "summary": "Mô tả tổng hợp đầy đủ...",
            "phases": {
                "overview": "...",
                "objects": "...",
                "colors": "...",
                "layout": "...",
                "environment": "..."
            },
            "total_tokens": 1234,
            "total_time_ms": 5678.9
        }
    """
    try:
        # Read image data
        image_data = await file.read()
        
        # Analyze
        result = vision_service.analyze_comprehensive(image_data)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/quick")
async def analyze_quick(file: UploadFile = File(...)):
    """
    Phân tích nhanh (1 câu hỏi duy nhất)
    
    Use case: Real-time monitoring cần response nhanh
    """
    from ..services.vision_service import VisionService
    
    try:
        image_data = await file.read()
        service = VisionService()
        result = service.analyze_frame(image_data)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_vision_health():
    """
    Check xem PC inference server có available không
    """
    try:
        status = vision_service.client.health_check()
        return {
            "success": True,
            "pc_server": status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### Register trong `backend/app/main.py`:

```python
from fastapi import FastAPI
from .api import vision  # Import vision router

app = FastAPI(title="Vision AI Backend")

# Include vision endpoints
app.include_router(vision.router)

# ... existing routes ...
```

---

## 🧪 Testing

### Test 1: PC Server Connection

```bash
# Trên Pi
cd ~/client
python3 test_connection.py 192.168.1.3
```

### Test 2: Simple Analysis

```python
# test_simple.py
from client.pc_inference_client import PCInferenceClient
from PIL import Image

client = PCInferenceClient(host="192.168.1.3", port=8080)

# Test với một ảnh
image = Image.open("test.jpg")
result = client.chat_completion(
    image=image,
    prompt="Mô tả ảnh này"
)

print(result["content"])
```

### Test 3: API Endpoint

```bash
# Test FastAPI endpoint
curl -X POST http://localhost:8000/api/vision/analyze \
  -F "file=@test.jpg"
```

---

## 📊 Performance Tips

### 1. Cache VLM Client
```python
# Singleton pattern - khởi tạo 1 lần duy nhất
from functools import lru_cache

@lru_cache()
def get_vision_service():
    return DetailedVisionService()
```

### 2. Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

async def analyze_async(image_data):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        vision_service.analyze_comprehensive,
        image_data
    )
```

### 3. Request Batching
```python
# Nếu có nhiều frames cùng lúc, batch chúng
async def batch_analyze(images: list):
    tasks = [analyze_async(img) for img in images]
    return await asyncio.gather(*tasks)
```

---

## 🔐 Security & Best Practices

### 1. Validate Image Size
```python
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

if len(image_data) > MAX_IMAGE_SIZE:
    raise ValueError("Image too large")
```

### 2. Timeout Handling
```python
# Đã có sẵn trong PCInferenceClient
client = PCInferenceClient(
    host="192.168.1.3",
    port=8080,
    timeout=30,  # 30 seconds
    max_retries=2
)
```

### 3. Error Handling
```python
try:
    result = client.chat_completion(image, prompt)
except ConnectionError:
    # PC server down
    return {"error": "Inference server unavailable"}
except TimeoutError:
    # Request quá lâu
    return {"error": "Request timeout"}
```

---

## 📈 Monitoring

### Log Request Metrics
```python
import logging
import time

logger = logging.getLogger(__name__)

def analyze_with_logging(image_data):
    start = time.time()
    
    try:
        result = vision_service.analyze_comprehensive(image_data)
        
        latency = (time.time() - start) * 1000
        
        logger.info(
            f"Vision analysis completed: "
            f"tokens={result['total_tokens']}, "
            f"latency={latency:.2f}ms"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        raise
```

---

## 🛠️ Troubleshooting

### PC Server Connection Refused
```bash
# Check PC server
curl http://192.168.1.3:8080/health

# Check firewall
sudo ufw allow 8080/tcp

# Restart server nếu cần
cd /home/baobao/Projects/Vintern-1b-v3.5-demo/pc-inference-server
./start_server.sh
```

### Slow Response Time
```python
# Enable verbose logging
client = PCInferenceClient(host="192.168.1.3", port=8080)
client.enable_debug()  # Shows timing for each step
```

### Context Memory Issues
```python
# Reset context sau mỗi frame để tránh memory leak
conversation_context = []

for frame in video_stream:
    result = client.chat_completion(
        image=frame,
        prompt="...",
        context=conversation_context  # Reuse within session
    )
    
    # Reset mỗi 10 frames
    if frame_count % 10 == 0:
        conversation_context = []
```

---

## 📚 Next Steps

1. ✅ Test connection giữa Pi và PC
2. ✅ Tích hợp vào 1 endpoint FastAPI (quick analyze)
3. ✅ Test với RTSP stream thật
4. ✅ Thêm detailed analysis endpoint
5. ⚙️ Optimize performance (caching, batching)
6. 📊 Add monitoring/logging
7. 🚀 Deploy to production

---

## 🔗 Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System overview
- [OUTPUT_LIMITATION.md](OUTPUT_LIMITATION.md) - Model limitations
- [client/README.md](client/README.md) - Client library API
- [pc-inference-server/README.md](pc-inference-server/README.md) - Server setup

---

**Happy Coding! 🎉** Có vấn đề gì cứ hỏi nhé!
