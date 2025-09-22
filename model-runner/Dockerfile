# Model Runner Dockerfile for Local Inference
# This container runs GGML/llama.cpp for local model inference

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    python3 \
    python3-pip \
    python3-dev \
    libopenblas-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone and build llama.cpp
RUN git clone https://github.com/ggml-org/llama.cpp.git && \
    cd llama.cpp && \
    git checkout master && \
    make clean && \
    make -j$(nproc) && \
    chmod +x main && \
    chmod +x llama-server

# Install Python dependencies for model conversion and utilities
RUN pip3 install --no-cache-dir \
    numpy \
    torch \
    transformers \
    huggingface_hub \
    pillow \
    requests \
    tqdm

# Copy model runner scripts
COPY scripts/ ./scripts/
COPY model_server.py ./
COPY convert_model.py ./
COPY requirements.txt ./

# Install Python requirements
RUN pip3 install --no-cache-dir -r requirements.txt

# Create model directory
RUN mkdir -p /models /app/logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash modelrunner && \
    chown -R modelrunner:modelrunner /app /models
USER modelrunner

# Set environment variables
ENV MODEL_PATH=/models
ENV LLAMA_CPP_PATH=/app/llama.cpp
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for model server
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command - run model server
CMD ["python3", "model_server.py"]