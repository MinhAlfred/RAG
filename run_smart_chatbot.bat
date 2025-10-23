@echo off
echo Starting Tin Hoc 11 Smart AI Assistant (OpenAI GPT-3.5)...
echo.
echo This is the INTELLIGENT version using OpenAI GPT-3.5-turbo
echo Much smarter responses than offline mode!
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
"F:/Ky 8/Capstone/RAG/.venv/Scripts/python.exe" scripts/openai_chatbot.py
pause