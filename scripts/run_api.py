#!/usr/bin/env python3
"""Script để chạy SGK RAG API Server"""

import sys
import os
from pathlib import Path

# Thêm project root vào Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Lên một cấp để đến project root
sys.path.insert(0, str(project_root))

try:
    import uvicorn
    from src.sgk_rag.api.main import app
    
    if __name__ == "__main__":
        print("🚀 Starting SGK Informatics RAG API Server...")
        print("📚 Sử dụng Ollama llama3.2:3b")
        print("🔗 API Documentation: http://localhost:8000/docs")
        print("🔗 ReDoc: http://localhost:8000/redoc")
        print("🔗 Health Check: http://localhost:8000/health")
        print("\n📋 Available Endpoints:")
        print("  - POST /ask - Hỏi câu hỏi đơn")
        print("  - POST /ask/batch - Hỏi nhiều câu hỏi")
        print("  - POST /slides/generate - Tạo slides")
        print("  - GET /health - Kiểm tra trạng thái")
        print("  - GET /stats - Thống kê hệ thống")
        print("  - GET /question/types - Loại câu hỏi")
        print("  - GET /slides/formats - Format slides")
        print("\n" + "="*50)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # Tắt reload để tránh lỗi
            log_level="info",
            access_log=True
        )
        
except ImportError as e:
    print(f"❌ Lỗi import: {e}")
    print("💡 Hãy đảm bảo đã cài đặt các dependencies:")
    print("   pip install fastapi uvicorn")
    sys.exit(1)
except Exception as e:
    print(f"❌ Lỗi khởi động server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)