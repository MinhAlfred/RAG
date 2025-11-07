# 🚀 Docker Deployment Guide

Comprehensive guide for deploying the RAG System using Docker and Docker Compose.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Modes](#deployment-modes)
5. [Service Management](#service-management)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Monitoring](#monitoring)

## 🚀 Quick Start

### 1. Using Makefile (Recommended)

```bash
# Initial setup (creates .env, builds images, starts services)
make setup

# View available commands
make help

# View logs
make logs

# Check health
make health
```

### 2. Using Docker Compose Directly

```bash
# Create environment file
cp .env.example .env
# Edit .env with your settings

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard

## 📦 Prerequisites

### Required
- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **2GB+ RAM** available for containers
- **5GB+ disk space** for images and data

### Optional
- **Make**: For using Makefile commands (pre-installed on Linux/Mac)
- **GPU Support**: NVIDIA Docker runtime for GPU acceleration
- **SSL Certificates**: For HTTPS in production

### Verify Installation

```bash
docker --version
# Docker version 24.0.0+

docker-compose --version
# Docker Compose version v2.20.0+
```

## ⚙️ Environment Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Settings

Edit `.env` file with your configuration:

```bash
# ============================================
# LLM Configuration
# ============================================
LLM_TYPE=gemini                 # ollama | gemini | openai
MODEL_NAME=gemini-2.0-flash-exp
GOOGLE_API_KEY=your_api_key     # Required for Gemini

# ============================================
# Vector Store (Choose one)
# ============================================

# Option 1: Use Docker Qdrant (Recommended for development)
VECTOR_STORE_TYPE=qdrant
QDRANT_HOST=qdrant              # Container name
QDRANT_PORT=6333

# Option 2: Use Qdrant Cloud (Recommended for production)
# QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
# QDRANT_API_KEY=your_api_key

# ============================================
# Embedding Configuration
# ============================================
EMBEDDING_MODEL=multilingual    # multilingual | vietnamese | openai
EMBEDDING_DEVICE=cpu            # cpu | cuda (requires GPU support)

# ============================================
# Service Discovery (Optional)
# ============================================
EUREKA_SERVER=http://eureka:8761/eureka/
APP_NAME=python-rag-service
APP_PORT=8000
```

### 3. Collection Name

Specify which collection to use:
```bash
COLLECTION_NAME=sgk_tin_kntt    # Your Qdrant collection name
```

## 🎯 Deployment Modes

### Mode 1: Development (with hot-reload)

```bash
# Using Makefile
make up-dev

# Or using Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Features:**
- Source code mounted for hot-reload
- Debug logging enabled
- Immediate code changes reflection

### Mode 2: Production

```bash
# Using Makefile
make up-prod

# Or using Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Features:**
- Optimized image with minimal layers
- Resource limits configured
- Nginx reverse proxy with rate limiting
- Enhanced security (non-root user)
- Auto-restart on failure

### Mode 3: Full Stack (with Ollama + Eureka)

```bash
# Using Makefile
make up-full

# Or using Docker Compose
docker-compose --profile with-ollama --profile with-eureka up -d
```

**Includes:**
- RAG API
- Qdrant vector database
- Ollama (local LLM)
- Eureka server (service discovery)

### Mode 4: Basic (RAG API + Qdrant only)

```bash
# Using Makefile
make up

# Or using Docker Compose
docker-compose up -d
```

**Includes:**
- RAG API
- Qdrant vector database

## 🛠️ Service Management

### Using Makefile

```bash
# Start services
make up              # Basic mode
make up-dev          # Development mode
make up-prod         # Production mode
make up-full         # Full stack

# Stop services
make down            # Stop without removing volumes
make down-volumes    # Stop and remove volumes

# View logs
make logs            # All services
make logs-api        # API only
make logs-qdrant     # Qdrant only

# Container shell
make shell           # Open bash in API container
make shell-root      # Open bash as root

# Restart services
make restart         # All services
make restart-api     # API only

# Health checks
make health          # API health
make db-stats        # Database statistics
make db-collections  # List collections

# Testing
make test            # Run tests
make test-cov        # Run tests with coverage

# Cleanup
make clean           # Remove containers and volumes
make clean-all       # Remove everything including images
```

### Using Docker Compose

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Execute command in container
docker-compose exec rag-api [command]

# Scale services
docker-compose up -d --scale rag-api=3
```

## 🏭 Production Deployment

### 1. Pre-deployment Checklist

- [ ] Update `.env` with production values
- [ ] Configure SSL certificates (if using HTTPS)
- [ ] Set strong API keys
- [ ] Configure resource limits
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Test disaster recovery

### 2. Build Production Image

```bash
# Build optimized production image
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Tag image for registry
docker tag rag-system:latest your-registry/rag-system:v1.0.0
```

### 3. Deploy with Nginx Reverse Proxy

```bash
# Start with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Services available:
# - API: http://localhost/api/
# - Health: http://localhost/health
# - Docs: http://localhost/docs
```

### 4. Configure SSL (HTTPS)

1. **Obtain SSL certificates** (Let's Encrypt recommended):
```bash
# Using certbot
certbot certonly --standalone -d your-domain.com
```

2. **Copy certificates**:
```bash
mkdir ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
```

3. **Uncomment HTTPS section** in `nginx.conf`

4. **Restart nginx**:
```bash
docker-compose restart nginx
```

### 5. Resource Limits

Edit `docker-compose.prod.yml` to adjust limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Max CPUs
      memory: 8G       # Max memory
    reservations:
      cpus: '2'        # Reserved CPUs
      memory: 4G       # Reserved memory
```

### 6. Scaling

```bash
# Scale API service to 3 instances
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale rag-api=3

# Nginx will load balance automatically
```

## 🔍 Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Check all services
docker-compose ps

# View resource usage
docker stats
```

### Logs

```bash
# Follow all logs
docker-compose logs -f

# API logs only
docker-compose logs -f rag-api

# Last 100 lines
docker-compose logs --tail=100 rag-api

# With timestamps
docker-compose logs -f --timestamps rag-api
```

### Metrics

```bash
# System statistics
curl http://localhost:8000/stats | jq

# Collections info
curl http://localhost:8000/collections | jq

# Qdrant metrics
curl http://localhost:6333/metrics
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs rag-api

# Check service status
docker-compose ps

# Rebuild image
docker-compose build --no-cache rag-api

# Check port availability
netstat -tuln | grep 8000
```

### Connection Refused to Qdrant

```bash
# Check if Qdrant is running
docker-compose ps qdrant

# Check Qdrant logs
docker-compose logs qdrant

# Test Qdrant connection
curl http://localhost:6333/health

# Restart Qdrant
docker-compose restart qdrant
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.prod.yml
# Or allocate more memory to Docker Desktop

# Clear unused data
docker system prune -a
```

### Permission Errors

```bash
# Fix data directory permissions
sudo chown -R 1000:1000 data/ logs/

# Or run as root (development only)
docker-compose exec -u root rag-api bash
```

### API Returns 503 Service Unavailable

```bash
# Check if vector store is initialized
curl http://localhost:8000/collections

# Check startup logs
docker-compose logs rag-api | grep -i "error\|fail"

# Verify .env configuration
docker-compose exec rag-api env | grep QDRANT
```

### Slow API Responses

```bash
# Check if using CPU instead of GPU
docker-compose exec rag-api env | grep EMBEDDING_DEVICE

# Monitor container resources
docker stats rag-api

# Scale API instances
docker-compose up -d --scale rag-api=2

# Check Qdrant performance
curl http://localhost:6333/metrics
```

## 🔐 Security Best Practices

### 1. Environment Variables
- Never commit `.env` file to git
- Use secrets management in production (Docker Swarm, Kubernetes)
- Rotate API keys regularly

### 2. Network Security
- Use private networks for inter-service communication
- Configure firewall rules
- Enable HTTPS in production
- Implement rate limiting (configured in nginx.conf)

### 3. Container Security
- Run as non-root user (configured in production Dockerfile)
- Use minimal base images
- Scan images for vulnerabilities
- Keep base images updated

### 4. Access Control
- Restrict Qdrant port (6333) to internal network only
- Use Nginx as reverse proxy
- Implement authentication middleware if needed

## 📊 Performance Tuning

### API Workers

```yaml
# In docker-compose.prod.yml
command: uvicorn src.sgk_rag.api.main:app --workers 4
# Rule of thumb: workers = (2 × CPU cores) + 1
```

### Database Optimization

```yaml
# Qdrant configuration
environment:
  - QDRANT__SERVICE__MAX_SEARCH_THREADS=4
  - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
```

### Resource Allocation

```yaml
# Adjust based on your workload
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

## 🔄 Backup & Recovery

### Backup Data

```bash
# Backup Qdrant data
docker-compose exec qdrant tar czf /tmp/qdrant-backup.tar.gz /qdrant/storage
docker cp rag-qdrant:/tmp/qdrant-backup.tar.gz ./backups/

# Backup application data
tar czf backup-$(date +%Y%m%d).tar.gz data/
```

### Restore Data

```bash
# Restore Qdrant data
docker cp ./backups/qdrant-backup.tar.gz rag-qdrant:/tmp/
docker-compose exec qdrant tar xzf /tmp/qdrant-backup.tar.gz -C /

# Restart services
docker-compose restart
```

## 🔧 Advanced Configuration

### GPU Support

1. **Install NVIDIA Docker runtime**
2. **Update docker-compose.yml**:
```yaml
rag-api:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

3. **Set environment**:
```bash
EMBEDDING_DEVICE=cuda
```

### Custom Ports

```yaml
# Change ports in docker-compose.yml
ports:
  - "8080:8000"  # API on port 8080
  - "6380:6333"  # Qdrant on port 6380
```

### External Qdrant Cloud

```yaml
# Remove qdrant service from docker-compose.yml
# Configure in .env
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_api_key
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Nginx Documentation](https://nginx.org/en/docs/)

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `make logs` or `docker-compose logs -f`
2. Verify configuration: Check `.env` file
3. Test connectivity: `make health`
4. Review this guide's troubleshooting section
5. Open an issue on GitHub with logs and configuration

---

**Happy Deploying! 🚀**
