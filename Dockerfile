# RunPod Serverless Worker Dockerfile for Document Extraction
# Optimized for GPU inference with vLLM

# Use official RunPod PyTorch base image
# Available images: https://github.com/runpod/containers
FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY docext/ ./docext/
COPY worker.py .

# Create directory for temporary files
RUN mkdir -p /tmp/docext_temp

# Set environment variables with defaults
ENV MODEL_NAME="Qwen/Qwen2.5-VL-3B-Instruct"
ENV VLM_PORT="8000"
ENV MAX_MODEL_LEN="15000"
ENV GPU_MEMORY_UTIL="0.98"
ENV MAX_NUM_IMGS="5"
ENV API_KEY="EMPTY"
ENV TMPDIR="/tmp/docext_temp"

# Expose port for vLLM server (internal only)
EXPOSE 8000

# Health check (optional, useful for debugging)
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/v1/models')" || exit 1

# Start both Gradio app and worker
# Gradio runs in background, worker starts after 60s delay
CMD python -m docext.app.app \
      --model_name hosted_vllm/${MODEL_NAME} \
      --vlm_server_host 0.0.0.0 \
      --vlm_server_port ${VLM_PORT} \
      --ui_port 7860 \
      --max_model_len ${MAX_MODEL_LEN} \
      --gpu_memory_utilization ${GPU_MEMORY_UTIL} \
      --max_num_imgs ${MAX_NUM_IMGS} & \
    sleep 60 && python -u worker.py
