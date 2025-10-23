@echo off
echo Starting Tin Hoc 11 AI Assistant Web Interface...
echo.
echo Opening in your default browser...
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
"F:/Ky 8/Capstone/RAG/.venv/Scripts/python.exe" -m streamlit run scripts/streamlit_chatbot.py --server.port 8501 --server.headless false