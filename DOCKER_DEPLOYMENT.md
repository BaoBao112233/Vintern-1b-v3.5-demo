# Multi-Camera Detection System - Docker Deployment

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and start all services
chmod +x docker-build.sh
./docker-build.sh
```

### Access

- **Main UI**: http://192.168.1.17:8000/ui
- **API Documentation**: http://192.168.1.17:8000/docs
- **Detection Service API**: http://192.168.1.17:8001/docs
- **Health Check**: http://192.168.1.17:8000/api/health

### Services

1. **Backend** (Port 8000)
   - Serves UI at `/ui`
   - API endpoints at `/api/*`
   - Camera management
   - WebSocket support

2. **Detection Service** (Port 8001)
   - Object detection with Coral TPU
   - Mock mode when Coral USB not available
   - SSD MobileNet V2 model

### Configuration

Edit `.env.docker` to configure:
- Camera IPs and credentials
- Mock mode (for testing without Coral)
- Log levels

### Docker Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f detection-service

# Check service status
docker-compose ps

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Remove all containers and volumes
docker-compose down -v
```

### Coral USB Support

To use Coral USB Accelerator:

1. Connect Coral USB to Raspberry Pi
2. Edit `.env.docker`: Set `MOCK_MODE=false`
3. Restart: `docker-compose restart`

The Coral USB is mounted into the container via `/dev/bus/usb` with privileged mode.

### Troubleshooting

**Services not starting:**
```bash
docker-compose logs
```

**Camera connection issues:**
```bash
# Check camera status
curl http://localhost:8000/api/cameras/status

# Test network
ping 192.168.1.11
```

**Coral TPU not detected:**
```bash
# Check USB devices
lsusb | grep "Global Unichip"

# Use mock mode
echo "MOCK_MODE=true" > .env.docker
docker-compose restart
```

**Port conflicts:**
```bash
# Check what's using ports
sudo lsof -i :8000
sudo lsof -i :8001

# Kill existing processes
sudo pkill -f uvicorn
```

### Development

Mount code for live development:

```yaml
# Add to docker-compose.yml
services:
  backend:
    volumes:
      - ./backend/app:/app/app:ro
```

### Production Notes

1. **Change CORS origins** in `backend/app/main.py`
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** with reverse proxy (nginx/traefik)
4. **Set resource limits** in docker-compose.yml
5. **Use docker secrets** for passwords

### System Requirements

- Docker 20.10+
- Docker Compose 1.29+
- 4GB+ RAM (Raspberry Pi 4)
- 16GB+ storage

### Performance

- **Detection**: 30-40 FPS with Coral TPU
- **Latency**: ~20-30ms per frame
- **Memory**: ~1-2GB RAM
- **CPU**: ~30-50% (video decoding)
