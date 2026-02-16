#!/bin/bash
###############################################################################
# Setup Script - Run này trên Raspberry Pi
###############################################################################

set -e

echo "======================================"
echo "🍓 Raspberry Pi Vision AI Setup"
echo "======================================"
echo ""

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found! Installing..."
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt --user

echo ""
echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Update PC IP in vision_service_example.py (line 43):"
echo "   pc_host='YOUR_PC_IP'"
echo ""
echo "2. Test connection:"
echo "   cd client"
echo "   python3 test_connection.py YOUR_PC_IP"
echo ""
echo "3. Test analysis:"
echo "   python3 smart_analyze.py test_image.jpg"
echo ""
echo "4. Integrate into your backend:"
echo "   See PI_INTEGRATION_GUIDE.md"
echo ""
