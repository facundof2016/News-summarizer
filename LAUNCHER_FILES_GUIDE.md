# Launcher Files - Complete Guide

## 📦 Updated Files Created

All launcher files have been updated for v1.0.0 with comprehensive error checking and helpful messages!

---

## 📋 Files Overview

### 1. **requirements.txt** ✅
**Purpose:** Python package dependencies  
**Updated:** Comprehensive documentation with installation notes  

**What's included:**
```
requests>=2.31.0         # HTTP requests (required)
beautifulsoup4>=4.12.0   # HTML parsing (required)
anthropic>=0.18.0        # AI summaries (optional)
```

**New features:**
- Detailed installation instructions
- Platform-specific notes (Windows/Linux/macOS)
- Troubleshooting tips
- Offline installation guide
- Security notes

**Install:**
```bash
pip install -r requirements.txt
```

---

### 2. **run_windows.bat** ✅
**Purpose:** Main app launcher for Windows  
**Alternative to:** EASIEST_NEWS_START.bat  

**Features:**
- ✅ Checks Python installation
- ✅ Verifies Python version (3.8+)
- ✅ Checks all required files exist
- ✅ Validates dependencies
- ✅ Helpful error messages
- ✅ Step-by-step progress display

**Usage:**
```
Double-click run_windows.bat
```

**Output:**
```
========================================================================
  EMERGENCY NEWS SUMMARIZER
  Version 1.0.0 - Ultra-Compact Reports for Radio Transmission
========================================================================

[1/4] Checking Python installation...
  ✓ Python 3.11.5 found

[2/4] Checking required files...
  ✓ news_summarizer.py found
  ✓ emergency_module.py found
  ✓ plaintext_generators.py found

[3/4] Checking Python dependencies...
  ✓ requests installed
  ✓ beautifulsoup4 installed
  ✓ anthropic installed (AI summaries available)

[4/4] Launching Emergency News Summarizer...

========================================================================
```

---

### 3. **run_unix.sh** ✅
**Purpose:** Main app launcher for Linux/macOS  
**New feature:** Cross-platform support!

**Features:**
- ✅ Colored output (green ✓, red ✗, yellow ⚠)
- ✅ Checks Python 3 installation
- ✅ Validates Python version
- ✅ Checks tkinter availability
- ✅ Platform-specific error messages
- ✅ X11 display handling

**Usage:**
```bash
chmod +x run_unix.sh
./run_unix.sh
```

**Platform notes:**
- **Ubuntu/Debian:** Install tkinter with `sudo apt-get install python3-tk`
- **macOS:** Use Python from python.org (includes tkinter)
- **Fedora/RHEL:** Install with `sudo dnf install python3-tkinter`

---

### 4. **RUN_EMERGENCY_CHECK.bat** ✅
**Purpose:** Standalone emergency checker launcher  
**Runs:** emergency_checker.py

**Features:**
- ✅ Checks Python installation
- ✅ Verifies emergency_checker.py exists
- ✅ Checks emergency_module.py dependency
- ✅ Helpful error messages
- ✅ Explains what the tool does

**Usage:**
```
Double-click RUN_EMERGENCY_CHECK.bat
```

**Output:**
```
========================================================================
  EMERGENCY INFORMATION CHECKER
  Emergency News Summarizer v1.0.0
========================================================================

This tool displays current emergency conditions in your terminal.

Checking:
  - National Weather Service alerts
  - USGS earthquakes (M4.5+)
  - FEMA disaster declarations
  - Emergency contact information

========================================================================

Starting emergency checker...

[Shows live emergency data]
```

---

## 🎯 Which Launcher to Use?

### **For Windows Users:**

**Option 1: EASIEST_NEWS_START.bat** (Simple)
```batch
@echo off
python news_summarizer.py
pause
```
- Minimal, just launches the app
- No error checking
- Fastest startup

**Option 2: run_windows.bat** (Recommended)
- Full error checking
- Validates everything
- Helpful messages
- Better for troubleshooting

**Recommendation:** Use `run_windows.bat` - it's more helpful!

---

### **For Linux/macOS Users:**

**Use: run_unix.sh**
- Only option for Unix systems
- Colored output
- Platform-specific help
- Checks tkinter availability

---

### **For Quick Emergency Check:**

**Use: RUN_EMERGENCY_CHECK.bat** (Windows)
- Quick terminal-based emergency info
- No GUI needed
- Fast startup

---

## 📊 File Comparison

| File | Platform | Purpose | Error Checking | Output |
|------|----------|---------|----------------|--------|
| **EASIEST_NEWS_START.bat** | Windows | Main app | None | Minimal |
| **run_windows.bat** | Windows | Main app | Full | Detailed |
| **run_unix.sh** | Linux/macOS | Main app | Full | Colored |
| **RUN_EMERGENCY_CHECK.bat** | Windows | Emergency check | Full | Detailed |

---

## 🚀 GitHub Upload Recommendations

### **Essential Files (Upload These):**
1. ✅ requirements.txt
2. ✅ run_windows.bat
3. ✅ run_unix.sh
4. ✅ EASIEST_NEWS_START.bat (keep as simple option)
5. ✅ RUN_EMERGENCY_CHECK.bat

