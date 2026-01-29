# Quick Start Guide

## Tóm tắt

Dự án đã được tách thành **2 services riêng biệt** giao tiếp qua **Ethernet LAN**:

### 1️⃣ Detection Service (Raspberry Pi 4 + Coral USB)
- **IP**: `192.168.100.10:8001`
- **Chức năng**: Object Detection realtime với Coral TPU
- **Code**: `detection-service/`

### 2️⃣ VLLM Service (Orange Pi RV 2)
- **IP**: `192.168.100.20:8002`
- **Chức năng**: Vision Language Model với INT8 quantization
- **Code**: `vllm-service/`

---

## 📁 Files Created

### Detection Service
```
detection-service/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/detect.py        # Detection endpoints
│   └── models/detector.py   # Coral TPU detector
├── Dockerfile.arm
├── docker-compose.yml
├── requirements.txt
└── .env.template
```

### VLLM Service
```
vllm-service/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/analyze.py       # Analysis endpoints
│   └── models/vllm.py       # Optimized VLLM
├── scripts/download_model.py
├── Dockerfile.arm64
├── docker-compose.yml
├── requirements.txt
└── .env.template
```

### Documentation
- `DEPLOYMENT.md` - Full deployment guide
- `README_DISTRIBUTED.md` - Architecture overview
- `detection-service/README.md`
- `vllm-service/README.md`

---

## 🚀 Deploy Nhanh

### Bước 1: Raspberry Pi 4 (Detection)

```bash
cd detection-service

# Tải model
mkdir -p models && cd models
wget https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
wget https://github.com/google-coral/test_data/raw/master/coco_labels.txt
cd ..

# Setup
cp .env.template .env
docker-compose up -d
```

### Bước 2: Orange Pi RV 2 (VLLM)

```bash
cd vllm-service

# Tải model
python3 scripts/download_model.py

# Setup
cp .env.template .env
docker-compose up -d
```

### Bước 3: Test

```bash
# Test Detection
curl http://192.168.100.10:8001/health

# Test VLLM
curl http://192.168.100.20:8002/health
```

---

## 📖 Tài liệu

1. **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Hướng dẫn deployment đầy đủ
2. **[README_DISTRIBUTED.md](./README_DISTRIBUTED.md)** - Kiến trúc hệ thống
3. **[walkthrough.md](./walkthrough.md)** - Implementation walkthrough (artifact)

---

## 🌐 Network Setup

```bash
# Raspberry Pi 4
sudo nano /etc/dhcpcd.conf
# Add: static ip_address=192.168.100.10/24

# Orange Pi RV 2
sudo nano /etc/netplan/01-network-manager-all.yaml
# Add: addresses: [192.168.100.20/24]
```

Xem chi tiết trong [DEPLOYMENT.md](./DEPLOYMENT.md).

---

## 🎯 Next Steps

- [ ] Deploy lên hardware thật
- [ ] Test detection service
- [ ] Test VLLM service
- [ ] Test integration end-to-end
- [ ] (Optional) Update frontend để connect với 2 services

**Happy deployment! 🚀**
