#!/bin/bash
# Simple script to download Vintern model using git clone

echo "🚀 Downloading Vintern-1B-v3.5 model..."

# Check if git-lfs is installed
if ! command -v git-lfs &> /dev/null; then
    echo "⚠️  Git LFS is not installed. Installing git-lfs..."
    
    # Try to install git-lfs
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y git-lfs
    elif command -v yum &> /dev/null; then
        sudo yum install -y git-lfs
    elif command -v brew &> /dev/null; then
        brew install git-lfs
    else
        echo "❌ Unable to install git-lfs automatically. Please install it manually:"
        echo "   Ubuntu/Debian: sudo apt-get install git-lfs"
        echo "   CentOS/RHEL: sudo yum install git-lfs"
        echo "   macOS: brew install git-lfs"
        exit 1
    fi
    
    # Initialize git-lfs
    git lfs install
fi

# Create models directory
mkdir -p models
cd models

# Remove existing model if present
if [ -d "Vintern-1B-v3_5" ]; then
    echo "📁 Removing existing model directory..."
    rm -rf Vintern-1B-v3_5
fi

# Clone the model repository with LFS
echo "📥 Cloning model repository (including LFS files)..."
GIT_LFS_SKIP_SMUDGE=0 git clone https://huggingface.co/5CD-AI/Vintern-1B-v3_5

if [ $? -eq 0 ]; then
    # Check if model files are properly downloaded
    cd Vintern-1B-v3_5
    MODEL_SIZE=$(wc -c < model.safetensors)
    if [ "$MODEL_SIZE" -gt 1000 ]; then
        echo "✅ Model downloaded successfully!"
        echo "📂 Model location: $(pwd)"
        echo "📊 Model size: $(du -h model.safetensors | cut -f1)"
        echo "🔧 You can now run: docker-compose up --build"
    else
        echo "⚠️  Model files may not be fully downloaded (LFS files)."
        echo "📥 Attempting to pull LFS files..."
        git lfs pull
        echo "✅ Model download completed!"
        echo "📂 Model location: $(pwd)"
        echo "📊 Model size: $(du -h model.safetensors | cut -f1)"
    fi
else
    echo "❌ Failed to download model. Please check your internet connection and try again."
    exit 1
fi