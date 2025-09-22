#!/bin/bash

# Vintern-1B Model Setup Script
# This script helps set up the local model for inference

set -e

MODEL_DIR="/models"
LLAMA_CPP_DIR="/app/llama.cpp"
HF_MODEL="5CD-AI/Vintern-1B-v3_5"

echo "🚀 Vintern-1B Local Model Setup"
echo "================================"

# Check if model directory exists
if [ ! -d "$MODEL_DIR" ]; then
    echo "❌ Model directory $MODEL_DIR not found"
    echo "Please mount a model directory to /models volume"
    exit 1
fi

echo "📁 Model directory: $MODEL_DIR"
echo "🔧 llama.cpp directory: $LLAMA_CPP_DIR"

# Check for existing model files
EXISTING_MODELS=$(find "$MODEL_DIR" -name "*.gguf" -o -name "*.ggml" -o -name "*.bin" 2>/dev/null || true)

if [ -n "$EXISTING_MODELS" ]; then
    echo "✅ Found existing model files:"
    echo "$EXISTING_MODELS"
    echo ""
    echo "To use these models, make sure they are compatible with llama.cpp"
else
    echo "⚠️  No existing model files found in $MODEL_DIR"
    echo ""
    echo "To set up a model, you have several options:"
    echo ""
    echo "1. Convert from Hugging Face (requires HF_TOKEN):"
    echo "   python3 /app/convert_model.py --token YOUR_HF_TOKEN"
    echo ""
    echo "2. Download pre-converted GGUF model:"
    echo "   # Download manually and place in $MODEL_DIR"
    echo ""
    echo "3. Use with Docker volume:"
    echo "   docker run -v /path/to/your/models:/models vintern-model-runner"
fi

echo ""
echo "🔍 Checking llama.cpp installation..."

if [ -f "$LLAMA_CPP_DIR/main" ]; then
    echo "✅ llama.cpp main executable found"
elif [ -f "$LLAMA_CPP_DIR/llama-server" ]; then
    echo "✅ llama.cpp server executable found"
else
    echo "❌ llama.cpp executables not found in $LLAMA_CPP_DIR"
    echo "Building llama.cpp..."
    
    if [ -d "$LLAMA_CPP_DIR" ]; then
        cd "$LLAMA_CPP_DIR"
        make clean
        make -j$(nproc)
        echo "✅ llama.cpp built successfully"
    else
        echo "❌ llama.cpp source not found"
        exit 1
    fi
fi

echo ""
echo "🏥 Health check..."

# Test if we can run a simple command
if [ -f "$LLAMA_CPP_DIR/main" ] && [ -n "$EXISTING_MODELS" ]; then
    MODEL_FILE=$(echo "$EXISTING_MODELS" | head -n1)
    echo "🧪 Testing model with: $MODEL_FILE"
    
    timeout 30s "$LLAMA_CPP_DIR/main" \
        -m "$MODEL_FILE" \
        -n 1 \
        -p "Hello" \
        --verbose \
        > /tmp/model_test.log 2>&1 || true
    
    if grep -q "Hello" /tmp/model_test.log; then
        echo "✅ Model test successful"
    else
        echo "⚠️  Model test inconclusive - check logs for details"
    fi
fi

echo ""
echo "📋 Setup Summary:"
echo "- Model directory: $MODEL_DIR"
echo "- Available models: $(find "$MODEL_DIR" -name "*.gguf" -o -name "*.ggml" -o -name "*.bin" 2>/dev/null | wc -l)"
echo "- llama.cpp ready: $([ -f "$LLAMA_CPP_DIR/main" ] && echo "Yes" || echo "No")"

echo ""
echo "🎉 Setup complete! Model server is ready to start."
echo "Run: python3 /app/model_server.py"