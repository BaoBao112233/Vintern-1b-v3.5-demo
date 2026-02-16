# Client Library - Raspberry Pi → PC Communication

Client code để Raspberry Pi giao tiếp với PC inference server qua LAN.

## 📋 Prerequisites

### Trên PC
1. ✅ PC inference server đang chạy
2. ✅ Port 8080 mở (không bị firewall block)
3. ✅ PC có static IP hoặc ghi nhớ IP hiện tại

### Trên Raspberry Pi
1. Python 3.8+
2. Installed packages:
   ```bash
   pip install requests pillow
   ```

## 🌐 Network Setup

### 1. Lấy PC IP Address

**Trên PC chạy:**
```bash
ip addr show | grep "inet " | grep -v "127.0.0.1"
# hoặc
hostname -I
```

Ví dụ output: `192.168.1.100`

### 2. Set Static IP (Khuyến nghị)

**Option A: Qua Router**
- Vào router admin panel
- DHCP settings → Reserve IP cho MAC address của PC
- Ví dụ: Reserve `192.168.1.100` cho PC

**Option B: Trên PC (Ubuntu)**
```bash
# Edit netplan config
sudo nano /etc/netplan/01-netcfg.yaml

# Thêm config:
network:
  version: 2
  ethernets:
    enp3s0:  # Thay bằng interface thực tế (xem với 'ip a')
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]

# Apply changes
sudo netplan apply
```

### 3. Mở Firewall Port

**Option A: UFW (Ubuntu)**
```bash
# Check firewall status
sudo ufw status

# Allow port 8080
sudo ufw allow 8080/tcp

# Verify
sudo ufw status
```

**Option B: iptables**
```bash
# Add rule
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Save rules (Ubuntu)
sudo netfilter-persistent save

# List rules
sudo iptables -L -n | grep 8080
```

**Option C: Disable firewall (not recommended)**
```bash
sudo ufw disable
```

## 🧪 Test Connection

### Trên Raspberry Pi:

**1. Test basic connectivity**
```bash
cd /home/baobao/Projects/Vintern-1b-v3.5-demo/client

# Sửa PC_IP trong script hoặc pass as argument
python test_connection.py 192.168.1.100
```

Expected output:
```
✅ Network Ping - PASS
✅ Port Check - PASS  
✅ HTTP Health - PASS
✅ Bandwidth Test - PASS
```

**2. Test inference với client**
```bash
# Download client files to Pi (hoặc copy qua)
scp pc_inference_client.py pi@<PI_IP>:~/

# Trên Pi:
python pc_inference_client.py test-image.jpg "Mô tả ảnh này"
```

## 📚 Usage Examples

### Example 1: Basic Usage

```python
from pc_inference_client import PCInferenceClient

# Initialize client với PC IP
client = PCInferenceClient(pc_host="192.168.1.100")

# Health check
if client.health_check():
    print("PC is ready!")
else:
    print("PC is not available")
    exit(1)

# Inference
result = client.chat_completion(
    image="path/to/image.jpg",
    prompt="Mô tả chi tiết những gì bạn thấy"
)

if "error" not in result:
    print(f"Response: {result['content']}")
    print(f"Time: {result['elapsed_time']:.2f}s")
else:
    print(f"Error: {result['error']}")

client.close()
```

### Example 2: Với Detection Results

```python
from pc_inference_client import PCInferenceClient

client = PCInferenceClient(pc_host="192.168.1.100")

# Giả sử bạn đã detect objects với YOLO
detections = [
    {"class": "person", "confidence": 0.95, "bbox": [100, 200, 150, 300]},
    {"class": "car", "confidence": 0.88, "bbox": [300, 150, 200, 250]}
]

# VLM sẽ analyze dựa trên detected objects
result = client.analyze_detections(
    image="frame.jpg",
    detections=detections
)

print(result['content'])
client.close()
```

### Example 3: Stream Processing (Camera)

```python
import cv2
from pc_inference_client import PCInferenceClient
from PIL import Image
import numpy as np

client = PCInferenceClient(pc_host="192.168.1.100")

# RTSP stream
cap = cv2.VideoCapture("rtsp://admin:pass@192.168.1.4/cam/realmonitor?channel=1&subtype=1")

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # Process every 30 frames (1 frame per second at 30fps)
    if frame_count % 30 == 0:
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        # Inference
        result = client.chat_completion(
            image=pil_image,
            prompt="Có gì bất thường không?"
        )
        
        if "error" not in result:
            print(f"[Frame {frame_count}] {result['content']}")
        else:
            print(f"[Frame {frame_count}] Error: {result['error']}")
    
    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
client.close()
```

### Example 4: Async Multiple Cameras

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pc_inference_client import PCInferenceClient

