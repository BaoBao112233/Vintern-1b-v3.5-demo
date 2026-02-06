# Multi-stage build for Detection Service
FROM python:3.9-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add Coral repository
RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" > /etc/apt/sources.list.d/coral-edgetpu.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

# Install Coral Edge TPU runtime
RUN apt-get update && apt-get install -y \
    libedgetpu1-std \
    python3-pycoral \
    && rm -rf /var/lib/apt/lists/*

# Final stage
FROM python:3.9-slim

WORKDIR /app

# Copy Coral libraries from builder
COPY --from=builder /usr/lib/python3/dist-packages/pycoral /usr/local/lib/python3.9/site-packages/pycoral
COPY --from=builder /usr/lib/python3/dist-packages/tflite_runtime /usr/local/lib/python3.9/site-packages/tflite_runtime
COPY --from=builder /usr/lib/aarch64-linux-gnu/libedgetpu* /usr/lib/aarch64-linux-gnu/ 2>/dev/null || true
COPY --from=builder /usr/lib/x86_64-linux-gnu/libedgetpu* /usr/lib/x86_64-linux-gnu/ 2>/dev/null || true

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create models directory
RUN mkdir -p /models

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
