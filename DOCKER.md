# Docker Deployment Guide for DocStrange

This guide explains how to deploy DocStrange using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 1.28+ (usually included with Docker Desktop)
- For GPU mode: NVIDIA GPU, CUDA drivers, and [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)

## Quick Start

### 1. Cloud Mode (CPU, Recommended for Most Users)

Cloud mode uses the Nanonets cloud API for processing. No GPU required!

```bash
# Start the service
docker-compose up -d docstrange-cloud

# View logs
docker-compose logs -f docstrange-cloud

# Access the web interface
open http://localhost:8000
```

The application will be available at `http://localhost:8000`

### 2. GPU Mode (Local Processing)

GPU mode processes everything locally using your NVIDIA GPU. Requires GPU setup.

```bash
# Start with GPU profile
docker-compose --profile gpu up -d docstrange-gpu

# View logs
docker-compose logs -f docstrange-gpu

# Access the web interface
open http://localhost:8001
```

The application will be available at `http://localhost:8001`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` to configure:

```env
# Optional: Add your Nanonets API key for higher rate limits
NANONETS_API_KEY=your_api_key_here

# Flask settings
FLASK_ENV=production
```

### API Key (Optional)

DocStrange offers three authentication options:

1. **Free tier without API key**: Rate-limited cloud processing
2. **Login with `docstrange login`**: 10,000 docs/month (not available in Docker)
3. **API key**: Get from [Nanonets Dashboard](https://app.nanonets.com/#/keys)

Set your API key in `.env`:
```env
NANONETS_API_KEY=your_api_key_here
```

## Docker Compose Services

### Service Overview

- **docstrange-cloud**: CPU-based service using cloud API (port 8000)
- **docstrange-gpu**: GPU-based service for local processing (port 8001)

### Start Specific Service

```bash
# Cloud mode only
docker-compose up -d docstrange-cloud

# GPU mode only (requires --profile gpu)
docker-compose --profile gpu up -d docstrange-gpu

# Both services
docker-compose --profile gpu up -d
```

## Common Commands

### Building Images

```bash
# Build cloud mode image
docker-compose build docstrange-cloud

# Build GPU mode image
docker-compose build docstrange-gpu

# Build all images
docker-compose --profile gpu build
```

### Managing Services

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Accessing the Container

```bash
# Cloud mode
docker exec -it docstrange-cloud bash

# GPU mode
docker exec -it docstrange-gpu bash
```

## Using the API

### Health Check

```bash
curl http://localhost:8000/api/health
```

### Upload and Convert Document

```bash
curl -X POST http://localhost:8000/api/convert \
  -F "file=@/path/to/document.pdf" \
  -F "output_format=markdown" \
  -F "processing_mode=cloud"
```

### Get System Info

```bash
curl http://localhost:8000/api/system-info
```

## Volumes and Persistence

DocStrange uses Docker volumes to persist:

- **Model cache**: Downloaded ML models (can be large, 2-5GB)
- **Configuration**: User settings and API tokens
- **Uploads/Outputs**: Optional mounted directories

### Volume Locations

```yaml
volumes:
  - docstrange-cache:/root/.cache          # Hugging Face models
  - docstrange-data:/root/.docstrange      # App data
  - ./uploads:/app/uploads                 # Input files
  - ./outputs:/app/outputs                 # Output files
```

### Managing Volumes

```bash
# List volumes
docker volume ls

# Remove volumes (clears cache, will re-download models)
docker volume rm docstrange-cache docstrange-data

# Backup volume
docker run --rm -v docstrange-cache:/data -v $(pwd):/backup ubuntu tar czf /backup/docstrange-cache.tar.gz /data
```

## GPU Mode Setup

### Prerequisites

1. **NVIDIA GPU with CUDA support**
2. **NVIDIA drivers installed**
3. **nvidia-docker runtime**

### Install nvidia-docker

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Verify GPU Access

```bash
# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Check GPU in running container
docker exec -it docstrange-gpu nvidia-smi
```

## Troubleshooting

### Port Already in Use

```bash
# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Change 8080 to any available port
```

### Out of Memory

Increase memory limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Increase from 4G
```

### GPU Not Detected

```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Check docker-compose GPU config
docker-compose --profile gpu config
```

### Models Not Downloading

Models download on first use and are cached. First startup may take 5-10 minutes.

```bash
# Watch logs during first start
docker-compose logs -f docstrange-cloud
```

### Permission Issues

```bash
# Fix volume permissions
docker exec -it docstrange-cloud chown -R root:root /root/.cache /root/.docstrange
```

## Production Deployment

### Using Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name docstrange.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for large files
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
    
    # Increase max upload size
    client_max_body_size 100M;
}
```

### Using Traefik

Add labels to `docker-compose.yml`:

```yaml
services:
  docstrange-cloud:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.docstrange.rule=Host(`docstrange.yourdomain.com`)"
      - "traefik.http.services.docstrange.loadbalancer.server.port=8000"
```

### Environment-Specific Configs

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Resource Requirements

### Cloud Mode (CPU)
- **Minimum**: 2 CPU cores, 2GB RAM
- **Recommended**: 4 CPU cores, 4GB RAM
- **Storage**: 2GB for cache

### GPU Mode
- **Minimum**: 1 NVIDIA GPU (4GB VRAM), 4GB RAM
- **Recommended**: 1 NVIDIA GPU (8GB+ VRAM), 8GB RAM
- **Storage**: 5GB for models and cache

## Security Considerations

1. **API Key**: Keep your API key secure, use environment variables
2. **Network**: Use reverse proxy with HTTPS in production
3. **File Upload**: Configure max file size appropriately
4. **Volume Permissions**: Ensure proper file permissions on mounted volumes

## Support

- **Issues**: [GitHub Issues](https://github.com/NanoNets/docstrange/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NanoNets/docstrange/discussions)
- **Documentation**: [README.md](README.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.
