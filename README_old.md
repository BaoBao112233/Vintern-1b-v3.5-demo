# Vintern-1B Realtime Camera Inference Demo

🎥 **Realtime camera inference demo using [5CD-AI/Vintern-1B-v3_5](https://huggingface.co/5CD-AI/Vintern-1B-v3_5) model**

This project provides a complete fullstack solution for realtime camera inference with a React frontend, FastAPI backend, and Docker deployment support. The system can run inference using either Hugging Face Inference API (remote) or local GGML/llama.cpp models.

## 🌟 Features

- **Realtime Camera Feed**: Browser-based camera access with live video stream
- **Dual Inference Modes**: Remote (Hugging Face API) and Local (GGML/llama.cpp) 
- **Multiple Communication Protocols**: WebSocket for low-latency realtime inference, HTTP REST API for request-based inference
- **Live Results Overlay**: Real-time bounding boxes, labels, and annotations on camera feed
- **Docker Deployment**: Complete containerized solution with docker-compose
- **Responsive UI**: Modern React interface with real-time status monitoring
- **Model Conversion Tools**: Scripts to convert HF models to GGUF format for local inference

## 🏗️ Architecture

```
┌─────────────────┐    WebSocket/HTTP    ┌──────────────────┐
│   Frontend      │ ←──────────────────→ │    Backend       │
│   React App     │                      │    FastAPI       │
│   - Camera Feed │                      │    - WebSocket   │
│   - Results UI  │                      │    - REST API    │
└─────────────────┘                      └──────────────────┘
                                                   │
                                         ┌─────────┴─────────┐
                                         │                   │
                                   ┌─────▼─────┐    ┌────▼────┐
                                   │ HF Client │    │ Local   │
                                   │ (Remote)  │    │ Runner  │
                                   └───────────┘    └─────────┘
```

## 📦 Project Structure

```
vintern-realtime-demo/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Main application
│   │   ├── api/
│   │   │   └── predict.py  # API routes
│   │   ├── services/
│   │   │   ├── hf_client.py        # Hugging Face client
│   │   │   ├── local_runner.py     # Local model runner
│   │   │   └── websocket_manager.py # WebSocket handler
│   │   └── utils/
│   │       └── image_processing.py # Image utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.jsx        # Main component
│   │   ├── components/
│   │   │   ├── CameraFeed.jsx      # Camera component
│   │   │   ├── StatusPanel.jsx     # Status display
│   │   │   ├── ControlPanel.jsx    # Settings control
│   │   │   └── ResultsPanel.jsx    # Results display
│   │   └── services/
│   │       ├── api.js     # HTTP API client
│   │       └── websocket.js # WebSocket client
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── model-runner/           # Local model service
│   ├── model_server.py    # Local inference server
│   ├── convert_model.py   # Model conversion script
│   ├── scripts/
│   │   └── setup.sh      # Setup utilities
│   └── Dockerfile
├── docker-compose.yml     # Docker orchestration
├── .env.template         # Environment template
└── README.md             # This file
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-username/vintern-realtime-demo.git
cd vintern-realtime-demo

# Copy environment template
cp .env.template .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
# For Hugging Face mode (easiest to start)
MODEL_MODE=hf
HF_TOKEN=your_huggingface_token_here

# For local mode (requires model conversion)
# MODEL_MODE=local
# LOCAL_MODEL_PATH=./models
```

Get your Hugging Face token from: https://huggingface.co/settings/tokens

### 3. Run with Docker Compose

```bash
# Start with Hugging Face mode (recommended for first run)
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Configuration Modes

### Remote Mode (Hugging Face API)

Easiest setup - uses Hugging Face Inference API:

```bash
MODEL_MODE=hf
HF_TOKEN=your_token_here
```

**Pros**: No local setup required, always up-to-date model
**Cons**: Requires internet, API rate limits, latency

### Local Mode (GGML/llama.cpp)

Runs model locally for better privacy and control:

```bash
MODEL_MODE=local
LOCAL_MODEL_PATH=./models
```

**Pros**: No internet required, better privacy, lower latency
**Cons**: Requires model conversion, more resources

## 🛠️ Local Model Setup

### Option 1: Automatic Conversion

```bash
# Start model-runner service to convert model
docker-compose --profile local up model-runner

# Or manually convert
docker run -v $(pwd)/models:/models vintern-model-runner \
    python3 /app/convert_model.py --token YOUR_HF_TOKEN
```

### Option 2: Manual Setup

1. **Download and convert model**:

```bash
# Create models directory
mkdir -p models

# Using Hugging Face transformers
python3 -c "
from transformers import AutoModel, AutoTokenizer
import torch

model_id = '5CD-AI/Vintern-1B-v3_5'
model = AutoModel.from_pretrained(model_id, torch_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(model_id)

model.save_pretrained('./models/vintern-1b-original')
tokenizer.save_pretrained('./models/vintern-1b-original')
"
```

2. **Convert to GGUF** (requires llama.cpp):

```bash
# Clone llama.cpp
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
make -j$(nproc)

# Convert model
python3 convert.py ../models/vintern-1b-original \
    --outfile ../models/vintern-1b-v3_5-q4_0.gguf \
    --outtype q4_0
```

3. **Run with local model**:

```bash
MODEL_MODE=local docker-compose --profile local up
```

## 📚 API Documentation

### REST API Endpoints

#### Health Check
```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "model_mode": "hf",
  "model_ready": true,
  "model_info": {...}
}
```

#### Single Image Prediction
```http
POST /api/predict
Content-Type: application/json

{
  "image_base64": "base64_encoded_image",
  "frame_id": "optional_frame_id",
  "resize_width": 640,
  "resize_height": 480
}
```

#### File Upload Prediction
```http
POST /api/predict/upload
Content-Type: multipart/form-data

file: image_file
frame_id: optional_frame_id
resize_width: 640
resize_height: 480
```

### WebSocket API

Connect to: `ws://localhost:8000/ws/predict`

Send frame:
```json
{
  "frame_id": "frame_123",
  "timestamp": 1640995200.0,
  "image_base64": "base64_encoded_image",
  "width": 640,
  "height": 480
}
```

Receive result:
```json
{
  "frame_id": "frame_123",
  "timestamp": 1640995200.0,
  "processing_time": 0.15,
  "success": true,
  "results": {
    "detection_results": [
      {
        "label": "person",
        "confidence": 0.95,
        "bbox": {"xmin": 100, "ymin": 50, "xmax": 300, "ymax": 400}
      }
    ],
    "total_objects": 1
  }
}
```

## 🎛️ Frontend Usage

### Camera Controls
- **Start Camera**: Initialize camera access
- **Stop Camera**: Stop camera feed
- **Settings**: Adjust resolution, FPS, overlay options

### Display Modes
- **Live Feed**: Real-time camera with overlay annotations
- **Results Panel**: Detailed inference results
- **Status Panel**: Connection and model status

### Configuration Options
- **Connection Mode**: WebSocket (realtime) or HTTP (request-based)
- **FPS**: 1-30 frames per second
- **Resolution**: 320x240 to 1280x720
- **Overlay**: Toggle result annotations on video

## 🚢 Deployment

### Development
```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend only  
cd frontend
npm install
npm start
```

### Production with Docker

1. **Configure for production**:
```bash
# Update .env for production
NODE_ENV=production
REACT_APP_BACKEND_URL=https://your-domain.com
REACT_APP_BACKEND_WS_URL=wss://your-domain.com

# Use production profile
docker-compose --profile production up -d
```

2. **With reverse proxy**:
```bash
# Includes Nginx reverse proxy with SSL
docker-compose --profile production up -d nginx
```

### Scaling

For high-traffic deployments:

```bash
# Multiple backend instances
docker-compose up --scale backend=3

# With load balancer
docker-compose --profile production up -d
```

## 🔧 Troubleshooting

### Common Issues

#### Camera Not Working
```bash
# Check browser permissions
# Ensure HTTPS in production
# Verify camera access in browser settings
```

#### Model Loading Errors
```bash
# Check HF token validity
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://huggingface.co/api/whoami

# Verify model path for local mode
ls -la ./models/
```

#### WebSocket Connection Issues  
```bash
# Check backend logs
docker-compose logs backend

# Verify WebSocket endpoint
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8000/ws/predict
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Adjust settings in .env
INFERENCE_THREADS=8
BACKEND_CPU_LIMIT=4
```

### Debug Mode

Enable detailed logging:
```bash
DEBUG=true
LOG_LEVEL=debug
docker-compose up
```

## 📊 Performance Optimization

### Frontend Optimizations
- Adjust FPS based on use case (5-10 FPS usually sufficient)
- Lower resolution for faster processing
- Use WebSocket for minimal latency
- Enable result overlay caching

### Backend Optimizations  
- Use local mode for better latency
- Increase inference threads for local mode
- Enable Redis caching (profile: cache)
- Adjust model quantization (q4_0 vs q8_0)

### Model Optimizations
- **q4_0**: Fastest, lower quality (~2-4GB)
- **q8_0**: Balanced performance (~4-8GB) 
- **f16**: Best quality, slower (~8-16GB)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)  
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[5CD-AI/Vintern-1B-v3_5](https://huggingface.co/5CD-AI/Vintern-1B-v3_5)** - The vision-language model
- **[llama.cpp](https://github.com/ggml-org/llama.cpp)** - Local inference engine
- **[ngxson/vintern-realtime-demo](https://github.com/ngxson/vintern-realtime-demo)** - Reference implementation
- **Hugging Face** - Model hosting and inference API
- **FastAPI** - High-performance web framework
- **React** - Frontend framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/vintern-realtime-demo/issues)  
- **Discussions**: [GitHub Discussions](https://github.com/your-username/vintern-realtime-demo/discussions)
- **Model Questions**: [Hugging Face Model Page](https://huggingface.co/5CD-AI/Vintern-1B-v3_5)

---

**Made with ❤️ for the AI community**