# 🚀 Docker Quick Start Guide

**Get the RAG System running in 2 minutes!**

## One-Command Setup

```bash
make setup
```

This command will:
1. ✅ Create `.env` file from template
2. ✅ Build Docker images
3. ✅ Start all services
4. ✅ Run health check

## Manual Setup (3 Steps)

### Step 1: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your API key:
```bash
GOOGLE_API_KEY=your_key_here
```

### Step 2: Start Services

```bash
docker-compose up -d
```

### Step 3: Verify

```bash
# Check status
docker-compose ps

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Main API endpoint |
| API Docs | http://localhost:8000/docs | Interactive documentation |
| Qdrant | http://localhost:6333/dashboard | Vector database UI |

## Common Commands

```bash
# View logs
make logs              # All services
make logs-api          # API only

# Stop services
make down              # Stop
make down-volumes      # Stop and remove data

# Restart
make restart           # All services
make restart-api       # API only

# Shell access
make shell             # Open bash in container

# Health & Stats
make health            # API health check
make db-stats          # Database statistics
make db-collections    # List collections

# Cleanup
make clean             # Remove containers
make clean-all         # Remove everything
```

## Test the API

### Using cURL

```bash
# Health check
curl http://localhost:8000/health | jq

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Máy tính là gì?",
    "return_sources": true
  }' | jq

# Generate slides
curl -X POST http://localhost:8000/slides/generate/json \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python cơ bản",
    "grade": 10,
    "slide_count": 5
  }' | jq
```

### Using Python

```python
import requests

# Ask question
response = requests.post("http://localhost:8000/ask", json={
    "question": "Hệ điều hành là gì?",
    "return_sources": True
})
print(response.json()["answer"])
```

## Deployment Modes

### Development (with hot-reload)
```bash
make up-dev
```
- Source code mounted
- Auto-reload on changes
- Debug logging

### Production (optimized)
```bash
make up-prod
```
- Optimized image
- Nginx reverse proxy
- Resource limits
- Security hardened

### Full Stack (Ollama + Eureka)
```bash
make up-full
```
- Local LLM (Ollama)
- Service discovery (Eureka)

## Troubleshooting

### Service won't start
```bash
# Check logs
make logs

# Rebuild
docker-compose build --no-cache
make up
```

### Can't connect to Qdrant
```bash
# Check if running
docker-compose ps qdrant

# Restart
docker-compose restart qdrant
```

### Port already in use
```bash
# Check what's using port 8000
netstat -tuln | grep 8000

# Or change port in docker-compose.yml
ports:
  - "8080:8000"  # Use port 8080 instead
```

### Out of memory
```bash
# Check usage
docker stats

# Clean up
make clean
docker system prune -a
```

## Next Steps

- 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions
- 🔧 Configure [.env](.env) for your environment
- 📚 Check [README.md](README.md) for API documentation
- 🧪 Run tests: `make test`

## Getting Help

```bash
# Show all commands
make help

# View API docs
# Open http://localhost:8000/docs in browser

# Check service status
docker-compose ps
```

---

**Happy Coding! 🎉**
