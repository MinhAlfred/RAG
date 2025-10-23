@echo off
echo Starting Tin Hoc 11 Offline AI Assistant...
echo.
echo This version works without API key - using smart search only
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
"F:/Ky 8/Capstone/RAG/.venv/Scripts/python.exe" scripts/offline_chatbot.py
pause