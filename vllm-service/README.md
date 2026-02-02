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
- Ubuntu 22.04 ARM64 or RISC-V
- Python 3.11+
- Hugging Face account and API token (for model inference)

## Setup

1. **Get Hugging Face API Token**
   - Create account at [huggingface.co](https://huggingface.co)
   - Go to Settings → Access Tokens
   - Create a new token with read permissions

2. **Configure Environment**
   ```bash
   cp .env.template .env
   # Edit .env and add your HF token:
   # HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx
   ```

## Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Download and quantize model
python3 scripts/download_model.py
```

## Usage

```bash
# Run with uvicorn (in virtual environment)
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8002

# Or with Docker
sudo docker build -f Dockerfile.arm64 -t vllm-service .
sudo docker run -p 8002:8002 vllm-service
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/analyze` - Analyze image with context
- `POST /api/chat` - Chat about image

## Network Configuration

Static IP: 192.168.100.20
Port: 8002
Detection Service: http://192.168.100.10:8001
