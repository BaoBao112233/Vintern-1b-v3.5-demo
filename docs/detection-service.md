# Detection Service for Raspberry Pi 4 + Coral USB

Object detection service sử dụng Google Coral USB Accelerator.

## Features
- TensorFlow Lite inference on Coral TPU
- Real-time object detection API
- WebSocket support for streaming
- Camera input handling
- ARM-optimized

## Requirements
- Raspberry Pi 4 (4GB+ RAM)
- Google Coral USB Accelerator
- Raspberry Pi OS 64-bit
- Python 3.9+

## Installation

```bash
# Install Coral dependencies
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y libedgetpu1-std python3-pycoral

# Install Python packages
pip install -r requirements.txt

# Download model
cd models
wget https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
wget https://github.com/google-coral/test_data/raw/master/coco_labels.txt
```

## Usage

```bash
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Or with Docker
docker build -f Dockerfile.arm -t detection-service .
docker run -p 8001:8001 --device /dev/bus/usb:/dev/bus/usb --privileged detection-service
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/detect` - Detect objects in image
- `WS /ws/stream` - WebSocket for real-time detection

## Network Configuration

Static IP: 192.168.100.10
Port: 8001
