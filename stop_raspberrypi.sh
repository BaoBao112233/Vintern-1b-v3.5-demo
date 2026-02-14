#!/bin/bash
# Stop script for Raspberry Pi 4 + Coral USB

echo "================================================"
echo "Stopping Raspberry Pi 4 Camera System"
echo "================================================"

echo ""
echo "Stopping services..."
sudo docker-compose -f docker-compose.raspberrypi.yml down

echo ""
echo "✅ Services stopped"
echo ""
echo "To start again: ./start_raspberrypi.sh"
echo ""
