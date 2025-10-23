# 🤖 Tin Học 11 RAG System

**Retrieval-Augmented Generation (RAG) System for Vietnamese Computer Science Education**

A complete AI assistant for Tin học 11 (Computer Science Grade 11) that combines OCR text extraction, vector search, and LLM capabilities to answer questions from Vietnamese textbooks.

## 🌟 Features

- **📖 Vietnamese OCR Processing**: Extracts text from PDF textbooks with high accuracy
- **🔍 Smart Vector Search**: Semantic search across 524 processed text chunks
- **🧠 AI-Powered Q&A**: Uses Google Gemini for intelligent responses
- **💻 Multiple Interfaces**: Command line, web interface, and offline mode
- **🆓 Free Tier Support**: Optimized for free API usage with offline fallback

## 🚀 Quick Start

### Option 1: Offline Mode (No API key needed)
```bash
# Double-click this file:
run_offline_chatbot.bat

# Or run manually:
python scripts/offline_chatbot.py
```

### Option 2: AI-Powered Mode (Requires API key)
```bash
# Set up your Google API key in .env file first
python scripts/simple_chatbot.py
```

### Option 3: Web Interface
```bash
# Double-click this file:
run_web_chatbot.bat

# Or run manually:
streamlit run scripts/streamlit_chatbot.py
```

## 🎯 Usage Examples

### Sample Questions
- "Hệ điều hành là gì?"
- "Windows có những tính năng gì?"
- "Phần mềm ứng dụng khác gì với phần mềm hệ thống?"
- "Cách bảo vệ máy tính khỏi virus?"
- "Microsoft Office có những phần mềm nào?"

## 🔄 Available Scripts

| Script | Purpose | API Required |
|--------|---------|-------------|
| `offline_chatbot.py` | Smart search without LLM | ❌ No |
| `simple_chatbot.py` | Full AI assistant | ✅ Yes |
| `streamlit_chatbot.py` | Web interface | ✅ Yes |
| `demo_search.py` | Search demonstration | ❌ No |

## 🆓 Free Tier Optimization

The system is optimized for Google Gemini's free tier:
- Uses `gemini-2.0-flash-lite` model
- Implements rate limiting and retry logic
- Provides offline fallback mode
- Optimized prompt engineering for token efficiency

Get your free API key from: https://makersuite.google.com/app/apikey

---

**Made with ❤️ for Vietnamese Computer Science Education** 🇻🇳
