b"""Manually create database tables - Optional script"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.sgk_rag.core.database import get_db_manager
from config.settings import settings

async def create_tables():
    """Create database tables manually"""
    print("=" * 70)
    print("CREATING DATABASE TABLES")
    print("=" * 70)
    print()

    # Check database configuration
    has_db_config = (
        settings.DATABASE_URL or
        all([settings.user, settings.password, settings.host, settings.dbname])
    )

    if not has_db_config:
        print("[ERROR] Database not configured!")
        print()
        print("Please set in .env file:")
        print("  user=postgres.projectref")
        print("  password=your_password")
        print("  host=aws-region.pooler.supabase.com")
        print("  port=6543")
        print("  dbname=postgres")
        return

    print(f"Database host: {settings.host}")
    print(f"Database user: {settings.user}")
    print(f"Database name: {settings.dbname}")
    print()

    try:
        print("Connecting to database...")
        db_manager = get_db_manager()

        print("Creating tables...")
        await db_manager.create_tables()

        print()
        print("[SUCCESS] Tables created successfully!")
        print()
        print("Tables created:")
        print("  - conversations")
        print("  - chat_messages")
        print()
        print("=" * 70)
        print("Database is ready!")
        print("=" * 70)
        print()
        print("You can now:")
        print("1. Start the API server: python -m src.sgk_rag.api.main")
        print("2. Use chat endpoints: POST /chat/messages")
        print("3. Check API docs: http://localhost:8000/docs")

    except Exception as e:
        print()
        print(f"[ERROR] Failed to create tables: {e}")
        print()
        print("Common issues:")
        print("1. Wrong database credentials in .env")
        print("2. Database not accessible (network/firewall)")
        print("3. Insufficient permissions")
        print()
        print("Try running test script first:")
        print("  python test_db_connection.py")

if __name__ == "__main__":
    asyncio.run(create_tables())
