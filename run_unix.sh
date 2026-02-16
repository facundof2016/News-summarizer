#!/bin/bash
################################################################################
# Emergency News Summarizer - Unix/Linux/macOS Launcher
# Version 1.0.0
################################################################################
#
# Purpose: Launch the main Emergency News Summarizer GUI application
#
# Features:
#  - Checks Python installation
#  - Verifies required files exist
#  - Checks dependencies
#  - Launches the GUI application
#
# Usage: 
#   chmod +x run_unix.sh
#   ./run_unix.sh
#
################################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Header
echo ""
echo "========================================================================"
echo "  EMERGENCY NEWS SUMMARIZER"
echo "  Version 1.0.0 - Ultra-Compact Reports for Radio Transmission"
echo "========================================================================"
echo ""
echo "Generating news, weather, space weather, and emergency alerts"
echo "optimized for HF/VHF packet radio, Winlink, and APRS."
echo ""
echo "========================================================================"
echo ""

################################################################################
# Step 1: Check Python Installation
################################################################################

echo "[1/4] Checking Python installation..."

# Try python3 first, then python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}  ERROR: Python is not installed!${NC}"
    echo ""
    echo "  Please install Python 3.8 or higher:"
    echo ""
    echo "  Ubuntu/Debian:"
    echo "    sudo apt-get update"
    echo "    sudo apt-get install python3 python3-pip python3-tk"
    echo ""
    echo "  macOS (with Homebrew):"
    echo "    brew install python-tk@3.11"
    echo ""
    echo "  Or download from: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

echo -e "${GREEN}  ✓ Python $PYTHON_VERSION found${NC}"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo -e "${RED}  ERROR: Python 3.8 or higher is required${NC}"
    echo "  You have Python $PYTHON_VERSION"
    exit 1
fi

################################################################################
# Step 2: Verify Required Files
################################################################################

echo ""
echo "[2/4] Checking required files..."

MISSING_FILES=0

if [ ! -f "news_summarizer.py" ]; then
    echo -e "${RED}  ERROR: news_summarizer.py not found!${NC}"
    MISSING_FILES=1
else
    echo -e "${GREEN}  ✓ news_summarizer.py found${NC}"
fi

if [ ! -f "emergency_module.py" ]; then
    echo -e "${RED}  ERROR: emergency_module.py not found!${NC}"
    MISSING_FILES=1
else
    echo -e "${GREEN}  ✓ emergency_module.py found${NC}"
fi

if [ ! -f "plaintext_generators.py" ]; then
    echo -e "${RED}  ERROR: plaintext_generators.py not found!${NC}"
    MISSING_FILES=1
else
    echo -e "${GREEN}  ✓ plaintext_generators.py found${NC}"
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo ""
    echo -e "${RED}  Some required files are missing!${NC}"
    echo "  Please make sure all files are in the same directory."
    echo ""
    exit 1
fi

################################################################################
# Step 3: Check Dependencies
################################################################################

echo ""
echo "[3/4] Checking Python dependencies..."

MISSING_DEPS=0

# Check requests
if $PYTHON_CMD -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}  ✓ requests installed${NC}"
else
    echo -e "${YELLOW}  WARNING: 'requests' package not found!${NC}"
    echo "  Run: pip3 install -r requirements.txt"
    MISSING_DEPS=1
fi

# Check beautifulsoup4
if $PYTHON_CMD -c "import bs4" 2>/dev/null; then
    echo -e "${GREEN}  ✓ beautifulsoup4 installed${NC}"
else
    echo -e "${YELLOW}  WARNING: 'beautifulsoup4' package not found!${NC}"
    echo "  Run: pip3 install -r requirements.txt"
    MISSING_DEPS=1
fi

# Check tkinter (required for GUI)
if $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
    echo -e "${GREEN}  ✓ tkinter installed${NC}"
else
    echo -e "${RED}  ERROR: 'tkinter' package not found!${NC}"
    echo ""
    echo "  Install tkinter:"
    echo "    Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "    Fedora/RHEL: sudo dnf install python3-tkinter"
    echo "    macOS: Usually included with Python from python.org"
    echo ""
    exit 1
fi

# Check anthropic (optional)
if $PYTHON_CMD -c "import anthropic" 2>/dev/null; then
    echo -e "${GREEN}  ✓ anthropic installed (AI summaries available)${NC}"
else
    echo -e "${BLUE}  NOTE: 'anthropic' package not found (optional for AI summaries)${NC}"
    echo "  Install with: pip3 install anthropic"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}  Required packages are missing!${NC}"
    echo ""
    echo "  Install them with:"
    echo "    pip3 install -r requirements.txt"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        exit 1
    fi
fi

################################################################################
# Step 4: Launch Application
################################################################################

echo ""
echo "[4/4] Launching Emergency News Summarizer..."
echo ""
echo "========================================================================"
echo ""

# Set display for X11 if needed
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

# Launch the GUI application
$PYTHON_CMD news_summarizer.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================================================"
    echo "  APPLICATION ERROR"
    echo "========================================================================"
    echo ""
    echo "  The application encountered an error."
    echo ""
    echo "  Common issues:"
    echo "    1. Missing dependencies - run: pip3 install -r requirements.txt"
    echo "    2. No X11 display - make sure DISPLAY is set"
    echo "    3. Permission issues - check file permissions"
    echo ""
    echo "  For detailed troubleshooting, see TROUBLESHOOTING.md"
    echo ""
    exit 1
fi

# Normal exit
echo ""
echo "Application closed."
echo ""
