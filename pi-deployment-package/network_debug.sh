#!/bin/bash

###############################################################################
# Network Troubleshooting Script
# Chạy script này trên Raspberry Pi để debug connection issues
###############################################################################

PC_IP="${1:-192.168.1.3}"
PC_PORT="${2:-8080}"

echo "========================================"
echo "🔍 Network Troubleshooting"
echo "========================================"
echo ""
echo "Testing connection to: $PC_IP:$PC_PORT"
echo ""

# 1. Ping test
echo "1️⃣  Testing network connectivity (ping)..."
if ping -c 3 -W 2 "$PC_IP" > /dev/null 2>&1; then
    echo "   ✅ Ping OK - Network is reachable"
    LATENCY=$(ping -c 3 "$PC_IP" | tail -1 | awk -F '/' '{print $5}')
    echo "   📊 Average latency: ${LATENCY}ms"
else
    echo "   ❌ Ping FAILED - Network is not reachable"
    echo ""
    echo "   Possible issues:"
    echo "   • Wrong IP address"
    echo "   • PC is offline"
    echo "   • Different subnet/network"
    echo "   • Network cable/WiFi issue"
    echo ""
    exit 1
fi

echo ""

# 2. Port connectivity test
echo "2️⃣  Testing port connectivity (telnet/nc)..."

# Try with timeout
if timeout 5 bash -c "</dev/tcp/$PC_IP/$PC_PORT" 2>/dev/null; then
    echo "   ✅ Port $PC_PORT is OPEN and accepting connections"
else
    echo "   ❌ Port $PC_PORT is NOT accessible"
    echo ""
    echo "   Possible issues:"
    echo "   • Firewall blocking port $PC_PORT on PC"
    echo "   • Server not listening on 0.0.0.0"
    echo "   • Server crashed/not running"
    echo ""
    echo "   On PC, run:"
    echo "   $ sudo ufw allow $PC_PORT/tcp"
    echo "   $ ps aux | grep llama-server"
    echo ""
    exit 1
fi

echo ""

# 3. HTTP health check
echo "3️⃣  Testing HTTP endpoint (curl)..."

RESPONSE=$(curl -s -m 10 "http://$PC_IP:$PC_PORT/health" 2>&1)
CURL_EXIT=$?

if [ $CURL_EXIT -eq 0 ]; then
    if echo "$RESPONSE" | grep -q '"status":"ok"'; then
        echo "   ✅ Health endpoint OK"
        echo "   📦 Response: $RESPONSE"
    else
        echo "   ⚠️  Got response but unexpected format"
        echo "   📦 Response: $RESPONSE"
    fi
else
    echo "   ❌ HTTP request FAILED"
    echo "   Error: $RESPONSE"
    echo ""
    echo "   Possible issues:"
    echo "   • Server returned error"
    echo "   • Timeout (server too slow)"
    echo "   • Wrong endpoint"
    echo ""
    exit 1
fi

echo ""

# 4. Full inference test
echo "4️⃣  Testing inference API..."

# Create a minimal test payload
TEST_PAYLOAD='{
  "messages": [
    {
      "role": "user",
      "content": "Test message"
    }
  ],
  "max_tokens": 10
}'

INFERENCE_RESPONSE=$(curl -s -m 15 \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD" \
    "http://$PC_IP:$PC_PORT/v1/chat/completions" 2>&1)

if echo "$INFERENCE_RESPONSE" | grep -q '"choices"'; then
    echo "   ✅ Inference API working"
    echo "   📦 Got valid response"
else
    echo "   ⚠️  Inference endpoint accessible but may have issues"
    echo "   Response: ${INFERENCE_RESPONSE:0:200}..."
fi

echo ""
echo "========================================"
echo "✅ All Tests Passed!"
echo "========================================"
echo ""
echo "Your Raspberry Pi can connect to PC inference server."
echo ""
echo "If smart_analyze.py still fails, try:"
echo "1. Increase timeout in the script"
echo "2. Check image file exists and is valid"
echo "3. Monitor PC server logs: tail -f /tmp/llama-server-*.log"
echo ""
echo "Quick test command:"
echo "  python3 quick_test.py test-fruits.jpg"
echo ""
