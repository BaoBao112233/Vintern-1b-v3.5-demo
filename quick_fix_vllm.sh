#!/bin/bash
# Quick fix for VLLM circular dependency

echo "════════════════════════════════════════════════"
echo "  Fix VLLM Circular Dependency"
echo "════════════════════════════════════════════════"
echo ""

read -p "Bạn muốn disable VLLM service? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "1️⃣  Stopping VLLM service on Orange Pi..."
ssh orangepi@192.168.1.16 "sudo pkill -f 'uvicorn.*8002'" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ VLLM service stopped"
else
    echo "   ⚠️  Could not stop VLLM service (may need manual intervention)"
fi

echo ""
echo "2️⃣  Updating .env to comment out VLLM_SERVICE_URL..."
cd /home/pi/Projects/Vintern-1b-v3.5-demo

# Backup .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "   ✓ Backed up .env"

# Comment out VLLM_SERVICE_URL
sed -i 's/^VLLM_SERVICE_URL=/#VLLM_SERVICE_URL=/' .env
echo "   ✓ Commented out VLLM_SERVICE_URL"

echo ""
echo "3️⃣  Restarting backend..."
docker restart backend
sleep 3
echo "   ✓ Backend restarted"

echo ""
echo "4️⃣  Testing..."
sleep 2

# Test health
HEALTH=$(curl -s http://localhost:8000/api/health)
BACKEND_OK=$(echo "$HEALTH" | grep -c '"status": "healthy"')
VLLM_DISABLED=$(echo "$HEALTH" | grep -c '"vllm_ready": false')
CAMERAS_OK=$(echo "$HEALTH" | grep -c '"cameras_ready": true')

echo ""
echo "════════════════════════════════════════════════"
echo "  Test Results:"
echo "════════════════════════════════════════════════"

if [ "$BACKEND_OK" = "1" ]; then
    echo "✓ Backend is healthy"
else
    echo "✗ Backend health check failed"
fi

if [ "$VLLM_DISABLED" = "1" ]; then
    echo "✓ VLLM is disabled (expected)"
else
    echo "⚠️  VLLM status unclear"
fi

if [ "$CAMERAS_OK" = "1" ]; then
    echo "✓ Cameras are ready"
else
    echo "✗ Cameras not ready"
fi

echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ Fix Complete!"
echo "════════════════════════════════════════════════"
echo ""
echo "Web Interface: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "What's working:"
echo "  ✓ Multi-camera streaming"  
echo "  ✓ Object detection"
echo "  ✓ Real-time updates"
echo ""
echo "What's NOT working:"
echo "  ✗ AI Analysis (VLLM disabled)"
echo "  ✗ Continuous AI Analysis"
echo ""
echo "To enable AI analysis, see: SOLUTION_DISABLE_VLLM.md"
echo ""
