"""
Tạo vector store từ TẤT CẢ các chunks trong data/processed
Collection name: sgk_tin
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sgk_rag.core.vector_store import VectorStoreManager
from src.sgk_rag.core.embedding_manager import EmbeddingManager
from config.logging_config import setup_logging
from config.settings import settings

logger = setup_logging(log_level="INFO")


def main():
    logger.info("=" * 70)
    logger.info("🚀 TẠO VECTOR STORE TỪ TẤT CẢ CHUNKS")
    logger.info("=" * 70)
    
    # Tìm tất cả file chunks
    processed_dir = Path("data/processed")
    chunk_files = list(processed_dir.glob("*_chunks.json"))
    
    if not chunk_files:
        logger.error(f"❌ Không tìm thấy file chunks nào trong {processed_dir}")
        return
    
    logger.info(f"📁 Tìm thấy {len(chunk_files)} file chunks:")
    for f in chunk_files:
        logger.info(f"   - {f.name}")
    
    # Khởi tạo managers
    logger.info("\n🔧 Khởi tạo Embedding Manager...")
    embedding_manager = EmbeddingManager(
        model_name="multilingual",
        device="cuda"  # Dùng GPU
    )
    
    logger.info("🔧 Khởi tạo Vector Store Manager...")
    vector_manager = VectorStoreManager(
        store_type="chroma",
        embedding_manager=embedding_manager,
        collection_name="sgk_tin",
        persist_directory=Path("data/vectorstores")
    )
    
    # Load tất cả chunks
    logger.info("\n📖 Đang load tất cả chunks...")
    all_chunks = []
    
    for chunk_file in chunk_files:
        logger.info(f"   Loading {chunk_file.name}...")
        chunks = vector_manager.load_chunks_from_json(chunk_file)
        all_chunks.extend(chunks)
    
    logger.info(f"\n✅ Tổng cộng: {len(all_chunks):,} chunks")
    
    # Tạo vector store
    logger.info("\n🎯 Đang tạo vector store 'sgk_tin'...")
    logger.info("⚠️  Quá trình này có thể mất vài phút...")
    
    vectorstore = vector_manager.create_vectorstore(
        chunks=all_chunks,
        collection_name="sgk_tin",
        batch_size=50  # Batch size nhỏ hơn để tránh quá tải GPU
    )
    
    # Thống kê
    logger.info("\n" + "=" * 70)
    logger.info("✅ HOÀN THÀNH!")
    logger.info("=" * 70)
    
    stats = vector_manager.get_statistics(vectorstore)
    logger.info(f"📊 Thống kê:")
    logger.info(f"   Collection: sgk_tin")
    logger.info(f"   Total documents: {stats.get('total_documents', 'N/A')}")
    logger.info(f"   Location: data/vectorstores/chroma_db/sgk_tin")
    
    # Phân bố theo lớp
    grade_count = {}
    for chunk in all_chunks:
        grade = chunk.metadata.grade if hasattr(chunk.metadata, 'grade') else chunk.metadata.get('grade', 'Unknown')
        grade_count[grade] = grade_count.get(grade, 0) + 1
    
    logger.info(f"\n📚 Phân bố theo lớp:")
    for grade in sorted(grade_count.keys()):
        logger.info(f"   Lớp {grade}: {grade_count[grade]:,} chunks")
    
    logger.info("\n🎉 Vector store đã sẵn sàng để sử dụng!")
    logger.info("💡 Bây giờ có thể chạy API server với collection 'sgk_tin'")


if __name__ == "__main__":
    main()
