# 🎓 Multi-Subject RAG System for Vietnamese Education

**Advanced Retrieval-Augmented Generation (RAG) System for Vietnamese K-12 Education**

A comprehensive AI-powered educational assistant that combines semantic search, LLM capabilities, automated slide generation, and mindmap creation to support Vietnamese textbooks across multiple subjects (Computer Science, Math, Literature, Physics, Chemistry, Biology) for grades 3-12.

## 🌟 Key Features

### Core Capabilities
- **🔍 Intelligent Q&A**: Context-aware answers using RAG with web search fallback
- **📊 Automated Slide Generation**: Create educational presentations with structured JSON output for PowerPoint integration
- **🗺️ Mindmap Generation**: Generate interactive mind maps for visual learning
- **💬 Chat with Memory**: Conversation management with persistent chat history (PostgreSQL/Supabase)
- **🌐 Hybrid Knowledge Retrieval**: Combines textbook knowledge base + live web search (DuckDuckGo)
- **📚 Multi-Subject Support**: Computer Science, Math, Literature, Physics, Chemistry, Biology
- **🎯 Grade-Specific Filtering**: Target content for grades 3-12
- **🚀 Production-Ready API**: FastAPI with OpenAPI documentation and async support

### Technical Features
- **Vector Search**: Qdrant Cloud/Local vector database with semantic embeddings (384-dim)
- **Multiple LLM Support**: Ollama (local), Google Gemini, OpenAI, Anthropic
- **OCR Processing**: Extract text from PDF textbooks (Tesseract + OpenCV)
- **Service Discovery**: Eureka integration for microservices architecture
- **Batch Processing**: Handle multiple questions concurrently
- **Type-Safe Models**: Pydantic models for all API requests/responses
- **CUDA Acceleration**: GPU-accelerated embeddings with automatic CPU fallback
- **Database Integration**: Async SQLAlchemy with PostgreSQL for chat persistence

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (main.py)                          │
│  /ask, /slides/generate/json, /mindmap/generate, /chat/*, /health    │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐   ┌────────────────┐   ┌─────────────────┐
│ RAG Pipeline │   │ Slide & Mindmap│   │  Chat Service   │
│              │   │   Generators   │   │  (with Memory)  │
└──────┬───────┘   └────────┬───────┘   └────────┬────────┘
       │                    │                     │
       │           ┌────────┴────────┐           │
       │           │                 │           │
       ▼           ▼                 ▼           ▼
┌────────────┐  ┌─────────┐  ┌─────────────┐  ┌──────────────┐
│Vector Store│  │   LLM   │  │ Web Search  │  │  PostgreSQL  │
│  (Qdrant)  │  │(Gemini/ │  │(DuckDuckGo) │  │  Database    │
│+ Embeddings│  │ Ollama) │  │             │  │(Conversations)│
└────────────┘  └─────────┘  └─────────────┘  └──────────────┘
       │
       ▼
┌──────────────┐
│   Eureka     │
│Service Disc. │
└──────────────┘
```

### Component Overview

**API Layer:**
- `main.py`: FastAPI application with 11+ endpoints
- `chat_api.py`: Conversation management endpoints
- `slide_generator.py`: PowerPoint-compatible JSON slide generation
- `mindmap_generator.py`: Interactive mindmap creation
- `auth.py`: API key authentication

**Core Layer:**
- `rag_pipeline.py`: Complete RAG orchestration with hybrid retrieval
- `vector_store.py`: Qdrant/Chroma/FAISS vector database management
- `embedding_manager.py`: Sentence transformers with CUDA auto-detection
- `web_search.py`: DuckDuckGo web search fallback
- `database.py`: Async database connection pool
- `chat_service.py`: Conversation and message persistence

**Data Layer:**
- SQLAlchemy async ORM models
- Qdrant Cloud vector storage (1,972+ documents)
- PostgreSQL/Supabase for chat history

## 📦 Installation

### Prerequisites
- Python 3.9+
- (Optional) Qdrant server or Qdrant Cloud account
- (Optional) GPU for faster embedding generation

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd RAG
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# === LLM Configuration ===
LLM_TYPE=ollama                    # ollama | gemini | openai | anthropic
MODEL_NAME=llama3.2:3b            # Model identifier
GOOGLE_API_KEY=your_key_here       # For Gemini
OPENAI_API_KEY=your_key_here       # For OpenAI (optional)
ANTHROPIC_API_KEY=your_key_here    # For Claude (optional)

# === Vector Store Configuration ===
VECTOR_STORE_TYPE=qdrant           # qdrant | chroma | faiss
COLLECTION_NAME_PREFIX=sgk_tin     # Default collection prefix

# === Qdrant Configuration ===
# Option 1: Qdrant Cloud (Recommended for production)
QDRANT_URL=https://your-cluster.us-west-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your_api_key_here
QDRANT_PREFER_GRPC=true

# Option 2: Local Qdrant (Development)
# QDRANT_HOST=localhost
# QDRANT_PORT=6333
# QDRANT_GRPC_PORT=6334

# === Embeddings Configuration ===
EMBEDDING_MODEL=multilingual       # multilingual | vietnamese | openai
EMBEDDING_DEVICE=auto             # auto | cuda | cpu (auto detects CUDA)
EMBEDDING_BATCH_SIZE=50

# === Database Configuration (for Chat with Memory) ===
# Option 1: Full DATABASE_URL (Recommended)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# Option 2: Separate parameters
# DB_USER=your_username
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=rag_db

# === Web Search Configuration ===
WEB_SEARCH_ENABLED=true            # Enable/disable web search fallback
WEB_SEARCH_MAX_RESULTS=3           # Number of web results
WEB_SEARCH_REGION=vn-vi            # Vietnam/Vietnamese region

# === Service Discovery (for Spring Boot integration) ===
EUREKA_SERVER=http://localhost:8761/eureka/
APP_NAME=python-rag-service
APP_PORT=8000

# === API Security ===
API_KEY=your_secure_api_key        # For API authentication
```

## 🚀 Usage

### Starting the API Server

```bash
# Run with Python
python scripts/run_api.py

# Or use the main module directly
python -m src.sgk_rag.api.main
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### API Endpoints

#### 1. Question & Answer

**POST /ask** - Ask a single question
```json
{
  "question": "Hệ điều hành là gì?",
  "question_type": "general",
  "grade_filter": 10,
  "return_sources": true,
  "max_sources": 5,
  "collection_name": "sgk_tin_kntt"
}
```

**Response:**
```json
{
  "question": "Hệ điều hành là gì?",
  "answer": "Hệ điều hành là phần mềm hệ thống quản lý...",
  "status": "success",
  "sources": [...],
  "processing_time": 1.23,
  "retrieval_mode": "hybrid",
  "web_search_used": true
}
```

**POST /ask/batch** - Ask multiple questions concurrently
```json
{
  "questions": ["Câu hỏi 1", "Câu hỏi 2"],
  "question_type": "general",
  "grade_filter": 10,
  "return_sources": false
}
```

#### 2. Slide Generation

**POST /slides/generate/json** - Generate structured slides (PowerPoint-compatible)
```json
{
  "topic": "Kiểu dữ liệu trong Python",
  "grade": 10,
  "slide_count": 8,
  "format": "json",
  "include_examples": true,
  "include_exercises": false
}
```

**Response:** Structured JSON with:
- PowerPoint layouts (TITLE, TITLE_AND_CONTENT, etc.)
- Placeholder types (TITLE, CONTENT, CODE, IMAGE, TABLE)
- Code blocks with syntax highlighting
- Tables and bullet points
- Image placeholders with descriptions

**POST /slides/generate** - Generate slides (legacy formats: markdown, html, text)

#### 3. Mindmap Generation

**POST /mindmap/generate** - Generate interactive mindmaps
```json
{
  "topic": "Lập trình Python",
  "grade": 10,
  "maxDepth": 3,
  "maxBranches": 5,
  "includeExamples": true
}
```

**Response:** Hierarchical node structure with:
- Center node and primary/secondary/tertiary branches
- Node types (CENTER, PRIMARY, SECONDARY, TERTIARY, EXAMPLE)
- Connections between nodes
- Sources from textbook

#### 4. Chat with Memory

**POST /chat/conversations** - Create a conversation
```json
{
  "user_id": "user123",
  "title": "Learning Python",
  "grade": 10,
  "subject": "Tin Học"
}
```

**POST /chat/conversations/{conversation_id}/messages** - Send message
```json
{
  "content": "Giải thích vòng lặp for trong Python",
  "use_rag": true
}
```

**GET /chat/conversations/{conversation_id}** - Get conversation with messages

**GET /chat/conversations** - List user conversations

#### 5. System Information

- **GET /health** - Health check and system status
- **GET /stats** - Detailed system statistics (vector store, LLM info)
- **GET /collections** - List available Qdrant collections
- **GET /question/types** - Supported question types
- **GET /slides/formats** - Supported slide formats

## 📚 Data Models

### Key Request Models

#### QuestionRequest
```python
{
  "question": str,              # Required
  "question_type": QuestionType,  # general | slide | explain | example
  "grade_filter": int | None,   # 3-12
  "return_sources": bool,       # Default: true
  "max_sources": int,           # 1-10, default: 5
  "collection_name": str | None # Optional collection
}
```

#### SlideRequest
```python
{
  "topic": str,                 # Required
  "grade": int | None,          # 3-12
  "slide_count": int,           # 1-20, default: 5
  "format": SlideFormat,        # json | markdown | html | text
  "include_examples": bool,     # Default: true
  "include_exercises": bool     # Default: false
}
```

### Key Response Models

#### QuestionResponse
- question, answer, status, sources[], processing_time
- retrieval_mode, docs_retrieved, fallback_used, web_search_used

#### JsonSlideResponse
- title, topic, grade, slides[], metadata, status, processing_time
- Each slide includes: slide_number, type, layout, placeholders[], code_block, table, images[]

See [src/sgk_rag/models/dto.py](src/sgk_rag/models/dto.py) for complete model definitions.

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src tests/

# Specific test
python scripts/test_vector_search.py
python scripts/test_json_slides.py
```

### Test Scripts
- `test_qdrant_connection.py` - Verify Qdrant connectivity
- `test_vector_search.py` - Test semantic search
- `test_json_slides.py` - Test slide generation
- `test_enhanced_chunking.py` - Test document processing

## 🔨 Development

### Creating Vector Store

```bash
# Process all textbooks for all grades
python scripts/create_vectorstore_all.py

# Or process specific files
python scripts/create_vectorstore.py --input data/raw/textbook.pdf
```

### Upload to Qdrant Cloud
```bash
python scripts/upload_to_qdrant_cloud.py
```

### Project Structure
```
RAG/
├── config/                 # Configuration files
│   ├── settings.py        # Pydantic settings with multi-subject support
│   └── logging_config.py  # Logging configuration
├── src/sgk_rag/
│   ├── api/               # FastAPI application layer
│   │   ├── main.py       # Main API server (11+ endpoints)
│   │   ├── chat_api.py   # Chat/conversation endpoints
│   │   ├── slide_generator.py    # Slide generation (JSON for PowerPoint)
│   │   ├── mindmap_generator.py  # Mindmap generation
│   │   ├── auth.py       # API key authentication
│   │   └── eureka_config.py      # Eureka service discovery
│   ├── core/              # Core RAG components
│   │   ├── rag_pipeline.py       # Main RAG orchestration
│   │   ├── vector_store.py       # Qdrant/Chroma/FAISS management
│   │   ├── embedding_manager.py  # Sentence transformers (CUDA support)
│   │   ├── web_search.py         # DuckDuckGo web search
│   │   ├── database.py           # Async database pool
│   │   ├── chat_service.py       # Conversation service
│   │   └── document_processor*.py # PDF/OCR processing
│   └── models/            # Data models (Pydantic + SQLAlchemy)
│       ├── dto.py         # API request/response DTOs
│       ├── chat_dto.py    # Chat-specific DTOs
│       ├── chat_models.py # SQLAlchemy ORM models
│       └── document.py    # Document/chunk models
├── scripts/               # Utility scripts
│   ├── run_api.py        # API launcher
│   ├── create_vectorstore.py     # Vector store creation
│   ├── upload_to_qdrant_cloud.py # Cloud deployment
│   └── test_*.py         # Testing scripts
├── data/                  # Data directory
│   ├── raw/              # Raw textbooks (10 grades)
│   ├── processed/        # Processed JSON chunks
│   ├── chunks/           # Original chunks
│   └── vectorstores/     # Vector store persistence
├── docs/                  # Documentation
│   ├── QDRANT_SETUP.md
│   ├── SPRING_BOOT_INTEGRATION.md
│   ├── SPRINGBOOT_PPTX_API_GUIDE.md
│   └── API_AUTHENTICATION.md
├── tests/                # Test suite
├── docker-compose*.yml   # Docker configurations
└── Dockerfile            # Multi-stage Docker build
```

## 🌐 Hybrid Retrieval System

The system uses a sophisticated hybrid approach:

1. **Primary: Vector Database Search**
   - Semantic search in Qdrant vector store
   - 1,972+ textbook chunks (grades 3-12)
   - 384-dimensional embeddings (paraphrase-multilingual-MiniLM-L12-v2)
   - COSINE distance metric
   - Grade and subject filtering

2. **Fallback: Web Search**
   - DuckDuckGo privacy-focused search
   - Activates when vector DB has low-confidence results
   - Region-specific (Vietnam/Vietnamese)
   - Configurable result count

3. **Combined Context**
   - Merges both sources for comprehensive answers
   - Cites sources from textbooks and web
   - Prioritizes textbook knowledge

Configuration in `.env`:
```bash
WEB_SEARCH_ENABLED=true        # Toggle web search
WEB_SEARCH_MAX_RESULTS=3       # Number of web results
WEB_SEARCH_REGION=vn-vi        # Vietnam region
```

## 🎯 Multi-Subject Support

Supported subjects (configurable in `settings.py`):
- **tin_hoc** (Computer Science)
- **toan** (Mathematics)
- **van** (Literature)
- **ly** (Physics)
- **hoa** (Chemistry)
- **sinh** (Biology)

Each subject has custom:
- Keywords for content detection
- Chapter/section parsing patterns
- Aliases for flexible querying

## 🔧 Advanced Configuration

### Chunk Settings
```python
CHUNK_SIZE = 800           # Characters per chunk
CHUNK_OVERLAP = 150        # Overlap between chunks
MIN_CHUNK_SIZE = 50        # Minimum chunk size
```

### Embedding Settings
```python
EMBEDDING_MODEL = "multilingual"  # multilingual | vietnamese | openai
EMBEDDING_BATCH_SIZE = 50        # Batch size for embedding
EMBEDDING_DEVICE = "cuda"        # cuda | cpu
```

### Vector Store Collections
Multiple collections for different subjects/grades:
- `sgk_tin_kntt` - Computer Science & CNTT
- `sgk_toan` - Mathematics
- Custom collections via `collection_name` parameter

## 📊 Slide Generation Features

The system generates PowerPoint-compatible JSON slides optimized for Spring Boot integration.

### Supported Slide Types
- **title_slide**: Title and subtitle with grade/subject metadata
- **content_slide**: Title + structured bullet points (max 7, 300 chars each)
- **code_slide**: Code examples with syntax highlighting and language detection
- **image_slide**: Image placeholders with descriptions and alt text
- **table_slide**: Structured tables with headers and data rows
- **exercise_slide**: Practice exercises with questions/answers
- **summary_slide**: Key takeaways and review points

### PowerPoint Layouts (Apache POI Compatible)
- **TITLE**: Cover slide layout
- **TITLE_AND_CONTENT**: Standard content layout
- **SECTION_HEADER**: Section dividers
- **TWO_CONTENT**: Two-column layout
- **COMPARISON**: Side-by-side comparison
- **TITLE_ONLY**: Title without content area
- **BLANK**: Blank canvas
- **CONTENT_WITH_CAPTION**: Content with caption area
- **PICTURE_WITH_CAPTION**: Image-focused layout

### Placeholder Types
- **TITLE**: Slide titles
- **SUBTITLE**: Subtitles
- **CONTENT**: Main text content with bullet points
- **CODE**: Code blocks with language syntax
- **IMAGE**: Image placeholders with positioning
- **TABLE**: Structured data tables

### Smart Content Generation
- Automatically detects code vs text content
- Prioritizes content slides over code slides
- Parses paragraphs into complete sentences
- Limits bullet points for readability (7 max, 300 chars)
- Extracts and formats code examples
- Generates contextual images and tables

### Output Formats
- **JSON** (Primary): Structured data for Spring Boot/Apache POI
- **Markdown**: Human-readable format
- **HTML**: Web-ready presentation
- **Text**: Plain text format

For Spring Boot integration details, see [docs/SPRINGBOOT_PPTX_API_GUIDE.md](docs/SPRINGBOOT_PPTX_API_GUIDE.md)

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Quick setup (one command)
make setup

# Or manually
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

Access the services:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### Deployment Options

#### Development Mode (with hot-reload)
```bash
make up-dev
# or
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Production Mode (optimized + Nginx)
```bash
make up-prod
# or
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### Full Stack (with Ollama + Eureka)
```bash
make up-full
# or
docker-compose --profile with-ollama --profile with-eureka up -d
```

### Available Make Commands

```bash
make help          # Show all commands
make build         # Build images
make up            # Start services
make down          # Stop services
make logs          # View logs
make shell         # Open shell in container
make test          # Run tests
make clean         # Clean up containers
make health        # Check API health
```

### Docker Architecture

**Services:**
- **rag-api**: FastAPI application (multi-stage Dockerfile)
- **qdrant**: Vector database for embeddings
- **nginx**: Reverse proxy with rate limiting (production)
- **ollama**: Local LLM server (optional)
- **eureka**: Service discovery (optional)

**Volumes:**
- `qdrant_storage`: Persistent vector database
- `ollama_data`: Local LLM models
- `./data`: Application data (mounted)

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 📝 Example Usage

### Python Client
```python
import requests

# 1. Ask a question with RAG
response = requests.post("http://localhost:8000/ask", json={
    "question": "Thuật toán sắp xếp nổi bọt hoạt động như thế nào?",
    "grade_filter": 11,
    "return_sources": true,
    "max_sources": 5
})
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} documents")
print(f"Web search used: {result['web_search_used']}")

# 2. Generate PowerPoint-compatible slides
response = requests.post("http://localhost:8000/slides/generate/json", json={
    "topic": "Biến và kiểu dữ liệu trong Python",
    "grade": 10,
    "slide_count": 8,
    "include_examples": true,
    "include_exercises": false
})
slides = response.json()
print(f"Generated {len(slides['slides'])} slides")

# 3. Create mindmap
response = requests.post("http://localhost:8000/mindmap/generate", json={
    "topic": "Lập trình hướng đối tượng",
    "grade": 11,
    "maxDepth": 3,
    "maxBranches": 5,
    "includeExamples": true
})
mindmap = response.json()
print(f"Mindmap nodes: {mindmap['totalNodes']}")

# 4. Chat with memory
# Create conversation
conv_response = requests.post("http://localhost:8000/chat/conversations", json={
    "user_id": "student123",
    "title": "Learning Python Basics",
    "grade": 10
})
conversation_id = conv_response.json()["id"]

# Send message
msg_response = requests.post(
    f"http://localhost:8000/chat/conversations/{conversation_id}/messages",
    json={
        "content": "Giải thích vòng lặp for trong Python",
        "use_rag": true
    }
)
print(msg_response.json()["assistant_message"]["content"])

# 5. Batch questions
response = requests.post("http://localhost:8000/ask/batch", json={
    "questions": [
        "Biến là gì?",
        "Hàm là gì?",
        "Vòng lặp là gì?"
    ],
    "grade_filter": 10,
    "return_sources": false
})
batch_results = response.json()
for result in batch_results["results"]:
    print(f"Q: {result['question']}\nA: {result['answer']}\n")
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Ask question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Máy tính là gì?",
    "return_sources": true,
    "grade_filter": 6
  }'

# Generate JSON slides
curl -X POST http://localhost:8000/slides/generate/json \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Kiểu dữ liệu Python",
    "grade": 10,
    "slide_count": 6,
    "include_examples": true
  }'

# Generate mindmap
curl -X POST http://localhost:8000/mindmap/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Thuật toán",
    "grade": 11,
    "maxDepth": 3,
    "maxBranches": 4
  }'

# List available collections
curl http://localhost:8000/collections

# Get system statistics
curl http://localhost:8000/stats
```

### JavaScript/TypeScript (Spring Boot Integration)
```typescript
// Fetch slides for PowerPoint generation
const response = await fetch('http://localhost:8000/slides/generate/json', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: 'Lập trình Python cơ bản',
    grade: 10,
    slide_count: 10,
    include_examples: true
  })
});

const slideData = await response.json();

// slideData.slides contains PowerPoint-compatible structure
slideData.slides.forEach((slide, index) => {
  console.log(`Slide ${index + 1}: ${slide.type} - ${slide.layout}`);
  // Process placeholders, code blocks, tables, etc.
});
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

[Specify your license here]

## 🔐 Authentication

API endpoints support API key authentication. Configure in `.env`:

```bash
API_KEY=your_secure_api_key
```

Include in requests:
```bash
curl -H "X-API-Key: your_secure_api_key" http://localhost:8000/ask
```

## 📚 Documentation

Additional documentation available in `docs/`:

- **[QDRANT_SETUP.md](docs/QDRANT_SETUP.md)** - Qdrant Cloud and local setup
- **[SPRING_BOOT_INTEGRATION.md](docs/SPRING_BOOT_INTEGRATION.md)** - Integrate with Spring Boot
- **[SPRINGBOOT_PPTX_API_GUIDE.md](docs/SPRINGBOOT_PPTX_API_GUIDE.md)** - PowerPoint generation guide
- **[API_AUTHENTICATION.md](docs/API_AUTHENTICATION.md)** - API security setup
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker and cloud deployment
- **[VECTOR_STORE_ARCHITECTURE.md](docs/VECTOR_STORE_ARCHITECTURE.md)** - Vector store details

## 🔧 Performance Tuning

### Embedding Optimization
- **CUDA Support**: Auto-detects GPU availability, falls back to CPU
- **Batch Processing**: Configurable batch size (default 50)
- **Model**: paraphrase-multilingual-MiniLM-L12-v2 (384-dim, fast)

### Database Optimization
- **Async SQLAlchemy**: Non-blocking database operations
- **Connection Pooling**: Reuses database connections
- **Lazy Loading**: Only loads data when needed

### Vector Search Optimization
- **Qdrant Cloud**: Distributed, high-performance vector search
- **COSINE Distance**: Optimal for semantic similarity
- **Filtered Search**: Grade and subject filtering for faster queries

### API Performance
- **Async FastAPI**: Non-blocking request handling
- **Batch Endpoints**: Process multiple requests concurrently
- **Caching**: LLM and embedding caching (configurable)

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors (SQLAlchemy metadata)**
- The system uses `metadata_json` attribute mapped to `metadata` column to avoid SQLAlchemy reserved names.

**2. CUDA Not Available**
- Set `EMBEDDING_DEVICE=cpu` in `.env` or use `auto` for automatic detection.

**3. Qdrant Connection Failed**
- Verify `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
- Check Qdrant Cloud dashboard for cluster status

**4. Database Connection Issues**
- Ensure `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:port/db`
- Create tables using SQL scripts in documentation

**5. LangChain Deprecation Warnings**
- Warnings for `HuggingFaceEmbeddings`, `Chroma`, `Ollama` are known and non-blocking
- Plan to migrate to updated imports in future releases

## 🚀 Future Enhancements

- [ ] Migration to langchain-huggingface for embeddings
- [ ] Support for more LLM providers (Cohere, Together AI)
- [ ] Real-time streaming responses
- [ ] Advanced RAG techniques (HyDE, Multi-Query)
- [ ] Audio/video content processing
- [ ] Multi-modal embeddings
- [ ] GraphRAG implementation
- [ ] Fine-tuned models for Vietnamese education

## 🙏 Acknowledgments

- **LangChain** - RAG framework and orchestration
- **Qdrant** - High-performance vector database
- **Google Gemini** - LLM capabilities
- **Ollama** - Local LLM deployment
- **Sentence Transformers** - Multilingual embeddings
- **FastAPI** - Modern async web framework
- **SQLAlchemy** - Async ORM for Python
- **DuckDuckGo** - Privacy-focused web search

## 📊 Project Statistics

- **Total Documents**: 1,972+ textbook chunks
- **Grades Covered**: 3-12 (10 grades)
- **Embedding Dimension**: 384
- **Supported Subjects**: 6 (Computer Science, Math, Literature, Physics, Chemistry, Biology)
- **API Endpoints**: 11+
- **Slide Types**: 7
- **PowerPoint Layouts**: 9

---

**Made with ❤️ for Vietnamese Education** 🇻🇳

**Contributors:** [Your Team/Contributors]  
**License:** [Specify License]  
**Contact:** For questions or issues, please open an issue on GitHub or contact [your email].

---

### Quick Links
- 📖 [Full Documentation](docs/)
- 🐳 [Docker Deployment](DEPLOYMENT.md)
- 🔌 [Spring Boot Integration](docs/SPRING_BOOT_INTEGRATION.md)
- 🎨 [Slide API Guide](docs/SPRINGBOOT_PPTX_API_GUIDE.md)
