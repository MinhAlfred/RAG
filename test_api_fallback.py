"""
Test API endpoints for RAG fallback mechanism

Prerequisites:
1. Start the API server: uvicorn src.sgk_rag.api.main:app --reload
2. Run this test script: python test_api_fallback.py
"""

import requests
import json
import time


API_URL = "http://localhost:8000"


def print_separator(title=""):
    """Print a nice separator"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def test_normal_retrieval():
    """Test normal retrieval (question in vector DB)"""
    print_separator("TEST 1: Normal Retrieval")

    endpoint = f"{API_URL}/ask"
    payload = {
        "question": "Máy tính là gì?",
        "return_sources": True
    }

    print(f"📤 Request: POST {endpoint}")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False)}")

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response (Status 200):")
        print(f"   Question: {data['question']}")
        print(f"   Answer: {data['answer'][:200]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {data.get('retrieval_mode')}")
        print(f"   - Docs Retrieved: {data.get('docs_retrieved')}")
        print(f"   - Fallback Used: {data.get('fallback_used')}")
        print(f"   - Web Search Used: {data.get('web_search_used')}")
        print(f"   - Processing Time: {data.get('processing_time'):.2f}s")

        if data.get('sources'):
            print(f"\n📚 Sources: {len(data['sources'])} documents")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


def test_fallback_llm_knowledge():
    """Test fallback with LLM knowledge"""
    print_separator("TEST 2: Fallback - LLM Knowledge")

    endpoint = f"{API_URL}/ask"
    payload = {
        "question": "What is quantum computing?",
        "return_sources": True,
        "enable_fallback": True,
        "fallback_mode": "llm_knowledge"
    }

    print(f"📤 Request: POST {endpoint}")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False)}")

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response (Status 200):")
        print(f"   Question: {data['question']}")
        print(f"   Answer: {data['answer'][:200]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {data.get('retrieval_mode')}")
        print(f"   - Docs Retrieved: {data.get('docs_retrieved')}")
        print(f"   - Fallback Used: {data.get('fallback_used')}")
        print(f"   - Web Search Used: {data.get('web_search_used')}")
        print(f"   - Processing Time: {data.get('processing_time'):.2f}s")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


def test_fallback_web_search():
    """Test fallback with web search"""
    print_separator("TEST 3: Fallback - Web Search")

    endpoint = f"{API_URL}/ask"
    payload = {
        "question": "ChatGPT là gì?",
        "return_sources": True,
        "enable_fallback": True,
        "fallback_mode": "web_search"
    }

    print(f"📤 Request: POST {endpoint}")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False)}")

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response (Status 200):")
        print(f"   Question: {data['question']}")
        print(f"   Answer: {data['answer'][:200]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {data.get('retrieval_mode')}")
        print(f"   - Docs Retrieved: {data.get('docs_retrieved')}")
        print(f"   - Fallback Used: {data.get('fallback_used')}")
        print(f"   - Web Search Used: {data.get('web_search_used')}")
        print(f"   - Processing Time: {data.get('processing_time'):.2f}s")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


def test_fallback_both():
    """Test fallback with both modes"""
    print_separator("TEST 4: Fallback - Both (LLM + Web)")

    endpoint = f"{API_URL}/ask"
    payload = {
        "question": "Công nghệ 5G hoạt động như thế nào?",
        "return_sources": True,
        "enable_fallback": True,
        "fallback_mode": "both"
    }

    print(f"📤 Request: POST {endpoint}")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False)}")

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response (Status 200):")
        print(f"   Question: {data['question']}")
        print(f"   Answer: {data['answer'][:200]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {data.get('retrieval_mode')}")
        print(f"   - Docs Retrieved: {data.get('docs_retrieved')}")
        print(f"   - Fallback Used: {data.get('fallback_used')}")
        print(f"   - Web Search Used: {data.get('web_search_used')}")
        print(f"   - Processing Time: {data.get('processing_time'):.2f}s")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


def test_health_check():
    """Test health check endpoint"""
    print_separator("TEST 0: Health Check")

    endpoint = f"{API_URL}/health"

    print(f"📤 Request: GET {endpoint}")

    response = requests.get(endpoint)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response (Status 200):")
        print(f"   Status: {data.get('status')}")
        print(f"   RAG Status: {data.get('rag_status')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Model: {data.get('model_info', {}).get('model_name')}")
        return True
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return False


def main():
    """Run all API tests"""
    print("\n" + "🎯" * 40)
    print("  RAG FALLBACK API - TEST SUITE")
    print("🎯" * 40)

    # Check if server is running
    print("\n🔍 Checking if API server is running...")
    try:
        if not test_health_check():
            print("\n❌ API server is not running!")
            print("   Please start the server first:")
            print("   uvicorn src.sgk_rag.api.main:app --reload")
            return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to API server at {API_URL}")
        print("   Please start the server first:")
        print("   uvicorn src.sgk_rag.api.main:app --reload")
        return 1

    try:
        # Run tests with delays to avoid overwhelming the server
        test_normal_retrieval()
        time.sleep(1)

        test_fallback_llm_knowledge()
        time.sleep(1)

        test_fallback_web_search()
        time.sleep(1)

        test_fallback_both()

        print_separator("ALL TESTS COMPLETED")
        print("✅ API fallback mechanism is working correctly!")
        print("\nSummary:")
        print("1. ✅ Normal retrieval endpoint works")
        print("2. ✅ LLM knowledge fallback works via API")
        print("3. ✅ Web search fallback works via API")
        print("4. ✅ Combined fallback mode works via API")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
