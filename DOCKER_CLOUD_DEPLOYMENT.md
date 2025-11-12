# 🚀 Docker Cloud Deployment Guide

**Deploy RAG System with Supabase + Qdrant Cloud**

This guide shows how to deploy the RAG API using Docker with cloud-based services (Supabase for PostgreSQL and Qdrant Cloud for vector storage).

## 📋 Prerequisites

- Docker and Docker Compose installed
- Supabase account (for PostgreSQL database)
- Qdrant Cloud account (for vector storage)
- Google Gemini API key (or OpenAI/Anthropic)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│     Docker Container (Local/VPS)        │
│  ┌───────────────────────────────────┐  │
│  │       RAG API Service             │  │
│  │   (FastAPI + LangChain)          │  │
│  └───────────┬───────────────────────┘  │
│              │                           │
└──────────────┼───────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│  Supabase   │  │ Qdrant Cloud│
│ PostgreSQL  │  │Vector Store │
│(Chat History│  │(Embeddings) │
└─────────────┘  └─────────────┘
```

## 🚀 Quick Start

### 1. Configure Environment Variables

```bash
# Copy the Docker environment template
cp .env.docker .env

# Edit .env with your actual credentials
nano .env  # or use your favorite editor
```

Required variables in `.env`:

```bash
# API Security
RAG_API_KEY=your-secure-api-key-here

# LLM Configuration
GOOGLE_API_KEY=your-google-api-key
LLM_TYPE=gemini
MODEL_NAME=gemini-2.5-flash

# Qdrant Cloud
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
COLLECTION_NAME_PREFIX=sgk_tin

# Supabase PostgreSQL
user=postgres.projectref
password=your-password
host=aws-region.pooler.supabase.com
port=5432
dbname=postgres

# Embedding
EMBEDDING_MODEL=multilingual
EMBEDDING_DEVICE=cpu
```

### 2. Build and Start Services

```bash
# Build the Docker image
make cloud-build

# Start the service
make cloud-up
```

Or manually:

```bash
docker-compose -f docker-compose.cloud.yml build
docker-compose -f docker-compose.cloud.yml up -d
```

### 3. Verify Deployment

```bash
# Check service status
make cloud-ps

# View logs
make cloud-logs

# Check health
make cloud-health

# Check stats
make cloud-stats
```

## 📝 Available Commands

### Cloud Deployment Commands

```bash
# Build
make cloud-build              # Build Docker image
make cloud-build-no-cache     # Rebuild without cache

# Start/Stop
make cloud-up                 # Start service
make cloud-up-with-nginx      # Start with Nginx reverse proxy
make cloud-down               # Stop service

# Monitoring
make cloud-logs               # View all logs
make cloud-logs-api          # View API logs only
make cloud-ps                # Show running containers

# Management
make cloud-restart           # Restart all services
make cloud-restart-api       # Restart API only
make cloud-shell             # Open bash shell in container

# Health Check
make cloud-health            # API health check
make cloud-stats             # System statistics

# Setup Guide
make cloud-setup             # Show setup instructions
```

## 🔧 Configuration Details

### Supabase Setup

1. **Create Supabase Project**
   - Go to https://supabase.com/dashboard
   - Create a new project
   - Note down your database credentials

2. **Get Connection Details**
   - Go to Project Settings → Database
   - Find "Connection string" section
   - Use "Session pooler" for better performance
   - Copy host, port, user, password

3. **Create Database Tables** (if not exists)
   ```sql
   -- Run this in Supabase SQL Editor

   CREATE TABLE conversations (
       id VARCHAR(36) PRIMARY KEY,
       user_id VARCHAR(255) NOT NULL,
       title VARCHAR(500),
       grade INTEGER,
       subject VARCHAR(100),
       created_at TIMESTAMPTZ DEFAULT NOW(),
       updated_at TIMESTAMPTZ DEFAULT NOW(),
       is_archived BOOLEAN DEFAULT FALSE,
       metadata JSONB
   );

   CREATE INDEX idx_conversations_user_id ON conversations(user_id);

   CREATE TABLE chat_messages (
       id VARCHAR(36) PRIMARY KEY,
       conversation_id VARCHAR(36) NOT NULL,
       role VARCHAR(50) NOT NULL,
       content TEXT NOT NULL,
       sources JSONB,
       retrieval_mode VARCHAR(50),
       docs_retrieved INTEGER,
       web_search_used BOOLEAN DEFAULT FALSE,
       created_at TIMESTAMPTZ DEFAULT NOW(),
       processing_time INTEGER,
       metadata JSONB,
       FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
   );

   CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
   ```

### Qdrant Cloud Setup

1. **Create Qdrant Cloud Account**
   - Go to https://cloud.qdrant.io/
   - Create a new cluster
   - Note down cluster URL and API key

2. **Create Collection**
   - Collections are auto-created by the API
   - Or create manually via Qdrant UI

### Google Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key
3. Copy and add to `.env`

## 🌐 Nginx Reverse Proxy (Optional)

For production deployments with SSL/HTTPS:

```bash
# Start with Nginx
make cloud-up-with-nginx
```

Edit `nginx.conf` for custom configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://rag-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 Security Best Practices

1. **API Key Protection**
   ```bash
   # Generate a secure API key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Environment Variables**
   - Never commit `.env` to version control
   - Use `.env.docker` as template only
   - Rotate keys regularly

3. **CORS Configuration**
   - In production, set specific origins:
   ```bash
   CORS_ORIGINS=https://your-frontend-domain.com
   ```

4. **Database Security**
   - Use Supabase connection pooler
   - Enable SSL connections
   - Restrict IP access if possible

## 🧪 Testing the Deployment

### 1. Health Check

```bash
curl http://localhost:8000/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "rag_status": "ready",
  "vector_store_info": {...},
  "model_info": {...}
}
```

### 2. Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "Máy tính là gì?",
    "return_sources": true
  }' | jq
