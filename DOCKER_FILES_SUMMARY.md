# 📦 Docker Files Summary

Complete overview of all Docker-related files created for the RAG System deployment.

## 📁 Files Created

### Core Docker Files

#### 1. `Dockerfile`
**Purpose**: Multi-stage Dockerfile for building the RAG API container

**Features**:
- **Base stage**: Python 3.11-slim with system dependencies (Tesseract OCR, OpenCV, etc.)
- **Development stage**: Source code mounted for hot-reload
- **Production stage**: Optimized, security-hardened (non-root user), minimal layers

**Build stages**:
```bash
docker build --target development -t rag-api:dev .
docker build --target production -t rag-api:prod .
```

#### 2. `docker-compose.yml`
**Purpose**: Main orchestration file for all services

**Services**:
- **rag-api**: FastAPI application (port 8000)
- **qdrant**: Vector database (ports 6333, 6334)
- **ollama**: Local LLM (port 11434) - profile: `with-ollama`
- **eureka**: Service discovery (port 8761) - profile: `with-eureka`

**Volumes**:
- `qdrant_storage`: Persistent vector database
- `ollama_data`: LLM models storage
- `./data`: Application data (mounted)
- `./logs`: Application logs (mounted)

#### 3. `docker-compose.dev.yml`
**Purpose**: Development-specific overrides

**Features**:
- Source code mounted for live reload
- Debug logging enabled
- Uvicorn with `--reload` flag
- Uses `development` build target

**Usage**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### 4. `docker-compose.prod.yml`
**Purpose**: Production-specific configuration

**Features**:
- Uses `production` build target
- Resource limits (CPU, memory)
- Multiple uvicorn workers
- Nginx reverse proxy with rate limiting
- Always restart policy

**Usage**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 5. `.dockerignore`
**Purpose**: Exclude files from Docker build context

**Excludes**:
- Python cache files (`__pycache__`, `*.pyc`)
- Virtual environments (`.venv`, `venv/`)
- Large data files (`data/raw/*.pdf`, `data/processed/`)
- Development files (`.git/`, `.vscode/`, `.idea/`)
- Test files and documentation

### Configuration Files

#### 6. `nginx.conf`
**Purpose**: Nginx reverse proxy configuration for production

**Features**:
- Rate limiting (10 req/s for API, 50 req/s general)
- CORS headers
- Proxy to rag-api:8000
- Health check endpoint (no rate limit)
- SSL/HTTPS support (commented, ready to enable)
- Timeouts configured (60s connect, 300s read)

**Routes**:
- `/api/*` → rag-api with rate limiting
- `/health` → rag-api (no rate limiting)
- `/docs` → API documentation
- `/` → root endpoint

#### 7. `Makefile`
**Purpose**: Convenient commands for Docker management

**Commands**:
```bash
make help          # Show all commands
make setup         # Initial setup (create .env, build, start)
make build         # Build images
make up            # Start basic services
make up-dev        # Start in dev mode
make up-prod       # Start in production mode
make up-full       # Start with Ollama + Eureka
make down          # Stop services
make logs          # View all logs
make logs-api      # View API logs
make shell         # Open bash in container
make test          # Run tests
make health        # Check API health
make db-stats      # Database statistics
make clean         # Remove containers and volumes
```

### Documentation Files

#### 8. `DEPLOYMENT.md`
**Purpose**: Comprehensive deployment guide (20+ sections)

**Contents**:
- Quick start guide
- Prerequisites and installation
- Environment configuration
- Deployment modes (dev, prod, full stack)
- Service management
- Production deployment checklist
- SSL/HTTPS configuration
- Monitoring and logging
- Troubleshooting guide
- Security best practices
- Performance tuning
- Backup and recovery
- Advanced configuration (GPU, scaling)

#### 9. `DOCKER_QUICKSTART.md`
**Purpose**: Get started in 2 minutes

**Contents**:
- One-command setup
- Manual 3-step setup
- Access points and URLs
- Common commands cheat sheet
- Quick API tests (cURL and Python)
- Deployment modes overview
- Common troubleshooting

### CI/CD Files

#### 10. `.github/workflows/docker-ci.yml`
**Purpose**: GitHub Actions workflow for continuous integration

**Jobs**:
1. **Test**: Run pytest with coverage
2. **Build**: Build and push Docker image to GHCR
3. **Security**: Scan with Trivy vulnerability scanner
4. **Deploy**: Optional deployment step (customizable)

**Triggers**:
- Push to main/develop branches
- Pull requests to main
- Tags matching `v*`

#### 11. `.github/workflows/docker-publish.yml`
**Purpose**: Publish to Docker Hub on release

