.PHONY: help build build-gpu up up-gpu down logs clean test shell

help: ## Show this help message
	@echo "DocStrange Docker Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build cloud mode Docker image
	docker-compose build docstrange-cloud

build-gpu: ## Build GPU mode Docker image
	docker-compose build docstrange-gpu

build-all: ## Build all Docker images
	docker-compose --profile gpu build

up: ## Start cloud mode service
	docker-compose up -d docstrange-cloud
	@echo "✅ DocStrange cloud mode started at http://localhost:8000"

up-gpu: ## Start GPU mode service
	docker-compose --profile gpu up -d docstrange-gpu
	@echo "✅ DocStrange GPU mode started at http://localhost:8001"

up-all: ## Start all services
	docker-compose --profile gpu up -d
	@echo "✅ All DocStrange services started"
	@echo "   Cloud mode: http://localhost:8000"
	@echo "   GPU mode:   http://localhost:8001"

down: ## Stop all services
	docker-compose --profile gpu down

restart: ## Restart cloud mode service
	docker-compose restart docstrange-cloud

restart-gpu: ## Restart GPU mode service
	docker-compose --profile gpu restart docstrange-gpu

logs: ## View cloud mode logs
	docker-compose logs -f docstrange-cloud

logs-gpu: ## View GPU mode logs
	docker-compose logs -f docstrange-gpu

ps: ## Show running containers
	docker-compose ps

shell: ## Open shell in cloud mode container
	docker exec -it docstrange-cloud bash

shell-gpu: ## Open shell in GPU mode container
	docker exec -it docstrange-gpu bash

test: ## Test the API
	@echo "Testing cloud mode API..."
	@curl -s http://localhost:8000/api/health | python -m json.tool || echo "Service not running on port 8000"

test-gpu: ## Test the GPU API
	@echo "Testing GPU mode API..."
	@curl -s http://localhost:8001/api/health | python -m json.tool || echo "Service not running on port 8001"

clean: ## Remove all containers and volumes
	docker-compose --profile gpu down -v
	@echo "⚠️  All containers and volumes removed"

clean-images: ## Remove all DocStrange images
	docker-compose --profile gpu down
	docker rmi docstrange-cloud docstrange-gpu 2>/dev/null || true
	@echo "🗑️  All DocStrange images removed"

prune: ## Clean up Docker system
	docker system prune -f
	@echo "🧹 Docker system cleaned"

env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "📝 Edit .env to configure your API key"; \
	else \
		echo "⚠️  .env already exists"; \
	fi

gpu-check: ## Check if GPU is available in container
	@docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi || \
		echo "❌ GPU not available. Install nvidia-docker: https://github.com/NVIDIA/nvidia-docker"

volumes: ## List Docker volumes
	@echo "DocStrange volumes:"
	@docker volume ls | grep docstrange || echo "No DocStrange volumes found"

backup-cache: ## Backup model cache
	@mkdir -p backups
	@docker run --rm -v docstrange-cache:/data -v $(PWD)/backups:/backup ubuntu tar czf /backup/docstrange-cache-$$(date +%Y%m%d-%H%M%S).tar.gz /data
	@echo "✅ Cache backed up to backups/"

restore-cache: ## Restore model cache (usage: make restore-cache FILE=backups/docstrange-cache-xxx.tar.gz)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Usage: make restore-cache FILE=backups/docstrange-cache-xxx.tar.gz"; \
		exit 1; \
	fi
	docker run --rm -v docstrange-cache:/data -v $(PWD)/backups:/backup ubuntu tar xzf /backup/$$(basename $(FILE)) -C /
	@echo "✅ Cache restored from $(FILE)"

stats: ## Show container stats
	docker stats docstrange-cloud docstrange-gpu --no-stream

update: ## Update to latest code and rebuild
	git pull
	docker-compose --profile gpu build
	docker-compose --profile gpu up -d
	@echo "✅ Updated and restarted"
