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

# Expose ports
EXPOSE 7860 8000

# Worker handles Gradio startup automatically
CMD ["python", "-u", "worker.py"]
