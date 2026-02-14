#!/bin/bash
# Download Vintern-1B model từ HuggingFace cho Raspberry Pi Inference

set -e  # Exit on error

echo "=================================================="
echo "📥 DOWNLOAD VINTERN-1B MODEL"
echo "=================================================="
echo ""

# Check if git-lfs is installed
if ! command -v git-lfs &> /dev/null; then
    echo "⚠️  Git LFS chưa được cài đặt!"
    echo "Đang cài đặt git-lfs..."
    sudo apt-get update
    sudo apt-get install -y git-lfs
    git lfs install
fi

# Model paths
MODEL_DIR="/home/pi/Projects/Vintern-1b-v3.5-demo/backend/models"
MODEL_PATH="$MODEL_DIR/Vintern-1B-v3_5"

# Create models directory if not exists
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

echo "📂 Model directory: $MODEL_PATH"
echo ""

# Clone model from HuggingFace
if [ -d "$MODEL_PATH" ]; then
    echo "⚠️  Model đã tồn tại tại $MODEL_PATH"
    read -p "Bạn có muốn tải lại không? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Xóa model cũ..."
        rm -rf "$MODEL_PATH"
    else
        echo "✅ Sử dụng model hiện có"
        exit 0
    fi
fi

echo "📥 Đang clone model từ HuggingFace..."
echo "Model: 5CD-AI/Vintern-1B-v3_5"
echo ""

# Check if logged in to HuggingFace
if ! huggingface-cli whoami &> /dev/null; then
    echo "⚠️  Bạn chưa đăng nhập HuggingFace!"
    echo "Vui lòng đăng nhập:"
    huggingface-cli login
fi

# Clone the model
git clone https://huggingface.co/5CD-AI/Vintern-1B-v3_5 "$MODEL_PATH"

echo ""
echo "✅ Download model hoàn tất!"
echo ""
echo "📊 Model size:"
du -sh "$MODEL_PATH"
echo ""
echo "📂 Model location: $MODEL_PATH"
echo ""
echo "=================================================="
echo "✅ HOÀN TẤT!"
echo "=================================================="
echo ""
echo "Tiếp theo:"
echo "1. Chạy: ./setup_local_inference.sh"
echo "2. Hoặc update .env và restart backend"
