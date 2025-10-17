"""Data Models for Documents - Generic for all subjects"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class DocumentMetadata:
    """Document metadata - Generic for all subjects"""
    source_file: str
    subject: Optional[str] = None  # "Tin học", "Toán", "Văn", etc.
    subject_key: Optional[str] = None  # "tin_hoc", "toan", "van", etc.
    page_number: int = None
    grade: Optional[int] = None
    education_level: Optional[str] = None
    chapter: Optional[int] = None
    chapter_title: Optional[str] = None
    section: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    has_code: bool = False
    has_table: bool = False
    has_formula: bool = False  # For math, physics, chemistry
    has_diagram: bool = False  # For biology, physics
    extraction_method: str = "text"
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = {
            "source_file": self.source_file,
            "subject": self.subject,
            "subject_key": self.subject_key,
            "page_number": self.page_number,
            "grade": self.grade,
            "education_level": self.education_level,
            "chapter": self.chapter,
            "chapter_title": self.chapter_title,
            "section": self.section,
            "topics": self.topics,
            "has_code": self.has_code,
            "has_table": self.has_table,
            "has_formula": self.has_formula,
            "has_diagram": self.has_diagram,
            "extraction_method": self.extraction_method,
            "created_at": self.created_at.isoformat()
        }
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class Chunk:
    """Document chunk"""
    chunk_id: str
    content: str
    metadata: DocumentMetadata
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "token_count": self.token_count
        }