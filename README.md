# Vintern-1B Enhanced Camera Demo

Dự án demo realtime camera với AI inference sử dụng model **5CD-AI/Vintern-1B-v3.5** chạy local, có tính năng:

- 🤖 **Local Model**: Tải và chạy model trực tiếp trên máy
- 🎯 **Object Detection**: Phát hiện vật thể với YOLO và vẽ bounding boxes
- 💬 **Chat Interface**: Hỏi đáp về vật thể trên camera
- 🔄 **Real-time Processing**: WebSocket cho inference realtime
- 🐳 **Docker Support**: Deploy dễ dàng với Docker Compose

## 🚀 Quick Start

### Bước 1: Chuẩn bị

```bash
# Clone repository
git clone <your-repo-url>
cd vintern-1b-v3.5-demo

# Copy environment file
cp .env.template .env
```

### Bước 2: Download Model

**Cách 1: Sử dụng script shell (Khuyến nghị)**
```bash
# Chạy script download
./download_model.sh
```

**Cách 2: Tải trực tiếp bằng git**
```bash
# Tạo thư mục models và tải model
mkdir -p models
cd models
git clone https://huggingface.co/5CD-AI/Vintern-1B-v3_5
cd ..
```

**Cách 3: Sử dụng Python script**
```bash
# Chạy Python script
python download_model.py
```

**Lưu ý**: Model sẽ được tự động download khi khởi động lần đầu nếu chưa có.

### Bước 3: Chạy với Docker

```bash
# Build và start containers
docker-compose up --build

# Hoặc chạy background
docker-compose up --build -d
```

### Bước 4: Truy cập ứng dụng

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

## 💡 Tính năng chính

### 1. 📷 Camera Feed
- Realtime camera access
- Configurable resolution và FPS
- Live object detection overlay

### 2. 🎯 Object Detection  
- YOLOv8 model for object detection
- Real-time bounding boxes
- Confidence threshold tuning
- Multiple object categories

### 3. 💬 Smart Chat
- Chat với AI về những gì thấy trên camera
- Context-aware responses dựa trên detected objects
- History lưu trữ cuộc trò chuyện
- Image analysis với bounding boxes

### 4. 🤖 AI Model
- **Model**: 5CD-AI/Vintern-1B-v3.5
- **Local Inference**: Chạy trực tiếp trên máy
- **GPU Acceleration**: Hỗ trợ CUDA
- **Memory Optimized**: Low memory usage

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Model mode: 'local' hoặc 'hf' (HuggingFace API)
MODEL_MODE=local

# Path to local model (tự động tạo khi download)
LOCAL_MODEL_PATH=./models/vintern-1b-v3.5

# HuggingFace token (chỉ cần khi dùng HF API)
# HF_TOKEN=your_token_here

# Frontend URLs
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_BACKEND_WS_URL=ws://localhost:8000
```

### GPU Support

Để sử dụng GPU, uncomment phần GPU config trong `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**Yêu cầu**: nvidia-docker runtime

## 📋 System Requirements

### Minimum
- **RAM**: 8GB+
- **Storage**: 5GB+ (cho model files)
- **CPU**: 4+ cores
- **Python**: 3.11+
- **Docker**: 20.10+

### Recommended  
- **RAM**: 16GB+
- **GPU**: NVIDIA với 6GB+ VRAM
- **Storage**: SSD 10GB+
- **CPU**: 8+ cores

## 🎯 Usage Examples

### Chat Commands
```
"Những vật thể nào bạn thấy?"
"Màu sắc của chiếc xe là gì?"
"Có bao nhiều người trong khung hình?"
"Mô tả chi tiết những gì bạn thấy"
```

## 📡 API Endpoints

### Chat & Vision
- `POST /api/chat` - Chat với AI về ảnh
- `POST /api/analyze-image` - Chỉ phân tích object detection  
- `GET /api/model-status` - Trạng thái model và detector

### Health & Status
- `GET /api/health` - Health check
- `GET /docs` - API documentation

### WebSocket
- `WS /ws/predict` - Realtime inference stream

## 🔍 Troubleshooting

### Model Loading Issues
```bash
# Check model files
ls -la models/vintern-1b-v3.5/

# Re-download model
rm -rf models/vintern-1b-v3.5/
python download_model.py
```

### Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose up --build --force-recreate

# Check logs
docker-compose logs backend
docker-compose logs frontend
```

## 📚 Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: React 18, WebSocket
- **AI Models**: Transformers, PyTorch
- **Object Detection**: Ultralytics YOLOv8
- **Infrastructure**: Docker, nginx

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`) 
5. Open Pull Request

## 🙏 Acknowledgments

- [5CD-AI/Vintern-1B-v3.5](https://huggingface.co/5CD-AI/Vintern-1B-v3_5) - AI Model
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - Object Detection
- [FastAPI](https://fastapi.tiangolo.com/) - Backend Framework
- [React](https://reactjs.org/) - Frontend Framework

---

🎯 **Happy Coding!** Nếu gặp vấn đề, hãy tạo issue trên GitHub.