# Raspberry Pi Deployment Package

Package này chứa tất cả file cần thiết để tích hợp Vision AI vào Raspberry Pi.

## 📦 Package Contents

```
pi-deployment-package/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── setup_on_pi.sh                     # Auto setup script
├── PI_INTEGRATION_GUIDE.md            # Chi tiết integration guide
├── OUTPUT_LIMITATION.md               # Model limitations explained
├── ARCHITECTURE.md                    # System architecture
├── QUICKSTART_PI.md                   # Quick start guide
├── smart_analyze.py                   # Smart multi-turn analyzer
├── detailed_test.py                   # Detailed analysis script
├── quick_test.py                      # Quick test script
└── client/
    ├── pc_inference_client.py         # Main client library
    ├── test_connection.py             # Connection test tool
    ├── backend_integration_example.py # Integration examples
    ├── vision_service_example.py      # Service wrapper
    ├── fastapi_endpoints_example.py   # FastAPI endpoints
    └── README.md                      # Client library docs
```

## 🚀 Quick Start

### Step 1: Transfer sang Pi

**Option A: SSH/SCP**
```bash
# Compress package
tar -czf pi-package.tar.gz .

# Copy to Pi
scp pi-package.tar.gz pi@<PI_IP>:~/

# On Pi
ssh pi@<PI_IP>
cd ~
tar -xzf pi-package.tar.gz
```

**Option B: USB**
Copy toàn bộ folder này sang USB, rồi copy vào Pi

### Step 2: Setup Dependencies

```bash
cd pi-deployment-package
chmod +x setup_on_pi.sh
./setup_on_pi.sh
```

### Step 3: Configure PC IP

Edit file `client/vision_service_example.py`, line 43:
```python
pc_host="192.168.1.3",  # ← Thay bằng IP thực của PC
```

### Step 4: Test Connection

```bash
cd client
python3 test_connection.py <PC_IP>
```

Kết quả mong đợi:
```
✅ PC Inference Server: AVAILABLE
🌐 Network: OK (latency: 2.3ms)
🖼️ Vision Model: Vintern-1B-v3.5
```

### Step 5: Test Analysis

```bash
# Quick test
python3 quick_test.py test_image.jpg

# Comprehensive test
python3 smart_analyze.py test_image.jpg
```

### Step 6: Integrate vào Backend

Xem chi tiết trong **PI_INTEGRATION_GUIDE.md**

Có 3 cách integrate:

1. **Simple**: Dùng `pc_inference_client.py` trực tiếp
2. **Service Wrapper**: Dùng `vision_service_example.py`
3. **FastAPI**: Dùng `fastapi_endpoints_example.py`

## 📚 Documentation

- **PI_INTEGRATION_GUIDE.md** - Chi tiết nhất, đọc file này trước
- **OUTPUT_LIMITATION.md** - Giải thích vì sao model output ngắn
- **client/README.md** - API reference của client library

## 🔧 Troubleshooting

### Connection Refused
```bash
# Check PC server
curl http://<PC_IP>:8080/health

# Check firewall on PC
sudo ufw allow 8080/tcp
```

### Import Error
```bash
# Install missing packages
pip3 install requests pillow --user
```

### Slow Performance
- Server chạy CPU-only mode (~2-3s/inference)
- Để tăng tốc: rebuild llama.cpp with CUDA on PC

## 🎯 Next Steps

1. ✅ Test connection
2. ✅ Test analysis scripts
3. ⚙️ Integrate into FastAPI backend
4. 📸 Connect RTSP cameras
5. 🚀 Deploy to production

## 📞 Support

Đọc PI_INTEGRATION_GUIDE.md để biết chi tiết!

---

**Good luck! 🎉**
