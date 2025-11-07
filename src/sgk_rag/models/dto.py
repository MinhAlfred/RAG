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


class PowerPointLayout(str, Enum):
    """PowerPoint slide layout types - matches Apache POI XSLFSlideLayout"""
    TITLE = "TITLE"  # Title slide
    TITLE_AND_CONTENT = "TITLE_AND_CONTENT"  # Title + body content
    SECTION_HEADER = "SECTION_HEADER"  # Section header
    TWO_CONTENT = "TWO_CONTENT"  # Title + two columns
    COMPARISON = "COMPARISON"  # Side by side comparison
    TITLE_ONLY = "TITLE_ONLY"  # Title only
    BLANK = "BLANK"  # Blank slide
    CONTENT_WITH_CAPTION = "CONTENT_WITH_CAPTION"  # Content with caption
    PICTURE_WITH_CAPTION = "PICTURE_WITH_CAPTION"  # Picture with caption


class PlaceholderType(str, Enum):
    """PowerPoint placeholder types - matches Apache POI Placeholder enum"""
    TITLE = "TITLE"  # Main title
    BODY = "BODY"  # Body text/content
    CENTERED_TITLE = "CENTERED_TITLE"  # Centered title
    SUBTITLE = "SUBTITLE"  # Subtitle
    DATE = "DATE"  # Date placeholder
    FOOTER = "FOOTER"  # Footer
    SLIDE_NUMBER = "SLIDE_NUMBER"  # Slide number
    CONTENT = "CONTENT"  # Generic content


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


class QuestionRequest(BaseModel):
    """Request model cho câu hỏi"""
    question: str = Field(..., description="Câu hỏi của người dùng", min_length=1)
    question_type: QuestionType = Field(default=QuestionType.GENERAL, description="Loại câu hỏi")
    grade_filter: Optional[int] = Field(None, description="Lọc theo lớp (3-12)", ge=3, le=12)
    return_sources: bool = Field(default=True, description="Có trả về nguồn tham khảo không")
    max_sources: int = Field(default=5, description="Số lượng nguồn tối đa", ge=1, le=10)
    collection_name: Optional[str] = Field(None, description="Tên collection trong Qdrant (mặc định: sgk_tin_kntt)")


class SlideRequest(BaseModel):
    """Request model cho tạo slide"""
    topic: str = Field(..., description="Chủ đề slide", min_length=1)
    grade: Optional[int] = Field(None, description="Lớp học (3-12)", ge=3, le=12)
    slide_count: int = Field(default=5, description="Số lượng slide", ge=1, le=20)
    format: SlideFormat = Field(default=SlideFormat.MARKDOWN, description="Định dạng output")
    include_examples: bool = Field(default=True, description="Có bao gồm ví dụ không")
    include_exercises: bool = Field(default=False, description="Có bao gồm bài tập không")
    collection_name: Optional[str] = Field(None, description="Tên collection trong Qdrant (mặc định: sgk_tin_kntt)")


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
    retrieval_mode: Optional[str] = Field(None, description="Chế độ trả lời (retrieval/fallback)")
    docs_retrieved: Optional[int] = Field(None, description="Số lượng tài liệu được tìm thấy")
    fallback_used: Optional[bool] = Field(None, description="Có sử dụng fallback không")
    web_search_used: Optional[bool] = Field(None, description="Có sử dụng tìm kiếm web không")


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


class BulletPoint(BaseModel):
    """Bullet point with formatting for Apache POI"""
    text: str = Field(..., description="Nội dung text")
    level: int = Field(default=0, description="Bullet level (0=main, 1=sub, 2=subsub)", ge=0, le=4)
    bold: bool = Field(default=False, description="In đậm")
    italic: bool = Field(default=False, description="In nghiêng")
    font_size: Optional[int] = Field(None, description="Font size in points", ge=8, le=72)


class TableCell(BaseModel):
    """Table cell data for Apache POI"""
    text: str = Field(..., description="Cell text content")
    bold: bool = Field(default=False, description="Bold text")
    background_color: Optional[str] = Field(None, description="Background color (hex: #RRGGBB)")
    align: TextAlignment = Field(default=TextAlignment.LEFT, description="Text alignment")


class TableData(BaseModel):
    """Table structure for Apache POI"""
    headers: List[str] = Field(..., description="Column headers")
    rows: List[List[TableCell]] = Field(..., description="Table rows with cell data")
    position: Optional[Position] = Field(None, description="Table position and size")
    has_header_row: bool = Field(default=True, description="First row is header")


class ImagePlaceholder(BaseModel):
    """Image placeholder for Apache POI"""
    placeholder_id: str = Field(..., description="Image placeholder identifier (e.g., {image1})")
    description: str = Field(..., description="Image description for context")
    suggested_search: Optional[str] = Field(None, description="Suggested search query for image")
    position: Position = Field(..., description="Image position and size")
    alt_text: Optional[str] = Field(None, description="Alternative text for accessibility")


