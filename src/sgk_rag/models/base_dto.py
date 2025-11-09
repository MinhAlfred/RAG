"""Base Models - Common enums and base classes"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class QuestionType(str, Enum):
    """Loại câu hỏi"""
    GENERAL = "general"  # Câu hỏi chung
    SLIDE = "slide"      # Tạo nội dung slide
    EXPLAIN = "explain"  # Giải thích khái niệm
    EXAMPLE = "example"  # Yêu cầu ví dụ


class TextAlignment(str, Enum):
    """Text alignment for Apache POI"""
    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"
    JUSTIFY = "JUSTIFY"


class Position(BaseModel):
    """Position and size for elements (images, shapes, tables)"""
    x: float = Field(..., description="X coordinate in inches")
    y: float = Field(..., description="Y coordinate in inches")
    width: float = Field(..., description="Width in inches")
    height: float = Field(..., description="Height in inches")


class SourceInfo(BaseModel):
    """Thông tin nguồn tham khảo"""
    content: str = Field(..., description="Nội dung trích dẫn")
    grade: str = Field(..., description="Lớp học")
    lesson_title: str = Field(..., description="Tiêu đề bài học")
    score: float = Field(..., description="Điểm tương đồng")
    chunk_id: Optional[str] = Field(None, description="ID của chunk")


class HealthResponse(BaseModel):
    """Response model cho health check"""
    status: str = Field(..., description="Trạng thái hệ thống")
    version: str = Field(..., description="Phiên bản API")
    rag_status: str = Field(..., description="Trạng thái RAG pipeline")
    vector_store_info: Dict[str, Any] = Field(..., description="Thông tin vector store")
    model_info: Dict[str, str] = Field(..., description="Thông tin model")


class ErrorResponse(BaseModel):
    """Response model cho lỗi"""
    error: str = Field(..., description="Thông báo lỗi")
    detail: Optional[str] = Field(None, description="Chi tiết lỗi")
    status_code: int = Field(..., description="Mã lỗi HTTP")
    timestamp: str = Field(..., description="Thời gian xảy ra lỗi")
