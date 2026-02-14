#!/bin/bash
# Monitor build progress

echo "Monitoring Docker build progress..."
echo "This may take 5-10 minutes on Raspberry Pi 4"
echo ""
echo "Press Ctrl+C to stop monitoring (build will continue in background)"
echo ""

sudo docker-compose -f docker-compose.raspberrypi.yml logs -f --tail=50
