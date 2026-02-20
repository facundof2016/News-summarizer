@echo off
REM Emergency News Summarizer + Welfare Board Launcher
REM Fixed version - doesn't require pip in PATH

REM Change to the script's directory
cd /d "%~dp0"

echo ========================================
echo Emcomm BBS + Welfare Board
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [1/5] Python found
echo.

REM Check for main application file
if not exist "emcomm_bbs.py" (
    echo [ERROR] emcomm_bbs.py not found!
    echo Please ensure you're in the correct directory.
    pause
    exit /b 1
)

echo [2/5] Main application found
echo.

REM Check for Welfare Board modules
set MISSING_MODULES=0

if not exist "parser.py" (
    echo [WARNING] parser.py not found - Welfare Board will be disabled
    set MISSING_MODULES=1
)
if not exist "validator.py" (
    echo [WARNING] validator.py not found - Welfare Board will be disabled
    set MISSING_MODULES=1
)
if not exist "aggregator.py" (
    echo [WARNING] aggregator.py not found - Welfare Board will be disabled
    set MISSING_MODULES=1
)
if not exist "output_generator.py" (
    echo [WARNING] output_generator.py not found - Welfare Board will be disabled
    set MISSING_MODULES=1
)
if not exist "file_watcher.py" (
    echo [WARNING] file_watcher.py not found - Welfare Board will be disabled
    set MISSING_MODULES=1
)

if %MISSING_MODULES%==0 (
    echo [3/5] Welfare Board modules found
) else (
    echo [3/5] Some Welfare Board modules missing ^(tab will be hidden^)
)
echo.

REM Check for watchdog library (FIXED - uses python -m pip)
python -c "import watchdog" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] watchdog library not installed
    echo Welfare Board requires this. Installing...
    python -m pip install watchdog
    if %errorlevel% neq 0 (
        echo [WARNING] Could not install watchdog automatically
        echo.
        echo Please run this command manually:
        echo    python -m pip install watchdog
        echo.
        echo Welfare Board will be disabled until installed
        echo Press any key to continue without Welfare Board...
        pause >nul
    ) else (
        echo [OK] watchdog installed successfully
    )
) else (
    echo [4/5] watchdog library found
)
echo.

REM Create necessary directories
if not exist "data\input" mkdir data\input >nul 2>&1
if not exist "data\archive" mkdir data\archive >nul 2>&1
if not exist "data\output" mkdir data\output >nul 2>&1
if not exist "data\error" mkdir data\error >nul 2>&1

echo [5/5] Directories ready
echo.
echo ========================================
echo Starting application...
echo ========================================
echo.

REM Launch the application
python emcomm_bbs.py

REM Check if it crashed
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Application exited with error code: %errorlevel%
    echo ========================================
    pause
    exit /b %errorlevel%
)

exit /b 0
