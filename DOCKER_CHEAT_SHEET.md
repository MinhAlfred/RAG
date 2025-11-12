# 🚀 Docker Quick Reference

## Cloud Deployment (Supabase + Qdrant Cloud)

### 🏁 Quick Start
```bash
# 1. Configure environment
cp .env.docker .env
# Edit .env with your credentials

# 2. Build & Start
make cloud-build
make cloud-up

# 3. Verify
make cloud-health
```

### 📦 Common Commands

| Action | Command |
|--------|---------|
| Build | `make cloud-build` |
| Start | `make cloud-up` |
| Stop | `make cloud-down` |
| Restart | `make cloud-restart` |
| Logs | `make cloud-logs` |
| Shell | `make cloud-shell` |
| Status | `make cloud-ps` |
| Health | `make cloud-health` |
| Stats | `make cloud-stats` |

### 🔧 Management

```bash
# View logs (follow mode)
make cloud-logs

# View last 100 lines
docker-compose -f docker-compose.cloud.yml logs --tail=100

# Restart after code changes
make cloud-build
make cloud-restart

# Access container shell
make cloud-shell

# Check resource usage
docker stats rag-api-cloud
```

### 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health | jq

# Ask question (requires API key)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"question": "Python là gì?"}' | jq

# Generate slides
curl -X POST http://localhost:8000/slides/generate/json \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"topic": "Python", "grade": 10, "slide_count": 5}' | jq

# Create conversation
curl -X POST http://localhost:8000/chat/conversations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"user_id": "user123", "title": "Learning"}' | jq
```

## Local Development (with Local Qdrant)

### 🏁 Quick Start
```bash
# 1. Configure
cp .env.example .env
# Edit .env

# 2. Start all services
make setup

# Or manually
make build
make up
```

### 📦 Common Commands

| Action | Command |
|--------|---------|
| Build | `make build` |
| Start (basic) | `make up` |
| Start (dev mode) | `make up-dev` |
| Start (production) | `make up-prod` |
| Start (full stack) | `make up-full` |
| Stop | `make down` |
| Restart | `make restart` |
| Logs | `make logs` |
| API Logs | `make logs-api` |
| Qdrant Logs | `make logs-qdrant` |
| Shell | `make shell` |
| Status | `make ps` |
| Health | `make health` |
| Stats | `make db-stats` |
| Collections | `make db-collections` |

### 🧹 Cleanup

```bash
# Stop and remove containers
make down

# Stop and remove volumes
make down-volumes

# Full cleanup
make clean

# Remove everything including images
make clean-all
```

## 🔑 Required Environment Variables

### Minimal Setup
```bash
# .env file
GOOGLE_API_KEY=your-key
RAG_API_KEY=your-secure-key
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-key
user=postgres.projectref
password=your-db-password
host=aws-region.pooler.supabase.com
dbname=postgres
```

### Generate Secure API Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Main API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative docs |
| Health | http://localhost:8000/health | Health check |
| Stats | http://localhost:8000/stats | System stats |
| Qdrant UI | http://localhost:6333/dashboard | Vector DB UI (local only) |

## 🐛 Troubleshooting

### Service won't start
```bash
make cloud-logs              # Check logs
make cloud-build-no-cache   # Rebuild
make cloud-up               # Restart
```

### Database issues
```bash
# Check connection
make cloud-shell
python -c "from config.settings import settings; print(settings.host)"
```

### Qdrant issues
```bash
# Test connection
curl -H "api-key: YOUR_KEY" https://your-cluster.qdrant.io:6333/collections
```

### API key issues
```bash
# Check if set
make cloud-shell
env | grep RAG_API_KEY

# Test with key
curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/health
```

### Port already in use
```bash
# Check what's using port 8000
netstat -tuln | grep 8000

# Or change port in docker-compose.cloud.yml
ports:
  - "8080:8000"
```

## 📚 Documentation

- **Full Cloud Guide**: `DOCKER_CLOUD_DEPLOYMENT.md`
- **Quick Start**: `DOCKER_QUICKSTART.md`
- **Deployment Guide**: `DEPLOYMENT.md`
- **Docker Files Summary**: `DOCKER_FILES_SUMMARY.md`
- **Main README**: `README.md`

## 🆘 Help

```bash
# Show all commands
make help

# Cloud setup guide
make cloud-setup

# Check service status
make cloud-ps
docker ps

# View container info
docker inspect rag-api-cloud
```

---

**Quick Reference Card - Keep this handy! 📋**
