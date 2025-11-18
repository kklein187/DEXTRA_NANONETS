# 🐳 Quick Start with Docker

This guide helps you run DocStrange in Docker containers.

## Prerequisites

1. **Docker** and **Docker Compose** installed
2. **Nanonets API Key** - Get yours at [https://app.nanonets.com/#/keys](https://app.nanonets.com/#/keys)
   - Free tier available at [https://nanonets.com](https://nanonets.com)

## Start in 1 Command

```bash
./docker-start.sh YOUR_API_KEY_HERE
```

That's it! The web interface will be available at **http://localhost:8000**

## Usage Options

```bash
# Cloud mode (default) - Uses Nanonets API, no GPU needed
./docker-start.sh YOUR_API_KEY_HERE cloud

# GPU mode - Local processing with NVIDIA GPU
./docker-start.sh YOUR_API_KEY_HERE gpu

# Both modes - Run both services
./docker-start.sh YOUR_API_KEY_HERE both
```

## What Happens

1. ✅ Checks Docker installation
2. ✅ Creates `.env` file with your API key
3. ✅ Builds Docker image (first time only, ~2-5 minutes)
4. ✅ Starts the service
5. ✅ Opens at http://localhost:8000

## Manual Setup (Alternative)

If you prefer manual control:

```bash
# 1. Create .env file
cp .env.example .env

# 2. Edit .env and add your API key
echo "NANONETS_API_KEY=YOUR_API_KEY" >> .env

# 3. Start the service
docker-compose up -d docstrange-cloud

# 4. View logs
docker-compose logs -f

# 5. Stop when done
docker-compose down
```

## Common Commands

```bash
# View logs
docker-compose logs -f docstrange-cloud

# Stop service
docker-compose down

# Restart service
docker-compose restart docstrange-cloud

# Get shell access
docker exec -it docstrange-cloud bash
```

## Troubleshooting

### "No connection" error when accessing localhost:8000
Wait 30-60 seconds for the container to fully start, then try again.

### Check if container is running
```bash
docker ps
```

### View container logs
```bash
docker-compose logs -f
```

### Port already in use
Edit `docker-compose.yml` and change:
```yaml
ports:
  - "8080:8000"  # Change 8000 to 8080 or any free port
```

## Full Documentation

- **Quick Reference:** [DOCKER_README.md](DOCKER_README.md)
- **Complete Guide:** [DOCKER.md](DOCKER.md)
- **Setup Summary:** [DOCKER_SETUP_SUMMARY.md](DOCKER_SETUP_SUMMARY.md)

## Support

- Get API Key: https://app.nanonets.com/#/keys
- Free Tier: https://nanonets.com
- Report Issues: [GitHub Issues](https://github.com/NanoNets/docstrange/issues)
