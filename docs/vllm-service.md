# VLLM Service for Orange Pi RV 2

Vision Language Model service với model optimization cho low-memory device.

## Features
- Vintern-1B-v3.5 với INT8 quantization
- Memory-optimized inference
- Context-aware analysis (nhận detected objects từ Detection Service)
- ARM64-optimized
- REST API

## Requirements
- Orange Pi RV 2 (4GB RAM)
- Ubuntu 22.04 ARM64
- Python 3.11+

## Installation

```bash
# Install Python packages
pip install -r requirements.txt

# Download and quantize model
python scripts/download_model.py
```

## Usage

```bash
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8002

# Or with Docker
docker build -f Dockerfile.arm64 -t vllm-service .
docker run -p 8002:8002 vllm-service
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/analyze` - Analyze image with context
- `POST /api/chat` - Chat about image

## Network Configuration

Static IP: 192.168.100.20
Port: 8002
Detection Service: http://192.168.100.10:8001
