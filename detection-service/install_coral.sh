#!/bin/bash
# Install Coral Edge TPU Runtime and dependencies

echo "📦 Installing Coral Edge TPU Runtime for Raspberry Pi..."

# Add Coral repository
echo "Adding Coral repository..."
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list

# Add Google Cloud public key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install Edge TPU runtime (standard version - lower power consumption)
echo "Installing Edge TPU runtime..."
sudo apt-get install -y libedgetpu1-std

# Note: Use libedgetpu1-max for maximum performance but higher power consumption
# sudo apt-get install -y libedgetpu1-max

# Install Python PyCoral library
echo "Installing PyCoral..."
sudo apt-get install -y python3-pycoral

# Install additional dependencies
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-numpy \
    python3-opencv \
    libatlas-base-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff5

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Check Coral USB
echo ""
echo "Checking for Coral USB Accelerator..."
if lsusb | grep -q "Global Unichip"; then
    echo "✅ Coral USB Accelerator detected!"
    lsusb | grep "Global Unichip"
else
    echo "⚠️  Coral USB Accelerator NOT detected"
    echo "   Please connect your Coral USB Accelerator and run this script again"
    echo ""
    echo "   If already connected, try:"
    echo "   1. Unplug and replug the Coral USB"
    echo "   2. Try a different USB port (preferably USB 3.0)"
    echo "   3. Reboot the Raspberry Pi"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "To test the installation, run:"
echo "  python3 -c 'from pycoral.utils import edgetpu; print(edgetpu.list_edge_tpus())'"
