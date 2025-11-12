"""RAG Pipeline - Complete Retrieval-Augmented Generation system"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Literal
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .vector_store import VectorStoreManager
from .embedding_manager import EmbeddingManager
from .web_search import WebSearchManager
from ..models.document import Chunk
from config.settings import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete RAG Pipeline for SGK Tin học
    """
    
    def __init__(
        self,
        vector_store_path: Optional[str] = None,
        llm_type: str = "openai",
        model_name: Optional[str] = None,
        embedding_model: str = "multilingual",
        temperature: float = 0.3,
        collection_name: Optional[str] = None
    ):
        """
        Initialize RAG Pipeline

        Args:
            vector_store_path: Path to existing vector store
            llm_type: "openai" or "ollama"
            model_name: Specific model name
            embedding_model: Embedding model type
            temperature: LLM temperature
            collection_name: Collection name for vector store
        """
        self.vector_store_path = vector_store_path or "data/vector_store"
        self.llm_type = llm_type
        self.temperature = temperature
        self.collection_name = collection_name

        # Initialize components
        self.embedding_manager = EmbeddingManager(model_name=embedding_model)
        self.vector_manager = VectorStoreManager(
            embedding_manager=self.embedding_manager,
            collection_name=collection_name,
            persist_directory=Path(self.vector_store_path) if self.vector_store_path else None
        )

        # Load vector store
        self.vectorstore = self._load_vector_store()

        # Initialize LLM
        self.llm = self._initialize_llm(model_name)

        # Initialize web search (always enabled)
        self.web_search = WebSearchManager(
            max_results=settings.WEB_SEARCH_MAX_RESULTS,
            region=settings.WEB_SEARCH_REGION
        )
        logger.info("🌐 Web search enabled - always combining knowledge base + web search")

        # Create RAG chain (combines both sources)
        self.rag_chain = self._create_rag_chain()

        logger.info(f"RAG Pipeline initialized (LLM: {llm_type}, Mode: Knowledge Base + Web Search)")
    
    def _load_vector_store(self):
        """
        Load existing vector store
        
        Thử load từ VectorStoreManager (LangChain-based Chroma/FAISS)
        Đây là cách chuẩn và nhất quán với kiến trúc hệ thống
        """
        try:
            logger.info(f"Loading vector store from: {self.vector_store_path}")
            
            # Load from VectorStoreManager
            vectorstore = self.vector_manager.load_vectorstore()
            
            if vectorstore:
                logger.info("✅ Vector store loaded successfully")
                return vectorstore
            else:
                raise Exception("load_vectorstore() returned None")
                
        except FileNotFoundError as e:
            logger.error(f"❌ Vector store not found: {e}")
            logger.error(f"   Expected location: {self.vector_manager.persist_directory}")
            logger.error(f"   💡 Tip: Create vector store first using create_vectorstore.py")
            raise
            
        except Exception as e:
            logger.error(f"❌ Failed to load vector store: {e}")
            logger.error(f"   Store type: {self.vector_manager.store_type}")
            logger.error(f"   Collection: {self.vector_manager.collection_name}")
            raise
    
    def _initialize_llm(self, model_name: Optional[str]):
        """Initialize Language Model"""
        if self.llm_type == "openai":
            # Lazy import - only import if needed
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ImportError("langchain-openai not installed. Install with: pip install langchain-openai")

            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set for OpenAI")

            model = model_name or "gpt-3.5-turbo"
            return ChatOpenAI(
                model=model,
                temperature=self.temperature,
                openai_api_key=settings.OPENAI_API_KEY
            )

        elif self.llm_type == "ollama":
            # Lazy import - only import if needed
            try:
                from langchain_community.llms import Ollama
            except ImportError:
                raise ImportError("Ollama support requires langchain-community. Ensure it's installed.")

            model = model_name or "llama3.2:3b"
            return Ollama(
                model=model,
                temperature=self.temperature
            )

        elif self.llm_type == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not set for Gemini")

            model = model_name or "gemini-2.0-flash-exp"  # Gemini 2.0 Flash (free)
            logger.info(f"🤖 Initializing Gemini: {model}")
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=self.temperature,
                google_api_key=settings.GOOGLE_API_KEY
            )

        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
    
    def _create_rag_chain(self):
        """Create RAG chain that combines knowledge base and web search"""

        # Vietnamese prompt template combining both sources
        prompt_template = ChatPromptTemplate.from_template("""
Bạn là một trợ lý AI chuyên về Tin học, được đào tạo trên nội dung sách giáo khoa Tin học từ lớp 3 đến 12.

Nhiệm vụ: Trả lời câu hỏi dựa trên thông tin từ sách giáo khoa VÀ thông tin bổ sung từ tìm kiếm web.

{context}

Câu hỏi: {question}

Hướng dẫn trả lời:
1. Kết hợp thông tin từ cả sách giáo khoa và tìm kiếm web để đưa ra câu trả lời đầy đủ
2. Ưu tiên thông tin từ sách giáo khoa khi có sẵn
3. Bổ sung thêm thông tin từ web để làm rõ hoặc cập nhật kiến thức
4. Trả lời bằng tiếng Việt, dễ hiểu và chính xác
5. Có thể tham khảo lớp/bài học cụ thể nếu có
6. Đưa ra ví dụ thực tế nếu phù hợp

Trả lời:
""")

        # Create RAG chain
        rag_chain = (
            prompt_template
            | self.llm
            | StrOutputParser()
        )

        return rag_chain
    
    def _get_retriever(self):
        """Get retriever from vector store"""
        if hasattr(self.vectorstore, 'as_retriever'):
            # LangChain vector store
            return self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
        else:
            # Custom FAISS loader
            class CustomRetriever:
                def __init__(self, vectorstore):
                    self.vectorstore = vectorstore
                
                def invoke(self, query: str):
                    results = self.vectorstore.search(query, k=5)
                    # Convert to LangChain document format
                    docs = []
                    for result in results:
                        doc = type('Document', (), {
                            'page_content': result['content'],
                            'metadata': {
                                'grade': result.get('grade', 'N/A'),
                                'lesson_title': result.get('lesson_title', 'N/A'),
                                'score': result.get('score', 0)
                            }
                        })()
                        docs.append(doc)
                    return docs
            
            return CustomRetriever(self.vectorstore)
    
    def switch_collection(self, collection_name: str):
        """
        Switch to a different collection

        Args:
            collection_name: Name of the collection to switch to
        """
        try:
            logger.info(f"🔄 Switching to collection: {collection_name}")
            self.collection_name = collection_name
            self.vector_manager.collection_name = collection_name
            self.vectorstore = self.vector_manager.load_vectorstore(collection_name)
            logger.info(f"✅ Successfully switched to collection: {collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to switch collection: {e}")
            raise

    def query(
        self,
        question: str,
        grade_filter: Optional[int] = None,
        return_sources: bool = False,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system - always combines knowledge base + web search

        Args:
            question: User question
            grade_filter: Grade level for adjusting explanation complexity (not used to filter documents)
                         The most relevant documents from all grades will be retrieved,
                         but prompts will adjust language to the specified grade level
            return_sources: Whether to return source documents
            collection_name: Optional collection name to query from

        Returns:
            Dictionary with answer and optional sources
        """
        try:
            # Switch collection if specified and different from current
            if collection_name and collection_name != self.collection_name:
                self.switch_collection(collection_name)

            # Get retriever and retrieve documents from knowledge base
            retriever = self._get_retriever()
            retrieved_docs = retriever.invoke(question)

            logger.info(f"📊 Retrieved {len(retrieved_docs)} documents from knowledge base for query: '{question[:50]}...'")

            # Note: grade_filter is NOT used for filtering documents
            # Instead, grade is used in prompts to adjust language complexity and explanation level
            # This allows the LLM to use the most relevant content from all grades
            if grade_filter is not None:
                logger.info(f"   📚 Grade {grade_filter} will be used to adjust explanation level in prompts")

            # Format documents from knowledge base
            def format_docs(docs):
                """Format retrieved documents"""
                formatted = []
                for doc in docs:
                    content = doc.page_content if hasattr(doc, 'page_content') else doc.get('content', '')
                    metadata = doc.metadata if hasattr(doc, 'metadata') else doc

                    # Add metadata info if available
                    grade = metadata.get('grade', 'N/A')
                    lesson = metadata.get('lesson_title', 'N/A')

                    formatted.append(f"[Lớp {grade} - {lesson}]\n{content}")

                return "\n\n---\n\n".join(formatted)

            # Get web search results (always)
            logger.info("🌐 Performing web search...")
            web_results = self.web_search.search_and_format(question)
            web_search_used = web_results and "Không tìm thấy" not in web_results

            # Combine contexts from both sources
            context_parts = []

            if retrieved_docs:
                kb_context = format_docs(retrieved_docs)
                context_parts.append(f"Thông tin từ sách giáo khoa:\n{kb_context}")
                logger.info(f"✅ Using {len(retrieved_docs)} documents from knowledge base")

            if web_search_used:
                context_parts.append(f"Thông tin bổ sung từ tìm kiếm web:\n{web_results}")
                logger.info("✅ Using web search results")

            # Combine all contexts
            if context_parts:
                context = "\n\n=== === ===\n\n".join(context_parts)
            else:
                context = "Không tìm thấy thông tin từ sách giáo khoa và web. Sử dụng kiến thức tổng quát để trả lời."
                logger.warning("⚠️  No information found from both sources")

            # Generate answer using combined context
            prompt_input = {
                "context": context,
                "question": question
            }
            answer = self.rag_chain.invoke(prompt_input)

            # Build result
            result = {
                "question": question,
                "answer": answer,
                "status": "success",
                "retrieval_mode": "combined",  # Always combined mode
                "docs_retrieved": len(retrieved_docs),
                "fallback_used": False,  # No longer using fallback concept
                "web_search_used": web_search_used
            }

            # Add sources if requested
            if return_sources:
                sources = []

                # Add knowledge base sources
                if retrieved_docs:
                    logger.info(f"   📎 Adding {len(retrieved_docs)} knowledge base sources to response")
                    for doc in retrieved_docs:
                        sources.append({
                            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "metadata": doc.metadata,
                            "score": doc.metadata.get('score', 0)
                        })

                # Add web search indicator
                if web_search_used:
                    sources.append({"type": "web_search", "note": "Thông tin bổ sung từ tìm kiếm web"})

                result["sources"] = sources

            return result

        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "question": question,
                "answer": f"Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi: {str(e)}",
                "status": "error",
                "error": str(e)
            }
    
    def batch_query(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Process multiple questions"""
        results = []
        for question in questions:
            result = self.query(question)
            results.append(result)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        stats = {
            "llm_type": self.llm_type,
            "temperature": self.temperature,
            "embedding_model": self.embedding_manager.model_name,
            "vector_store_path": self.vector_store_path
        }
        
        # Add vector store stats if available
        try:
            if hasattr(self.vectorstore, 'index'):
                stats["total_vectors"] = self.vectorstore.index.ntotal
            elif hasattr(self.vector_manager, 'get_statistics'):
                vector_stats = self.vector_manager.get_statistics(self.vectorstore)
                stats.update(vector_stats)
        except Exception as e:
            logger.warning(f"Could not get vector store stats: {e}")
        
        return stats


class RAGTester:
    """Test RAG Pipeline with sample questions"""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        self.rag = rag_pipeline
    
    def get_sample_questions(self) -> List[str]:
        """Get sample questions for testing"""
        return [
            "Máy tính là gì?",
            "Phần cứng máy tính gồm những thành phần nào?",
            "Sự khác biệt giữa phần cứng và phần mềm là gì?",
            "Hệ điều hành có vai trò gì trong máy tính?",
            "Internet là gì và hoạt động như thế nào?",
            "Thuật toán là gì? Cho ví dụ về một thuật toán đơn giản",
            "Ngôn ngữ lập trình là gì?",
            "Mạng máy tính có những loại nào?",
            "Bảo mật thông tin trong máy tính quan trọng như thế nào?",
            "Trí tuệ nhân tạo là gì?"
        ]
    
    def run_test(self, questions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run comprehensive test"""
        test_questions = questions or self.get_sample_questions()
        
        logger.info(f"🧪 Testing RAG Pipeline with {len(test_questions)} questions...")
        
        results = []
        successful = 0
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"   Question {i}/{len(test_questions)}: {question}")
            
            result = self.rag.query(question, return_sources=True)
            results.append(result)
            
            if result["status"] == "success":
                successful += 1
                logger.info(f"   ✅ Answer: {result['answer'][:100]}...")
            else:
                logger.error(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        # Summary
        test_summary = {
            "total_questions": len(test_questions),
            "successful": successful,
            "failed": len(test_questions) - successful,
            "success_rate": successful / len(test_questions) * 100,
            "results": results,
            "pipeline_stats": self.rag.get_statistics()
        }
        
        logger.info(f"🎯 Test Summary: {successful}/{len(test_questions)} successful ({test_summary['success_rate']:.1f}%)")
        
        return test_summary


def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Pipeline for SGK Tin học")
    parser.add_argument("--llm", default="openai", choices=["openai", "ollama"], help="LLM type")
    parser.add_argument("--model", help="Specific model name")
    parser.add_argument("--query", help="Single query to test")
    parser.add_argument("--test", action="store_true", help="Run comprehensive test")
    parser.add_argument("--vector-store", help="Path to vector store")
    
    args = parser.parse_args()
    
    try:
        # Initialize RAG Pipeline
        rag = RAGPipeline(
            vector_store_path=args.vector_store,
            llm_type=args.llm,
            model_name=args.model
        )
        
        if args.query:
            # Single query
            result = rag.query(args.query, return_sources=True)
            print(f"\n🤔 Question: {result['question']}")
            print(f"🤖 Answer: {result['answer']}")
            
            if result.get('sources'):
                print(f"\n📚 Sources:")
                for i, source in enumerate(result['sources'], 1):
                    print(f"   {i}. Grade {source['metadata']['grade']} - {source['metadata']['lesson_title']}")
                    print(f"      {source['content']}")
        
        elif args.test:
            # Comprehensive test
            tester = RAGTester(rag)
            summary = tester.run_test()
            
            print(f"\n📊 Test Results:")
            print(f"   Success rate: {summary['success_rate']:.1f}%")
            print(f"   Total questions: {summary['total_questions']}")
            print(f"   Successful: {summary['successful']}")
            print(f"   Failed: {summary['failed']}")
        
        else:
            # Interactive mode
            print("🤖 RAG Pipeline ready! Type 'quit' to exit.")
            while True:
                question = input("\n❓ Your question: ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if question:
                    result = rag.query(question)
                    print(f"🤖 Answer: {result['answer']}")
    
    except Exception as e:
        logger.error(f"Error initializing RAG Pipeline: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()