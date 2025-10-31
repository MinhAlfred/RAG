# Qdrant Vector Database Setup Guide

## Overview

Your RAG system has been successfully migrated to support Qdrant vector database. Qdrant is a high-performance vector similarity search engine with advanced filtering capabilities.

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `qdrant-client>=1.12.1` - Qdrant Python client
- `langchain-qdrant>=0.2.0` - LangChain integration for Qdrant

### 2. Install Qdrant Server

#### Option A: Docker (Recommended)

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

#### Option B: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"  # REST API
      - "6334:6334"  # gRPC API
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
```

Then run:
```bash
docker-compose up -d
```

#### Option C: Qdrant Cloud

Sign up at [cloud.qdrant.io](https://cloud.qdrant.io) and get your cluster URL and API key.

## Configuration

### Environment Variables

Update your `.env` file (or create one from `.env.example`):

```bash
# Vector Store Configuration
VECTOR_STORE_TYPE=qdrant

# Qdrant Local Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_PREFER_GRPC=false

# For Qdrant Cloud (uncomment if using cloud)
# QDRANT_URL=https://your-cluster.qdrant.io
# QDRANT_API_KEY=your-api-key-here
```

### Settings in Code

The configuration is automatically loaded from `config/settings.py`:

```python
VECTOR_STORE_TYPE: Literal["chroma", "faiss", "qdrant"] = "qdrant"
QDRANT_HOST: str = "localhost"
QDRANT_PORT: int = 6333
QDRANT_GRPC_PORT: int = 6334
QDRANT_API_KEY: Optional[str] = None
QDRANT_URL: Optional[str] = None
QDRANT_PREFER_GRPC: bool = False
```

## Creating Vector Store

### Option 1: Using create_vectorstore.py

```bash
python scripts/create_vectorstore.py \
    --input data/processed \
    --collection sgk_tin \
    --store-type qdrant
```

### Option 2: Programmatically

```python
from src.sgk_rag.core.vector_store import VectorStoreManager
from src.sgk_rag.core.embedding_manager import EmbeddingManager

# Initialize managers
embedding_manager = EmbeddingManager(model_name="multilingual")
vector_manager = VectorStoreManager(
    store_type="qdrant",
    embedding_manager=embedding_manager,
    collection_name="sgk_tin"
)

# Load chunks from JSON
chunks = vector_manager.load_chunks_from_json("data/processed/chunks.json")

# Create vector store
vectorstore = vector_manager.create_vectorstore(
    chunks=chunks,
    collection_name="sgk_tin"
)
```

## Using the RAG System

### Initialize RAG Pipeline

```python
from src.sgk_rag.core.rag_pipeline import RAGPipeline

rag = RAGPipeline(
    vector_store_path="data/vectorstores",
    llm_type="ollama",
    model_name="llama3.2:3b",
    collection_name="sgk_tin"
)
```

### Query the System

```python
# Single query
result = rag.query(
    question="Máy tính là gì?",
    grade_filter=6,  # Optional: filter by grade
    return_sources=True
)

print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
```

## API Server

The FastAPI server automatically uses Qdrant based on your configuration:

```bash
# Start the server
python -m uvicorn src.sgk_rag.api.main:app --reload --port 8000
```

Test endpoints:
```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Máy tính là gì?",
    "grade_filter": 6,
    "return_sources": true
  }'

# Get statistics
curl http://localhost:8000/stats
```

## Advantages of Qdrant

1. **Performance**: Highly optimized for large-scale similarity search
2. **Filtering**: Advanced metadata filtering during search
3. **Scalability**: Horizontal scaling support
4. **GRPC Support**: Faster communication with gRPC protocol
5. **Payload Storage**: Store full document payloads alongside vectors
6. **Cloud Ready**: Easy deployment to Qdrant Cloud
7. **Quantization**: Built-in vector quantization for memory efficiency

## Monitoring

### Check Qdrant Status

```bash
# Via REST API
curl http://localhost:6333/collections

# Check specific collection
curl http://localhost:6333/collections/sgk_tin
```

### Web UI

Qdrant provides a web UI at: http://localhost:6333/dashboard

## Troubleshooting

### Connection Refused

- Ensure Qdrant server is running: `docker ps`
- Check port availability: `netstat -an | grep 6333`
- Verify firewall settings

### Collection Not Found

```python
# List all collections
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections()
print(collections)
```

### Performance Issues

- Enable gRPC: Set `QDRANT_PREFER_GRPC=true`
- Use batch operations for large datasets
- Consider increasing Docker memory limits

## Migration from ChromaDB

If you have existing ChromaDB data:

1. Export data from ChromaDB
2. Load chunks from JSON
3. Create new Qdrant collection
4. Update `.env` to use Qdrant

```python
# Export from ChromaDB
from src.sgk_rag.core.vector_store import VectorStoreManager

# Old ChromaDB manager
old_manager = VectorStoreManager(store_type="chroma", collection_name="sgk_tin")
old_vectorstore = old_manager.load_vectorstore()

# Get all documents (if supported)
# Then create new Qdrant collection with the documents
```

## Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant GitHub](https://github.com/qdrant/qdrant)
- [LangChain-Qdrant Integration](https://python.langchain.com/docs/integrations/vectorstores/qdrant)
