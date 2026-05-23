@echo off
title Agent Meeting Room
cd /d "%~dp0"

echo.
echo  Agent Meeting Room
echo  ------------------
echo  Checking Ollama...

REM Check if Ollama is running
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo  [!] Ollama is not running. Starting it...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
)

echo  Starting server...
start "" "http://localhost:5000"
python app.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Could not start. Make sure Python and dependencies are installed.
    echo  Run: pip install -r requirements.txt
    pause
)
