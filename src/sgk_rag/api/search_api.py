"""
Simple Vector Search API for Tin Hoc 11 RAG System
Easy-to-use functions for searching Vietnamese educational content
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.vector_search import TinHoc11VectorSearch

# Initialize global search instance
_search_instance = None

def initialize_search(collection_name: str = "sgk_tin_hoc_11_tin_hoc11") -> bool:
    """
    Initialize the vector search system
    
    Args:
        collection_name: ChromaDB collection name
        
    Returns:
        True if successful, False otherwise
    """
    global _search_instance
    
    try:
        _search_instance = TinHoc11VectorSearch(collection_name)
        return True
    except Exception as e:
        logging.error(f"Failed to initialize search: {e}")
        return False

def search(
    query: str, 
    num_results: int = 5,
    page_range: Optional[tuple] = None,
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Search the Tin Hoc 11 textbook
    
    Args:
        query: Search query in Vietnamese or English
        num_results: Number of results to return (default: 5)
        page_range: Optional tuple (start_page, end_page) to limit search
        min_score: Minimum similarity score threshold
        
    Returns:
        List of search results with content, scores, and metadata
        
    Example:
        results = search("Hệ điều hành là gì?", num_results=3)
        for result in results:
            print(f"Page {result['page_number']}: {result['content'][:100]}...")
    """
    global _search_instance
    
    if _search_instance is None:
        if not initialize_search():
            return []
    
    try:
        if page_range:
            start_page, end_page = page_range
            return _search_instance.search_by_page_range(
                query, start_page, end_page, k=num_results
            )
        else:
            return _search_instance.search_educational_topics(
                query, k=num_results
            )
    except Exception as e:
        logging.error(f"Search failed: {e}")
        return []

def search_similar_to_page(
    page_number: int, 
    num_results: int = 5,
    exclude_same_page: bool = True
) -> List[Dict[str, Any]]:
    """
    Find content similar to a specific page
    
    Args:
        page_number: Reference page number
        num_results: Number of results to return
        exclude_same_page: Whether to exclude the same page from results
        
    Returns:
        List of similar content from other pages
    """
    global _search_instance
    
    if _search_instance is None:
        if not initialize_search():
            return []
    
    try:
        return _search_instance.search_similar_content(
            page_number, k=num_results, exclude_same_page=exclude_same_page
        )
    except Exception as e:
        logging.error(f"Similar search failed: {e}")
        return []

def get_page_content(page_number: int) -> Optional[str]:
    """
    Get all content from a specific page
    
    Args:
        page_number: Page number to retrieve
        
    Returns:
        Page content as string, or None if not found
    """
    global _search_instance
    
    if _search_instance is None:
        if not initialize_search():
            return None
    
    try:
        return _search_instance.get_page_content(page_number)
    except Exception as e:
        logging.error(f"Failed to get page content: {e}")
        return None

