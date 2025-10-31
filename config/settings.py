"""Configuration Management - Generic cho mọi môn học"""

from pathlib import Path
from typing import Optional, Literal, Dict, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application Settings"""

    # Project
    PROJECT_NAME: str = "Multi-Subject RAG System"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    VECTORSTORE_DIR: Path = DATA_DIR / "vectorstores"
    LOG_DIR: Path = BASE_DIR / "logs"

    # OCR Settings
    OCR_ENABLED: bool = False
    OCR_LANGUAGE: str = "vie+eng"
    OCR_DPI: int = 300

    # Document Processing
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    MIN_CHUNK_SIZE: int = 50

    # Subject Configuration (có thể mở rộng)
    SUPPORTED_SUBJECTS: Dict[str, Dict] = {
        "tin_hoc": {
            "name": "Tin học",
            "aliases": ["tin học", "computer science", "informatics", "cntt"],
            "keywords": [
                "thuật toán", "lập trình", "python", "biến", "hàm",
                "vòng lặp", "điều kiện", "mảng", "chuỗi", "file",
                "cấu trúc dữ liệu", "máy tính", "internet"
            ],
            "chapter_patterns": [
                r'Chương\s+(\d+)[:\s.]*(.+)',
                r'CHƯƠNG\s+([IVXLCDM]+)[:\s.]*(.+)',
            ],
            "section_patterns": [
                r'Bài\s+(\d+)[:\s.]*(.+)',
                r'§\s*(\d+)[:\s.]*(.+)',
            ]
        },
        "toan": {
            "name": "Toán",
            "aliases": ["toán", "toán học", "math", "mathematics"],
            "keywords": [
                "phương trình", "bất phương trình", "hàm số", "đạo hàm",
                "tích phân", "hình học", "tam giác", "đường tròn",
                "véc tơ", "ma trận", "số học", "đại số"
            ],
            "chapter_patterns": [
                r'Chương\s+(\d+)[:\s.]*(.+)',
                r'CHƯƠNG\s+([IVXLCDM]+)[:\s.]*(.+)',
            ],
            "section_patterns": [
                r'Bài\s+(\d+)[:\s.]*(.+)',
                r'§\s*(\d+)[:\s.]*(.+)',
                r'Tiết\s+(\d+)[:\s.]*(.+)',
            ]
        },
        "van": {
            "name": "Ngữ văn",
            "aliases": ["ngữ văn", "văn", "literature"],
            "keywords": [
                "văn học", "thơ", "truyện", "tiểu thuyết", "tác giả",
                "nhân vật", "tác phẩm", "văn bản", "nghệ thuật",
                "phong cách", "tu từ", "biểu đạt"
            ],
            "chapter_patterns": [
                r'Phần\s+(\d+)[:\s.]*(.+)',
                r'PHẦN\s+([IVXLCDM]+)[:\s.]*(.+)',
            ],
            "section_patterns": [
                r'Bài\s+(\d+)[:\s.]*(.+)',
                r'Văn bản\s+(\d+)[:\s.]*(.+)',
            ]
        },
        "ly": {
            "name": "Vật lý",
            "aliases": ["vật lý", "vật lí", "physics"],
            "keywords": [
                "lực", "áp suất", "nhiệt", "quang học", "điện",
                "từ trường", "sóng", "dao động", "năng lượng",
                "chuyển động", "vận tốc", "gia tốc"
            ],
            "chapter_patterns": [
                r'Chương\s+(\d+)[:\s.]*(.+)',
            ],
            "section_patterns": [
                r'Bài\s+(\d+)[:\s.]*(.+)',
                r'§\s*(\d+)[:\s.]*(.+)',
            ]
        },
        "hoa": {
            "name": "Hóa học",
            "aliases": ["hóa học", "hóa", "chemistry"],
            "keywords": [
                "nguyên tố", "phản ứng", "hóa học", "hợp chất",
                "dung dịch", "axit", "bazơ", "muối", "oxi hóa",
                "khử", "ion", "electron", "mol"
            ],
            "chapter_patterns": [
                r'Chương\s+(\d+)[:\s.]*(.+)',
            ],
            "section_patterns": [
                r'Bài\s+(\d+)[:\s.]*(.+)',
            ]
        },
        "sinh": {
            "name": "Sinh học",
            "aliases": ["sinh học", "sinh", "biology"],
            "keywords": [
                "tế bào", "di truyền", "tiến hóa", "sinh thái",
                "hệ sinh thái", "quang hợp", "hô hấp", "protein",
                "adn", "arn", "gen", "nhiễm sắc thể"
            ],
            "chapter_patterns": [
                r'Chương\s+(\d+)[:\s.]*(.+)',
            ],
            "section_patterns": [
                r'Bài\s+(\d+)[:\s.]*(.+)',
            ]
        },
        # Có thể thêm môn khác...
    }

    # LLM Settings
    LLM_TYPE: Literal["ollama", "openai", "anthropic", "gemini"] = "ollama"
    MODEL_NAME: str = "llama3.2:3b"

    # Google Gemini Settings
    GOOGLE_API_KEY: Optional[str] = None
    
    # Embedding Settings
    EMBEDDING_MODEL: Literal["openai", "multilingual", "vietnamese"] = "multilingual"
    EMBEDDING_BATCH_SIZE: int = 50
    EMBEDDING_DEVICE: str = "cuda"  # "cpu" or "cuda" - Dùng GPU để tăng tốc

    # Vector Store
    VECTOR_STORE_TYPE: Literal["chroma", "faiss", "qdrant"] = "qdrant"
    COLLECTION_NAME_PREFIX: str = "sgk_tin"  # Collection tất cả lớp 3-12
    COLLECTION_NAME: str = "sgk_tin"  # Alias for backward compatibility
    VECTOR_STORE_PATH: str = "data/vectorstores"

    # Qdrant Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_URL: Optional[str] = None  # For cloud: "https://xxx.qdrant.io"
    QDRANT_PREFER_GRPC: bool = False  # Use gRPC for better performance

    # API Keys
    OPENAI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        for dir_path in [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.VECTORSTORE_DIR,
            self.LOG_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_subject_config(self, subject_key: str) -> Optional[Dict]:
        """Get configuration for a subject"""
        return self.SUPPORTED_SUBJECTS.get(subject_key)

    def detect_subject_from_filename(self, filename: str) -> Optional[str]:
        """Auto-detect subject from filename"""
        filename_lower = filename.lower()

        for subject_key, config in self.SUPPORTED_SUBJECTS.items():
            # Check subject name and aliases
            for alias in config['aliases']:
                if alias in filename_lower:
                    return subject_key

        return None


settings = Settings()