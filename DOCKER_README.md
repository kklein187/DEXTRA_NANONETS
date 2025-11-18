# 🐳 DocStrange - Docker Deployment

Quick guide to run DocStrange in Docker.

## 🚀 Quick Start

### Option 1: Automated Script (Easiest)

**Required: Get your API key from [https://app.nanonets.com/#/keys](https://app.nanonets.com/#/keys)**

```bash
# Start cloud mode (default)
./docker-start.sh YOUR_API_KEY_HERE

# Or specify the mode explicitly
./docker-start.sh YOUR_API_KEY_HERE cloud
./docker-start.sh YOUR_API_KEY_HERE gpu
./docker-start.sh YOUR_API_KEY_HERE both
```

The script will:
- Validate your API key is provided
- Check your Docker installation
- Create configuration files with your API key
- Start the selected service

### Option 2: Manual Start

**Cloud Mode (Recommended)**
```bash
# Start the service
docker-compose up -d docstrange-cloud

# Access at http://localhost:8000
```

**GPU Mode (Requires NVIDIA GPU)**
```bash
# Start the service
docker-compose --profile gpu up -d docstrange-gpu

# Access at http://localhost:8001
```

## 📋 Prerequisites

- **Docker 20.10+** - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose 1.28+** - Usually included with Docker Desktop
- **For GPU**: NVIDIA GPU + [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)

## ⚙️ Configuration

**API Key Required:** Docker mode requires a Nanonets API key (interactive login doesn't work in containers)

1. **Get your API key:** [Nanonets Dashboard](https://app.nanonets.com/#/keys)
   - Free tier available at [https://nanonets.com](https://nanonets.com)

2. **Option A: Use the start script (recommended)**
   ```bash
   ./docker-start.sh YOUR_API_KEY_HERE
   ```

3. **Option B: Manual configuration**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env and add your API key
   nano .env
   ```
   
   Add this line:
   ```env
   NANONETS_API_KEY=your_api_key_here
   ```

## 🎯 Usage

### Using Makefile (Recommended)

```bash
# See all available commands
make help

# Start cloud mode
make up

# Start GPU mode
make up-gpu

# View logs
make logs

# Stop services
make down
```

### Using Docker Compose

```bash
# Cloud mode
docker-compose up -d docstrange-cloud
docker-compose logs -f docstrange-cloud
docker-compose down

# GPU mode
docker-compose --profile gpu up -d docstrange-gpu
docker-compose logs -f docstrange-gpu
docker-compose --profile gpu down

# Both modes
docker-compose --profile gpu up -d
```

## 🌐 Accessing the Application

- **Cloud Mode:** http://localhost:8000
- **GPU Mode:** http://localhost:8001
- **Health Check:** http://localhost:8000/api/health
- **System Info:** http://localhost:8000/api/system-info

## 📡 API Examples

### Upload and Convert Document

```bash
curl -X POST http://localhost:8000/api/convert \
  -F "file=@document.pdf" \
  -F "output_format=markdown" \
  -F "processing_mode=cloud"
```

### Check Health

```bash
curl http://localhost:8000/api/health
```

## 🔧 Troubleshooting

### Port Already in Use
Edit `docker-compose.yml` and change the port:
```yaml
ports:
  - "8080:8000"  # Changed from 8000:8000
```

### GPU Not Detected
```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If fails, install nvidia-docker
# Follow: https://github.com/NVIDIA/nvidia-docker
```

### Models Not Downloading
First startup takes 5-10 minutes to download models. Watch the logs:
```bash
docker-compose logs -f
```

### Out of Memory
Increase memory limit in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Increase as needed
```

## 💾 Data Persistence

Docker volumes persist:
- Downloaded models (2-5GB)
- Configuration files
- Uploaded/processed documents

```bash
# List volumes
docker volume ls | grep docstrange

# Backup cache
make backup-cache

# Clean volumes
docker-compose down -v
```

## 🏗️ Building Images

```bash
# Build cloud mode
docker-compose build docstrange-cloud

# Build GPU mode
docker-compose build docstrange-gpu

# Build all
docker-compose --profile gpu build
```

## 📊 Resource Requirements

### Cloud Mode (CPU)
- **Min:** 2 CPU cores, 2GB RAM
- **Recommended:** 4 CPU cores, 4GB RAM
- **Storage:** 2GB for cache

### GPU Mode
- **Min:** NVIDIA GPU (4GB VRAM), 4GB RAM
- **Recommended:** NVIDIA GPU (8GB+ VRAM), 8GB RAM
- **Storage:** 5GB for models

## 🔒 Production Deployment

For production use:

1. **Use environment variables for secrets**
2. **Set up reverse proxy (Nginx/Traefik)**
3. **Enable HTTPS**
4. **Configure proper resource limits**
5. **Set up monitoring and logging**

See [DOCKER.md](DOCKER.md) for detailed production setup.

## 📚 Documentation

- **Full Docker Guide:** [DOCKER.md](DOCKER.md)
- **Main Documentation:** [README.md](README.md)
- **Issues:** [GitHub Issues](https://github.com/NanoNets/docstrange/issues)
- **Discussions:** [GitHub Discussions](https://github.com/NanoNets/docstrange/discussions)

## 🆘 Support

- Report bugs: [GitHub Issues](https://github.com/NanoNets/docstrange/issues)
- Ask questions: [GitHub Discussions](https://github.com/NanoNets/docstrange/discussions)
- Documentation: [README.md](README.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) file.
