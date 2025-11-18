# Multi-stage build for DocStrange application
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For pdf2image
    poppler-utils \
    # For image processing
    libgl1 \
    libglib2.0-0 \
    # For pandoc
    pandoc \
    # Build tools for some Python packages
    gcc \
    g++ \
    make \
    # For downloading files
    wget \
    curl \
    # For EasyOCR and image processing
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
COPY README.md .
COPY LICENSE .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e .

# Copy the entire application
COPY docstrange/ ./docstrange/
COPY examples/ ./examples/
COPY scripts/ ./scripts/
COPY mcp_server_module/ ./mcp_server_module/
COPY docker_entrypoint.py .

# Create directories for models and cache
RUN mkdir -p /root/.cache/huggingface \
    /root/.cache/torch \
    /root/.docstrange \
    /app/uploads \
    /app/outputs

# Expose port for web application
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python", "docker_entrypoint.py"]
