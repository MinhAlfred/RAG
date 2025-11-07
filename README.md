# 🎓 Multi-Subject RAG System for Vietnamese Education

**Advanced Retrieval-Augmented Generation (RAG) System for Vietnamese K-12 Education**

A comprehensive AI-powered educational assistant that combines semantic search, LLM capabilities, and automated slide generation to support Vietnamese textbooks across multiple subjects (Computer Science, Math, Literature, Physics, Chemistry, Biology) for grades 3-12.

## 🌟 Key Features

### Core Capabilities
- **🔍 Intelligent Q&A**: Context-aware answers using RAG with web search fallback
- **📊 Automated Slide Generation**: Create educational presentations with structured JSON output
- **🌐 Hybrid Knowledge Retrieval**: Combines textbook knowledge base + live web search
- **📚 Multi-Subject Support**: Computer Science, Math, Literature, Physics, Chemistry, Biology
- **🎯 Grade-Specific Filtering**: Target content for grades 3-12
- **🚀 Production-Ready API**: FastAPI with OpenAPI documentation

### Technical Features
- **Vector Search**: Qdrant vector database with semantic embeddings
- **Multiple LLM Support**: Ollama (local), Google Gemini, OpenAI, Anthropic
- **OCR Processing**: Extract text from PDF textbooks (Tesseract + OpenCV)
- **Service Discovery**: Eureka integration for microservices architecture
- **Batch Processing**: Handle multiple questions concurrently
- **Type-Safe Models**: Pydantic models for all API requests/responses

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server (main.py)                 │
│   /ask, /slides/generate, /health, /stats, /collections     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ RAG Pipeline │ │  Slide   │ │   Eureka     │
│              │ │Generator │ │   Client     │
└──────┬───────┘ └────┬─────┘ └──────────────┘
       │              │
   ┌───┴──────────────┴────┐
   │                       │
   ▼                       ▼
┌────────────────┐  ┌─────────────┐
│ Vector Store   │  │   LLM       │
│   (Qdrant)     │  │  (Gemini/   │
│ + Embeddings   │  │   Ollama)   │
└────────────────┘  └─────────────┘
```

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
GOOGLE_API_KEY=your_key_here       # For Gemini (optional)
OPENAI_API_KEY=your_key_here       # For OpenAI (optional)

# === Vector Store ===
VECTOR_STORE_TYPE=qdrant           # qdrant | chroma | faiss
COLLECTION_NAME=sgk_tin            # Default collection

# === Qdrant Configuration ===
# Option 1: Qdrant Cloud (Recommended)
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_api_key

# Option 2: Local Qdrant
# QDRANT_HOST=localhost
# QDRANT_PORT=6333

# === Embeddings ===
EMBEDDING_MODEL=multilingual       # multilingual | vietnamese | openai
EMBEDDING_DEVICE=cuda              # cuda | cpu

# === Service Discovery ===
EUREKA_SERVER=http://localhost:8761/eureka/
APP_NAME=python-rag-service
APP_PORT=8000
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

**POST /ask/batch** - Ask multiple questions
```json
{
  "questions": ["Câu hỏi 1", "Câu hỏi 2"],
  "question_type": "general",
  "grade_filter": 10,
  "return_sources": false
}
```

#### 2. Slide Generation

**POST /slides/generate/json** - Generate structured slides (for PowerPoint/Spring Boot)
```json
{
  "topic": "Kiểu dữ liệu trong Python",
  "grade": 10,
  "slide_count": 5,
  "format": "json",
  "include_examples": true,
  "include_exercises": false
}
```

**Response:** Structured JSON with slide types, layouts, placeholders, code blocks, tables, and images.

**POST /slides/generate** - Generate slides (legacy formats: markdown, html, text)

#### 3. System Information

- **GET /health** - Health check and system status
- **GET /stats** - Detailed system statistics
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
│   ├── api/               # FastAPI application
│   │   ├── main.py       # API routes and server
│   │   ├── slide_generator.py  # Slide generation logic
│   │   └── eureka_config.py    # Eureka integration
│   ├── core/              # Core RAG components
│   │   ├── rag_pipeline.py       # Main RAG pipeline
│   │   ├── vector_store.py       # Vector store management
│   │   ├── embedding_manager.py  # Embedding generation
│   │   ├── web_search.py         # Web search integration
│   │   └── document_processor*.py # PDF/OCR processing
│   └── models/            # Data models
│       ├── dto.py         # API request/response models
│       └── document.py    # Document/chunk models
├── scripts/               # Utility scripts
├── data/                  # Data directory
│   ├── raw/              # Raw textbooks (PDFs)
│   ├── processed/        # Processed documents
│   └── vectorstores/     # Vector store data
└── tests/                # Test suite
```

## 🌐 Web Search Integration

The system automatically combines:
1. **Knowledge Base Search**: Semantic search in textbook vector store
2. **Web Search**: DuckDuckGo search for recent/supplementary information

Configuration in `config/settings.py`:
```python
WEB_SEARCH_MAX_RESULTS = 3    # Number of web results
WEB_SEARCH_REGION = "vn-vi"   # Vietnam region
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

### Supported Slide Types
- **title_slide**: Title and subtitle
- **content_slide**: Title + bullet points
- **code_slide**: Code examples with syntax highlighting
- **image_slide**: Image placeholders with descriptions
- **table_slide**: Structured tables
- **exercise_slide**: Practice exercises
- **summary_slide**: Key takeaways

### PowerPoint Layouts
Supports Apache POI-compatible layouts:
- TITLE, TITLE_AND_CONTENT, SECTION_HEADER
- TWO_CONTENT, COMPARISON, TITLE_ONLY
- BLANK, CONTENT_WITH_CAPTION, PICTURE_WITH_CAPTION

### Output Formats
- **JSON**: Structured data for Spring Boot/PowerPoint generation
- **Markdown**: Human-readable format
- **HTML**: Web-ready presentation
- **Text**: Plain text format

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

# Ask a question
response = requests.post("http://localhost:8000/ask", json={
    "question": "Thuật toán sắp xếp nổi bọt hoạt động như thế nào?",
    "grade_filter": 11,
    "return_sources": true
})
print(response.json()["answer"])

# Generate slides
response = requests.post("http://localhost:8000/slides/generate/json", json={
    "topic": "Biến và kiểu dữ liệu trong Python",
    "grade": 10,
    "slide_count": 8,
    "include_examples": true
})
slides = response.json()
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Ask question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Máy tính là gì?", "return_sources": true}'

# List collections
curl http://localhost:8000/collections
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

[Specify your license here]

## 🙏 Acknowledgments

- LangChain for RAG framework
- Qdrant for vector database
- Google Gemini for LLM capabilities
- Sentence Transformers for embeddings

---

**Made with ❤️ for Vietnamese Education** 🇻🇳

For questions or issues, please open an issue on GitHub.