```

### 3. Generate Slides

```bash
curl -X POST http://localhost:8000/slides/generate/json \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Python cơ bản",
    "grade": 10,
    "slide_count": 5
  }' | jq
```

### 4. Chat with Memory

```bash
# Create conversation
curl -X POST http://localhost:8000/chat/conversations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_id": "user123",
    "title": "Learning Python"
  }' | jq

# Send message
curl -X POST http://localhost:8000/chat/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "conversation_id": "conversation-id-from-above",
    "content": "Python là gì?"
  }' | jq
```

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
make cloud-logs

# Last 100 lines
docker-compose -f docker-compose.cloud.yml logs --tail=100 rag-api
```

### Check Resource Usage

```bash
docker stats rag-api-cloud
```

### System Statistics

```bash
curl http://localhost:8000/stats | jq
```

## 🔄 Updates and Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
make cloud-build-no-cache
make cloud-restart
```

### Backup Data

```bash
# Backup logs
cp -r logs logs-backup-$(date +%Y%m%d)

# Database backup (via Supabase)
# Go to Supabase Dashboard → Database → Backups
```

### Clean Up

```bash
# Stop services
make cloud-down

# Remove containers and images
docker-compose -f docker-compose.cloud.yml down --rmi all

# Clean up Docker system
docker system prune -a
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
make cloud-logs

# Rebuild without cache
make cloud-build-no-cache
make cloud-up
```

### Database Connection Issues

```bash
# Test database connection
docker-compose -f docker-compose.cloud.yml exec rag-api python -c "
from config.settings import settings
print(f'DB Host: {settings.host}')
print(f'DB User: {settings.user}')
print(f'DB Name: {settings.dbname}')
"
```

### Qdrant Connection Issues

```bash
# Check Qdrant connectivity
curl -X GET "https://your-cluster.cloud.qdrant.io:6333/collections" \
  -H "api-key: your-api-key"
```

### API Key Authentication Failing

```bash
# Verify API key in .env
docker-compose -f docker-compose.cloud.yml exec rag-api env | grep RAG_API_KEY

# Test with correct header
curl -H "X-API-Key: your-actual-key" http://localhost:8000/health
```

## 🎯 Production Deployment Checklist

- [ ] All API keys configured in `.env`
- [ ] Secure `RAG_API_KEY` generated and set
- [ ] CORS origins restricted to your frontend domains
- [ ] Supabase database tables created
- [ ] Qdrant Cloud collection populated with embeddings
- [ ] Health check passing
- [ ] Test queries working
- [ ] Logs directory mounted for persistence
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] SSL/HTTPS configured (if using Nginx)

## 📚 Next Steps

1. **Populate Vector Store**
   ```bash
   # Upload your textbook PDFs and create embeddings
   python scripts/create_vectorstore_all.py
   ```

2. **Configure Monitoring**
   - Set up log aggregation (e.g., ELK stack)
   - Configure alerts for errors
   - Monitor API response times

3. **Scale**
   - Adjust Docker resource limits
   - Use multiple API instances with load balancer
   - Upgrade Supabase/Qdrant plans as needed

## 🆘 Getting Help

- **API Documentation**: http://localhost:8000/docs
- **View All Commands**: `make help`
- **Check Service Status**: `make cloud-ps`
- **View Logs**: `make cloud-logs`

---

**Happy Deploying! 🚀**
