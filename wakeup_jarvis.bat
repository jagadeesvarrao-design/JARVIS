@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title JARVIS SYSTEM - STARTUP IN PROGRESS
color 0a

:: 1. Wait 30 seconds for WiFi & OneDrive to load
echo [SYSTEM] Startup detected. Waiting 30 seconds for system stabilization...
timeout /t 30 /nobreak >nul

:: 2. Move to the correct folder
echo [SYSTEM] Locating Jarvis directory...
cd /d "C:\Users\DELL\OneDrive\Desktop\assistent"

:: Check if directory and project files exist (waiting for OneDrive mount)
if not exist "jarvis_api.py" (
    echo [WARNING] Jarvis directory not synchronized yet. Waiting 15 more seconds...
    timeout /t 15 /nobreak >nul
)

:: 3. Run Jarvis API Backend Server (starts Core JARVIS + Port 5001 API)
if exist ".venv\Scripts\python.exe" (
    echo [SYSTEM] Awakening Jarvis API Server via virtual environment...
    start "JARVIS Core API" ".venv\Scripts\python.exe" jarvis_api.py
) else (
    echo [SYSTEM] Awakening Jarvis API Server via uv...
    start "JARVIS Core API" "C:\Users\DELL\.local\bin\uv.exe" run jarvis_api.py
)

:: 4. Wait 5 seconds for API server to initialize
timeout /t 5 /nobreak >nul

:: 5. Run Next.js / Ultron Web HUD Client
echo [SYSTEM] Awakening Ultron HUD Web Client...
cd /d "C:\Users\DELL\OneDrive\Desktop\PROJECTS\ultron-by-sagar-builds"
start "Ultron HUD Web" cmd /c "npm run dev"

echo [SYSTEM] All systems initiated successfully.
