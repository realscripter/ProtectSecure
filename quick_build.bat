@echo off
REM Quick build script for Windows
echo Building ProtectSecure...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Run build
echo.
echo Starting build process...
python build.py

echo.
echo Build complete!
pause
