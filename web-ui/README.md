# 🎨 Web UI cho Vintern Vision Test

## ✅ GIẢI QUYẾT VẤN ĐỀ

**Vấn đề ban đầu:** Web UI mặc định của llama.cpp **không hỗ trợ upload ảnh** cho multimodal models.

**Giải pháp:** Tạo custom Web UI với:
- ✅ Upload/drag-drop ảnh
- ✅ Preview ảnh
- ✅ Nhập prompt tiếng Việt
- ✅ Hiển thị response đẹp
- ✅ Show timing và token stats

## 🚀 Cách Sử Dụng

### 1. Start cả 2 services

```bash
cd /home/baobao/Projects/Vintern-1b-v3.5-demo

# Terminal 1: PC Inference Server (đã chạy)
cd models/gguf
/home/baobao/Projects/llama.cpp-vintern/build/bin/llama-server \
  -m Vintern-1B-v3_5-Q8_0.gguf \
  --mmproj mmproj-Vintern-1B-v3_5-Q8_0.gguf \
  --host 0.0.0.0 \
  --port 8080

# Terminal 2: Web UI (đã chạy)
cd web-ui
python3 -m http.server 3000
```

### 2. Mở browser

```
http://localhost:3000
```

### 3. Test với ảnh

1. **Click** vào hộp upload hoặc **kéo thả** ảnh
2. **Nhập** câu hỏi (mặc định: "Mô tả chi tiết những gì bạn thấy trong ảnh này.")
3. **Click** "🚀 Phân tích ảnh"
4. **Đợi** 2-3s (CPU mode) hoặc ~0.5s (nếu có GPU)
5. **Xem** kết quả!

## 📊 Test Results

### Test với test-fruits.jpg
```
✅ SUCCESS!
Response: "Hình ảnh chụp cận cảnh một đống trái cây,"
Time: ~2-3s
Tokens: 313
```

## 🎯 Features

### Web UI Features
- ✅ Drag & drop upload
- ✅ Image preview
- ✅ Vietnamese prompt support
- ✅ Loading animation
- ✅ Error handling
- ✅ Response stats (time + tokens)
- ✅ Beautiful gradient UI
- ✅ Responsive design

### API Endpoints
```
POST http://localhost:8080/v1/chat/completions

Body:
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
        {"type": "text", "text": "Your prompt"}
      ]
    }
  ],
  "max_tokens": 200,
  "temperature": 0.1
}
```

## 🔧 Troubleshooting

### Lỗi "Failed to tokenize prompt"
**Nguyên nhân:** Server chưa load mmproj đúng, hoặc sai format

**Giải pháp:**
```bash
# Stop server cũ
pkill -f llama-server

# Start lại với mmproj
cd /home/baobao/Projects/Vintern-1b-v3.5-demo/models/gguf
/home/baobao/Projects/llama.cpp-vintern/build/bin/llama-server \
  -m Vintern-1B-v3_5-Q8_0.gguf \
  --mmproj mmproj-Vintern-1B-v3_5-Q8_0.gguf \
  --host 0.0.0.0 \
  --port 8080
```

### Web UI không load
```bash
# Check port 3000
lsof -i :3000

# Kill và restart
pkill -f "http.server 3000"
cd /home/baobao/Projects/Vintern-1b-v3.5-demo/web-ui
python3 -m http.server 3000
```

### Inference quá chậm
- **Hiện tại:** CPU-only (~2-3s)
- **Nâng cấp GPU:** Xem [pc-inference-server/README.md](../pc-inference-server/README.md)

## 📂 File Structure

```
web-ui/
├── index.html          # Web UI chính
└── README.md          # Docs này

quick_test.py          # CLI test script
test-fruits.jpg        # Sample image
```

## 🎓 Example Prompts

Tiếng Việt:
- "Mô tả chi tiết những gì bạn thấy trong ảnh này."
- "Có những trái cây nào trong ảnh?"
- "Màu sắc chủ đạo là gì?"
- "Đây là ảnh chụp ở đâu?"

English:
- "Describe this image in detail."
- "What fruits do you see?"
- "What are the main colors?"
- "Where was this photo taken?"

## 🚀 Next Steps

### Để integrate vào Pi backend:

1. **Copy web UI sang Pi:**
```bash
scp -r web-ui/ pi@<PI_IP>:~/
```

2. **Integrate vào FastAPI:**
```python
# Serve static files
from fastapi.staticfiles import StaticFiles
app.mount("/ui", StaticFiles(directory="web-ui"), name="ui")
```

3. **Or use React:** Copy design vào React frontend hiện có

---

**Ready to use!** Mở http://localhost:3000 và test thử! 🎉