**Why all of them?**
- requirements.txt - Everyone needs dependencies
- run_windows.bat - Best Windows launcher
- EASIEST_NEWS_START.bat - Simple fallback for Windows
- run_unix.sh - Linux/macOS support
- RUN_EMERGENCY_CHECK.bat - Bonus emergency tool

**Total size:** ~20 KB for all launchers

---

## 📝 Usage Instructions for GitHub

### **In README.md, you can say:**

**Quick Start (Windows):**
```bash
# Clone repository
git clone https://github.com/yourusername/emergency-news-radio.git
cd emergency-news-radio

# Install dependencies
pip install -r requirements.txt

# Run the app
run_windows.bat
```

**Quick Start (Linux/macOS):**
```bash
# Clone repository
git clone https://github.com/yourusername/emergency-news-radio.git
cd emergency-news-radio

# Install dependencies
pip3 install -r requirements.txt

# Make launcher executable
chmod +x run_unix.sh

# Run the app
./run_unix.sh
```

**Emergency Checker (Windows):**
```bash
# Quick emergency information check
RUN_EMERGENCY_CHECK.bat
```

---

## 🔧 Error Messages Explained

### **"Python is not installed or not in PATH"**

**Windows (run_windows.bat):**
```
ERROR: Python is not installed or not in PATH!

Please install Python 3.8 or higher from:
  https://www.python.org/downloads/

During installation, make sure to:
  [x] Add Python to PATH
```

**Linux/macOS (run_unix.sh):**
```
ERROR: Python is not installed!

Please install Python 3.8 or higher:

Ubuntu/Debian:
  sudo apt-get update
  sudo apt-get install python3 python3-pip python3-tk

macOS (with Homebrew):
  brew install python-tk@3.11

Or download from: https://www.python.org/downloads/
```

---

### **"Required files are missing"**

Both launchers check for:
- news_summarizer.py
- emergency_module.py
- plaintext_generators.py

If any are missing, you'll see exactly which ones.

---

### **"Required packages are missing"**

The launchers check for:
- requests (required)
- beautifulsoup4 (required)
- anthropic (optional - for AI summaries)
- tkinter (required on Linux/macOS - usually included on Windows)

Missing packages are clearly indicated with installation instructions.

---

## 💡 Pro Tips

### **Tip 1: Use the Full Launchers for New Users**
```
Recommend: run_windows.bat or run_unix.sh
Why: They catch problems before the app launches
```

### **Tip 2: EASIEST_NEWS_START.bat for Experienced Users**
```
If you know everything works, use the simple launcher
Faster startup, no checking overhead
```

### **Tip 3: Check Dependencies Once**
```bash
# Verify everything is installed
python -c "import requests, bs4, anthropic"

# If no errors, everything is good!
```

### **Tip 4: Emergency Checker for Quick Checks**
```
Use RUN_EMERGENCY_CHECK.bat for:
- Quick terminal view of current alerts
- No GUI needed
- Fast startup
- Good for SSH/remote sessions
```

---

## 🎨 Customization

### **Add Your Own Launcher:**

You can create custom launchers for specific use cases:

**Example: Auto-start with specific region:**
```batch
@echo off
REM Custom launcher for Region 4 only
python news_summarizer.py --region 4
pause
```

**Example: Emergency-only launcher:**
```batch
@echo off
REM Emergency information only
python news_summarizer.py --emergency-only
pause
```

---

## ✅ Testing Checklist

After downloading all files:

**Windows:**
- [ ] Run `run_windows.bat` - Does it launch?
- [ ] Run `EASIEST_NEWS_START.bat` - Does it launch?
- [ ] Run `RUN_EMERGENCY_CHECK.bat` - Does it show emergency data?

**Linux/macOS:**
- [ ] Run `chmod +x run_unix.sh`
- [ ] Run `./run_unix.sh` - Does it launch?
- [ ] Check for tkinter errors

**All Platforms:**
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify all dependencies install correctly

---

## 📞 Troubleshooting

### **Launcher won't run:**
- Make sure you're in the correct directory
- Check file permissions (chmod +x on Unix)
- Verify Python is installed

### **Dependencies fail to install:**
- Update pip: `pip install --upgrade pip`
- Try with --user flag: `pip install --user -r requirements.txt`
- Check internet connection

### **GUI won't start (Linux):**
- Install tkinter: `sudo apt-get install python3-tk`
- Set DISPLAY: `export DISPLAY=:0`
- Check X11 is running

---

## 🎉 Summary

**What's New:**
- ✅ Comprehensive requirements.txt with documentation
- ✅ Full-featured run_windows.bat with error checking
- ✅ Cross-platform run_unix.sh for Linux/macOS
- ✅ Updated RUN_EMERGENCY_CHECK.bat for emergency tool
- ✅ Helpful error messages throughout
- ✅ Platform-specific installation instructions

**All files ready for GitHub upload!** 🚀

Upload all launcher files to give users the best experience on their platform! 📡✨
