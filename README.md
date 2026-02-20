# Emcomm BBS

**Emergency Communications Bulletin Board System for Amateur Radio**

Emcomm BBS is a Windows desktop application that provides two core services for emergency communications nets:

1. **News & Information Aggregator** — Fetches, summarizes, and saves radio-ready bulletins from public data sources (news, NWS weather, NOAA space weather, emergency alerts, power outages, and Twitter/X feeds) on a configurable schedule.

2. **Welfare Check-in Board** — Monitors a folder for incoming welfare check-in files received over [VarAC](https://www.varac-hamradio.com/) or any other digital transfer mode, validates them, and generates a live TXT/HTML/CSV board for net control use.

All output files are written directly to the VarAC BBS serving directory (`C:\VarAC BBS` by default), so stations requesting content over the air receive the most recently generated files automatically.

---

## Features

### Main Tab — Bulletin Generation
| Checkbox | Source | Output |
|---|---|---|
| News Summary | BBC, AP, CNN + Anthropic AI | `news_YYYY-MM-DD_HHMM.txt/.pdf/.html` |
| Weather Forecasts | NWS API (by FEMA region) | `weather_rN_YYYY-MM-DD_HHMM.txt/.pdf` |
| Space Weather | NOAA SWPC | `space_weather_YYYY-MM-DD_HHMM.txt/.pdf` |
| Emergency Alerts | NWS, USGS, FEMA, NIFC | `emergency_YYYY-MM-DD_HHMM.txt/.html` |
| Power Outages | DOE/ORNL ODIN API | `power_outages_MMDD_HHMM.txt` |
| Twitter Feed | Twitter/X API v2 | `twitter_YYYY-MM-DD_HHMM.txt/.html` |

### Power Outage Geographical Enrichment
The power outage report uses the public **ODIN API** (`odin.ornl.gov`) — no API key required. Each utility is automatically mapped to its state using a built-in EIA Form 861 lookup table (~185 entries) with name-pattern inference as fallback. The report shows outages grouped by state and sorted by most-affected utilities.

### Welfare Board Tab
- Watches a folder for incoming `.txt` check-in files in real time
- Validates required fields: `CALLSIGN`, `NAME`, `LOCATION`, `STATUS`
- Optional `POWER` field: `ON`, `OFF`, or `GENERATOR` — color-coded in HTML output
- Detects and handles retransmissions (exact duplicate) vs. updates (changed content)
- Generates TXT (radio-compact), HTML (live-refresh every 30s), and CSV outputs
- Configurable time windows (e.g., Morning Net 08:00–10:00, Evening Net 19:00–21:00)

---

## Requirements

- **Python 3.8+** — [python.org](https://www.python.org/downloads/)
- **Windows** (tested on Windows 10/11; uses Tkinter GUI)
- Internet connection for data fetching

Install Python dependencies:
```
pip install -r requirements.txt
```

Or just run `RUN.bat` — it installs `watchdog` automatically if missing.

### Optional API Keys
| Feature | Key Required | Where to Get It |
|---|---|---|
| AI News Summary | Anthropic API key | [console.anthropic.com](https://console.anthropic.com) |
| Twitter/X Feed | Twitter Bearer Token | [developer.twitter.com](https://developer.twitter.com) |
| News, Weather, Space Weather, Alerts, Power Outages | **None** | — |

---

## Installation

1. **Clone this branch** or download the ZIP and extract it to a folder of your choice.

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Launch the app:**
   - Double-click `RUN.bat` (recommended), or
   - Run `python emcomm_bbs.py` from the command line.

4. **First-time setup** — see `Emcomm_BBS_User_Guide.txt` for full step-by-step instructions.

---

## File Structure

```
emcomm_bbs/
│
├── emcomm_bbs.py                  # Main application (GUI + all bulletin generators)
│
├── Welfare Board modules
├── aggregator.py                  # Check-in deduplication and update tracking
├── file_watcher.py                # Folder monitoring (watchdog)
├── output_generator.py            # TXT/HTML/CSV welfare board generation
├── parser.py                      # Check-in file parser and field validator
├── plaintext_generators.py        # Ultra-compact plain text report formatters
├── validator.py                   # Business logic validation (status, time windows)
├── welfare_board.py               # Welfare Board GUI tab
│
├── welfare_checkin_template.txt   # Blank check-in form for distribution to stations
│
├── RUN.bat                        # Simple launcher (auto-installs watchdog)
├── RUN_EMERGENCY_SUITE_FIXED.bat  # Full diagnostic launcher with pre-flight checks
├── requirements.txt               # Python dependencies
├── Emcomm_BBS_User_Guide.txt      # Complete user documentation
│
└── examples/
    ├── EXAMPLE_KK4ODA_welfare.txt         # Sample initial check-in
    ├── EXAMPLE_KK4ODA_welfare_-_2.txt     # Sample updated check-in (same station)
    └── EXAMPLE_W1ABC_welfare.txt          # Sample check-in from second station
```

---

## Check-in Template Format

Distribute `welfare_checkin_template.txt` to participating stations before the net. The format is:

```
CALLSIGN: KK4ODA

NAME: Benito

LOCATION: Atlanta, GA

STATUS: SAFE

POWER: ON

MESSAGE: All good here. Generator fueled for 72 hours.
```

**Required fields:** `CALLSIGN`, `NAME`, `LOCATION`, `STATUS`  
**Optional fields:** `POWER`, `MESSAGE`

Valid `STATUS` values: `SAFE` · `NEED ASSISTANCE` · `TRAFFIC`  
Valid `POWER` values: `ON` · `OFF` · `GENERATOR`

---

## VarAC Integration

1. Set the Welfare Board **Monitor Folder** to your VarAC `Files in` directory.
2. Set the **Output Directory** (Settings tab) to `C:\VarAC BBS` (or your VarAC BBS path).
3. Stations transmit their completed check-in file via VarAC file transfer to your BBS callsign.
4. VarAC drops the file in `Files in` → Emcomm BBS picks it up within seconds → board updates automatically.

---

## Data Sources

| Source | Data | API |
|---|---|---|
| BBC / AP / CNN | News headlines | Web scrape (public) |
| NOAA NWS | Weather forecasts | `api.weather.gov` (no key) |
| NOAA SWPC | Space weather / HF conditions | `services.swpc.noaa.gov` (no key) |
| NOAA NWS | Active weather alerts | `api.weather.gov/alerts` (no key) |
| USGS | Earthquake data | `earthquake.usgs.gov` (no key) |
| FEMA | Disaster declarations | `www.fema.gov/api` (no key) |
| NIFC | Active wildfires | `arcgis.nifc.gov` (no key) |
| DOE/ORNL ODIN | Power outages | `odin.ornl.gov/odi/status` (no key) |
| EIA Form 861 | Utility→state mapping | Built-in lookup table (no key) |
| Twitter/X | Agency feeds | API v2 Bearer Token (free tier) |
| Anthropic Claude | AI news summary | API key (paid) |

---

## License

This project is shared for the amateur radio community. No warranty is expressed or implied. Use at your own risk during actual emergency operations — always have backup communication plans.

**73 de KK4ODA**
