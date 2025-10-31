"""Test Qdrant Cloud Connection"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from config.settings import settings

def test_qdrant_connection():
    """Test connection to Qdrant Cloud"""

    print("=" * 70)
    print("Testing Qdrant Cloud Connection")
    print("=" * 70)

    # Display configuration
    print(f"\n📋 Configuration:")
    print(f"   URL: {settings.QDRANT_URL}")
    print(f"   API Key: {'*' * 40}{settings.QDRANT_API_KEY[-10:] if settings.QDRANT_API_KEY else 'Not set'}")
    print(f"   Prefer gRPC: {settings.QDRANT_PREFER_GRPC}")

    try:
        # Initialize client
        print(f"\n🔌 Connecting to Qdrant Cloud...")

        if settings.QDRANT_URL:
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                prefer_grpc=settings.QDRANT_PREFER_GRPC,
                timeout=30  # 30 seconds timeout
            )
        else:
            print("❌ Error: QDRANT_URL is not set in .env file")
            return False

        # Test connection by getting collections
        print(f"✅ Connected successfully!")

        # Get collections
        collections = client.get_collections()
        print(f"\n📚 Collections in your Qdrant Cloud:")

        if collections.collections:
            for col in collections.collections:
                print(f"   • {col.name}")

                # Get collection details
                try:
                    info = client.get_collection(col.name)
                    print(f"      - Points: {info.points_count}")
                    print(f"      - Vectors: {info.config.params.vectors.size}D")
                    print(f"      - Distance: {info.config.params.vectors.distance.name}")
                except Exception as e:
                    print(f"      - Error getting details: {e}")
        else:
            print(f"   No collections found. You can create one by running:")
            print(f"   python scripts/create_vectorstore.py")

        # Test collection creation (optional)
        print(f"\n✨ Connection test passed!")
        print(f"\n💡 Next steps:")
        print(f"   1. Install dependencies: pip install -r requirements.txt")
        print(f"   2. Create vector store: python scripts/create_vectorstore.py")
        print(f"   3. Start API server: python -m uvicorn src.sgk_rag.api.main:app --reload")

        return True

    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"   Error: {str(e)}")
        print(f"\n🔍 Troubleshooting:")
        print(f"   1. Check your QDRANT_URL in .env file")
        print(f"   2. Verify your QDRANT_API_KEY is correct")
        print(f"   3. Ensure your Qdrant Cloud cluster is active")
        print(f"   4. Check your internet connection")
        print(f"   5. Try visiting: {settings.QDRANT_URL.replace(':6333', '')}/dashboard")

        return False

if __name__ == "__main__":
    success = test_qdrant_connection()
    sys.exit(0 if success else 1)
