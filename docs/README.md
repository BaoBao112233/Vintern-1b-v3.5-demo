# Documentation Index

Tài liệu hướng dẫn cho hệ thống 2 services phân tán.

## 📚 Tài liệu chính

### 1. [QUICKSTART.md](./QUICKSTART.md)
**Quick Start Guide** - Hướng dẫn nhanh để bắt đầu
- Tóm tắt kiến trúc
- Deploy nhanh
- Test cơ bản

### 2. [DEPLOYMENT.md](./DEPLOYMENT.md)
**Full Deployment Guide** - Hướng dẫn deployment đầy đủ
- Cấu hình mạng Ethernet LAN
- Setup từng bước cho Raspberry Pi 4
- Setup từng bước cho Orange Pi RV 2
- Troubleshooting
- Performance monitoring
- Maintenance

### 3. [README_DISTRIBUTED.md](./README_DISTRIBUTED.md)
**Architecture Overview** - Tổng quan kiến trúc hệ thống
- Sơ đồ kiến trúc
- Data flow
- API documentation
- Configuration
- Performance metrics

### 4. [detection-service.md](./detection-service.md)
**Detection Service Documentation**
- Raspberry Pi 4 + Coral USB
- Object detection với TensorFlow Lite
- API endpoints
- Model information

### 5. [vllm-service.md](./vllm-service.md)
**VLLM Service Documentation**
- Orange Pi RV 2 
- Vision Language Model với quantization
- API endpoints
- Memory optimization

---

## 🏗️ Kiến trúc tóm tắt

```
Detection Service           VLLM Service
(Raspberry Pi 4)           (Orange Pi RV 2)
192.168.100.10:8001   ←→   192.168.100.20:8002
   Coral USB TPU              4GB RAM
   Object Detection        Vision-Language
```

---

## 🚀 Bắt đầu nhanh

1. **Đọc** [QUICKSTART.md](./QUICKSTART.md) để có overview
2. **Follow** [DEPLOYMENT.md](./DEPLOYMENT.md) để deploy
3. **Tham khảo** [README_DISTRIBUTED.md](./README_DISTRIBUTED.md) cho API details

---

## 📖 Đọc theo thứ tự

Nếu bạn mới bắt đầu, đọc theo thứ tự:

1. ✅ [QUICKSTART.md](./QUICKSTART.md) - Hiểu overview
2. ✅ [README_DISTRIBUTED.md](./README_DISTRIBUTED.md) - Hiểu kiến trúc
3. ✅ [detection-service.md](./detection-service.md) - Hiểu Detection Service
4. ✅ [vllm-service.md](./vllm-service.md) - Hiểu VLLM Service
5. ✅ [DEPLOYMENT.md](./DEPLOYMENT.md) - Deploy lên hardware

---

## 🔗 Links nhanh

- Detection Service code: `../detection-service/`
- VLLM Service code: `../vllm-service/`
- Docker Compose configs: Trong mỗi service directory
- Environment templates: `.env.template` trong mỗi service

---

## 💡 Tips

- **Test local trước:** Có thể test cả 2 services trên 1 máy bằng cách thay đổi IP trong `.env`
- **Memory issues:** Nếu Orange Pi bị out of memory, đổi `QUANTIZATION_BITS=4` trong VLLM service
- **Network issues:** Kiểm tra firewall và static IP configuration
- **Coral không nhận:** Chạy `lsusb | grep Google` để kiểm tra

---

## 📞 Support

Nếu gặp vấn đề:
1. Check logs: `docker-compose logs -f`
2. Check [DEPLOYMENT.md](./DEPLOYMENT.md) Troubleshooting section
3. Verify network: `ping <service-ip>`
