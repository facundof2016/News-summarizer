@echo off
REM Simple launcher that installs watchdog if needed

REM Change to the script's directory
cd /d "%~dp0"

echo Checking for watchdog library...

REM Check if watchdog is installed
python -c "import watchdog" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing watchdog...
    python -m pip install watchdog
    if %errorlevel% neq 0 (
        echo.
        echo WARNING: Could not install watchdog
        echo Welfare Board tab will not appear
        echo.
        echo You can install it manually later with:
        echo    python -m pip install watchdog
        echo.
        echo Press any key to continue...
        pause >nul
    ) else (
        echo Watchdog installed successfully!
        echo.
    )
) else (
    echo Watchdog already installed
    echo.
)

echo Starting Emcomm BBS...
echo.
python emcomm_bbs.py

if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error
    pause
)