def process_camera(camera_id, pc_host):
    """Process one camera in separate thread"""
    client = PCInferenceClient(pc_host=pc_host)
    
    # Capture frame from camera
    frame_path = f"camera_{camera_id}_frame.jpg"
    
    result = client.chat_completion(
        image=frame_path,
        prompt=f"Camera {camera_id}: Mô tả tình hình"
    )
    
    client.close()
    return camera_id, result

async def main():
    pc_host = "192.168.1.100"
    camera_ids = [1, 2]
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(executor, process_camera, cam_id, pc_host)
            for cam_id in camera_ids
        ]
        
        results = await asyncio.gather(*tasks)
        
        for cam_id, result in results:
            print(f"\nCamera {cam_id}:")
            if "error" not in result:
                print(result['content'])
            else:
                print(f"Error: {result['error']}")

asyncio.run(main())
```

## 🔧 Configuration

### Client Settings

```python
client = PCInferenceClient(
    pc_host="192.168.1.100",  # PC IP address
    pc_port=8080,              # Server port
    timeout=30,                # Request timeout (seconds)
    max_retries=3,             # Retry failed requests
    retry_delay=1.0            # Delay between retries
)
```

### Image Encoding Options

```python
result = client.chat_completion(
    image="image.jpg",
    prompt="...",
    max_tokens=200,           # Max tokens in response
    temperature=0.1           # 0=deterministic, 1=creative
)

# Hoặc với custom encoding
image_url = client.encode_image(
    image="large_image.jpg",
    max_size=(1024, 1024),   # Resize to max 1024x1024
    quality=85                # JPEG quality
)
```

## 🚨 Troubleshooting

### Pi không connect được PC

**1. Check network:**
```bash
ping 192.168.1.100
```

**2. Check port:**
```bash
nc -zv 192.168.1.100 8080
# hoặc
telnet 192.168.1.100 8080
```

**3. Check PC server:**
Trên PC:
```bash
# Server có đang chạy?
ps aux | grep llama-server

# Port có listening?
netstat -tlnp | grep 8080

# Firewall status
sudo ufw status
```

**4. Check firewall rules:**
```bash
# Trên PC
sudo iptables -L -n | grep 8080
```

### Request timeout

**Nguyên nhân:**
- PC CPU-only inference chậm (~2-3s)
- Network latency cao
- PC overloaded

**Giải pháp:**
```python
# Tăng timeout
client = PCInferenceClient(
    pc_host="192.168.1.100",
    timeout=60  # 60 seconds
)

# Hoặc upgrade PC lên GPU
# → Xem pc-inference-server/README.md
```

### Connection refused

**Nguyên nhân:**
- Server không chạy
- Wrong IP/port
- Firewall block

**Debug:**
```bash
# Trên PC
curl http://localhost:8080/health  # OK?
curl http://192.168.1.100:8080/health  # OK?

# Trên Pi
curl http://192.168.1.100:8080/health  # Fail?
```

## 📊 Performance Tips

### 1. Resize images trước khi gửi
```python
# Good - resize to 1024x1024
result = client.chat_completion(
    image="large_4k_image.jpg",  # Will auto-resize
    prompt="..."
)
```

### 2. Batch processing thay vì realtime
```python
# Collect frames
frames = []
for i in range(10):
    frame = capture_frame()
    frames.append(frame)

# Process batch
for frame in frames:
    result = client.chat_completion(frame, "...")
```

### 3. Rate limiting
```python
import time

last_inference = 0
MIN_INTERVAL = 1.0  # 1 second between inferences

while True:
    frame = capture_frame()
    
    now = time.time()
    if now - last_inference >= MIN_INTERVAL:
        result = client.chat_completion(frame, "...")
        last_inference = now
```

## 📡 Network Performance

### Bandwidth Usage Estimate

| Image Size | Encoded Size | Per Request | 1 FPS | 5 FPS |
|------------|--------------|-------------|-------|-------|
| 640x480 | ~50 KB | ~70 KB | 0.56 Mbps | 2.8 Mbps |
| 1024x768 | ~100 KB | ~140 KB | 1.1 Mbps | 5.6 Mbps |
| 1920x1080 | ~200 KB | ~280 KB | 2.2 Mbps | 11.2 Mbps |

**Khuyến nghị:**
- 100Mbps LAN: ✅ OK cho 2 cameras @ 5 FPS
- 1Gbps LAN: ✅ OK cho nhiều cameras

### Latency Estimate

```
Pi → PC round trip:
├─ Network: ~1-5ms (LAN)
├─ Encoding: ~50-100ms (Pi resize/encode)
├─ Inference: ~2000-3000ms (PC CPU-only)
├─ Decoding: ~10ms
└─ Total: ~2-3 seconds

Với PC GPU:
└─ Total: ~300-500ms (nhanh hơn 5-10x)
```

## 🔗 Integration với Backend

Xem [backend integration examples](../backend/README.md) để integrate client vào FastAPI backend.

---

**Ready to use!** Chạy `test_connection.py` để bắt đầu.
