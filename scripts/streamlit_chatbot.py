#!/usr/bin/env python3
"""
Streamlit Web Interface for Tin Hoc 11 Chatbot
A user-friendly web interface for the RAG chatbot
"""

import sys
from pathlib import Path
import os
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import streamlit as st
    from scripts.gemini_chatbot import TinHoc11ChatBot
except ImportError as e:
    st.error(f"Missing dependencies: {e}")
    st.info("Install with: pip install streamlit")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Tin Học 11 AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}

.user-message {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
}

.bot-message {
    background-color: #f3e5f5;
    border-left: 4px solid #9c27b0;
}

.sources {
    background-color: #fff3e0;
    padding: 0.5rem;
    border-radius: 0.25rem;
    margin-top: 0.5rem;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

def initialize_chatbot():
    """Initialize the chatbot"""
    if 'chatbot' not in st.session_state:
        with st.spinner('Đang khởi tạo AI Assistant...'):
            try:
                # Get API key from sidebar or environment
                api_key = st.sidebar.text_input(
                    "Google API Key", 
                    type="password",
                    help="Nhập API key từ Google AI Studio"
                )
                
                if api_key:
                    os.environ["GOOGLE_API_KEY"] = api_key
                
                st.session_state.chatbot = TinHoc11ChatBot()
                st.session_state.messages = []
                st.success("✅ AI Assistant đã sẵn sàng!")
                
            except Exception as e:
                st.error(f"❌ Lỗi khởi tạo: {e}")
                st.info("Vui lòng kiểm tra API key và thử lại")
                return False
    
    return True

def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Tin Học 11 AI Assistant</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #666;">
            Trợ lý AI thông minh cho môn Tin học lớp 11
        </p>
        <p style="color: #888;">
            Powered by Google Gemini Pro + Vector Search
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Cài đặt")
        
        # API Key input
        st.subheader("🔑 Google API Key")
        st.info("Lấy API key từ: https://makersuite.google.com/app/apikey")
        
        # Instructions
        st.subheader("📖 Hướng dẫn")
        st.markdown("""
        **Tôi có thể giúp bạn:**
        - Trả lời câu hỏi về Tin học
        - Giải thích khái niệm, định nghĩa
        - Hướng dẫn sử dụng phần mềm
        - Tìm thông tin trong sách giáo khoa
        
        **Ví dụ câu hỏi:**
        - "Hệ điều hành là gì?"
        - "Cách bảo vệ máy tính khỏi virus?"
        - "Windows có những tính năng gì?"
        """)
        
        # Clear chat button
        if st.button("🗑️ Xóa lịch sử chat"):
            st.session_state.messages = []
            if 'chatbot' in st.session_state:
                st.session_state.chatbot.clear_history()
            st.rerun()
    
    # Initialize chatbot
    if not initialize_chatbot():
        st.stop()
    
    # Initialize chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Chào bạn! Tôi là trợ lý AI cho môn Tin học 11. Bạn có câu hỏi gì về Tin học không? 😊",
            "sources": []
        })
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources if available
            if message.get("sources") and message["role"] == "assistant":
                with st.expander("📚 Nguồn tham khảo"):
                    for source in message["sources"]:
                        st.write(f"• {source}")
    
    # Chat input
    if prompt := st.chat_input("Đặt câu hỏi về Tin học..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "sources": []
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner("Đang suy nghĩ..."):
                try:
                    # Get response from chatbot
                    response = st.session_state.chatbot.chat(prompt)
                    
                    # Display response
                    message_placeholder.markdown(response['answer'])
                    
                    # Add to message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response['answer'],
                        "sources": response['sources']
                    })
                    
                    # Show sources
                    if response['sources']:
                        with st.expander("📚 Nguồn tham khảo"):
                            for source in response['sources']:
                                st.write(f"• {source}")
                    
                    # Show detailed search results if available
                    if response['search_results']:
                        with st.expander("🔍 Thông tin chi tiết từ sách"):
                            for i, result in enumerate(response['search_results'], 1):
                                st.write(f"**Trang {result['page']}:**")
                                content = result['content']
                                if len(content) > 300:
                                    content = content[:300] + "..."
                                st.write(content)
                                st.divider()
                
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
                    st.info("Vui lòng thử lại hoặc kiểm tra kết nối mạng")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🇻🇳 Tin Học 11 AI Assistant | Powered by Google Gemini Pro + ChromaDB
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()