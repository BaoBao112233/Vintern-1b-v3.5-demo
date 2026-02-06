#!/bin/bash
# Build and run with Docker Compose

set -e

echo "🐳 Building Multi-Camera Detection System with Docker..."

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

# Create necessary directories
mkdir -p logs
mkdir -p models

# Copy simple frontend to backend/static if frontend build doesn't exist
if [ ! -d "frontend/build" ]; then
    echo "📦 Frontend build not found, using simple UI..."
    mkdir -p backend/static
    cp frontend-simple/index.html backend/static/
    echo "✅ Simple UI copied to backend/static"
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access points:"
echo "   - Main UI: http://192.168.1.17:8000/ui"
echo "   - API Docs: http://192.168.1.17:8000/docs"
echo "   - Detection API: http://192.168.1.17:8001/docs"
echo ""
echo "📊 Check status:"
echo "   docker-compose ps"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
