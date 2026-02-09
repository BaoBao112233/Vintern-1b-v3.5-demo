#!/bin/bash
# Quick test script to verify Docker deployment

set -e

echo "🧪 Testing Multi-Camera Detection System..."
echo ""

# Check if services are running
echo "1️⃣ Checking Docker services..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running"
else
    echo "❌ Services not running. Starting them..."
    docker-compose up -d
    echo "⏳ Waiting for services to start..."
    sleep 10
fi

echo ""
echo "2️⃣ Testing Backend Health..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Backend is healthy"
    echo "$HEALTH_RESPONSE" | jq '.' 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "❌ Backend health check failed"
    echo "$HEALTH_RESPONSE"
fi

echo ""
echo "3️⃣ Testing Detection Service..."
DET_HEALTH=$(curl -s http://localhost:8001/health 2>/dev/null || echo "failed")
if echo "$DET_HEALTH" | grep -q "healthy"; then
    echo "✅ Detection service is healthy"
    echo "$DET_HEALTH" | jq '.' 2>/dev/null || echo "$DET_HEALTH"
else
    echo "❌ Detection service health check failed"
    echo "$DET_HEALTH"
fi

echo ""
echo "4️⃣ Testing UI Access..."
UI_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$UI_RESPONSE" = "200" ]; then
    echo "✅ UI is accessible at http://localhost:8000/"
else
    echo "❌ UI not accessible (HTTP $UI_RESPONSE)"
fi

echo ""
echo "5️⃣ Testing Camera Status..."
CAMERA_STATUS=$(curl -s http://localhost:8000/api/cameras/status)
echo "$CAMERA_STATUS" | jq '.' 2>/dev/null || echo "$CAMERA_STATUS"

echo ""
echo "📊 Summary:"
echo "   - Backend API: http://192.168.1.17:8000/docs"
echo "   - Camera UI: http://192.168.1.17:8000/"
echo "   - Detection API: http://192.168.1.17:8001/docs"
echo ""
echo "📝 View logs with: docker-compose logs -f"
