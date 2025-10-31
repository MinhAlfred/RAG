"""
Simple script to upload chunks to Qdrant Cloud
This is a simplified version specifically for Qdrant Cloud deployment
"""

import sys
import json
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main(collection_name_override: str = None):
    print("=" * 80)
    print("🚀 Qdrant Cloud Upload Script")
    print("=" * 80)

    # Step 1: Import dependencies
    print("\n[1/6] Importing dependencies...")
    try:
        from config.settings import settings
        from src.sgk_rag.core.vector_store import VectorStoreManager
        from src.sgk_rag.core.embedding_manager import EmbeddingManager
        print("✅ Dependencies imported successfully")
    except Exception as e:
        print(f"❌ Error importing dependencies: {e}")
        print("\n💡 Make sure you've installed all requirements:")
        print("   pip install -r requirements.txt")
        return False

    # Step 2: Verify configuration
    print("\n[2/6] Verifying Qdrant Cloud configuration...")
    if not settings.QDRANT_URL:
        print("❌ QDRANT_URL not set in .env file")
        print("💡 Add this to your .env file:")
        print("   QDRANT_URL=https://fc13446b-1e9b-468c-a9d5-c2437c304a5e.us-west-1-0.aws.cloud.qdrant.io:6333")
        return False

    if not settings.QDRANT_API_KEY:
        print("❌ QDRANT_API_KEY not set in .env file")
        print("💡 Add this to your .env file:")
        print("   QDRANT_API_KEY=your-api-key-here")
        return False

    print(f"✅ Qdrant URL: {settings.QDRANT_URL}")
    print(f"✅ API Key: {'*' * 40}{settings.QDRANT_API_KEY[-10:]}")

    # Step 3: Test connection
    print("\n[3/6] Testing connection to Qdrant Cloud...")
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30
        )

        # Test connection
        collections = client.get_collections()
        print(f"✅ Connected successfully!")
        print(f"   Existing collections: {len(collections.collections)}")
        for col in collections.collections:
            info = client.get_collection(col.name)
            print(f"   - {col.name}: {info.points_count} points")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify your QDRANT_URL is correct")
        print("   3. Verify your QDRANT_API_KEY is correct")
        print("   4. Check Qdrant Cloud status: https://status.qdrant.io/")
        return False

    # Step 4: Find chunk files
    print("\n[4/6] Looking for chunk files...")

    # Try data/chunks first, then data/processed
    chunks_dir = project_root / "data" / "chunks"
    if not chunks_dir.exists():
        chunks_dir = project_root / "data" / "processed"

    if not chunks_dir.exists():
        print(f"❌ Chunks directory not found: {chunks_dir}")
        print("\n💡 You need to process your documents first:")
        print("   python scripts/process_documents.py")
        return False

    chunk_files = list(chunks_dir.rglob("*_chunks.json"))

    if not chunk_files:
        print(f"❌ No chunk files found in {chunks_dir}")
        print("\n💡 Process your documents first to create chunks:")
        print("   python scripts/process_documents.py --input data/raw/your_file.txt")
        return False

    print(f"✅ Found {len(chunk_files)} chunk file(s):")
    for i, f in enumerate(chunk_files, 1):
        file_size = f.stat().st_size / 1024  # KB
        print(f"   {i}. {f.name} ({file_size:.1f} KB)")

    # Step 5: Initialize embedding manager
    print(f"\n[5/6] Initializing embedding model ({settings.EMBEDDING_MODEL})...")
    print("⏳ This may take 30-60 seconds on first run (downloading model)...")

    try:
        embedding_manager = EmbeddingManager(
            model_name=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )

        # Test embedding
        test_vec = embedding_manager.embed_query("test")
        print(f"✅ Embedding model ready (dimension: {len(test_vec)})")

    except Exception as e:
        print(f"❌ Error initializing embedding model: {e}")
        return False

    # Step 6: Upload chunks to Qdrant Cloud
    print(f"\n[6/6] Uploading chunks to Qdrant Cloud...")

    collection_name = collection_name_override or settings.COLLECTION_NAME_PREFIX or "sgk_tin"
    print(f"   Collection: {collection_name}")

    try:
        # Initialize vector store manager
        vector_manager = VectorStoreManager(
            store_type="qdrant",
            embedding_manager=embedding_manager,
            collection_name=collection_name
        )

        # Process each file
        all_chunks = []
        for chunk_file in chunk_files:
            print(f"\n   📄 Loading: {chunk_file.name}")
            chunks = vector_manager.load_chunks_from_json(chunk_file)
            print(f"      ✓ Loaded {len(chunks)} chunks")
            all_chunks.extend(chunks)

        print(f"\n   📊 Total chunks to upload: {len(all_chunks)}")
        print(f"   ⏳ Creating embeddings and uploading to Qdrant Cloud...")
        print(f"      This may take several minutes depending on data size...")

        start_time = time.time()

        # Create vector store (this will upload to Qdrant Cloud)
        vectorstore = vector_manager.create_vectorstore(
            chunks=all_chunks,
            collection_name=collection_name,
            batch_size=50
        )

        elapsed = time.time() - start_time

        print(f"\n   ✅ Upload completed in {elapsed:.1f} seconds!")

        # Get statistics
        stats = vector_manager.get_statistics(vectorstore)
        print(f"\n   📊 Collection Statistics:")
        print(f"      - Collection: {stats.get('collection_name')}")
        print(f"      - Total documents: {stats.get('total_documents')}")
        print(f"      - Vector dimension: {stats.get('dimension')}")
        print(f"      - Distance metric: {stats.get('distance')}")

        # Test search
        print(f"\n   🔍 Testing search...")
        results = vector_manager.search(vectorstore, "Máy tính là gì?", k=3)
        print(f"      ✓ Search working! Found {len(results)} results")

        if results:
            print(f"\n      Top result:")
            print(f"      - Grade: {results[0].metadata.get('grade', 'N/A')}")
            print(f"      - Lesson: {results[0].metadata.get('lesson_title', 'N/A')}")
            print(f"      - Content: {results[0].page_content[:100]}...")

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        print("\n" + traceback.format_exc())
        return False

    # Success!
    print("\n" + "=" * 80)
    print("🎉 SUCCESS! Your data is now in Qdrant Cloud!")
    print("=" * 80)
    print(f"\n✨ Next steps:")
    print(f"   1. View your data: https://cloud.qdrant.io/")
    print(f"   2. Start the API server:")
    print(f"      python -m uvicorn src.sgk_rag.api.main:app --reload --port 8000")
    print(f"   3. Test the API:")
    print(f"      curl http://localhost:8000/health")
    print(f"      curl -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{{\"question\": \"Máy tính là gì?\"}}'")

    return True


if __name__ == "__main__":
    import sys

    # Check for collection name argument
    collection_name = None
    if len(sys.argv) > 1:
        collection_name = sys.argv[1]
        print(f"📝 Using custom collection name: {collection_name}")

    try:
        success = main(collection_name_override=collection_name)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
