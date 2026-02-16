#!/bin/bash
###############################################################################
# Network Setup Verification Script
# Chạy script này để verify toàn bộ network configuration
###############################################################################

set -e

echo "=========================================="
echo "  Network Setup Verification"
echo "=========================================="
echo ""
echo "Usage: $0 [PC_IP]"
echo "Example: $0 192.168.1.100"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - THAY ĐỔI CHỖ NÀY!
PC_IP="${1:-192.168.1.100}"  # <-- Argument or default, usage: ./verify_network.sh <PC_IP>
PC_PORT="8080"
PI_IP=""                      # Will auto-detect

# Detect current IP
echo -e "${YELLOW}📍 Detecting current device IP...${NC}"
if command -v hostname &> /dev/null; then
    CURRENT_IP=$(hostname -I | awk '{print $1}')
    echo -e "   Current IP: ${GREEN}$CURRENT_IP${NC}"
    PI_IP=$CURRENT_IP
else
    echo -e "   ${RED}Cannot detect IP${NC}"
fi

echo ""
echo "=========================================="
echo "  Configuration Check"
echo "=========================================="
echo "PC IP:       $PC_IP"
echo "PC Port:     $PC_PORT"
echo "Pi IP:       $PI_IP"
echo ""

# Function to check status
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

TOTAL_TESTS=0
PASSED_TESTS=0

# Test 1: Check if running on Pi or PC
echo "=========================================="
echo "  Test 1: Device Detection"
echo "=========================================="
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$CURRENT_IP" == "$PC_IP" ]; then
    echo -e "${YELLOW}⚠️  Running on PC${NC}"
    echo "   This script is meant to run on Raspberry Pi"
    echo "   But we'll check PC configuration..."
    IS_PC=true
else
    echo -e "${GREEN}✅ Running on Raspberry Pi${NC}"
    IS_PC=false
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
echo ""

# Test 2: Ping PC
echo "=========================================="
echo "  Test 2: Network Connectivity (Ping)"
echo "=========================================="
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$IS_PC" = true ]; then
    echo "Skipping (already on PC)"
else
    echo -n "Pinging $PC_IP... "
    if ping -c 3 -W 2 "$PC_IP" &> /dev/null; then
        check_status 0
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        check_status 1
        echo -e "${RED}   → Check network cable/WiFi${NC}"
        echo -e "${RED}   → Check PC is on same network${NC}"
    fi
fi
echo ""

# Test 3: Port check
echo "=========================================="
echo "  Test 3: Port Connectivity"
echo "=========================================="
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$IS_PC" = true ]; then
    echo -n "Checking if port $PC_PORT is listening... "
    if netstat -tlnp 2>/dev/null | grep -q ":$PC_PORT"; then
        check_status 0
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        check_status 1
        echo -e "${RED}   → Start llama-server first${NC}"
    fi
else
    echo -n "Checking port $PC_PORT on $PC_IP... "
    if nc -zv -w 3 "$PC_IP" "$PC_PORT" &> /dev/null; then
        check_status 0
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        check_status 1
        echo -e "${RED}   → Check if llama-server is running on PC${NC}"
        echo -e "${RED}   → Check firewall on PC${NC}"
    fi
fi
echo ""

# Test 4: HTTP health check
echo "=========================================="
echo "  Test 4: HTTP Health Check"
echo "=========================================="
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo -n "Checking http://$PC_IP:$PC_PORT/health... "
if curl -s -f -m 5 "http://$PC_IP:$PC_PORT/health" &> /dev/null; then
    check_status 0
    PASSED_TESTS=$((PASSED_TESTS + 1))
    
    RESPONSE=$(curl -s "http://$PC_IP:$PC_PORT/health")
    echo "   Response: $RESPONSE"
else
    check_status 1
    echo -e "${RED}   → Server not responding${NC}"
fi
echo ""

# Test 5: Check firewall (if on PC)
if [ "$IS_PC" = true ]; then
    echo "=========================================="
    echo "  Test 5: Firewall Check (PC)"
    echo "=========================================="
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if command -v ufw &> /dev/null; then
        UFW_STATUS=$(sudo ufw status 2>/dev/null | grep "$PC_PORT")
        if [ -n "$UFW_STATUS" ]; then
            echo -e "${GREEN}✅ UFW rule found for port $PC_PORT${NC}"
            echo "   $UFW_STATUS"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${YELLOW}⚠️  No UFW rule found for port $PC_PORT${NC}"
            echo -e "${YELLOW}   Run: sudo ufw allow $PC_PORT/tcp${NC}"
        fi
    else
        echo "UFW not installed"
    fi
    echo ""
fi

# Test 6: Check Python dependencies
echo "=========================================="
echo "  Test 6: Python Dependencies"
echo "=========================================="
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo -n "Checking Python packages... "
if python3 -c "import requests, PIL" 2>/dev/null; then
    check_status 0
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    check_status 1
    echo -e "${RED}   → Install: pip install requests pillow${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo "Tests passed: $PASSED_TESTS / $TOTAL_TESTS"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✅ All tests PASSED!${NC}"
    echo -e "${GREEN}✅ Network is configured correctly${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test inference:"
    echo "     python3 client/pc_inference_client.py image.jpg"
    echo ""
    echo "  2. Start backend service:"
    echo "     python3 client/backend_integration_example.py"
    echo ""
else
    echo -e "${RED}❌ Some tests FAILED${NC}"
    echo -e "${RED}❌ Fix issues above before proceeding${NC}"
    echo ""
    
    if [ "$IS_PC" = false ]; then
        echo "Troubleshooting on PC:"
        echo "  1. Check server is running:"
        echo "     ps aux | grep llama-server"
        echo ""
        echo "  2. Check port is listening:"
        echo "     netstat -tlnp | grep $PC_PORT"
        echo ""
        echo "  3. Open firewall:"
        echo "     sudo ufw allow $PC_PORT/tcp"
        echo ""
        echo "  4. Test from PC itself:"
        echo "     curl http://localhost:$PC_PORT/health"
        echo ""
    fi
fi

echo "=========================================="
