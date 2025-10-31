"""Script to create vector store from processed chunks"""

import sys
import argparse
from pathlib import Path
from typing import List
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from config.settings import settings
from config import logging_config
from src.sgk_rag.core.vector_store import VectorStoreManager
from src.sgk_rag.core.embedding_manager import EmbeddingManager

logger = logging_config.setup_logging(log_level="INFO", log_dir=settings.LOG_DIR)


def create_vectorstore_from_file(
        json_file: Path,
        collection_name: str,
        embedding_model: str,
        store_type: str
):
    """Create vector store from a single JSON file"""

    # Initialize managers
    embedding_manager = EmbeddingManager(model_name=embedding_model)
    vector_manager = VectorStoreManager(
        store_type=store_type,
        embedding_manager=embedding_manager,
        collection_name=collection_name
    )

    # Load chunks
    chunks = vector_manager.load_chunks_from_json(json_file)

    # Create vector store
    vectorstore = vector_manager.create_vectorstore(
        chunks,
        collection_name=collection_name,
        batch_size=50
    )

    # Get statistics
    stats = vector_manager.get_statistics(vectorstore)

    logger.info(f"\n📊 Statistics:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")

    return vectorstore, vector_manager


def create_vectorstores_batch(
        processed_dir: Path,
        embedding_model: str,
        store_type: str,
        organize_by_subject: bool = True
):
    """Create vector stores for all processed chunks"""

    # Find all chunk files
    json_files = list(processed_dir.rglob("*_chunks.json"))

    if not json_files:
        logger.error(f"No chunk files found in {processed_dir}")
        return

    logger.info(f"\n{'=' * 70}")
    logger.info(f"🚀 BATCH VECTOR STORE CREATION")
    logger.info(f"{'=' * 70}")
    logger.info(f"Found {len(json_files)} chunk files\n")

    # Initialize embedding manager once (reuse for all)
    embedding_manager = EmbeddingManager(model_name=embedding_model)

    created_stores = []

    for idx, json_file in enumerate(json_files, 1):
        logger.info(f"\n[{idx}/{len(json_files)}] Processing: {json_file.name}")
        logger.info(f"{'─' * 70}")

        # Determine collection name
        if organize_by_subject:
            # Extract subject and grade from filename or parent folder
            if json_file.parent.name in settings.SUPPORTED_SUBJECTS:
                subject = json_file.parent.name
            else:
                subject = "general"

            # Extract grade from filename
            grade_match = re.search(r'lop_(\d+)', json_file.stem)
            grade = grade_match.group(1) if grade_match else "unknown"

            collection_name = f"{subject}_lop_{grade}"
        else:
            collection_name = json_file.stem.replace("_chunks", "")

        try:
            vector_manager = VectorStoreManager(
                store_type=store_type,
                embedding_manager=embedding_manager,
                collection_name=collection_name
            )

            # Load and create
            chunks = vector_manager.load_chunks_from_json(json_file)
            vectorstore = vector_manager.create_vectorstore(
                chunks,
                collection_name=collection_name,
                batch_size=50
            )

            stats = vector_manager.get_statistics(vectorstore)
            logger.info(f"   ✓ Created: {collection_name} ({stats.get('total_documents', 'N/A')} docs)")

            created_stores.append({
                'file': json_file.name,
                'collection': collection_name,
                'stats': stats
            })

        except Exception as e:
            logger.error(f"   ❌ Error: {e}", exc_info=True)
            continue

    # Summary
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ BATCH CREATION COMPLETED!")
    logger.info(f"{'=' * 70}")
    logger.info(f"   Successfully created: {len(created_stores)} vector stores")
    logger.info(f"   Output directory: {settings.VECTORSTORE_DIR}/")


def test_search(vectorstore, vector_manager, queries: List[str] = None):
    """Test search functionality"""

    if queries is None:
        queries = [
            "Thuật toán là gì?",
            "Cách sử dụng vòng lặp trong Python",
            "Giải phương trình bậc 2"
        ]

    logger.info(f"\n{'=' * 70}")
    logger.info(f"🔍 TESTING SEARCH")
    logger.info(f"{'=' * 70}\n")

    for query in queries:
        logger.info(f"Query: '{query}'")
        logger.info(f"{'─' * 70}")

        results = vector_manager.search(vectorstore, query, k=3)

        for i, doc in enumerate(results, 1):
            logger.info(f"\n   [{i}] Page: {doc.metadata.get('page_number', 'N/A')}")
            logger.info(f"       Subject: {doc.metadata.get('subject', 'N/A')}")
            logger.info(f"       Grade: {doc.metadata.get('grade', 'N/A')}")
            logger.info(f"       Content: {doc.page_content[:150]}...")

        logger.info("")


def main():
    parser = argparse.ArgumentParser(
        description="Create vector stores from processed chunks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create from single file
  python scripts/create_vectorstore.py data/processed/tin_hoc_lop_10_chunks.json

  # Batch create from directory
  python scripts/create_vectorstore.py data/processed/ --batch

  # Use OpenAI embeddings
  python scripts/create_vectorstore.py data/processed/ --batch --embedding openai

  # Use FAISS instead of Chroma
  python scripts/create_vectorstore.py data/processed/ --batch --store-type faiss

  # Test search after creation
  python scripts/create_vectorstore.py data/processed/tin_hoc_lop_10_chunks.json --test-search
        """
    )

    parser.add_argument(
        "input",
        type=str,
        help="Input chunk JSON file or directory"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all files in directory"
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default=None,
        help="Collection name (auto-generated if not specified)"
    )
    parser.add_argument(
        "--embedding",
        type=str,
        choices=["openai", "multilingual", "vietnamese"],
        default="multilingual",
        help="Embedding model (default: multilingual)"
    )
    parser.add_argument(
        "--store-type",
        type=str,
        choices=["chroma", "faiss", "qdrant"],
        default="qdrant",
        help="Vector store type (default: qdrant)"
    )
    parser.add_argument(
        "--test-search",
        action="store_true",
        help="Test search after creation"
    )
    parser.add_argument(
        "--no-organize",
        action="store_true",
        help="Don't organize by subject (batch mode)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        logger.error(f"Input not found: {input_path}")
        return

    if args.batch:
        # Batch mode
        if not input_path.is_dir():
            logger.error("Batch mode requires a directory")
            return

        create_vectorstores_batch(
            input_path,
            embedding_model=args.embedding,
            store_type=args.store_type,
            organize_by_subject=not args.no_organize
        )

    else:
        # Single file mode
        if not input_path.is_file():
            logger.error("Single file mode requires a JSON file")
            return

        # Auto-generate collection name if not provided
        if not args.collection_name:
            args.collection_name = input_path.stem.replace("_chunks", "")

        vectorstore, vector_manager = create_vectorstore_from_file(
            input_path,
            collection_name=args.collection_name,
            embedding_model=args.embedding,
            store_type=args.store_type
        )

        # Test search if requested
        if args.test_search:
            test_search(vectorstore, vector_manager)

    logger.info(f"\n💡 Next step: Query the vector store")
    logger.info(f"   python scripts/query_rag.py")


if __name__ == "__main__":
    main()