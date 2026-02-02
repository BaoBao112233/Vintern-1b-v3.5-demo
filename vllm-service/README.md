# VLLM Service for Orange Pi RV 2

Vision Language Model proxy service for low-memory RISC-V device.

## Architecture

**IMPORTANT**: This service runs on RISC-V architecture which cannot run PyTorch. It acts as a **proxy** that forwards requests to a backend inference service running on a GPU-capable machine.

```
[Orange Pi RISC-V] (vllm-service:8002) 
        ↓ forwards to
[Backend Server] (e.g., 192.168.1.14:8000) - Runs actual Vintern model with GPU
```

## Features
- Lightweight proxy service for RISC-V
- Forwards inference requests to GPU backend
- Memory-optimized for 4GB RAM
- REST API compatible with detection service

## Requirements
- Orange Pi RV 2 (4GB RAM)  
- Ubuntu 22.04 ARM64 or RISC-V
- Python 3.11+
- **Backend inference server** with GPU running Vintern model

## Setup

1. **Setup Backend Inference Service** (on GPU machine)
   - Clone and setup the main backend service on a machine with GPU
   - Ensure it's accessible from Orange Pi network
   - Default URL: `http://192.168.1.14:8000`

2. **Configure Environment** (on Orange Pi)
   ```bash
   cp .env.template .env
   # Edit .env and set:
   # BACKEND_INFERENCE_URL=http://your-gpu-server:8000
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
