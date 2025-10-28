"""Test vector search để debug vấn đề similarity search"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sgk_rag.core.vector_store import VectorStoreManager
from src.sgk_rag.core.embedding_manager import EmbeddingManager
from config.logging_config import setup_logging

logger = setup_logging(log_level="INFO")


def main():
    logger.info("=" * 70)
    logger.info("🔍 Testing Vector Search")
    logger.info("=" * 70)
    
    # Initialize managers
    logger.info("\n1️⃣ Khởi tạo Embedding Manager...")
    embedding_mgr = EmbeddingManager(model_name="multilingual", device="cuda")
    
    logger.info("2️⃣ Khởi tạo Vector Store Manager...")
    vector_mgr = VectorStoreManager(
        store_type="chroma",
        embedding_manager=embedding_mgr,
        collection_name="sgk_tin",
        persist_directory=Path("data/vectorstores")
    )
    
    logger.info("3️⃣ Load vector store...")
    vectorstore = vector_mgr.load_vectorstore()
    
    # Test queries
    queries = [
        "kiểu dữ liệu trong python",
        "liệt kê kiểu dữ liệu python",
        "int float str bool list tuple dict",
        "biến và kiểu dữ liệu",
    ]
    
    for query in queries:
        logger.info(f"\n{'='*70}")
        logger.info(f"🔎 Query: '{query}'")
        logger.info(f"{'='*70}")
        
        # Search using vector store
        results = vector_mgr.search(
            vectorstore=vectorstore,
            query=query,
            k=5
        )
        
        logger.info(f"📊 Found {len(results)} results:")
        
        for i, doc in enumerate(results, 1):
            metadata = doc.metadata
            content_preview = doc.page_content[:150].replace('\n', ' ')
            
            logger.info(f"\n   Result {i}:")
            logger.info(f"      Grade: {metadata.get('grade', 'N/A')}")
            logger.info(f"      Lesson: {metadata.get('lesson_title', 'N/A')}")
            logger.info(f"      Chapter: {metadata.get('chapter_title', 'N/A')}")
            logger.info(f"      Subject: {metadata.get('subject', 'N/A')}")
            logger.info(f"      Chunk ID: {metadata.get('chunk_id', 'N/A')}")
            logger.info(f"      Content: {content_preview}...")
    
    # Get collection stats
    logger.info(f"\n{'='*70}")
    logger.info("📊 Collection Statistics:")
    logger.info(f"{'='*70}")
    
    stats = vector_mgr.get_statistics(vectorstore)
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    
    logger.info("\n✅ Test completed!")


if __name__ == "__main__":
    main()
