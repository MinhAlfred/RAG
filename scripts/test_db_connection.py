"""Test Database Connection - Verify Supabase PostgreSQL connection"""

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port", "5432")
DBNAME = os.getenv("dbname")

print("=" * 70)
print("TESTING DATABASE CONNECTION")
print("=" * 70)
print(f"User: {USER}")
print(f"Host: {HOST}")
print(f"Port: {PORT}")
print(f"Database: {DBNAME}")
print(f"Password: {'*' * len(PASSWORD) if PASSWORD else 'NOT SET'}")
print()

# Connect to the database
try:
    print("Attempting to connect...")
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        connect_timeout=10  # 10 second timeout
    )
    print("[SUCCESS] Connection successful!")
    print()

    # Create a cursor to execute SQL queries
    cursor = connection.cursor()

    # Test query 1: Get current time
    print("Test 1: Fetching current time...")
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"   Current Time: {result[0]}")
    print()

    # Test query 2: Get PostgreSQL version
    print("Test 2: Fetching PostgreSQL version...")
    cursor.execute("SELECT version();")
    result = cursor.fetchone()
    print(f"   Version: {result[0][:50]}...")
    print()

    # Test query 3: Check current database
    print("Test 3: Checking current database...")
    cursor.execute("SELECT current_database();")
    result = cursor.fetchone()
    print(f"   Connected to database: {result[0]}")
    print()

    # Test query 4: List existing tables
    print("Test 4: Listing existing tables...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    if tables:
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
    else:
        print("   No tables found (will be created on first API startup)")
    print()

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("[SUCCESS] Connection closed successfully.")
    print()
    print("=" * 70)
    print("ALL TESTS PASSED - Database is ready!")
    print("=" * 70)
    print()
    print("Next step: Start your API server")
    print("  python -m src.sgk_rag.api.main")

except psycopg2.OperationalError as e:
    print("[ERROR] Connection failed - Operational Error")
    print()
    print(f"Error: {e}")
    print()
    print("Common issues:")
    print("1. [X] Incorrect hostname - Check your Supabase project URL")
    print("2. [X] Wrong password - Verify your database password")
    print("3. [X] Wrong dbname - Try 'postgres' or check your Supabase dashboard")
    print("4. [X] Firewall/Network issue - Check internet connection")
    print("5. [X] Supabase project paused - Ensure project is active")
    print()
    print("How to fix:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Settings -> Database -> Connection String")
    print("4. Look for the database name (usually 'postgres')")
    print("5. Copy the connection details to your .env file")

except Exception as e:
    print(f"[ERROR] Failed to connect: {e}")
    print()
    print("Please check your .env file configuration:")
    print("  user=postgres")
    print("  password=YOUR_PASSWORD")
    print("  host=db.YOUR_PROJECT_REF.supabase.co")
    print("  port=5432")
    print("  dbname=postgres")
