@echo off
title Agent Meeting Room — Build
color 0A
echo.
echo  =============================================
echo   Agent Meeting Room — Release Builder
echo  =============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ from python.org
    pause & exit /b 1
)

REM Check/install PyInstaller
echo [1/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller --quiet
)

REM Install project dependencies
echo [2/4] Installing dependencies...
pip install -r requirements.txt --quiet

REM Clean old build
echo [3/4] Cleaning previous build...
if exist "dist\AgentMeetingRoom.exe" del /f /q "dist\AgentMeetingRoom.exe"
if exist "build" rmdir /s /q build

REM Copy icon to root for spec
if not exist "icon.ico" copy /y "assets\icon.ico" "icon.ico" >nul 2>&1

REM Run PyInstaller
echo [4/4] Building executable...
pyinstaller AgentMeetingRoom.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause & exit /b 1
)

echo.
echo  =============================================
echo   Build complete!
echo   Output: dist\AgentMeetingRoom.exe
echo  =============================================
echo.
pause
