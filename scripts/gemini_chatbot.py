#!/usr/bin/env python3
"""
Gemini Pro RAG Chatbot for Tin Hoc 11
Combines vector search with Google's Gemini Pro for intelligent Q&A
"""

import sys
import os
from pathlib import Path
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.sgk_rag.core.vector_store import VectorStoreManager
    from src.sgk_rag.core.embedding_manager import EmbeddingManager
except ImportError:
    print("Warning: Could not import some modules. Using fallback.")

# Google Generative AI
import google.generativeai as genai

# Setup logging
import logging
logging.basicConfig(level=logging.WARNING)


class TinHoc11ChatBot:
    """RAG Chatbot using Gemini Pro and vector search"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the chatbot
        
        Args:
            api_key: Google API key for Gemini Pro (optional, can use env var)
        """
        print("🤖 Initializing Tin Hoc 11 AI Assistant...")
        
        # Initialize Gemini
        self._setup_gemini(api_key)
        
        # Initialize vector search
        self._setup_vector_search()
        
        # Conversation history
        self.conversation_history = []
        
        print("✅ AI Assistant ready!")
    
    def _setup_gemini(self, api_key: Optional[str] = None):
        """Setup Gemini Pro"""
        try:
            # Get API key
            if api_key:
                genai.configure(api_key=api_key)
            elif os.getenv("GOOGLE_API_KEY"):
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            else:
                # Prompt user for API key
                print("\n🔑 Google API Key required for Gemini Pro")
                print("Get your API key from: https://makersuite.google.com/app/apikey")
                api_key = input("Enter your Google API Key: ").strip()
                genai.configure(api_key=api_key)
                
                # Save to environment for this session
                os.environ["GOOGLE_API_KEY"] = api_key
            
            # Initialize the model
            self.model = genai.GenerativeModel('gemini-pro')
            
            # Test the connection
            response = self.model.generate_content("Hello")
            print("✅ Gemini Pro connected successfully")
            
        except Exception as e:
            print(f"❌ Failed to setup Gemini Pro: {e}")
            print("Please check your API key and try again")
            sys.exit(1)
    
    def _setup_vector_search(self):
        """Setup vector search system"""
        try:
            print("🔄 Loading textbook database...")
            
            self.embedding_manager = EmbeddingManager(
                model_name="multilingual",
                device="cpu"
            )
            
            self.vector_manager = VectorStoreManager(
                store_type="chroma",
                embedding_manager=self.embedding_manager,
                collection_name="sgk_tin_hoc_11_tin_hoc11"
            )
            
            self.vectorstore = self.vector_manager.load_vectorstore("sgk_tin_hoc_11_tin_hoc11")
            
            # Get database stats
            stats = self.vector_manager.get_statistics(self.vectorstore)
            print(f"✅ Textbook loaded: {stats.get('total_documents', 'N/A')} documents")
            
        except Exception as e:
            print(f"❌ Failed to setup vector search: {e}")
            sys.exit(1)
    
    def search_textbook(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """Search the textbook for relevant content"""
        try:
            results = self.vector_manager.search(
                vectorstore=self.vectorstore,
                query=query,
                k=num_results
            )
            
            processed_results = []
            for result in results:
                processed_results.append({
                    'content': result.page_content,
                    'page': result.metadata.get('page_number', 'N/A'),
                    'source': 'Tin học 11'
                })
            
            return processed_results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def generate_answer(self, question: str, context_results: List[Dict]) -> str:
        """Generate answer using Gemini Pro with textbook context"""
        
        # Build context from search results
        context = ""
        for i, result in enumerate(context_results, 1):
            context += f"\n[Trang {result['page']}]\n{result['content']}\n"
        
        # Create the prompt in Vietnamese
        prompt = f"""Bạn là một trợ lý AI chuyên về Tin học, được thiết kế để giúp học sinh học môn Tin học lớp 11.

NGUYÊN TẮC TRẢ LỜI:
1. Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu
2. Sử dụng thông tin từ sách giáo khoa được cung cấp
3. Giải thích khái niệm một cách đơn giản, phù hợp với học sinh
4. Đưa ra ví dụ cụ thể khi có thể
5. Nếu không có thông tin trong sách, hãy nói rõ và đưa ra kiến thức tổng quát

THÔNG TIN TỪ SÁCH GIÁO KHOA:
{context}

CÂU HỎI CỦA HỌC SINH:
{question}

HÃY TRẢ LỜI CÂU HỎI DỰA TRÊN THÔNG TIN SÁCH GIÁO KHOA VÀ KIẾN THỨC TIN HỌC:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Lỗi khi tạo câu trả lời: {e}"
    
    def chat(self, user_input: str) -> Dict[str, Any]:
        """Process a chat message and return response"""
        
        # Search for relevant content
        print("🔍 Đang tìm kiếm thông tin...")
        search_results = self.search_textbook(user_input, num_results=3)
        
        if not search_results:
            # No search results, use general knowledge
            prompt = f"""Bạn là trợ lý AI về Tin học. Câu hỏi: {user_input}
            
Hãy trả lời bằng tiếng Việt, đơn giản và phù hợp với học sinh lớp 11."""
            
            try:
                response = self.model.generate_content(prompt)
                answer = response.text
            except Exception as e:
                answer = f"❌ Lỗi: {e}"
            
            return {
                'question': user_input,
                'answer': answer,
                'sources': [],
                'search_results': []
            }
        
        # Generate answer with context
        print("🤖 Đang tạo câu trả lời...")
        answer = self.generate_answer(user_input, search_results)
        
        # Add to conversation history
        self.conversation_history.append({
            'question': user_input,
            'answer': answer,
            'timestamp': time.time()
        })
        
        return {
            'question': user_input,
            'answer': answer,
            'sources': [f"Trang {r['page']}" for r in search_results],
            'search_results': search_results
        }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🗑️ Đã xóa lịch sử trò chuyện")


def interactive_chat():
    """Interactive chat interface"""
    print("🇻🇳 TIN HỌC 11 AI ASSISTANT")
    print("=" * 60)
    print("Trợ lý AI chuyên về Tin học lớp 11")
    print("Powered by Google Gemini Pro + Vector Search")
    print("=" * 60)
    print()
    print("📖 Tôi có thể giúp bạn:")
    print("  • Trả lời câu hỏi về Tin học")
    print("  • Giải thích khái niệm, định nghĩa")
    print("  • Hướng dẫn sử dụng phần mềm")
    print("  • Tìm thông tin trong sách giáo khoa")
    print()
    print("💡 Lệnh đặc biệt:")
    print("  • 'examples' - Xem câu hỏi mẫu")
    print("  • 'history' - Xem lịch sử trò chuyện")
    print("  • 'clear' - Xóa lịch sử")
    print("  • 'quit' - Thoát")
    print("=" * 60)
    
    # Initialize chatbot
    chatbot = TinHoc11ChatBot()
    
    # Example questions
    example_questions = [
        "Hệ điều hành là gì?",
        "Phần mềm ứng dụng khác gì với phần mềm hệ thống?",
        "Cách bảo vệ máy tính khỏi virus?",
        "Windows có những tính năng gì?",
        "Làm thế nào để tạo folder mới?",
        "Internet hoạt động như thế nào?",
        "Cách sao lưu dữ liệu an toàn?",
        "Microsoft Office gồm những ứng dụng nào?"
    ]
    
    try:
        while True:
            print("\n" + "="*80)
            user_input = input("🙋 Hãy đặt câu hỏi: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'thoát', 'q']:
                print("👋 Tạm biệt! Chúc bạn học tốt!")
                break
            
            if user_input.lower() in ['examples', 'ví dụ', 'mẫu']:
                print("\n💡 CÂU HỎI MẪU:")
                for i, example in enumerate(example_questions, 1):
                    print(f"  {i}. {example}")
                print("\n📝 Hãy copy một câu hỏi hoặc đặt câu hỏi của riêng bạn!")
                continue
            
            if user_input.lower() in ['history', 'lịch sử']:
                history = chatbot.get_conversation_history()
                if history:
                    print("\n📚 LỊCH SỬ TRÒ CHUYỆN:")
                    for i, item in enumerate(history[-5:], 1):  # Show last 5
                        print(f"\n{i}. Q: {item['question']}")
                        print(f"   A: {item['answer'][:100]}...")
                else:
                    print("📝 Chưa có lịch sử trò chuyện")
                continue
            
            if user_input.lower() in ['clear', 'xóa']:
                chatbot.clear_history()
                continue
            
            # Process the question
            print("\n" + "="*80)
            print(f"🙋 Câu hỏi: {user_input}")
            print("-" * 80)
            
            response = chatbot.chat(user_input)
            
            # Display answer
            print("🤖 Trả lời:")
            print(response['answer'])
            
            # Display sources if available
            if response['sources']:
                print(f"\n📚 Nguồn tham khảo: {', '.join(response['sources'])}")
            
            # Ask if user wants to see search results
            if response['search_results']:
                show_sources = input("\n📖 Xem thông tin chi tiết từ sách? (y/n): ").strip().lower()
                if show_sources in ['y', 'yes', 'có', 'c']:
                    print("\n📚 THÔNG TIN TỪ SÁCH GIÁO KHOA:")
                    for i, result in enumerate(response['search_results'], 1):
                        print(f"\n📄 {i}. Trang {result['page']}:")
                        print("-" * 40)
                        content = result['content']
                        if len(content) > 300:
                            content = content[:300] + "..."
                        print(content)
    
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt! Chúc bạn học tốt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")


def quick_test():
    """Quick test of the chatbot"""
    print("🧪 TESTING GEMINI PRO CHATBOT")
    print("=" * 40)
    
    chatbot = TinHoc11ChatBot()
    
    test_questions = [
        "Hệ điều hành là gì?",
        "Phần mềm ứng dụng có những loại nào?",
        "Cách bảo vệ máy tính?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 Test {i}: {question}")
        print("-" * 40)
        
        response = chatbot.chat(question)
        
        print("🤖 Answer:")
        print(response['answer'][:200] + "..." if len(response['answer']) > 200 else response['answer'])
        
        if response['sources']:
            print(f"📚 Sources: {', '.join(response['sources'])}")
    
    print("\n✅ Test completed!")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tin Hoc 11 AI Chatbot")
    parser.add_argument('--test', action='store_true', help='Run quick test')
    parser.add_argument('--api-key', type=str, help='Google API key')
    
    args = parser.parse_args()
    
    if args.test:
        quick_test()
    else:
        interactive_chat()


if __name__ == "__main__":
    main()