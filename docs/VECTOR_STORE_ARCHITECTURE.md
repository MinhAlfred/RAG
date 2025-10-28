# Vector Store Architecture - Kiến trúc Vector Store

## Tổng quan

Hệ thống RAG hiện tại có **2 cách tạo và load vector store** song song. Document này giải thích lý do và cách sử dụng.

---

## 🏗️ Hai Hệ thống Vector Store

### 1. **VectorStoreManager** (LangChain-based) - ✅ ĐƯỢC KHUYẾN NGHỊ

**File**: `src/sgk_rag/core/vector_store.py`

#### Đặc điểm:
- Sử dụng LangChain's Chroma hoặc FAISS
- Tích hợp tốt với LangChain ecosystem
- Hỗ trợ metadata filtering
- Persist directory: `data/vectorstores/`

#### Cấu trúc thư mục:
```
data/vectorstores/
├── chroma_db/
│   └── sgk_tin_hoc/
│       ├── chroma.sqlite3
│       └── <collection_id>/
└── faiss_index/
    └── sgk_tin_hoc/
        ├── index.faiss
        └── index.pkl
```

#### Cách sử dụng:
```python
from src.sgk_rag.core.vector_store import VectorStoreManager
from src.sgk_rag.core.embedding_manager import EmbeddingManager

# Initialize
embedding_mgr = EmbeddingManager()
vector_mgr = VectorStoreManager(
    store_type="chroma",  # hoặc "faiss"
    embedding_manager=embedding_mgr
)

# Load chunks
chunks = vector_mgr.load_chunks_from_json("data/processed/sgk_tin_hoc_10_chunks.json")

# Create vector store
vectorstore = vector_mgr.create_vectorstore(chunks, collection_name="sgk_tin_hoc_10")

# Load existing
vectorstore = vector_mgr.load_vectorstore(collection_name="sgk_tin_hoc_10")

# Search với metadata filter
results = vector_mgr.search(
    vectorstore,
    query="Thuật toán là gì?",
    k=5,
    filter_dict={"grade": 10}
)
```

---

### 2. **VectorStoreCreator/Loader** (Custom FAISS) - ⚠️ LEGACY

**File**: `scripts/create_vector_store.py`

#### Đặc điểm:
- FAISS thuần túy, không qua LangChain
- Sử dụng SentenceTransformers trực tiếp
- Lưu metadata riêng trong JSON
- Persist directory: `data/vector_store/`

#### Cấu trúc thư mục:
```
data/vector_store/
├── faiss_index.bin          # Binary FAISS index
├── chunks_metadata.json     # Metadata của tất cả chunks
├── embeddings.npy           # Embeddings (optional, for debug)
└── vector_store_info.json   # Thông tin về vector store
```

#### Cách sử dụng:
```python
from scripts.create_vector_store import VectorStoreCreator, VectorStoreLoader

# Create (one-time)
creator = VectorStoreCreator()
stats = creator.create_vector_store(
    processed_dir="data/processed",
    output_dir="data/vector_store"
)

# Load
loader = VectorStoreLoader("data/vector_store")
loader.load()

# Search
results = loader.search("Thuật toán là gì?", k=5, grade_filter=10)
```

---

## 🔄 Tích hợp trong RAGPipeline

### Trước đây (có vấn đề):

```python
def _load_vector_store(self):
    try:
        # Thử VectorStoreManager trước
        vectorstore = self.vector_manager.load_vectorstore()
        if vectorstore:
            return vectorstore
    except:
        pass
    
    # Fallback: load từ scripts (❌ VI PHẠM KIẾN TRÚC)
    from scripts.create_vector_store import VectorStoreLoader
    loader = VectorStoreLoader(self.vector_store_path)
    return loader
```

**Vấn đề:**
1. ❌ Import từ `scripts/` vào `src/` (vi phạm separation of concerns)
2. ❌ Không nhất quán - không biết đang dùng hệ thống nào
3. ❌ Khó maintain khi có 2 cách hoạt động khác nhau

### Hiện tại (đã sửa):

```python
def _load_vector_store(self):
    """
    Chỉ dùng VectorStoreManager (LangChain-based)
    Đây là cách chuẩn và nhất quán
    """
    try:
        vectorstore = self.vector_manager.load_vectorstore()
        if vectorstore:
            return vectorstore
        else:
            raise Exception("load_vectorstore() returned None")
    except Exception as e:
        logger.error(f"Failed to load: {e}")
        logger.error("💡 Create vector store first!")
        raise
```

**Ưu điểm:**
1. ✅ Kiến trúc rõ ràng
2. ✅ Dễ debug khi có lỗi
3. ✅ Nhất quán với LangChain ecosystem

---

## 📋 So sánh Chi tiết

| Tiêu chí | VectorStoreManager | VectorStoreCreator |
|----------|-------------------|-------------------|
| **Framework** | LangChain | Custom FAISS |
| **Backend** | Chroma/FAISS | FAISS only |
| **Embedding** | LangChain embeddings | SentenceTransformers |
| **Metadata** | In vector store | Separate JSON |
| **Filtering** | ✅ Native support | ⚠️ Manual filter |
| **LangChain integration** | ✅ Seamless | ❌ Manual conversion |
| **Persist dir** | `data/vectorstores/` | `data/vector_store/` |
| **Use in RAG** | ✅ Recommended | ⚠️ Legacy |

---

## 🎯 Khuyến nghị Sử dụng

### Cho dự án mới:
👉 **Sử dụng `VectorStoreManager`** (LangChain-based)

### Nếu đã có vector store cũ:
1. **Migration**: Convert sang LangChain format
2. **Hoặc**: Tiếp tục dùng `VectorStoreLoader` nhưng tách riêng

### Ví dụ Migration:

```python
# Load từ old format
from scripts.create_vector_store import VectorStoreLoader
old_loader = VectorStoreLoader("data/vector_store")
old_loader.load()

# Load chunks
chunks = old_loader.chunks_metadata

# Create new format
from src.sgk_rag.core.vector_store import VectorStoreManager
vector_mgr = VectorStoreManager(store_type="chroma")

# Convert chunks to proper format
from src.sgk_rag.models.document import Chunk, DocumentMetadata
new_chunks = []
for c in chunks:
    metadata = DocumentMetadata(**c['metadata'])
    chunk = Chunk(
        chunk_id=c['chunk_id'],
        content=c['content'],
        metadata=metadata,
        token_count=c.get('token_count')
    )
    new_chunks.append(chunk)

# Create new vector store
vectorstore = vector_mgr.create_vectorstore(new_chunks, "sgk_collection")
```

---

## 🐛 Troubleshooting

### Lỗi: "Vector store not found"

**Nguyên nhân**: Chưa tạo vector store hoặc sai đường dẫn

**Giải pháp**:
```bash
# Check thư mục
ls data/vectorstores/chroma_db/
ls data/vector_store/

# Tạo mới nếu chưa có
python scripts/create_vectorstore.py --input data/processed --output data/vectorstores
```

### Lỗi: "Could not load from core modules"

**Nguyên nhân**: Vector store được tạo bằng hệ thống khác

**Giải pháp**: Kiểm tra xem đang có vector store ở đâu và migration nếu cần

---

## 📚 Tài liệu liên quan

- [LangChain Vector Stores](https://python.langchain.com/docs/modules/data_connection/vectorstores/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
