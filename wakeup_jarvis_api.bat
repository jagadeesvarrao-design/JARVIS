@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title JARVIS SYSTEM - API SERVER MODE
color 0a

echo [SYSTEM] Locating Jarvis directory...
cd /d "C:\Users\DELL\OneDrive\Desktop\assistent"

if exist ".venv\Scripts\python.exe" (
    echo [SYSTEM] Awakening Jarvis API Server via virtual environment on port 5001...
    ".venv\Scripts\python.exe" jarvis_api.py
) else (
    echo [SYSTEM] Awakening Jarvis API Server via uv on port 5001...
    "C:\Users\DELL\.local\bin\uv.exe" run jarvis_api.py
)

if %ERRORLEVEL% neq 0 (
    echo [CRASH DETECTED] Jarvis API stopped with exit code %ERRORLEVEL%.
    pause
)
