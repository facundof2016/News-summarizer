# Changelog

All notable changes to the Emergency News Summarizer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024-12-14

### 🎉 Initial Release

Complete emergency communications tool optimized for low-bandwidth radio transmission.

### ✨ Features

#### Core Functionality
- **News Summaries** - BBC News and Associated Press headlines
- **AI-Powered Analysis** - Optional Claude API integration for intelligent summaries
- **Weather Forecasts** - All 50 US states, 120+ cities across 10 FEMA regions
- **Space Weather** - Real-time HF band propagation conditions
- **Emergency Alerts** - NWS warnings, USGS earthquakes, FEMA disasters
- **Twitter Feeds** - Customizable emergency account monitoring

#### Radio Optimization
- **Ultra-Compact Format** - 95% smaller than PDF alternatives (~40 KB vs 700 KB)
- **Fast Transmission** - 3 minutes @ 1200 baud vs 70 minutes for PDFs
- **Plain Text Output** - 75 chars/line, word-wrapped for packet radio
- **Complete Information** - No truncation, full emergency details preserved

#### User Interface
- **Selective Output Generation** - Checkboxes to choose which reports to create
- **Regional Selection** - Individual FEMA weather region selection (R1-R10)
- **Quick Selection Buttons** - "Select All" / "None" for weather regions
- **Automatic Updates** - Scheduled generation every 6 hours (configurable 1-24h)
- **Easy-to-Use GUI** - Windows desktop application, no command line needed

#### Customization
- **Customizable Twitter Accounts** - Monitor any emergency accounts
- **Flexible Update Intervals** - Main reports: 1-24h, Twitter: 1-12h
- **API Key Management** - Optional Anthropic and Twitter API integration
- **Directory Selection** - Choose custom save location

#### File Management
- **Minimal Storage** - Keeps only newest file set (~40 KB)
- **Auto-Cleanup** - Old files removed before each generation
- **Compact Filenames** - Format: `type_MMDD_HHMM.txt`

### 🔧 Technical Implementation

#### Space Weather Module
- Real-time K-index from NOAA API
- Calculated A-index from K-index
- Individual band conditions (80m, 40m, 30m, 20m, 17m, 15m, 12m, 10m)
- Smart propagation calculations based on solar flux + K-index
- Complete 3-day NOAA forecast (no truncation)

#### Emergency Alerts Module
- Complete NWS alert information (event, areas, headline, description, timing)
- Full earthquake details (magnitude, location, time, depth)
- Complete FEMA disaster information (number, state, type, title, date)
- Up to 15 alerts, 10 earthquakes, 5 FEMA disasters per report

#### Twitter Integration
- Twitter API v2 support
- Customizable account list via GUI
- Complete tweet text with smart word wrapping
- Long URL handling (URLs on separate lines)
- Debug logging for truncation detection

#### News Module
- AI-powered summaries using Claude Sonnet 4
- Fallback to basic summaries without API key
- Detailed logging (AI vs basic summary)
- Duplicate headline prevention

### 🐛 Bug Fixes

#### Band Conditions Display
- **Fixed:** Band conditions showing "No data available"
- **Solution:** Added real-time K-index fetching from NOAA API
- **Enhancement:** Individual band calculations instead of grouped ranges

#### Tweet File Generation
- **Fixed:** Tweet files not being generated
- **Solution:** Added missing method call in generate_all()
- **Result:** Tweets now generated on both schedules (6h main + 1h Twitter)

#### News Headline Duplication
- **Fixed:** Headlines appearing twice in news file
- **Solution:** Changed basic summary to overview instead of listing headlines
- **Result:** 50% file size reduction (12 KB → 6 KB)

#### Space Weather Forecast Truncation
- **Fixed:** Forecast showing only 3 lines with cut-off text
- **Solution:** Increased fetcher limit (500 → 3000 chars), removed line limit, added word wrapping
- **Result:** Complete 3-day forecast with all details

#### Emergency Alert Information
- **Fixed:** Alerts truncated at 25/35 characters
- **Solution:** Removed all truncation limits, added word wrapping
- **Enhancement:** Added description field with critical details
- **Result:** Complete alert information (headlines, descriptions, timing)

#### Tweet Text Truncation
- **Fixed:** Tweets truncated after two lines
- **Solution:** Improved word wrapping, handles long URLs, removes hard limits
- **Result:** Complete tweet text, no information loss

### 📊 File Size Comparison

| Format | Size | Transmission @ 1200 baud |
|--------|------|--------------------------|
| PDF (compressed) | 700 KB | 70 minutes |
| HTML | 850 KB | 85 minutes |
| **Plain Text** | **40 KB** | **3 minutes** |

**Reduction:** 95% smaller, 25× faster transmission

### 🗺️ Coverage

- **States:** All 50 US states
- **Cities:** 120+ major cities
- **FEMA Regions:** All 10 regions
- **Weather Sources:** OpenWeatherMap API
- **Space Weather:** NOAA Space Weather Prediction Center
- **Emergency:** NWS, USGS, FEMA, NASA APIs

### 📡 Radio Modes Supported

- HF Packet Radio (300/1200 baud)
- VHF/UHF Packet (9600 baud)
- Winlink (HF/VHF)
- APRS Bulletins
- Any digital mode supporting text files

### 💾 Storage

- **Per Generation:** ~40 KB (full set) or 2-21 KB (selective)
- **Retention:** Only newest set kept
- **File Count:** 1-15 files depending on selection

### 🔐 Security

- No API keys stored in code (GUI entry only)
- Sensitive files excluded via .gitignore
- No personal data in output files

### 📝 Documentation

- Comprehensive README with examples
- Detailed feature guides (SELECTIVE_OUTPUT_FEATURE.md, etc.)
- Bug fix documentation for all resolved issues
- GitHub setup guide for contributors

### 🎯 Use Cases

- Amateur Radio EmComm/ARES operations
- RACES emergency communications
- SKYWARN severe weather spotting
- Field Day operations
- Emergency management coordination
- Weather net transmissions
- DX/Contest propagation updates

---

## [Unreleased]

### Planned Features
- MacOS and Linux support
- Additional news sources (Reuters, AFP)
- International weather (WMO)
- Enhanced space weather predictions
- Direct APRS integration
- Winlink RMS connector
- Web interface option
- Mobile companion app

---

## Version History Summary

- **v1.0.0** (2024-12-14) - Initial release with full feature set

---

## Notes

### Breaking Changes
None in v1.0.0 (initial release)

### Deprecations
None in v1.0.0 (initial release)

### Migration Guide
Not applicable for v1.0.0 (initial release)

---

For detailed information about specific features and fixes, see the documentation in `/docs`.

For support and bug reports, please visit [GitHub Issues](https://github.com/yourusername/emergency-news-radio/issues).