**Features**:
- Multi-platform builds (amd64, arm64)
- Triggered on GitHub releases
- Manual workflow dispatch option
- Automatic versioning (semver)
- Updates Docker Hub description

## 🚀 Quick Start

### 1. One Command Setup
```bash
make setup
```

### 2. Manual Setup
```bash
# Configure environment
cp .env.example .env
# Edit .env file with your settings

# Build and start
docker-compose up -d

# Check status
docker-compose ps
make health
```

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐│
│  │  Qdrant    │  │  RAG API   │  │  Nginx (prod)      ││
│  │  :6333     │◄─┤  :8000     │◄─┤  :80, :443         ││
│  │  Vector DB │  │  FastAPI   │  │  Reverse Proxy     ││
│  └────────────┘  └────────────┘  └────────────────────┘│
│       │                │                                 │
│       │           ┌────┴────┐                           │
│       │           │         │                           │
│  ┌────▼─────┐  ┌─▼──────┐ ┌▼────────┐                 │
│  │ Ollama   │  │ Eureka │ │ Data    │                 │
│  │ :11434   │  │ :8761  │ │ Volumes │                 │
│  │ (opt.)   │  │ (opt.) │ │         │                 │
│  └──────────┘  └────────┘ └─────────┘                 │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Deployment Modes Comparison

| Feature | Basic | Development | Production | Full Stack |
|---------|-------|-------------|------------|------------|
| **Command** | `make up` | `make up-dev` | `make up-prod` | `make up-full` |
| **Services** | API + Qdrant | API + Qdrant | API + Qdrant + Nginx | All services |
| **Hot Reload** | ❌ | ✅ | ❌ | ❌ |
| **Nginx** | ❌ | ❌ | ✅ | ✅ |
| **Ollama** | ❌ | ❌ | ❌ | ✅ |
| **Eureka** | ❌ | ❌ | ❌ | ✅ |
| **Resource Limits** | ❌ | ❌ | ✅ | ✅ |
| **Security** | Basic | Basic | Enhanced | Enhanced |
| **Workers** | 1 | 1 | 4 | 4 |
| **Use Case** | Testing | Development | Production | Full demo |

## 🔑 Key Features

### Multi-Stage Build
- **Base**: Common dependencies
- **Development**: Quick iteration
- **Production**: Optimized & secure

### Service Profiles
- Optional services (Ollama, Eureka)
- Start only what you need
- Resource-efficient

### Security
- Non-root user in production
- Rate limiting via Nginx
- Health checks enabled
- Secrets via environment variables

### Monitoring
- Health check endpoints
- Docker healthcheck integration
- Logging to stdout/stderr
- Resource usage tracking

### Scalability
- Horizontal scaling support (`docker-compose up --scale`)
- Load balancing via Nginx
- Resource limits configured
- Multiple workers

## 📋 Pre-requisites Checklist

- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] 2GB+ RAM available
- [ ] 5GB+ disk space
- [ ] `.env` file configured
- [ ] API keys set (GOOGLE_API_KEY, etc.)
- [ ] Ports available (8000, 6333, 6334)

## 🧪 Testing the Setup

```bash
# 1. Health check
make health

# 2. View logs
make logs

# 3. Check services
docker-compose ps

# 4. Test API
curl http://localhost:8000/health | jq

# 5. Test question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Test"}' | jq

# 6. View database
curl http://localhost:8000/collections | jq
```

## 🔧 Customization Points

### Port Changes
Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Change 8080 to your preferred port
```

### Resource Limits
Edit `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

### Environment Variables
Edit `.env`:
```bash
LLM_TYPE=gemini
MODEL_NAME=gemini-2.0-flash-exp
EMBEDDING_DEVICE=cuda  # For GPU
```

### Nginx Configuration
Edit `nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;
# Change rate from 10r/s to 20r/s
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Qdrant Docker](https://qdrant.tech/documentation/quick-start/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

## 🆘 Common Issues

### Port Already in Use
```bash
# Check what's using port 8000
netstat -tuln | grep 8000
# Or change port in docker-compose.yml
```

### Permission Denied
```bash
# Fix data directory permissions
sudo chown -R 1000:1000 data/ logs/
```

### Out of Memory
```bash
# Check usage
docker stats
# Clean up
make clean
docker system prune -a
```

### Service Unhealthy
```bash
# Check logs
make logs-api
# Restart service
docker-compose restart rag-api
```

## 🎉 Success Indicators

✅ All services show "Up (healthy)" in `docker-compose ps`
✅ `make health` returns status: "healthy"
✅ Can access API docs at http://localhost:8000/docs
✅ Qdrant dashboard loads at http://localhost:6333/dashboard
✅ Test question returns valid response

---

**Ready to deploy! 🚀**

For detailed instructions, see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Main documentation