def search_definitions(term: str, num_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search for definitions of technical terms
    
    Args:
        term: Technical term to define
        num_results: Number of definition results
        
    Returns:
        List of definition-focused results
    """
    # Create definition-focused queries
    definition_queries = [
        f"{term} là gì",
        f"định nghĩa {term}",
        f"khái niệm {term}",
        f"{term} có nghĩa là",
        term
    ]
    
    all_results = []
    for query in definition_queries:
        results = search(query, num_results=num_results)
        all_results.extend(results)
    
    # Remove duplicates and prioritize definition-like content
    unique_results = []
    seen_pages = set()
    
    for result in all_results:
        page_key = f"page_{result['page_number']}"
        if page_key not in seen_pages:
            content_lower = result['content'].lower()
            
            # Prioritize content that looks like definitions
            if any(word in content_lower for word in ['là', 'được gọi là', 'có nghĩa', 'định nghĩa']):
                result['is_definition'] = True
                unique_results.insert(0, result)  # Put definitions first
            else:
                result['is_definition'] = False
                unique_results.append(result)
            
            seen_pages.add(page_key)
    
    return unique_results[:num_results]

def search_examples(topic: str, num_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search for examples related to a topic
    
    Args:
        topic: Topic to find examples for
        num_results: Number of example results
        
    Returns:
        List of example-focused results
    """
    example_queries = [
        f"ví dụ {topic}",
        f"{topic} ví dụ",
        f"thực hành {topic}",
        f"bài tập {topic}",
        f"minh họa {topic}"
    ]
    
    all_results = []
    for query in example_queries:
        results = search(query, num_results=num_results)
        all_results.extend(results)
    
    # Filter for content that contains examples
    example_results = []
    for result in all_results:
        content_lower = result['content'].lower()
        if any(word in content_lower for word in ['ví dụ', 'thực hành', 'bài tập', 'minh họa', 'chẳng hạn']):
            result['has_examples'] = True
            example_results.append(result)
    
    return example_results[:num_results]

def get_database_info() -> Dict[str, Any]:
    """
    Get information about the vector database
    
    Returns:
        Dictionary with database statistics and info
    """
    global _search_instance
    
    if _search_instance is None:
        if not initialize_search():
            return {}
    
    try:
        return _search_instance.get_database_statistics()
    except Exception as e:
        logging.error(f"Failed to get database info: {e}")
        return {}

# Convenience functions for common educational queries
def what_is(term: str) -> List[Dict[str, Any]]:
    """Search for 'What is...' type questions"""
    return search_definitions(term, num_results=3)

def how_to(task: str) -> List[Dict[str, Any]]:
    """Search for 'How to...' type questions"""
    how_queries = [
        f"cách {task}",
        f"làm thế nào để {task}",
        f"hướng dẫn {task}",
        f"phương pháp {task}"
    ]
    
    all_results = []
    for query in how_queries:
        results = search(query, num_results=3)
        all_results.extend(results)
    
    return all_results[:5]

def find_topics_on_page(page_number: int) -> List[str]:
    """
    Extract main topics from a specific page
    
    Args:
        page_number: Page to analyze
        
    Returns:
        List of main topics found on the page
    """
    content = get_page_content(page_number)
    if not content:
        return []
    
    # Simple topic extraction based on common patterns
    topics = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # Look for headers and definitions
        if any(pattern in line.lower() for pattern in ['chương', 'bài', 'mục', '.']):
            if len(line) < 100 and len(line) > 5:  # Reasonable header length
                topics.append(line)
    
    return topics[:10]  # Return top 10 topics


# Example usage functions
def demo_basic_search():
    """Demonstrate basic search functionality"""
    print("🔍 BASIC SEARCH DEMO")
    print("=" * 40)
    
    # Initialize search
    if not initialize_search():
        print("❌ Failed to initialize search")
        return
    
    # Demo searches
    queries = [
        "Hệ điều hành Windows",
        "Phần mềm ứng dụng", 
        "Mạng máy tính",
        "Bảo mật thông tin"
    ]
    
    for query in queries:
        print(f"\n🔍 Searching: '{query}'")
        print("-" * 30)
        
        results = search(query, num_results=2)
        
        for i, result in enumerate(results, 1):
            print(f"Result {i} (Page {result['page_number']}):")
            print(f"  {result['content'][:100]}...")
            print()

def demo_specialized_search():
    """Demonstrate specialized search functions"""
    print("🎯 SPECIALIZED SEARCH DEMO")
    print("=" * 40)
    
    # What is...
    print("\n📖 What is 'hệ điều hành'?")
    definitions = what_is("hệ điều hành")
    for i, result in enumerate(definitions[:2], 1):
        print(f"  {i}. (Page {result['page_number']}) {result['content'][:80]}...")
    
    # How to...
    print("\n🛠️ How to 'sử dụng máy tính'?")
    instructions = how_to("sử dụng máy tính")
    for i, result in enumerate(instructions[:2], 1):
        print(f"  {i}. (Page {result['page_number']}) {result['content'][:80]}...")
    
    # Examples
    print("\n📝 Examples for 'phần mềm':")
    examples = search_examples("phần mềm")
    for i, result in enumerate(examples[:2], 1):
        print(f"  {i}. (Page {result['page_number']}) {result['content'][:80]}...")


if __name__ == "__main__":
    # Run demos
    demo_basic_search()
    print("\n" + "="*60 + "\n")
    demo_specialized_search()
    
    # Show database info
    print("\n📊 DATABASE INFO")
    print("=" * 20)
    info = get_database_info()
    for key, value in info.items():
        print(f"  {key}: {value}")