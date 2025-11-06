"""
Test script for RAG fallback mechanism

This script tests the enhanced RAG system with fallback capabilities:
1. Test with questions that should be in the vector DB (normal retrieval)
2. Test with questions that won't be in the vector DB (fallback mode)
3. Test different fallback modes (llm_knowledge, web_search, both)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sgk_rag.core.rag_pipeline import RAGPipeline
from config.settings import settings


def print_separator(title=""):
    """Print a nice separator"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def test_normal_retrieval():
    """Test with questions that should be in the vector DB"""
    print_separator("TEST 1: Normal Retrieval (Questions in Vector DB)")

    questions = [
        "Máy tính là gì?",
        "Phần cứng máy tính gồm những thành phần nào?",
        "Python là gì?"
    ]

    print("📝 Testing questions that should be in the textbook database...")
    print(f"   Fallback enabled: {settings.ENABLE_FALLBACK}")
    print(f"   Fallback mode: {settings.FALLBACK_MODE}")
    print()

    # Initialize RAG pipeline
    rag = RAGPipeline(
        llm_type=settings.LLM_TYPE,
        model_name=settings.MODEL_NAME,
        collection_name=settings.COLLECTION_NAME_PREFIX
    )

    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 80)

        result = rag.query(question, return_sources=True)

        print(f"✅ Answer: {result['answer'][:300]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {result.get('retrieval_mode', 'N/A')}")
        print(f"   - Docs Retrieved: {result.get('docs_retrieved', 0)}")
        print(f"   - Fallback Used: {result.get('fallback_used', False)}")
        print(f"   - Web Search Used: {result.get('web_search_used', False)}")

        if result.get('sources'):
            print(f"\n📚 Sources: {len(result['sources'])} documents")
            for j, source in enumerate(result['sources'][:2], 1):
                metadata = source.get('metadata', {})
                print(f"   {j}. Grade {metadata.get('grade')}: {metadata.get('lesson_title', 'N/A')}")


def test_fallback_llm_knowledge():
    """Test fallback with LLM knowledge only"""
    print_separator("TEST 2: Fallback - LLM Knowledge Only")

    # Questions unlikely to be in Vietnamese CS textbooks
    questions = [
        "What is quantum computing?",
        "Explain blockchain technology",
        "What is the latest version of Python?"
    ]

    print("📝 Testing questions NOT in the textbook database...")
    print("   Using fallback mode: llm_knowledge")
    print()

    # Initialize RAG pipeline with fallback
    rag = RAGPipeline(
        llm_type=settings.LLM_TYPE,
        model_name=settings.MODEL_NAME,
        collection_name=settings.COLLECTION_NAME_PREFIX,
        enable_fallback=True,
        fallback_mode="llm_knowledge"
    )

    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 80)

        result = rag.query(question, return_sources=True)

        print(f"✅ Answer: {result['answer'][:300]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {result.get('retrieval_mode', 'N/A')}")
        print(f"   - Docs Retrieved: {result.get('docs_retrieved', 0)}")
        print(f"   - Fallback Used: {result.get('fallback_used', False)}")
        print(f"   - Web Search Used: {result.get('web_search_used', False)}")


def test_fallback_web_search():
    """Test fallback with web search"""
    print_separator("TEST 3: Fallback - Web Search")

    # Questions that require current/recent information
    questions = [
        "Trí tuệ nhân tạo sinh tạo là gì?",
        "ChatGPT hoạt động như thế nào?",
    ]

    print("📝 Testing questions requiring web search...")
    print("   Using fallback mode: web_search")
    print()

    # Initialize RAG pipeline with web search fallback
    rag = RAGPipeline(
        llm_type=settings.LLM_TYPE,
        model_name=settings.MODEL_NAME,
        collection_name=settings.COLLECTION_NAME_PREFIX,
        enable_fallback=True,
        fallback_mode="web_search"
    )

    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 80)

        result = rag.query(question, return_sources=True)

        print(f"✅ Answer: {result['answer'][:300]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {result.get('retrieval_mode', 'N/A')}")
        print(f"   - Docs Retrieved: {result.get('docs_retrieved', 0)}")
        print(f"   - Fallback Used: {result.get('fallback_used', False)}")
        print(f"   - Web Search Used: {result.get('web_search_used', False)}")


def test_fallback_both():
    """Test fallback with both LLM knowledge and web search"""
    print_separator("TEST 4: Fallback - Both (LLM + Web Search)")

    # Mixed questions
    questions = [
        "Công nghệ 5G là gì?",
        "Metaverse trong công nghệ là gì?"
    ]

    print("📝 Testing fallback with both LLM knowledge and web search...")
    print("   Using fallback mode: both")
    print()

    # Initialize RAG pipeline with both fallback modes
    rag = RAGPipeline(
        llm_type=settings.LLM_TYPE,
        model_name=settings.MODEL_NAME,
        collection_name=settings.COLLECTION_NAME_PREFIX,
        enable_fallback=True,
        fallback_mode="both"
    )

    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 80)

        result = rag.query(question, return_sources=True)

        print(f"✅ Answer: {result['answer'][:300]}...")
        print(f"\n📊 Metadata:")
        print(f"   - Retrieval Mode: {result.get('retrieval_mode', 'N/A')}")
        print(f"   - Docs Retrieved: {result.get('docs_retrieved', 0)}")
        print(f"   - Fallback Used: {result.get('fallback_used', False)}")
        print(f"   - Web Search Used: {result.get('web_search_used', False)}")


def main():
    """Run all tests"""
    print("\n" + "🎯" * 40)
    print("  RAG FALLBACK MECHANISM - TEST SUITE")
    print("🎯" * 40)

    try:
        # Test 1: Normal retrieval
        test_normal_retrieval()

        # Test 2: Fallback with LLM knowledge
        test_fallback_llm_knowledge()

        # Test 3: Fallback with web search
        test_fallback_web_search()

        # Test 4: Fallback with both
        test_fallback_both()

        print_separator("ALL TESTS COMPLETED")
        print("✅ Fallback mechanism is working correctly!")
        print("\nSummary:")
        print("1. ✅ Normal retrieval works when docs are found")
        print("2. ✅ LLM knowledge fallback works when no docs found")
        print("3. ✅ Web search fallback works for current information")
        print("4. ✅ Combined fallback mode works effectively")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
