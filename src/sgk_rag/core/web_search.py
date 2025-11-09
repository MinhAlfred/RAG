"""Web Search Module - Fallback for when vector DB has no relevant information"""

import logging
from typing import List, Dict, Optional
from ddgs import DDGS

logger = logging.getLogger(__name__)


class WebSearchManager:
    """
    Manager for web search fallback in RAG system
    Uses DuckDuckGo for privacy-focused web search
    """

    def __init__(self, max_results: int = 3, region: str = "vn-vi"):
        """
        Initialize web search manager

        Args:
            max_results: Maximum number of search results to return
            region: Region for search (vn-vi for Vietnam/Vietnamese)
        """
        self.max_results = max_results
        self.region = region
        logger.info(f"WebSearchManager initialized (max_results={max_results}, region={region})")

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Search the web for information

        Args:
            query: Search query
            max_results: Override default max_results

        Returns:
            List of search results with title, body, and href
        """
        try:
            results_count = max_results or self.max_results
            logger.info(f"🔍 Searching web for: '{query}' (max_results={results_count})")

            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    region=self.region,
                    safesearch='moderate',
                    max_results=results_count
                ))

            if results:
                logger.info(f"✅ Found {len(results)} web results")
                return results
            else:
                logger.warning(f"⚠️ No web results found for query: '{query}'")
                return []

        except Exception as e:
            logger.error(f"❌ Web search error: {e}")
            return []

    def format_results_for_context(self, results: List[Dict[str, str]]) -> str:
        """
        Format search results into a context string for LLM

        Args:
            results: List of search results

        Returns:
            Formatted context string
        """
        if not results:
            return "Không tìm thấy thông tin từ web."

        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'N/A')
            body = result.get('body', 'N/A')
            source = result.get('href', 'N/A')

            formatted.append(f"[Kết quả {i} - {title}]\n{body}\nNguồn: {source}")

        return "\n\n---\n\n".join(formatted)

    def search_and_format(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Search and format results in one call

        Args:
            query: Search query
            max_results: Override default max_results

        Returns:
            Formatted context string
        """
        results = self.search(query, max_results)
        return self.format_results_for_context(results)


def main():
    """Test web search functionality"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python web_search.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Test search
    search_manager = WebSearchManager(max_results=3)
    results = search_manager.search(query)

    print(f"\n🔍 Search Query: {query}")
    print(f"📊 Results found: {len(results)}\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['body'][:200]}...")
        print(f"   Source: {result['href']}\n")

    print("\n" + "="*80)
    print("Formatted Context:")
    print("="*80)
    print(search_manager.format_results_for_context(results))


if __name__ == "__main__":
    main()
