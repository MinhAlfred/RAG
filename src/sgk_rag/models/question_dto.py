"""Question Models - Request/Response models for Q&A functionality"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .base_dto import QuestionType, SourceInfo


class QuestionRequest(BaseModel):
    """Request model cho câu hỏi"""
    question: str = Field(..., description="Câu hỏi của người dùng", min_length=1)
    question_type: QuestionType = Field(default=QuestionType.GENERAL, description="Loại câu hỏi")
    grade_filter: Optional[int] = Field(None, description="Lọc theo lớp (3-12)", ge=3, le=12)
    return_sources: bool = Field(default=True, description="Có trả về nguồn tham khảo không")
    max_sources: int = Field(default=5, description="Số lượng nguồn tối đa", ge=1, le=10)
    collection_name: Optional[str] = Field(None, description="Tên collection trong Qdrant (mặc định: sgk_tin_kntt)")


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
    "collection_name": "sgk_tin_kntt"
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
