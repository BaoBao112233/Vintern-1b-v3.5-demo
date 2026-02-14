# 🚀 HƯỚNG DẪN SETUP ARCHITECTURE PHÂN TÁN

## 🎯 Mục tiêu
**GIẢI QUYẾT**: Sử dụng Orange Pi để chạy VLLM service, Raspberry Pi chạy model inference → Không bị circular dependency, chia tải hiệu quả!

## 📊 Architecture Đúng

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER                             │
│                  http://192.168.1.14:8000                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              🍇 RASPBERRY PI 4 (192.168.1.14)               │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Backend API (Port 8000)                             │   │
│  │  ├─ /api/cameras/...        (Camera streaming)      │   │
│  │  ├─ /api/chat               (User chat) ───────┐    │   │
│  │  └─ /api/generate           (Model inference)   │    │   │
│  │       └─ LocalVinternModel                       │    │   │
│  │          └─ Vintern-1B-v3.5 (PyTorch)           │    │   │
│  └─────────────────────────────────────────────────┘   │   │
│                                                          │   │
│  📦 Models: /backend/models/Vintern-1B-v3_5             │   │
│  💾 RAM: ~3-4GB cho model inference                     │   │
└──────────────────────────────────────────────────────────┘  │
                           │                                   │
                           │ /api/chat gọi →                  │
                           ▼                                   │
┌─────────────────────────────────────────────────────────────┐
│            🍊 ORANGE PI RV2 (192.168.1.16)                  │
│                 RISC-V CPU, No PyTorch                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  VLLM Proxy Service (Port 8002)                      │   │
│  │  └─ Proxy Mode                                       │   │
│  │     └─ BACKEND_INFERENCE_URL =                       │   │
│  │        http://192.168.1.14:8000/api/generate        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ⚡ Vai trò: API Gateway + Request formatting            │ │
│  💾 RAM: ~500MB (không chạy model)                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Proxy request về ↑
                           └───────────────────────────────────┘
```

## 🔄 Flow Request

### 1. User Chat Request
```
1. Browser → Raspberry Pi: POST /api/chat
   {
     "message": "Phân tích ảnh này",
     "image_base64": "..."
   }

2. Raspberry Pi /api/chat → Orange Pi: POST http://192.168.1.16:8002/analyze
   {
     "messages": [...],
     "max_tokens": 512
   }

3. Orange Pi VLLM Proxy → Raspberry Pi: POST http://192.168.1.14:8000/api/generate
   {
     "messages": [...],
     "temperature": 0.7
   }

4. Raspberry Pi /api/generate:
   - Load Vintern model từ /backend/models/
   - Run inference với PyTorch
   - Return response

5. Orange Pi → Raspberry Pi /api/chat → Browser
   {
     "content": "Trong ảnh có...",
     "processing_time": 2.5
   }
```

### 2. Continuous Analysis
```
1. Browser timer (5s) → Raspberry Pi: POST /api/chat (auto)
2. Same flow như trên
3. Display kết quả trên UI
```

## ✅ Ưu điểm Architecture này

| Aspect | Benefit |
|--------|---------|
| **Không Loop** | Raspberry Pi `/api/generate` khác `/api/chat` → không circular dependency |
| **Phân tải** | Orange Pi handle API formatting, Raspberry Pi chạy model |
| **Scalable** | Có thể thêm nhiều Orange Pi proxy cho load balancing |
| **RISC-V Compatible** | Orange Pi không cần PyTorch, chỉ cần HTTP proxy |
| **RAM Efficient** | Orange Pi dùng ít RAM, Raspberry Pi tập trung vào inference |

## 🚀 Cài đặt

### Bước 1: Download Model (Raspberry Pi)

```bash
cd /home/pi/Projects/Vintern-1b-v3.5-demo
./download_vintern_model.sh
```

**Requirements:**
- ~5GB disk space
- `git-lfs` installed
- HuggingFace account

### Bước 2: Setup Toàn bộ System

```bash
./setup_local_inference.sh
```

Script này sẽ:
1. ✅ Kiểm tra model đã download
2. ✅ Cấu hình Raspberry Pi backend (.env)
3. ✅ Cấu hình Orange Pi VLLM proxy (via SSH)
4. ✅ Restart services
5. ✅ Test endpoints

### Bước 3: Verify

```bash
# Check Raspberry Pi backend
curl http://192.168.1.14:8000/api/health

# Check Raspberry Pi inference endpoint
curl http://192.168.1.14:8000/api/model-info

# Check Orange Pi VLLM proxy
curl http://192.168.1.16:8002/

