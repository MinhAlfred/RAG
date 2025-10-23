#!/usr/bin/env python3
"""
Simple Gemini Pro RAG Chatbot for Tin Hoc 11
Standalone version without complex dependencies
"""

import os
import json
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Install with: pip install google-generativeai chromadb sentence-transformers")
    exit(1)


class SimpleRAGChatbot:
    """Simple RAG chatbot using Gemini Pro"""
    
    def __init__(self):
        self.conversation_history = []
        self._setup_gemini()
        self._setup_embedding_model()
        self._setup_vector_db()
        
    def _setup_gemini(self):
        """Setup Google Gemini Pro"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ Error: GOOGLE_API_KEY not found in environment")
            print("Please set your API key in .env file")
            exit(1)
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        print("✅ Google Gemini 2.0 Flash Lite initialized (Free tier optimized)")
        
    def _setup_embedding_model(self):
        """Setup embedding model for vector search"""
        try:
            print("🔄 Loading embedding model...")
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            exit(1)
            
    def _setup_vector_db(self):
        """Setup ChromaDB connection"""
        try:
            print("🔄 Connecting to ChromaDB...")
            
            # ChromaDB path - check different possible locations
            db_paths = [
                Path(__file__).parent.parent / "data" / "vectorstores" / "chroma_db",
                Path(__file__).parent.parent / "data" / "vectorstores"
            ]
            
            self.chroma_client = None
            for db_path in db_paths:
                try:
                    self.chroma_client = chromadb.PersistentClient(
                        path=str(db_path),
                        settings=ChromaSettings(anonymized_telemetry=False)
                    )
                    collections = [c.name for c in self.chroma_client.list_collections()]
                    if collections:
                        print(f"Found collections at {db_path}: {collections}")
                        break
                except Exception:
                    continue
            
            if not self.chroma_client:
                print("❌ No ChromaDB found")
                exit(1)
            
            # Get the collection - try different names
            collection_names = [
                "sgk_tin_hoc_11_tin_hoc11",
                "test_tin_hoc_11"
            ]
            
            self.collection = None
            for collection_name in collection_names:
                try:
                    self.collection = self.chroma_client.get_collection(collection_name)
                    count = self.collection.count()
                    print(f"✅ Connected to ChromaDB: {count} documents in '{collection_name}'")
                    break
                except Exception:
                    continue
            
            if not self.collection:
                print(f"❌ No valid collection found. Available: {[c.name for c in self.chroma_client.list_collections()]}")
                exit(1)
                
        except Exception as e:
            print(f"❌ Error connecting to ChromaDB: {e}")
            exit(1)
    
    def search_textbook(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the textbook for relevant content"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    search_results.append({
                        'content': doc,
                        'page': metadata.get('page_number', 'Unknown'),
                        'score': 1 - distance,  # Convert distance to similarity
                        'metadata': metadata
                    })
            
            return search_results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def generate_answer(self, query: str, search_results: List[Dict]) -> str:
        """Generate answer using Gemini Pro with search context"""
        try:
            # Prepare context from search results
            context = ""
            if search_results:
                context = "\n\n".join([
                    f"Trang {result['page']}: {result['content']}"
                    for result in search_results[:3]  # Use top 3 results
                ])
            
            # Vietnamese prompt for educational content (optimized for free tier)
            prompt = f"""Trả lời câu hỏi về Tin học 11 dựa trên nội dung sách giáo khoa:

Nội dung sách:
{context}

Câu hỏi: {query}

Trả lời ngắn gọn bằng tiếng Việt, dễ hiểu cho học sinh lớp 11:"""

            # Generate response with retry for rate limits
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                        print(f"⏳ Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e
            
        except Exception as e:
            if "429" in str(e):
                return "⏳ Đang quá tải, vui lòng thử lại sau ít phút. Hệ thống đã tìm thấy thông tin liên quan trong sách."
            elif "quota" in str(e).lower():
                return "💡 API quota đã hết. Vui lòng kiểm tra tài khoản Google AI hoặc thử lại ngày mai."
            else:
                return f"❌ Lỗi tạo câu trả lời: {e}"
    
    def chat(self, query: str) -> Dict[str, Any]:
        """Main chat function"""
        print(f"\n🔍 Tìm kiếm: {query}")
        
        # Search for relevant content
        search_results = self.search_textbook(query)
        
        if not search_results:
            return {
                'answer': "Xin lỗi, tôi không tìm thấy thông tin liên quan trong sách giáo khoa. Bạn có thể đặt câu hỏi khác không?",
                'sources': [],
                'search_results': []
            }
        
        print(f"📚 Tìm thấy {len(search_results)} kết quả liên quan")
        
        # Generate answer
        answer = self.generate_answer(query, search_results)
        
        # Prepare sources
        sources = [f"Trang {r['page']}" for r in search_results[:3]]
        
        # Add to conversation history
        self.conversation_history.append({
            'query': query,
            'answer': answer,
            'sources': sources
        })
        
        return {
            'answer': answer,
            'sources': sources,
            'search_results': search_results
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🗑️ Đã xóa lịch sử trò chuyện")


def main():
    """Main interactive loop"""
    print("🤖 Tin Học 11 AI Assistant")
    print("=" * 50)
    print("Trợ lý AI cho môn Tin học lớp 11")
    print("Gõ 'quit' để thoát, 'clear' để xóa lịch sử")
    print("=" * 50)
    
    try:
        chatbot = SimpleRAGChatbot()
        print("\n✅ Chatbot đã sẵn sàng! Hãy đặt câu hỏi về Tin học:")
        
        while True:
            try:
                # Get user input
                query = input("\n💬 Bạn: ").strip()
                
                if query.lower() in ['quit', 'exit', 'thoát']:
                    print("👋 Tạm biệt!")
                    break
                    
                if query.lower() in ['clear', 'xóa']:
                    chatbot.clear_history()
                    continue
                    
                if not query:
                    continue
                
                # Get response
                print("\n🤔 Đang suy nghĩ...")
                response = chatbot.chat(query)
                
                # Display response
                print(f"\n🤖 AI: {response['answer']}")
                
                if response['sources']:
                    print(f"\n📚 Nguồn: {', '.join(response['sources'])}")
                
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
                
    except Exception as e:
        print(f"❌ Lỗi khởi tạo chatbot: {e}")


if __name__ == "__main__":
    main()