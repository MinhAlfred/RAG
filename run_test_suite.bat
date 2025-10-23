@echo off
echo ===================================================
echo    Smart AI Chatbot Test Suite
echo ===================================================
echo.
echo This tool helps you test the OpenAI chatbot with:
echo   - Predefined questions by category
echo   - Interactive Q&A mode  
echo   - Quick test with 3 basic questions
echo.
echo Make sure you have set OPENAI_API_KEY in .env file
echo ===================================================
echo.

cd /d "%~dp0"
"F:/Ky 8/Capstone/RAG/.venv/Scripts/python.exe" scripts/test_interactive.py
echo.
echo ===================================================
echo Test completed! Press any key to close...
pause >nul