# Test end-to-end (from browser)
# 1. Go to http://192.168.1.14:8000
# 2. Enable "Continuous AI Analysis"
# 3. Watch results appear automatically
```

## 📝 File Changes

### 1. Raspberry Pi Backend

**backend/app/api/inference.py** (NEW)
```python
# Endpoint để Orange Pi gọi đến
@router.post("/generate")
async def generate_inference(request: GenerateRequest):
    return await local_model.generate_response(...)
```

**backend/app/main.py** (UPDATED)
```python
from app.api.inference import router as inference_router
app.include_router(inference_router, prefix="/api", tags=["inference"])
```

**backend/.env** (UPDATED)
```bash
MODEL_MODE=local
USE_LOCAL_MODEL=true
LOCAL_MODEL_PATH=/home/pi/Projects/Vintern-1b-v3.5-demo/backend/models/Vintern-1B-v3_5
VLLM_SERVICE_URL=http://192.168.1.16:8002
```

### 2. Orange Pi VLLM Service

**vllm-service/.env** (UPDATED)
```bash
USE_PROXY_MODE=true
BACKEND_INFERENCE_URL=http://192.168.1.14:8000/api/generate
MODEL_ID=5CD-AI/Vintern-1B-v3_5
```

## 🧪 Testing

### Manual Test Flow

```bash
# 1. Test Raspberry Pi inference directly
curl -X POST http://192.168.1.14:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# Expected: {"content": "...", "processing_time": 2.5}

# 2. Test Orange Pi proxy
curl -X POST http://192.168.1.16:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 50
  }'

# Expected: Same format, proxied from Raspberry Pi

# 3. Test full flow via /api/chat
curl -X POST http://192.168.1.14:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mô tả ảnh này",
    "image_base64": "..."
  }'

# Expected: Complete analysis response
```

## 📊 Resource Usage

| Device | Component | RAM | CPU | Disk |
|--------|-----------|-----|-----|------|
| **Raspberry Pi** | Backend | ~500MB | 20-30% | - |
| | Vintern Model | ~3-4GB | 70-90% (inference) | 5GB |
| | **Total** | **~4-5GB** | **Variable** | **5GB** |
| **Orange Pi** | VLLM Proxy | ~300MB | 5-10% | <100MB |

## 🔥 Performance

- **First inference**: ~5-10 giây (load model)
- **Subsequent inferences**: ~2-3 giây
- **Continuous analysis**: Update mỗi 5-30 giây (configurable)

## ⚠️ Troubleshooting

### Issue: Model không load được

```bash
# Check model exists
ls -la /home/pi/Projects/Vintern-1b-v3.5-demo/backend/models/Vintern-1B-v3_5

# Check backend logs
docker logs -f backend

# Expected: "✅ Model được load thành công!"
```

### Issue: Orange Pi không kết nối được

```bash
# Test SSH
ssh orangepi@192.168.1.16

# Test VLLM service
ssh orangepi@192.168.1.16 "docker ps | grep vllm"

# Restart VLLM
ssh orangepi@192.168.1.16 "cd ~/Projects/Vintern-1b-v3.5-demo/vllm-service && docker compose restart"
```

### Issue: Circular dependency vẫn còn

```bash
# Check Orange Pi .env
ssh orangepi@192.168.1.16 "cat ~/Projects/Vintern-1b-v3.5-demo/vllm-service/.env"

# MUST have:
# BACKEND_INFERENCE_URL=http://192.168.1.14:8000/api/generate
# NOT: http://192.168.1.14:8000/api/chat
```

## 🎉 Success Indicators

Khi setup thành công, bạn sẽ thấy:

1. ✅ Health check shows:
   ```json
   {
     "status": "healthy",
     "model_ready": true,
     "vllm_ready": true,
     "cameras_ready": true
   }
   ```

2. ✅ Browser console shows:
   ```
   ✓ Continuous Analysis UI is present
   ✓ Cameras are ready
   ✓ VLLM is ready
   ✓ AI Analysis working
   ```

3. ✅ Logs show:
   ```
   [Raspberry Pi] ✅ Model được load thành công!
   [Orange Pi] ✅ Proxy connected to http://192.168.1.14:8000/api/generate
   [Browser] 🤖 AI phân tích: Trong ảnh có...
   ```

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra logs: `docker logs -f backend`
2. Test từng endpoint riêng lẻ (xem phần Testing)
3. Verify .env files trên cả 2 devices
4. Restart services: `./setup_local_inference.sh`

---

**Tác giả**: Generated by GitHub Copilot  
**Ngày**: 2026-02-14  
**Version**: 1.0
