# Deployment Guide - Distributed Setup via Ethernet LAN

Hướng dẫn deploy 2 services trên Raspberry Pi 4 và Orange Pi RV 2 kết nối qua Ethernet LAN.

## Hardware Setup

### Raspberry Pi 4 (Detection Service)
- **Device**: Raspberry Pi 4 (4GB RAM minimum)
- **Accelerator**: Google Coral USB Accelerator
- **Camera**: USB Camera hoặc Pi Camera Module
- **OS**: Raspberry Pi OS 64-bit
- **Network**: Ethernet LAN - Static IP **192.168.100.10**
- **Service Port**: 8001

### Orange Pi RV 2 (VLLM Service)
- **Device**: Orange Pi RV 2 (4GB RAM)
- **OS**: Ubuntu 22.04 ARM64
- **Network**: Ethernet LAN - Static IP **192.168.100.20**
- **Service Port**: 8002

## Network Configuration

### 1. Configure Static IP on Raspberry Pi 4

```bash
# Edit network configuration
sudo nano /etc/dhcpcd.conf

# Add at the end:
interface eth0
static ip_address=192.168.100.10/24
static routers=192.168.100.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Restart networking
sudo systemctl restart dhcpcd
```

### 2. Configure Static IP on Orange Pi RV 2

```bash
# Edit netplan configuration
sudo nano /etc/netplan/01-network-manager-all.yaml

# Add/modify:
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.100.20/24
      gateway4: 192.168.100.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]

# Apply configuration
sudo netplan apply
```

### 3. Verify Connectivity

```bash
# From Raspberry Pi - ping Orange Pi
ping 192.168.100.20

# From Orange Pi - ping Raspberry Pi
ping 192.168.100.10

# Test port connectivity
nc -zv 192.168.100.20 8002  # From Pi
nc -zv 192.168.100.10 8001  # From Orange Pi
```

### 4. Configure Firewall (Optional)

```bash
# On both devices
sudo ufw allow from 192.168.100.0/24
sudo ufw allow 8001/tcp  # On Raspberry Pi
sudo ufw allow 8002/tcp  # On Orange Pi
sudo ufw enable
```

## Deployment Steps

### Step 1: Setup Detection Service (Raspberry Pi 4)

```bash
# SSH into Raspberry Pi
ssh pi@192.168.100.10

# Clone repository
git clone <your-repo-url>
cd Vintern-1b-v3.5-demo/detection-service

# Install Coral TPU dependencies
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y libedgetpu1-std python3-pycoral

# Download TFLite model
mkdir -p models
cd models
wget https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
wget https://github.com/google-coral/test_data/raw/master/coco_labels.txt
cd ..

# Copy environment file
cp .env.template .env

# Build and run with Docker
sudo docker-compose up --build -d

# Check logs
sudo docker-compose logs -f
```

**Verify Coral USB is detected:**
```bash
lsusb | grep "Google"
# Should show: Bus XXX Device XXX: ID 1a6e:089a Google Inc.
```

**Test Detection Service:**
```bash
curl http://192.168.100.10:8001/health
```

### Step 2: Setup VLLM Service (Orange Pi RV 2)

```bash
# SSH into Orange Pi
ssh orangepi@192.168.100.20

# Clone repository
git clone <your-repo-url>
cd Vintern-1b-v3.5-demo/vllm-service

# Copy environment file
cp .env.template .env

# Download model (this will take ~5-10 minutes)
python3 scripts/download_model.py

# Build and run with Docker
sudo docker-compose up --build -d

# Monitor logs and memory usage
sudo docker-compose logs -f
```

**Monitor Memory Usage:**
```bash
# In another terminal
watch -n 2 free -h
htop  # or top
```

**Test VLLM Service:**
```bash
curl http://192.168.100.20:8002/health
```

### Step 3: Test End-to-End Integration

**Test Detection API:**
```bash
# Upload an image to detection service
curl -X POST http://192.168.100.10:8001/api/detect/upload \
  -F "file=@test_image.jpg" \
  -F "draw_boxes=true"
```

**Test VLLM Analysis:**
```bash
# Send detection results to VLLM for analysis
curl -X POST http://192.168.100.20:8002/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_description": "A photo from camera",
    "detected_objects": [
      {"name": "person", "confidence": 0.95},
      {"name": "car", "confidence": 0.87}
    ],
    "question": "Mô tả những gì bạn thấy trong ảnh"
  }'
```

## Troubleshooting

### Coral USB Not Detected

```bash
# Check USB devices
lsusb

# Check kernel logs
dmesg | grep -i tpu

# Reinstall Coral runtime
sudo apt-get remove --purge libedgetpu1-std python3-pycoral
sudo apt-get install libedgetpu1-std python3-pycoral

# Replug Coral USB
```

### VLLM Out of Memory

```bash
# Edit docker-compose.yml to use 4-bit quantization
USE_QUANTIZATION=true
QUANTIZATION_BITS=4  # Change from 8 to 4

# Rebuild
sudo docker-compose down
sudo docker-compose up --build -d
```

### Network Connection Issues

```bash
# Check routes
ip route show

# Check if services are listening
sudo netstat -tulpn | grep 8001  # On Raspberry Pi
sudo netstat -tulpn | grep 8002  # On Orange Pi

# Check firewall
sudo ufw status
```

### Docker Build Fails

```bash
# Clean Docker cache
sudo docker system prune -a

# Build without cache
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

## Service Management

### Start Services
```bash
# On each device
cd <service-directory>
sudo docker-compose up -d
```

### Stop Services
```bash
sudo docker-compose down
```

### View Logs
```bash
sudo docker-compose logs -f
```

### Restart Services
```bash
sudo docker-compose restart
```

### Update Services
```bash
git pull
sudo docker-compose down
sudo docker-compose up --build -d
```

## Performance Monitoring

### Check Detection Service Performance
```bash
# On Raspberry Pi
curl http://192.168.100.10:8001/api/status

# Monitor CPU/Memory
htop
```

### Check VLLM Service Performance
```bash
# On Orange Pi
curl http://192.168.100.20:8002/api/model-info

# Monitor memory
watch -n 1 free -m

# Check temperature
cat /sys/class/thermal/thermal_zone0/temp
```

## Maintenance

### Update Models

**Detection Service:**
```bash
cd detection-service/models
# Download new model and update MODEL_PATH in .env
```

**VLLM Service:**
```bash
cd vllm-service
python3 scripts/download_model.py
sudo docker-compose restart
```

### Backup Configuration
```bash
# Backup .env files and docker-compose.yml
tar -czf backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

## Security Recommendations

1. **Change Default Passwords**: Update default SSH passwords on both devices
2. **Firewall**: Enable and configure UFW to only allow necessary ports
3. **Updates**: Regularly update system packages
4. **SSH Keys**: Use SSH keys instead of passwords for remote access
5. **Network Isolation**: Consider using VLAN for service isolation

## Support

For issues or questions:
- Check logs: `sudo docker-compose logs`
- Verify network: `ping <service-ip>`
- GitHub Issues: Create issue with logs and configuration
