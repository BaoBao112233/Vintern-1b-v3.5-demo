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

### Using Docker (Recommended)

```bash
# Build and run with Docker Compose
sudo docker compose up --build -d

# Check logs
sudo docker compose logs -f

# Stop service
sudo docker compose down
```

### Manual Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages (lightweight dependencies for proxy mode)
pip install -r requirements.riscv.txt

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## Usage

The service acts as a proxy and forwards all inference requests to the backend GPU server.

```bash
# Test health endpoint
curl http://localhost:8002/health

# Test analysis endpoint
curl -X POST http://localhost:8002/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_description": "A red car on the street",
    "detected_objects": [{"class": "car", "confidence": 0.95}],
    "question": "What color is the car?"
  }'
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/analyze` - Analyze image with context
- `POST /api/chat` - Chat about image

## Network Configuration

Static IP: 192.168.100.20
Port: 8002
Detection Service: http://192.168.100.10:8001
