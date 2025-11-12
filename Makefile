# ============================================
# Makefile for RAG System Docker Management
# ============================================

.PHONY: help build up down logs shell test clean

# Default target
help:
	@echo "RAG System Docker Commands:"
	@echo ""
	@echo "Local Development (with local Qdrant):"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make up-dev         - Start in development mode"
	@echo "  make up-prod        - Start in production mode"
	@echo "  make up-full        - Start with Ollama + Eureka"
	@echo ""
	@echo "Cloud Deployment (Supabase + Qdrant Cloud):"
	@echo "  make cloud-build    - Build for cloud deployment"
	@echo "  make cloud-up       - Start cloud deployment"
	@echo "  make cloud-down     - Stop cloud deployment"
	@echo "  make cloud-logs     - View cloud deployment logs"
	@echo "  make cloud-restart  - Restart cloud deployment"
	@echo ""
	@echo "General Commands:"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View logs"
	@echo "  make logs-api       - View API logs only"
	@echo "  make shell          - Open shell in API container"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make ps             - Show running containers"
	@echo "  make restart        - Restart all services"

# Build images
build:
	docker-compose build

build-no-cache:
	docker-compose build --no-cache

# Start services
up:
	docker-compose up -d

up-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

up-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

up-full:
	docker-compose --profile with-ollama --profile with-eureka up -d

# Stop services
down:
	docker-compose down

down-volumes:
	docker-compose down -v

# View logs
logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f rag-api

logs-qdrant:
	docker-compose logs -f qdrant

# Container management
shell:
	docker-compose exec rag-api /bin/bash

shell-root:
	docker-compose exec -u root rag-api /bin/bash

ps:
	docker-compose ps

restart:
	docker-compose restart

restart-api:
	docker-compose restart rag-api

# Testing
test:
	docker-compose exec rag-api pytest tests/

test-cov:
	docker-compose exec rag-api pytest --cov=src tests/

# Database management
db-stats:
	curl http://localhost:8000/stats | jq

db-collections:
	curl http://localhost:8000/collections | jq

health:
	curl http://localhost:8000/health | jq

# Clean up
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all:
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af

# Initial setup
setup:
	@echo "Creating .env file from template..."
	@cp -n .env.example .env || echo ".env already exists"
	@echo "Building images..."
	@make build
	@echo "Starting services..."
	@make up
	@echo "Waiting for services to be ready..."
	@sleep 10
	@make health
	@echo ""
	@echo "Setup complete! API is running at http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Qdrant UI: http://localhost:6333/dashboard"

# ============================================
# Cloud Deployment Commands
# ============================================

cloud-build:
	docker-compose -f docker-compose.cloud.yml build

cloud-build-no-cache:
	docker-compose -f docker-compose.cloud.yml build --no-cache

cloud-up:
	docker-compose -f docker-compose.cloud.yml up -d

cloud-up-with-nginx:
	docker-compose -f docker-compose.cloud.yml --profile with-nginx up -d

cloud-down:
	docker-compose -f docker-compose.cloud.yml down

cloud-logs:
	docker-compose -f docker-compose.cloud.yml logs -f

cloud-logs-api:
	docker-compose -f docker-compose.cloud.yml logs -f rag-api

cloud-restart:
	docker-compose -f docker-compose.cloud.yml restart

cloud-restart-api:
	docker-compose -f docker-compose.cloud.yml restart rag-api

cloud-shell:
	docker-compose -f docker-compose.cloud.yml exec rag-api /bin/bash

cloud-ps:
	docker-compose -f docker-compose.cloud.yml ps

cloud-health:
	curl http://localhost:8000/health | jq

cloud-stats:
	curl http://localhost:8000/stats | jq

cloud-setup:
	@echo "==================================================="
	@echo "Cloud Deployment Setup"
	@echo "==================================================="
	@echo ""
	@echo "Step 1: Configure environment variables"
	@cp -n .env.docker .env 2>/dev/null || echo ".env already exists"
	@echo "  -> Edit .env with your cloud credentials:"
	@echo "     - GOOGLE_API_KEY"
	@echo "     - QDRANT_URL and QDRANT_API_KEY"
	@echo "     - Supabase credentials (user, password, host, dbname)"
	@echo "     - RAG_API_KEY"
	@echo ""
	@echo "Step 2: Build and start services"
	@echo "  -> Run: make cloud-build && make cloud-up"
	@echo ""
	@echo "Step 3: Check health"
	@echo "  -> Run: make cloud-health"
	@echo ""
	@echo "==================================================="
