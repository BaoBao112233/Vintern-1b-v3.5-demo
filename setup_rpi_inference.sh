#!/bin/bash
# Script to setup Raspberry Pi as inference backend

echo "════════════════════════════════════════════════════════════"
echo "  Setup Vintern Model Inference on Raspberry Pi"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if we're on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
fi

echo "📦 Installing PyTorch and Transformers..."
pip3 install --upgrade pip
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip3 install transformers accelerate sentencepiece protobuf

echo ""
echo "📥 Downloading Vintern-1B-v3.5 model..."
python3 << 'PYTHON_SCRIPT'
from transformers import AutoModel, AutoTokenizer
import os

model_id = "5CD-AI/Vintern-1B-v3_5"
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")

print(f"Downloading {model_id}...")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
    print("✓ Tokenizer downloaded")
    
    model = AutoModel.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    print("✓ Model downloaded")
    print(f"✓ Model cached at: {cache_dir}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Note: This may take time depending on network speed")
    
PYTHON_SCRIPT

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ✅ Setup Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Backend will now use local model inference"
echo "  2. Orange Pi VLLM service will proxy to this Raspberry Pi inference"
echo "  3. Test with: ./test_continuous_analysis.sh"
echo ""
echo "⚠️  Note: First inference may be slow (~30s) while model loads into RAM"
echo "   Raspberry Pi 4GB can run Vintern-1B but will use swap if needed"
echo ""