class CodeBlock(BaseModel):
    """Code block with formatting for Apache POI"""
    code: str = Field(..., description="Code snippet")
    language: str = Field(default="python", description="Programming language")
    highlight_lines: Optional[List[int]] = Field(None, description="Line numbers to highlight")
    font_family: str = Field(default="Courier New", description="Monospace font")
    font_size: int = Field(default=10, description="Font size", ge=8, le=24)
    position: Optional[Position] = Field(None, description="Code block position")


class PlaceholderContent(BaseModel):
    """Content mapped to specific PowerPoint placeholder"""
    placeholder_type: PlaceholderType = Field(..., description="PowerPoint placeholder type")
    text_content: Optional[str] = Field(None, description="Plain text content")
    bullet_points: Optional[List[BulletPoint]] = Field(None, description="Formatted bullet points")
    alignment: TextAlignment = Field(default=TextAlignment.LEFT, description="Text alignment")


class JsonSlideContent(BaseModel):
    """Enhanced slide content for Apache POI PPTX generation"""
    slide_number: int = Field(..., description="Số thứ tự slide", ge=1)
    type: SlideType = Field(..., description="Loại slide")
    layout: PowerPointLayout = Field(..., description="PowerPoint layout type")

    # Placeholder-based content (PRIMARY - for Apache POI)
    placeholders: List[PlaceholderContent] = Field(default_factory=list, description="Content mapped to placeholders")

    # Legacy fields (for backward compatibility)
    title: str = Field(..., description="Tiêu đề slide")
    subtitle: Optional[str] = Field(None, description="Phụ đề (cho title slide)")
    content: Optional[Any] = Field(None, description="Nội dung chính - simple list of strings for backward compatibility")

    # Structured content (for complex slides)
    code_block: Optional[CodeBlock] = Field(None, description="Code block with formatting")
    table: Optional[TableData] = Field(None, description="Table data")
    images: Optional[List[ImagePlaceholder]] = Field(None, description="Image placeholders")

    # Metadata
    notes: Optional[str] = Field(None, description="Ghi chú cho giáo viên")
    key_points: Optional[List[str]] = Field(None, description="Các điểm chính")

    # Deprecated fields (kept for backward compatibility - DO NOT USE)
    code: Optional[str] = Field(None, description="[Deprecated] Use code_block.code instead")
    language: Optional[str] = Field(None, description="[Deprecated] Use code_block.language instead")
    explanation: Optional[str] = Field(None, description="[Deprecated] Use notes instead")
    image_placeholder: Optional[str] = Field(None, description="[Deprecated] Use images[] instead")
    caption: Optional[str] = Field(None, description="[Deprecated] Use images[].description instead")


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
    collection_name: Optional[str] = Field(None, description="Tên collection trong Qdrant (mặc định: sgk_tin_kntt)")


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
    "max_sources": 3,
    "collection_name": "sgk_tin_kntt"  # Optional: specify collection
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
            "layout": "TITLE",
            "placeholders": [
                {
                    "placeholder_type": "TITLE",
                    "text_content": "Kiểu dữ liệu trong Python",
                    "alignment": "CENTER"
                },
                {
                    "placeholder_type": "SUBTITLE",
                    "text_content": "Lớp 10 - Tin học",
                    "alignment": "CENTER"
                }
            ],
            "title": "Kiểu dữ liệu trong Python",
            "subtitle": "Lớp 10 - Tin học"
        },
        {
            "slide_number": 2,
            "type": "content_slide",
            "layout": "TITLE_AND_CONTENT",
            "placeholders": [
                {
                    "placeholder_type": "TITLE",
                    "text_content": "Các kiểu dữ liệu cơ bản",
                    "alignment": "LEFT"
                },
                {
                    "placeholder_type": "BODY",
                    "bullet_points": [
                        {"text": "int - Số nguyên (vd: 1, 2, -5)", "level": 0, "bold": True, "font_size": 18},
                        {"text": "float - Số thực (vd: 3.14, -0.5)", "level": 0, "bold": False, "font_size": 18},
                        {"text": "str - Chuỗi ký tự (vd: 'Hello')", "level": 0, "bold": False, "font_size": 18},
                        {"text": "bool - Giá trị logic (True/False)", "level": 0, "bold": False, "font_size": 18}
                    ],
                    "alignment": "LEFT"
                }
            ],
            "title": "Các kiểu dữ liệu cơ bản",
            "content": ["int - Số nguyên", "float - Số thực", "str - Chuỗi ký tự", "bool - Logic"],
            "notes": "Giải thích chi tiết: int dùng cho số không có phần thập phân, float cho số có phần thập phân, str cho văn bản, bool cho điều kiện đúng/sai"
        },
        {
            "slide_number": 3,
            "type": "code_slide",
            "layout": "TITLE_AND_CONTENT",
            "placeholders": [
                {
                    "placeholder_type": "TITLE",
                    "text_content": "Ví dụ minh họa",
                    "alignment": "LEFT"
                }
            ],
            "title": "Ví dụ minh họa",
            "code_block": {
                "code": "x = 10  # int\ny = 3.14  # float\nname = 'Python'  # str\nis_valid = True  # bool",
                "language": "python",
                "font_family": "Courier New",
                "font_size": 10,
                "position": {"x": 1.0, "y": 2.5, "width": 8.5, "height": 4.0}
            }
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