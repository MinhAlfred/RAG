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
from .eureka_config import EurekaConfig, register_with_eureka_async, stop_eureka_async


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
        print("\n" + "="*70)
        print("🚀 ĐANG KHỞI TẠO RAG PIPELINE")
        print("="*70)

        # Khởi tạo RAG pipeline với LLM từ settings
        # Sử dụng collection từ settings
        from config.settings import settings

        print(f"\n📊 Configuration:")
        print(f"   🤖 LLM Type: {settings.LLM_TYPE.upper()}")
        print(f"   🧠 Model: {settings.MODEL_NAME}")
        print(f"   📦 Collection: {settings.COLLECTION_NAME_PREFIX}")
        print(f"   🔢 Embedding: {settings.EMBEDDING_MODEL}")
        print(f"   💾 Vector Store: {settings.VECTOR_STORE_TYPE.upper()}")
        if settings.QDRANT_URL:
            print(f"   ☁️  Qdrant Cloud: Connected")
        print()

        rag_pipeline = RAGPipeline(
            vector_store_path="data/vectorstores",
            llm_type=settings.LLM_TYPE,
            model_name=settings.MODEL_NAME,
            collection_name=settings.COLLECTION_NAME_PREFIX
        )

        # Khởi tạo slide generator
        slide_generator = SlideGenerator(rag_pipeline)

        print("\n✅ RAG Pipeline đã sẵn sàng!")
        print("="*70)
        
        # Test pipeline
        print("\n🧪 Testing pipeline...")
        test_response = rag_pipeline.query("Máy tính là gì?")
        if isinstance(test_response, dict) and test_response.get('status') == 'success':
            answer = test_response.get('answer', '')
            print(f"✅ Test successful: {answer[:80]}...")
        else:
            print(f"⚠️  Test response: {str(test_response)[:80]}...")
        
        # Register with Eureka (if configured)
        try:
            eureka_config = EurekaConfig.from_env()
            await register_with_eureka_async(eureka_config, health_check_url="/health")
        except Exception as e:
            print(f"⚠️ Eureka registration skipped: {e}")
            print("   Service will run without service discovery")
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo RAG Pipeline: {e}")
        print(traceback.format_exc())
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup khi shutdown server"""
    try:
        print("🛑 Shutting down...")
        await stop_eureka_async()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Error during shutdown: {e}")


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
        from config.settings import settings
        model_info = {
            "llm_type": settings.LLM_TYPE,
            "model_name": settings.MODEL_NAME,
            "embedding_model": settings.EMBEDDING_MODEL
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
        
        # Query RAG pipeline với return_sources và collection_name
        response = rag_pipeline.query(
            request.question,
            grade_filter=request.grade_filter,
            return_sources=request.return_sources,
            collection_name=request.collection_name  # Use collection from request
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
                    max_sources=3,  # Giới hạn sources cho batch
                    collection_name=request.collection_name  # Pass collection name
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


@app.get("/collections")
async def get_available_collections():
    """Lấy danh sách collections có sẵn trong Qdrant"""
    try:
        from config.settings import settings
        from qdrant_client import QdrantClient

        # Connect to Qdrant
        if settings.QDRANT_URL:
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )

        # Get all collections
        collections = client.get_collections().collections

        collection_list = []
        for col in collections:
            try:
                info = client.get_collection(col.name)
                collection_list.append({
                    "name": col.name,
                    "points_count": info.points_count,
                    "vectors_count": info.vectors_count if hasattr(info, 'vectors_count') else info.points_count
                })
            except Exception as e:
                collection_list.append({
                    "name": col.name,
                    "points_count": 0,
                    "error": str(e)
                })

        return {
            "collections": collection_list,
            "total_collections": len(collection_list),
            "default_collection": settings.COLLECTION_NAME_PREFIX,
            "current_collection": rag_pipeline.collection_name if rag_pipeline else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collections: {str(e)}")


@app.get("/stats")
async def get_system_stats():
    """Lấy thống kê hệ thống"""
    try:
        if rag_pipeline is None:
            raise HTTPException(status_code=503, detail="RAG Pipeline chưa sẵn sàng")

        stats = rag_pipeline.get_statistics()

        return {
            "rag_pipeline": stats,
            "api_info": {
                "version": "1.0.0",
                "endpoints": [
                    "/ask", "/ask/batch", "/slides/generate",
                    "/health", "/stats", "/question/types", "/slides/formats", "/collections"
                ],
                "models": {
                    "llm": f"{settings.LLM_TYPE}/{settings.MODEL_NAME}",
                    "embedding": settings.EMBEDDING_MODEL
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    from config.settings import settings

    print("\n" + "="*70)
    print("🚀 STARTING SGK INFORMATICS RAG API")
    print("="*70)
    print(f"🤖 LLM: {settings.LLM_TYPE.upper()} - {settings.MODEL_NAME}")
    print(f"📦 Collection: {settings.COLLECTION_NAME_PREFIX}")
    print(f"🔗 API Docs: http://localhost:8000/docs")
    print(f"❤️  Health Check: http://localhost:8000/health")
    print("="*70 + "\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )