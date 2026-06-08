@echo off
cd /d "%~dp0"
uv run streamlit run dashboard.py --server.headless true