@echo off
echo ================================================
echo News Summarizer - Ultra Simple Launcher
echo ================================================
echo.

REM Go to where this file is
cd /d "%~dp0"

echo Current folder: %CD%
echo.

REM Check Python
echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK!
echo.

REM Install packages
echo [2/4] Installing packages (this may take 1-2 minutes)...
echo Installing beautifulsoup4...
python -m pip install beautifulsoup4
echo Installing requests...
python -m pip install requests
echo Installing reportlab...
python -m pip install reportlab
echo Installing anthropic...
python -m pip install anthropic
echo Installing lxml...
python -m pip install lxml
echo.

REM Verify
echo [3/4] Verifying packages...
python -c "import bs4; print('  beautifulsoup4: OK')"
python -c "import requests; print('  requests: OK')"
python -c "import reportlab; print('  reportlab: OK')"
python -c "import anthropic; print('  anthropic: OK')"
python -c "import lxml; print('  lxml: OK')"
echo.

REM Run
echo [4/4] Starting News Summarizer...
echo.
python news_summarizer.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    pause
)
