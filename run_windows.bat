@echo off
REM ============================================================================
REM Emergency News Summarizer - Windows Launcher
REM Version 1.0.0
REM ============================================================================
REM 
REM Purpose: Launch the main Emergency News Summarizer GUI application
REM
REM Features:
REM  - Checks Python installation
REM  - Verifies required files exist
REM  - Checks dependencies
REM  - Launches the GUI application
REM
REM Usage: Double-click this file, or run from command line
REM ============================================================================

title Emergency News Summarizer

echo.
echo ========================================================================
echo   EMERGENCY NEWS SUMMARIZER
echo   Version 1.0.0 - Ultra-Compact Reports for Radio Transmission
echo ========================================================================
echo.
echo Generating news, weather, space weather, and emergency alerts
echo optimized for HF/VHF packet radio, Winlink, and APRS.
echo.
echo ========================================================================
echo.

REM ============================================================================
REM Step 1: Check Python Installation
REM ============================================================================

echo [1/4] Checking Python installation...

python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python is not installed or not in PATH!
    echo.
    echo   Please install Python 3.8 or higher from:
    echo     https://www.python.org/downloads/
    echo.
    echo   During installation, make sure to:
    echo     [x] Add Python to PATH
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   ✓ Python %PYTHON_VERSION% found

REM ============================================================================
REM Step 2: Verify Required Files
REM ============================================================================

echo.
echo [2/4] Checking required files...

set MISSING_FILES=0

if not exist "news_summarizer.py" (
    echo   ERROR: news_summarizer.py not found!
    set MISSING_FILES=1
) else (
    echo   ✓ news_summarizer.py found
)

if not exist "emergency_module.py" (
    echo   ERROR: emergency_module.py not found!
    set MISSING_FILES=1
) else (
    echo   ✓ emergency_module.py found
)

if not exist "plaintext_generators.py" (
    echo   ERROR: plaintext_generators.py not found!
    set MISSING_FILES=1
) else (
    echo   ✓ plaintext_generators.py found
)

if %MISSING_FILES%==1 (
    echo.
    echo   Some required files are missing!
    echo   Please make sure all files are in the same directory.
    echo.
    pause
    exit /b 1
)

REM ============================================================================
REM Step 3: Check Dependencies
REM ============================================================================

echo.
echo [3/4] Checking Python dependencies...

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo   WARNING: 'requests' package not found!
    echo   Run: pip install -r requirements.txt
    set MISSING_DEPS=1
) else (
    echo   ✓ requests installed
)

python -c "import bs4" >nul 2>&1
if errorlevel 1 (
    echo   WARNING: 'beautifulsoup4' package not found!
    echo   Run: pip install -r requirements.txt
    set MISSING_DEPS=1
) else (
    echo   ✓ beautifulsoup4 installed
)

python -c "import anthropic" >nul 2>&1
if errorlevel 1 (
    echo   NOTE: 'anthropic' package not found (optional for AI summaries)
    echo   Install with: pip install anthropic
) else (
    echo   ✓ anthropic installed (AI summaries available)
)

if defined MISSING_DEPS (
    echo.
    echo   Required packages are missing!
    echo.
    echo   Install them with:
    echo     pip install -r requirements.txt
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" exit /b 1
)

REM ============================================================================
REM Step 4: Launch Application
REM ============================================================================

echo.
echo [4/4] Launching Emergency News Summarizer...
echo.
echo ========================================================================
echo.

REM Launch the GUI application
python news_summarizer.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ========================================================================
    echo   APPLICATION ERROR
    echo ========================================================================
    echo.
    echo   The application encountered an error.
    echo.
    echo   Common issues:
    echo     1. Missing dependencies - run: pip install -r requirements.txt
    echo     2. Port already in use - close other instances
    echo     3. Permission issues - run as administrator
    echo.
    echo   For detailed troubleshooting, see TROUBLESHOOTING.md
    echo.
    pause
    exit /b 1
)

REM Normal exit
echo.
echo Application closed.
echo.
pause
