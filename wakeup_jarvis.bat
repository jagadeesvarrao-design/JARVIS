@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title JARVIS SYSTEM - WAITING FOR NETWORK...
color 0a

:: 1. Wait 30 seconds for WiFi & OneDrive to load
echo [SYSTEM] Startup detected. Waiting 30 seconds for system stabilization...
timeout /t 30 /nobreak >nul

:: 2. Move to the correct folder
echo [SYSTEM] Locating Jarvis directory...
cd /d "C:\Users\DELL\OneDrive\Desktop\assistent"

:: Check if directory and project files exist (waiting for OneDrive mount)
if not exist "jarvis_gui.py" (
    echo [WARNING] Jarvis directory not synchronized yet. Waiting 15 more seconds...
    timeout /t 15 /nobreak >nul
)

:: 3. Run Jarvis using the virtual environment python directly
if exist ".venv\Scripts\python.exe" (
    echo [SYSTEM] Awakening Jarvis via virtual environment...
    ".venv\Scripts\python.exe" jarvis_gui.py
) else (
    echo [SYSTEM] Awakening Jarvis via uv...
    "C:\Users\DELL\.local\bin\uv.exe" run jarvis_gui.py
)

:: 4. Keep window open if it crashes (so you can see why)
if %ERRORLEVEL% neq 0 (
    echo [CRASH DETECTED] Jarvis stopped with exit code %ERRORLEVEL%.
    pause
) 
