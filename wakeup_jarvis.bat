@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title JARVIS SYSTEM - WAITING FOR NETWORK...
color 0a

:: 1. Wait 30 seconds for WiFi & OneDrive to load
echo [SYSTEM] Startup detected. Waiting 30 seconds for system stabilizaton...
timeout /t 30 /nobreak >nul

:: 2. Move to the correct folder
echo [SYSTEM] Locating Jarvis directory...
cd /d "C:\Users\DELL\OneDrive\Desktop\assistent"

:: 3. Run Jarvis
echo [SYSTEM] Awakening Jarvis...
python jarvis_gui.py

:: 4. Keep window open if it crashes (so you can see why)
echo [CRASH DETECTED] Jarvis stopped. Read the error above.
pause 
