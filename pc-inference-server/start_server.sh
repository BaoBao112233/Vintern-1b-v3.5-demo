#!/bin/bash

###############################################################################
#  PC Inference Server - Vintern 1B with llama.cpp
#  
#  Chạy model inference server trên PC cho Raspberry Pi gửi request qua LAN
###############################################################################

set -e

# Paths
LLAMA_SERVER="/home/baobao/Projects/llama.cpp-vintern/build/bin/llama-server"
MODEL_DIR="/home/baobao/Projects/Vintern-1b-v3.5-demo/models/gguf"
MODEL="Vintern-1B-v3_5-Q8_0.gguf"
MMPROJ="mmproj-Vintern-1B-v3_5-Q8_0.gguf"

# Server config
HOST="0.0.0.0"  # Listen on all interfaces để Pi có thể connect
PORT="8080"
THREADS="4"      # i3-10105F có 4 cores
CTX_SIZE="4096"  # Context size - increased for longer conversations
BATCH_SIZE="512"

# Log file
LOG_DIR="/home/baobao/Projects/Vintern-1b-v3.5-demo/pc-inference-server/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/server_$(date +%Y%m%d_%H%M%S).log"

echo "===========================================" | tee -a "$LOG_FILE"
echo " PC Inference Server Startup" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"
echo "Time: $(date)" | tee -a "$LOG_FILE"
echo "Model: $MODEL" | tee -a "$LOG_FILE"
echo "MMProj: $MMPROJ" | tee -a "$LOG_FILE"
echo "Host: $HOST:$PORT" | tee -a "$LOG_FILE"
echo "Threads: $THREADS" | tee -a "$LOG_FILE"
echo "Context: $CTX_SIZE" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"

# Check if llama-server exists
if [ ! -f "$LLAMA_SERVER" ]; then
    echo "ERROR: llama-server not found at $LLAMA_SERVER" | tee -a "$LOG_FILE"
    echo "Please build llama.cpp first" | tee -a "$LOG_FILE"
    exit 1
fi

# Check if model exists
if [ ! -f "$MODEL_DIR/$MODEL" ]; then
    echo "ERROR: Model not found at $MODEL_DIR/$MODEL" | tee -a "$LOG_FILE"
    exit 1
fi

if [ ! -f "$MODEL_DIR/$MMPROJ" ]; then
    echo "ERROR: MMProj not found at $MODEL_DIR/$MMPROJ" | tee -a "$LOG_FILE"
    exit 1
fi

# Check GPU status
echo "" | tee -a "$LOG_FILE"
echo "GPU Status:" | tee -a "$LOG_FILE"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>&1 | tee -a "$LOG_FILE" || echo "No GPU detected or nvidia-smi not available" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Start server
cd "$MODEL_DIR"

echo "Starting llama-server..." | tee -a "$LOG_FILE"
echo "Command: $LLAMA_SERVER -m $MODEL --mmproj $MMPROJ ..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run server with CPU for now (add -ngl 99 for GPU support if rebuild with CUDA)
"$LLAMA_SERVER" \
    -m "$MODEL" \
    --mmproj "$MMPROJ" \
    --chat-template vicuna \
    --host "$HOST" \
    --port "$PORT" \
    -t "$THREADS" \
    -c "$CTX_SIZE" \
    -b "$BATCH_SIZE" \
    --log-disable \
    2>&1 | tee -a "$LOG_FILE"

# Note: Để enable GPU, rebuild llama.cpp với CUDA và thêm flag: -ngl 99
