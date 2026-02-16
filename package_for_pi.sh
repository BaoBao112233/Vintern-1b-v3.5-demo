#!/bin/bash

###############################################################################
# Package Everything for Raspberry Pi Transfer
# 
# Script này tạo một package hoàn chỉnh để copy sang Raspberry Pi
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "======================================="
echo "📦 Packaging for Raspberry Pi"
echo "======================================="
echo ""

# Create temp directory
PACKAGE_DIR="$PROJECT_ROOT/pi-deployment-package"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

echo "📁 Creating package structure..."

# 1. Copy client library
echo "  → Client library..."
mkdir -p "$PACKAGE_DIR/client"
cp -r "$PROJECT_ROOT/client"/*.py "$PACKAGE_DIR/client/"
cp "$PROJECT_ROOT/client/README.md" "$PACKAGE_DIR/client/" 2>/dev/null || true

# 2. Copy analysis scripts
echo "  → Analysis scripts..."
cp "$PROJECT_ROOT/smart_analyze.py" "$PACKAGE_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/detailed_test.py" "$PACKAGE_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/quick_test.py" "$PACKAGE_DIR/" 2>/dev/null || true

# 3. Copy documentation
echo "  → Documentation..."
cp "$PROJECT_ROOT/PI_INTEGRATION_GUIDE.md" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/OUTPUT_LIMITATION.md" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/ARCHITECTURE.md" "$PACKAGE_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/QUICKSTART_PI.md" "$PACKAGE_DIR/" 2>/dev/null || true

# 4. Create requirements.txt for Pi
echo "  → Requirements file..."
cat > "$PACKAGE_DIR/requirements.txt" << 'EOF'
# Python dependencies for Raspberry Pi
requests>=2.28.0
pillow>=9.0.0
python-multipart>=0.0.5  # For FastAPI file uploads
fastapi>=0.100.0
uvicorn[standard]>=0.20.0

# Optional but recommended
python-dotenv>=0.19.0    # For config management
aiofiles>=23.0.0         # For async file operations
EOF

# 5. Create setup script for Pi
echo "  → Setup script for Pi..."
cat > "$PACKAGE_DIR/setup_on_pi.sh" << 'EOFSETUP'
#!/bin/bash
###############################################################################
# Setup Script - Run này trên Raspberry Pi
###############################################################################

set -e

echo "======================================"
echo "🍓 Raspberry Pi Vision AI Setup"
echo "======================================"
echo ""

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found! Installing..."
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt --user

echo ""
echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Update PC IP in vision_service_example.py (line 43):"
echo "   pc_host='YOUR_PC_IP'"
echo ""
echo "2. Test connection:"
echo "   cd client"
echo "   python3 test_connection.py YOUR_PC_IP"
echo ""
echo "3. Test analysis:"
echo "   python3 smart_analyze.py test_image.jpg"
echo ""
echo "4. Integrate into your backend:"
echo "   See PI_INTEGRATION_GUIDE.md"
echo ""
EOFSETUP

chmod +x "$PACKAGE_DIR/setup_on_pi.sh"

# 6. Create README for the package
echo "  → Package README..."
cat > "$PACKAGE_DIR/README.md" << 'EOFREADME'
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
EOFREADME

# 7. Create test image (placeholder)
echo "  → Test assets..."
if [ -f "$PROJECT_ROOT/test-fruits.jpg" ]; then
    cp "$PROJECT_ROOT/test-fruits.jpg" "$PACKAGE_DIR/test_image.jpg"
fi

# 8. Compress everything
echo ""
echo "📦 Creating archive..."
cd "$PROJECT_ROOT"
tar -czf pi-deployment-package.tar.gz pi-deployment-package/

# Get size
PACKAGE_SIZE=$(du -sh pi-deployment-package.tar.gz | cut -f1)

echo ""
echo "======================================="
echo "✅ Package Created Successfully!"
echo "======================================="
echo ""
echo "📦 Package location:"
echo "   $PROJECT_ROOT/pi-deployment-package.tar.gz"
echo "   Size: $PACKAGE_SIZE"
echo ""
echo "📁 Uncompressed folder:"
echo "   $PROJECT_ROOT/pi-deployment-package/"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Transfer to Raspberry Pi:"
echo "   scp pi-deployment-package.tar.gz pi@<PI_IP>:~/"
echo ""
echo "2. On Pi, extract:"
echo "   tar -xzf pi-deployment-package.tar.gz"
echo "   cd pi-deployment-package"
echo ""
echo "3. Run setup:"
echo "   ./setup_on_pi.sh"
echo ""
echo "4. Read guide:"
echo "   cat PI_INTEGRATION_GUIDE.md"
echo ""
echo "======================================="
echo ""
