"""API Models - Pydantic models for request/response"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class QuestionType(str, Enum):
    """Loại câu hỏi"""
    GENERAL = "general"  # Câu hỏi chung
    SLIDE = "slide"      # Tạo nội dung slide
    EXPLAIN = "explain"  # Giải thích khái niệm
    EXAMPLE = "example"  # Yêu cầu ví dụ


class SlideFormat(str, Enum):
    """Định dạng slide"""
    POWERPOINT = "powerpoint"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    JSON = "json"  # JSON structure format


class SlideType(str, Enum):
    """Loại slide"""
    TITLE = "title_slide"
    CONTENT = "content_slide"
    CODE = "code_slide"
    IMAGE = "image_slide"
    TABLE = "table_slide"
    EXERCISE = "exercise_slide"
    SUMMARY = "summary_slide"


class QuestionRequest(BaseModel):
    """Request model cho câu hỏi"""
    question: str = Field(..., description="Câu hỏi của người dùng", min_length=1)
    question_type: QuestionType = Field(default=QuestionType.GENERAL, description="Loại câu hỏi")
    grade_filter: Optional[int] = Field(None, description="Lọc theo lớp (3-12)", ge=3, le=12)
    return_sources: bool = Field(default=True, description="Có trả về nguồn tham khảo không")
    max_sources: int = Field(default=5, description="Số lượng nguồn tối đa", ge=1, le=10)


class SlideRequest(BaseModel):
    """Request model cho tạo slide"""
    topic: str = Field(..., description="Chủ đề slide", min_length=1)
    grade: Optional[int] = Field(None, description="Lớp học (3-12)", ge=3, le=12)
    slide_count: int = Field(default=5, description="Số lượng slide", ge=1, le=20)
    format: SlideFormat = Field(default=SlideFormat.MARKDOWN, description="Định dạng output")
    include_examples: bool = Field(default=True, description="Có bao gồm ví dụ không")
    include_exercises: bool = Field(default=False, description="Có bao gồm bài tập không")


class SourceInfo(BaseModel):
    """Thông tin nguồn tham khảo"""
    content: str = Field(..., description="Nội dung trích dẫn")
    grade: str = Field(..., description="Lớp học")
    lesson_title: str = Field(..., description="Tiêu đề bài học")
    score: float = Field(..., description="Điểm tương đồng")
    chunk_id: Optional[str] = Field(None, description="ID của chunk")


class QuestionResponse(BaseModel):
    """Response model cho câu hỏi"""
    question: str = Field(..., description="Câu hỏi gốc")
    answer: str = Field(..., description="Câu trả lời")
    status: str = Field(..., description="Trạng thái (success/error)")
    sources: Optional[List[SourceInfo]] = Field(None, description="Danh sách nguồn tham khảo")
    processing_time: Optional[float] = Field(None, description="Thời gian xử lý (giây)")
    error: Optional[str] = Field(None, description="Thông báo lỗi nếu có")


class SlideContent(BaseModel):
    """Nội dung một slide"""
    slide_number: int = Field(..., description="Số thứ tự slide")
    title: str = Field(..., description="Tiêu đề slide")
    content: str = Field(..., description="Nội dung slide")
    notes: Optional[str] = Field(None, description="Ghi chú cho slide")
    sources: Optional[List[str]] = Field(None, description="Nguồn tham khảo")


# New JSON Structure Models for Spring Boot Integration
class JsonSlideMetadata(BaseModel):
    """Metadata cho slide JSON"""
    total_slides: int = Field(..., description="Tổng số slides")
    estimated_duration: str = Field(..., description="Thời gian dự kiến (phút)")
    sources: List[str] = Field(default_factory=list, description="Nguồn tài liệu")
    generated_at: str = Field(..., description="Thời gian tạo (ISO format)")
    grade_level: Optional[str] = Field(None, description="Lớp học")


class JsonSlideContent(BaseModel):
    """Nội dung slide cho JSON format - flexible content type"""
    slide_number: int = Field(..., description="Số thứ tự slide", ge=1)
    type: SlideType = Field(..., description="Loại slide")
    title: str = Field(..., description="Tiêu đề slide")
    
    # Flexible content - can be string, list, or dict
    content: Optional[Any] = Field(None, description="Nội dung chính - có thể là string, list bullets, hoặc structured data")
    subtitle: Optional[str] = Field(None, description="Phụ đề (cho title slide)")
    
    # Code-specific fields
    code: Optional[str] = Field(None, description="Code snippet (cho code slide)")
    language: Optional[str] = Field(None, description="Ngôn ngữ lập trình")
    
    # Image-specific fields
    image_placeholder: Optional[str] = Field(None, description="Placeholder cho hình ảnh (vd: {image1})")
    caption: Optional[str] = Field(None, description="Chú thích hình ảnh")
    
    # Common fields
    explanation: Optional[str] = Field(None, description="Giải thích chi tiết")
    notes: Optional[str] = Field(None, description="Ghi chú cho giáo viên")
    key_points: Optional[List[str]] = Field(None, description="Các điểm chính")


class JsonSlideResponse(BaseModel):
    """Response model cho JSON structure - dành cho Spring Boot"""
    title: str = Field(..., description="Tiêu đề bài giảng")
    topic: str = Field(..., description="Chủ đề")
    grade: Optional[int] = Field(None, description="Lớp học (3-12)")
    slides: List[JsonSlideContent] = Field(..., description="Danh sách slides")
    metadata: JsonSlideMetadata = Field(..., description="Metadata")
    status: str = Field(default="success", description="Trạng thái")
    processing_time: Optional[float] = Field(None, description="Thời gian xử lý (giây)")
    error: Optional[str] = Field(None, description="Thông báo lỗi nếu có")


class SlideResponse(BaseModel):
    """Response model cho tạo slide"""
    topic: str = Field(..., description="Chủ đề slide")
    slides: List[SlideContent] = Field(..., description="Danh sách slides")
    format: SlideFormat = Field(..., description="Định dạng output")
    total_slides: int = Field(..., description="Tổng số slides")
    grade_level: Optional[str] = Field(None, description="Cấp độ lớp học")
    status: str = Field(..., description="Trạng thái (success/error)")
    processing_time: Optional[float] = Field(None, description="Thời gian xử lý (giây)")
    error: Optional[str] = Field(None, description="Thông báo lỗi nếu có")


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


class BatchQuestionRequest(BaseModel):
    """Request model cho nhiều câu hỏi"""
    questions: List[str] = Field(..., description="Danh sách câu hỏi", min_items=1, max_items=10)
    question_type: QuestionType = Field(default=QuestionType.GENERAL, description="Loại câu hỏi")
    grade_filter: Optional[int] = Field(None, description="Lọc theo lớp (3-12)", ge=3, le=12)
    return_sources: bool = Field(default=False, description="Có trả về nguồn tham khảo không")


class BatchQuestionResponse(BaseModel):
    """Response model cho nhiều câu hỏi"""
    results: List[QuestionResponse] = Field(..., description="Kết quả các câu hỏi")
    total_questions: int = Field(..., description="Tổng số câu hỏi")
    successful: int = Field(..., description="Số câu hỏi thành công")
    failed: int = Field(..., description="Số câu hỏi thất bại")
    processing_time: float = Field(..., description="Tổng thời gian xử lý (giây)")


# Example data for API documentation
EXAMPLE_QUESTION_REQUEST = {
    "question": "Máy tính là gì?",
    "question_type": "general",
    "grade_filter": None,
    "return_sources": True,
    "max_sources": 3
}

EXAMPLE_SLIDE_REQUEST = {
    "topic": "Phần cứng máy tính",
    "grade": 6,
    "slide_count": 5,
    "format": "markdown",
    "include_examples": True,
    "include_exercises": False
}

EXAMPLE_JSON_SLIDE_RESPONSE = {
    "title": "Kiểu dữ liệu trong Python",
    "topic": "Python Data Types",
    "grade": 10,
    "slides": [
        {
            "slide_number": 1,
            "type": "title_slide",
            "title": "Kiểu dữ liệu trong Python",
            "subtitle": "Lớp 10 - Tin học"
        },
        {
            "slide_number": 2,
            "type": "content_slide",
            "title": "Các kiểu dữ liệu cơ bản",
            "content": [
                "int (số nguyên)",
                "float (số thực)",
                "str (xâu ký tự)",
                "bool (logic)"
            ],
            "notes": "Giải thích chi tiết cho giáo viên"
        },
        {
            "slide_number": 3,
            "type": "code_slide",
            "title": "Ví dụ minh họa",
            "code": "x = 10  # int\ny = 3.14  # float\nname = 'Python'  # str\nis_valid = True  # bool",
            "language": "python",
            "explanation": "Khai báo biến với các kiểu khác nhau"
        }
    ],
    "metadata": {
        "total_slides": 3,
        "estimated_duration": "15 phút",
        "sources": ["SGK Tin học 10", "Chương 2"],
        "generated_at": "2025-10-28T15:48:00Z",
        "grade_level": "Lớp 10"
    },
    "status": "success",
    "processing_time": 2.5
}

EXAMPLE_QUESTION_RESPONSE = {
    "question": "Máy tính là gì?",
    "answer": "Máy tính là thiết bị điện tử có khả năng xử lý thông tin theo các chương trình được lập trình sẵn...",
    "status": "success",
    "sources": [
        {
            "content": "Máy tính là thiết bị điện tử...",
            "grade": "6",
            "lesson_title": "Giới thiệu về máy tính",
            "score": 0.95,
            "chunk_id": "chunk_001"
        }
    ],
    "processing_time": 1.23
}