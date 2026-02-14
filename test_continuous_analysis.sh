#!/bin/bash
# Test script for continuous AI analysis feature

echo "=========================================="
echo "Testing Continuous AI Analysis Feature"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check backend health
echo "1. Checking backend health..."
HEALTH=$(curl -s http://localhost:8000/api/health)
echo "$HEALTH" | python3 -m json.tool > /tmp/health.json

if grep -q '"status": "healthy"' /tmp/health.json; then
    echo -e "${GREEN}✓${NC} Backend is healthy"
else
    echo -e "${RED}✗${NC} Backend health check failed"
fi

# Check VLLM status
if grep -q '"vllm_ready": true' /tmp/health.json; then
    echo -e "${GREEN}✓${NC} VLLM service is ready"
else
    echo -e "${YELLOW}⚠${NC} VLLM service is NOT ready"
    echo "   You need to fix VLLM service on Orange Pi"
    echo "   See FIX_VLLM_SERVICE.md for instructions"
fi

# Check cameras
if grep -q '"cameras_ready": true' /tmp/health.json; then
    echo -e "${GREEN}✓${NC} Cameras are ready"
    CAM_COUNT=$(grep -o '"cam[0-9]"' /tmp/health.json | wc -l)
    echo "   Found $CAM_COUNT cameras"
else
    echo -e "${RED}✗${NC} Cameras not ready"
fi

echo ""

# Test 2: Check if HTML has continuous analysis feature
echo "2. Checking web interface features..."
HTML=$(curl -s http://localhost:8000/)

if echo "$HTML" | grep -q "autoContinuousAnalysis"; then
    echo -e "${GREEN}✓${NC} Continuous Analysis UI is present"
else
    echo -e "${RED}✗${NC} Continuous Analysis UI not found"
    echo "   Try: Ctrl+Shift+R to hard refresh browser"
fi

if echo "$HTML" | grep -q "Analyze with AI"; then
    echo -e "${GREEN}✓${NC} Manual AI analysis buttons present"
else
    echo -e "${YELLOW}⚠${NC} Manual analysis buttons not found"
fi

echo ""

# Test 3: Test camera frames API
echo "3. Testing camera frames API..."
FRAMES=$(curl -s "http://localhost:8000/api/cameras/all/frames?detect=false")

CAM1_HAS_IMAGE=$(echo "$FRAMES" | python3 -c "import sys, json; data=json.load(sys.stdin); print('image_base64' in data.get('cameras',{}).get('cam1',{}))" 2>/dev/null)
CAM2_HAS_IMAGE=$(echo "$FRAMES" | python3 -c "import sys, json; data=json.load(sys.stdin); print('image_base64' in data.get('cameras',{}).get('cam2',{}))" 2>/dev/null)

if [ "$CAM1_HAS_IMAGE" = "True" ]; then
    echo -e "${GREEN}✓${NC} Camera 1 is streaming"
else
    echo -e "${RED}✗${NC} Camera 1 not streaming"
fi

if [ "$CAM2_HAS_IMAGE" = "True" ]; then
    echo -e "${GREEN}✓${NC} Camera 2 is streaming"
else
    echo -e "${RED}✗${NC} Camera 2 not streaming"
fi

echo ""

# Test 4: Test VLLM API (if available)
echo "4. Testing VLLM API..."
VLLM_TEST=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Test","include_objects":false}' 2>&1)

if echo "$VLLM_TEST" | grep -q "Backend service unavailable"; then
    echo -e "${YELLOW}⚠${NC} VLLM is in proxy mode (NEEDS FIX)"
    echo "   Error: Circular dependency detected"
    echo "   Action: Follow FIX_VLLM_SERVICE.md"
elif echo "$VLLM_TEST" | grep -q "VLLM service"; then
    echo -e "${YELLOW}⚠${NC} VLLM service not available"
    echo "   The continuous analysis will not work until VLLM is fixed"
else
    echo -e "${GREEN}✓${NC} VLLM API responding"
    echo "   Response: $(echo "$VLLM_TEST" | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','')[:50])" 2>/dev/null)..."
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Web Interface: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Features added:"
echo "  ✓ Continuous AI Analysis checkbox"
echo "  ✓ Analysis interval selector (5s/10s/15s/30s)"
echo "  ✓ AI Analysis statistics display"
echo "  ✓ Background analysis for both cameras"
echo ""
echo "Usage:"
echo "  1. Open web interface in browser"
echo "  2. Hard refresh: Ctrl+Shift+R (clear cache)"
echo "  3. Check 'Continuous AI Analysis' checkbox"
echo "  4. Camera frames will be analyzed periodically"
echo ""
echo "IMPORTANT:"
if grep -q '"vllm_ready": true' /tmp/health.json; then
    echo -e "  ${GREEN}VLLM is ready!${NC} Continuous analysis will work."
else
    echo -e "  ${YELLOW}VLLM needs to be fixed!${NC}"
    echo "  Follow instructions in: FIX_VLLM_SERVICE.md"
    echo "  SSH: ssh orangepi@192.168.1.16"
fi

echo ""
