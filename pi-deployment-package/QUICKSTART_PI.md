# 🍓 Quick Start cho Raspberry Pi

Hướng dẫn nhanh setup Raspberry Pi để giao tiếp với PC inference server.

## 📋 Bước 1: Chuẩn Bị Network

### Trên PC (đã setup xong)
```bash
# 1. Lấy PC IP
ip addr show | grep "inet " | grep -v "127.0.0.1"
# Example output: 192.168.1.100

# 2. Check server đang chạy
curl http://localhost:8080/health
# Should return: {"status":"ok"}

# 3. Mở firewall nếu cần
sudo ufw allow 8080/tcp
```

### Trên Raspberry Pi

**1. Check network connectivity**
```bash
# Ping PC
ping -c 4 192.168.1.100  # Thay bằng IP của PC

# Check có thể telnet vào port
nc -zv 192.168.1.100 8080
```

**2. Cài Python dependencies**
```bash
# Update packages
sudo apt update
sudo apt install -y python3-pip python3-venv

# Create virtual environment
python3 -m venv ~/vintern-env
source ~/vintern-env/bin/activate

# Install dependencies
pip install requests pillow
```

## 📦 Bước 2: Copy Client Code sang Pi

### Option A: Git (khuyến nghị)
```bash
# Trên Pi
cd ~
# Option 1: Clone full repo
git clone <your-repo-url>
cd Vintern-1b-v3.5-demo/client

# Option 2: Clone and copy only client folder
git clone <your-repo-url>
cp -r Vintern-1b-v3.5-demo/client ~/pi-client
cd ~/pi-client
```

### Option B: SCP từ PC
```bash
# Trên PC
cd /home/baobao/Projects/Vintern-1b-v3.5-demo

# Copy client folder sang Pi
scp -r client/ pi@<PI_IP>:~/pi-client/

# Copy verification script
scp verify_network.sh pi@<PI_IP>:~/

# Trên Pi  
cd ~/pi-client
pip install -r requirements.txt
```

### Option C: Download trực tiếp
```bash
# Trên Pi (nếu repo đã push lên GitHub)
wget https://raw.githubusercontent.com/<user>/Vintern-1b-v3.5-demo/main/client/pc_inference_client.py
wget https://raw.githubusercontent.com/<user>/Vintern-1b-v3.5-demo/main/client/test_connection.py
wget https://raw.githubusercontent.com/<user>/Vintern-1b-v3.5-demo/main/client/requirements.txt
pip install -r requirements.txt
```

## 🧪 Bước 3: Test Connection

**3.1. Quick verification script**
```bash
# Trên Pi
cd ~

# Run verification (pass PC IP as argument)
./verify_network.sh 192.168.1.100

# Expected: All tests PASS
# ✅ Network Ping - PASS
# ✅ Port Check - PASS
# ✅ HTTP Health - PASS
# ✅ Python Dependencies - PASS
```

**3.2. Detailed connection test**
```bash
# Trên Pi
cd ~/pi-client  # hoặc ~/client
python test_connection.py 192.168.1.100

# Expected: All tests PASS
# ✅ Network Ping - PASS
# ✅ Port Check - PASS
# ✅ HTTP Health - PASS
# ✅ Bandwidth Test - PASS
```

## 🖼️ Bước 4: Test Inference

```bash
# Trên Pi, download test image
wget https://raw.githubusercontent.com/opencv/opencv/master/samples/data/fruits.jpg -O test.jpg

# Test inference
python pc_inference_client.py test.jpg "Mô tả những gì bạn thấy"

# Expected output:
# ✅ PC server is ready!
# ✅ Response:
# [Model's description of the image]
# Time: 2.xx s
```

## 🔧 Troubleshooting

### ❌ Test connection fail?

**1. Ping không thành công:**
```bash
# Trên Pi
ip addr show  # Check Pi IP
ip route      # Check gateway

# Trên PC  
ip addr show  # Verify PC IP
```

**2. Port không mở:**
```bash
# Trên PC
sudo ufw status
sudo ufw allow 8080/tcp

# Check server
ps aux | grep llama-server
netstat -tlnp | grep 8080
```

**3. Firewall block:**
```bash
# Trên PC - temporarily disable (for testing)
sudo ufw disable

# Test từ Pi
curl http://192.168.1.100:8080/health

# Re-enable và mở port
sudo ufw enable
sudo ufw allow 8080/tcp
```

### ❌ Inference timeout?

```python
# Edit pc_inference_client.py
client = PCInferenceClient(
    pc_host="192.168.1.100",
    timeout=60  # Tăng lên 60 seconds
)
```

### ❌ Slow network?

```bash
# Test bandwidth
# Trên Pi
iperf3 -c 192.168.1.100

# Expected: >90 Mbps for 100Mbps LAN
```

## 🎯 Next: Integrate vào Backend

Sau khi test thành công, integrate vào backend:

```python
# backend/services/pc_vlm_client.py
from client.pc_inference_client import PCInferenceClient

class PCVLMService:
    def __init__(self, pc_host: str):
        self.client = PCInferenceClient(pc_host=pc_host)
    
    async def analyze_frame(self, frame, prompt: str):
        # Your integration logic
        result = self.client.chat_completion(frame, prompt)
        return result
```

Xem: [Backend Integration Guide](backend/README.md)

## 📚 References

- [Client Library Docs](client/README.md)
- [PC Server Setup](pc-inference-server/README.md)
- [Full Architecture](ARCHITECTURE.md)

---

**Ready!** Giờ Pi đã có thể giao tiếp với PC! 🎉
