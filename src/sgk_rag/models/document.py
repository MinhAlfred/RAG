"""Data Models for Documents - Generic for all subjects"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


# =========================================================
# Document Metadata
# =========================================================
@dataclass
class DocumentMetadata:
    source_file: str
    subject: Optional[str] = None
    subject_key: Optional[str] = None
    page_number: int = None
    grade: Optional[int] = None
    education_level: Optional[str] = None

    # Thêm các field bị thiếu
    chapter_number: Optional[int] = None
    chapter_title: Optional[str] = None
    chapter: Optional[str] = None

    lesson_number: Optional[int] = None
    lesson_title: Optional[str] = None

    section: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    has_code: bool = False
    has_table: bool = False
    has_formula: bool = False
    has_diagram: bool = False
    extraction_method: str = "text"
    created_at: datetime = field(default_factory=datetime.now)


    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        # Các trường quan trọng luôn giữ lại (kể cả None) để hỗ trợ query/filter
        important_fields = {
            "chapter_number", "chapter_title", "chapter", 
            "lesson_number", "lesson_title", "section"
        }
        
        data = {
            "source_file": self.source_file,
            "subject": self.subject,
            "subject_key": self.subject_key,
            "page_number": self.page_number,
            "grade": self.grade,
            "education_level": self.education_level,
            "chapter_number": self.chapter_number,
            "chapter_title": self.chapter_title,
            "chapter": self.chapter,
            "lesson_number": self.lesson_number,
            "lesson_title": self.lesson_title,
            "section": self.section,
            "topics": self.topics,
            "has_code": self.has_code,
            "has_table": self.has_table,
            "has_formula": self.has_formula,
            "has_diagram": self.has_diagram,
            "extraction_method": self.extraction_method,
            "created_at": self.created_at.isoformat()
        }
        # Giữ lại các trường quan trọng ngay cả khi None, loại bỏ các trường khác nếu None
        return {k: v for k, v in data.items() if v is not None or k in important_fields}

# =========================================================
# Chunk Object
# =========================================================
@dataclass
class Chunk:
    """Represents a processed text chunk from document"""

    chunk_id: str
    content: str
    metadata: DocumentMetadata
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert chunk to serializable dictionary"""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "token_count": self.token_count,
        }
