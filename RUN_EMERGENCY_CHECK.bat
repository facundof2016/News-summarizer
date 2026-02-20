@echo off
REM ============================================================================
REM Emergency Information Checker - Quick Launch Script
REM Emergency News Summarizer v1.0.0
REM ============================================================================
REM 
REM Purpose: Launch the standalone emergency checker tool
REM What it does: Display current emergency conditions in terminal
REM  - NWS weather alerts
REM  - USGS earthquakes (M4.5+)
REM  - FEMA disaster declarations
REM  - Emergency contact numbers
REM
REM Usage: Double-click this file, or run from command line
REM ============================================================================

title Emergency Information Checker

echo.
echo ========================================================================
echo   EMERGENCY INFORMATION CHECKER
echo   Emergency News Summarizer v1.0.0
echo ========================================================================
echo.
echo This tool displays current emergency conditions in your terminal.
echo.
echo Checking:
echo   - National Weather Service alerts
echo   - USGS earthquakes (M4.5+)
echo   - FEMA disaster declarations
echo   - Emergency contact information
echo.
echo Press Ctrl+C at any time to exit.
echo.
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Check if emergency_checker.py exists
if not exist "emergency_checker.py" (
    echo ERROR: emergency_checker.py not found!
    echo.
    echo Please make sure you're running this from the correct directory.
    echo The file should be in the same folder as this batch file.
    echo.
    pause
    exit /b 1
)

REM Check if emergency_module.py exists (required dependency)
if not exist "emergency_module.py" (
    echo ERROR: emergency_module.py not found!
    echo.
    echo This file is required for the emergency checker to work.
    echo Please make sure all files are in the same directory.
    echo.
    pause
    exit /b 1
)

REM Run the emergency checker
echo Starting emergency checker...
echo.
python emergency_checker.py

REM Check if there was an error
if errorlevel 1 (
    echo.
    echo ========================================================================
    echo   ERROR OCCURRED
    echo ========================================================================
    echo.
    echo The emergency checker encountered an error.
    echo.
    echo Common issues:
    echo   1. Missing dependencies - run: pip install -r requirements.txt
    echo   2. No internet connection - checker needs internet to fetch data
    echo   3. API rate limits - try again in a few minutes
    echo.
    echo For more help, see TROUBLESHOOTING.md or create an issue on GitHub.
    echo.
)

echo.
echo ========================================================================
echo.
pause
