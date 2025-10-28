"""FastAPI Server - API cho RAG Q&A và Slide Generation"""

import time
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.rag_pipeline import RAGPipeline
from ..models.dto import (
    QuestionRequest, QuestionResponse, SlideRequest, SlideResponse,
    HealthResponse, ErrorResponse, BatchQuestionRequest, BatchQuestionResponse,
    SourceInfo, SlideContent, QuestionType, SlideFormat,
    JsonSlideResponse  # Import JSON response model
)
from .slide_generator import SlideGenerator


# Khởi tạo FastAPI app
app = FastAPI(
    title="SGK Informatics RAG API",
    description="API cho hệ thống RAG Q&A và tạo slide từ SGK Tin học",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
rag_pipeline: RAGPipeline = None
slide_generator: SlideGenerator = None


@app.on_event("startup")
async def startup_event():
    """Khởi tạo RAG pipeline khi start server"""
    global rag_pipeline, slide_generator
    
    try:
        print("🚀 Đang khởi tạo RAG Pipeline...")
        
        # Khởi tạo RAG pipeline với Ollama llama3.2:3b
        # Sử dụng collection sgk_tin (tất cả lớp 3-12)
        rag_pipeline = RAGPipeline(
            vector_store_path="data/vectorstores",
            llm_type="ollama",
            model_name="llama3.2:3b",
            collection_name="sgk_tin"
        )
        
        # Khởi tạo slide generator
        slide_generator = SlideGenerator(rag_pipeline)
        
        print("✅ RAG Pipeline đã sẵn sàng!")
        
        # Test pipeline
        test_response = rag_pipeline.query("Máy tính là gì?")
        if isinstance(test_response, str):
            print(f"🧪 Test query thành công: {test_response[:100]}...")
        else:
            print(f"🧪 Test query thành công: {str(test_response)[:100]}...")
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo RAG Pipeline: {e}")
        print(traceback.format_exc())
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            status_code=500,
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "SGK Informatics RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Kiểm tra RAG pipeline
        if rag_pipeline is None:
            raise HTTPException(status_code=503, detail="RAG Pipeline chưa được khởi tạo")
        
        # Lấy thông tin vector store
        vector_store_info = {}
        try:
            stats = rag_pipeline.get_stats()
            vector_store_info = {
                "total_chunks": stats.get("total_chunks", 0),
                "embedding_dim": stats.get("embedding_dim", 0),
                "index_type": stats.get("index_type", "unknown")
            }
        except:
            vector_store_info = {"status": "unavailable"}
        
        # Thông tin model
        model_info = {
            "llm_type": "ollama",
            "model_name": "llama3.2:3b",
            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        }
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            rag_status="ready",
            vector_store_info=vector_store_info,
            model_info=model_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Endpoint để hỏi câu hỏi"""
    start_time = time.time()
    
    try:
        if rag_pipeline is None:
            raise HTTPException(status_code=503, detail="RAG Pipeline chưa sẵn sàng")
        
        # Query RAG pipeline với return_sources
        response = rag_pipeline.query(
            request.question,
            grade_filter=request.grade_filter,
            return_sources=request.return_sources
        )
        
        # Extract answer và sources từ response
        if isinstance(response, dict):
            answer = response.get('answer', str(response))
            # Sources đã được trả về từ query() nếu return_sources=True
            sources_data = response.get('sources', [])
            
            # Convert sources sang SourceInfo format
            sources = []
            if request.return_sources and sources_data:
                for src in sources_data:
                    metadata = src.get('metadata', {})
                    # Convert grade to string (metadata có thể chứa int hoặc str)
                    grade_value = metadata.get("grade", "Không xác định")
                    grade_str = str(grade_value) if grade_value is not None else "Không xác định"
                    
                    sources.append(
                        SourceInfo(
                            content=src.get('content', ''),
                            grade=grade_str,
                            lesson_title=metadata.get("lesson_title", "Không xác định") or "Không xác định",
                            score=float(metadata.get('score', 0.0)),
                            chunk_id=metadata.get("chunk_id")
                        )
                    )
        else:
            answer = str(response)
            sources = []
        
        processing_time = time.time() - start_time
        
        return QuestionResponse(
            question=request.question,
            answer=answer,
            status="success",
            sources=sources if request.return_sources else None,
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"Lỗi khi xử lý câu hỏi: {e}")
        
        return QuestionResponse(
            question=request.question,
            answer="",
            status="error",
            sources=None,
            processing_time=processing_time,
            error=str(e)
        )


@app.post("/ask/batch", response_model=BatchQuestionResponse)
async def ask_batch_questions(request: BatchQuestionRequest):
    """Endpoint để hỏi nhiều câu hỏi cùng lúc"""
    start_time = time.time()
    
    try:
        if rag_pipeline is None:
            raise HTTPException(status_code=503, detail="RAG Pipeline chưa sẵn sàng")
        
        results = []
        successful = 0
        failed = 0
        
        for question in request.questions:
            try:
                # Tạo QuestionRequest cho từng câu hỏi
                q_request = QuestionRequest(
                    question=question,
                    question_type=request.question_type,
                    grade_filter=request.grade_filter,
                    return_sources=request.return_sources,
                    max_sources=3  # Giới hạn sources cho batch
                )
                
                # Gọi ask_question
                response = await ask_question(q_request)
                results.append(response)
                
                if response.status == "success":
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                results.append(QuestionResponse(
                    question=question,
                    answer="",
                    status="error",
                    error=str(e),
                    processing_time=0
                ))
        
        total_time = time.time() - start_time
        
        return BatchQuestionResponse(
            results=results,
            total_questions=len(request.questions),
            successful=successful,
            failed=failed,
            processing_time=total_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@app.post("/slides/generate", response_model=SlideResponse)
async def generate_slides(request: SlideRequest):
    """Endpoint để tạo slides (legacy - trả về SlideResponse)"""
    start_time = time.time()
    
    try:
        if slide_generator is None:
            raise HTTPException(status_code=503, detail="Slide Generator chưa sẵn sàng")
        
        # Nếu format là JSON, redirect tới JSON endpoint
        if request.format == SlideFormat.JSON:
            return JSONResponse(
                content={
                    "error": "Use /slides/generate/json endpoint for JSON format",
                    "redirect": "/slides/generate/json"
                },
                status_code=400
            )
        
        # Tạo slides
        slides = slide_generator.generate_slides(request)
        
        # Format slides theo yêu cầu
        formatted_content = slide_generator.format_slides(slides, request.format)
        
        # Cập nhật content của slides với formatted content nếu cần
        if request.format != SlideFormat.MARKDOWN:
            # Tạo một slide tổng hợp cho các format khác
            summary_slide = SlideContent(
                slide_number=0,
                title=f"Slides - {request.topic}",
                content=formatted_content,
                notes=f"Slides được format theo {request.format.value}",
                sources=[]
            )
            slides = [summary_slide]
        
        processing_time = time.time() - start_time
        
        return SlideResponse(
            topic=request.topic,
            slides=slides,
            format=request.format,
            total_slides=len(slides),
            grade_level=f"Lớp {request.grade}" if request.grade else None,
            status="success",
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"Lỗi khi tạo slides: {e}")
        print(traceback.format_exc())
        
        return SlideResponse(
            topic=request.topic,
            slides=[],
            format=request.format,
            total_slides=0,
            grade_level=f"Lớp {request.grade}" if request.grade else None,
            status="error",
            processing_time=processing_time,
            error=str(e)
        )


@app.post("/slides/generate/json", response_model=JsonSlideResponse)
async def generate_slides_json(request: SlideRequest):
    """
    Endpoint để tạo slides với JSON structure - dành cho Spring Boot integration
    
    Trả về structured JSON với:
    - Typed slides (title, content, code, image, exercise)
    - Flexible content (string, list, dict)
    - Metadata (duration, sources, timestamp)
    - Type-safe với Pydantic models
    """
    try:
        if slide_generator is None:
            raise HTTPException(status_code=503, detail="Slide Generator chưa sẵn sàng")
        
        # Tạo slides với JSON structure
        json_response = slide_generator.generate_slides_json(request)
        
        return json_response
        
    except Exception as e:
        print(f"Lỗi khi tạo JSON slides: {e}")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate JSON slides: {str(e)}"
        )


@app.get("/slides/formats")
async def get_slide_formats():
    """Lấy danh sách các format slide hỗ trợ"""
    return {
        "formats": [
            {"value": "markdown", "label": "Markdown", "description": "Format Markdown chuẩn"},
            {"value": "html", "label": "HTML", "description": "HTML với CSS styling"},
            {"value": "powerpoint", "label": "PowerPoint Guide", "description": "Hướng dẫn tạo PowerPoint"},
            {"value": "text", "label": "Plain Text", "description": "Text thuần không format"},
            {
                "value": "json",
                "label": "JSON Structure",
                "description": "Structured JSON cho Spring Boot integration (use /slides/generate/json endpoint)"
            }
        ]
    }


@app.get("/question/types")
async def get_question_types():
    """Lấy danh sách các loại câu hỏi hỗ trợ"""
    return {
        "types": [
            {"value": "general", "label": "Câu hỏi chung", "description": "Câu hỏi thông thường"},
            {"value": "slide", "label": "Tạo slide", "description": "Yêu cầu tạo nội dung slide"},
            {"value": "explain", "label": "Giải thích", "description": "Giải thích khái niệm"},
            {"value": "example", "label": "Ví dụ", "description": "Yêu cầu ví dụ cụ thể"}
        ]
    }


@app.get("/stats")
async def get_system_stats():
    """Lấy thống kê hệ thống"""
    try:
        if rag_pipeline is None:
            raise HTTPException(status_code=503, detail="RAG Pipeline chưa sẵn sàng")
        
        stats = rag_pipeline.get_stats()
        
        return {
            "rag_pipeline": stats,
            "api_info": {
                "version": "1.0.0",
                "endpoints": [
                    "/ask", "/ask/batch", "/slides/generate", 
                    "/health", "/stats", "/question/types", "/slides/formats"
                ],
                "models": {
                    "llm": "ollama/llama3.2:3b",
                    "embedding": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting SGK Informatics RAG API...")
    print("📚 Sử dụng Ollama llama3.2:3b")
    print("🔗 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )