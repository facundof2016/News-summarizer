#!/usr/bin/env python3
"""
Emcomm BBS Desktop App
Fetches news from BBC, AP, and CNN every 6 hours and generates PDF summaries
Includes weather forecasts for major US cities and space weather conditions
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import shutil
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from reportlab.rl_config import defaultPageSize
import anthropic
import json

# Enable PDF compression for smaller file sizes
from reportlab.pdfgen import canvas
canvas.Canvas.setPageCompression = lambda self, val: setattr(self, '_pageCompression', 1)

# Import emergency module
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from emergency_module import EmergencyDataFetcher, EmergencyResourcesFetcher, SocialMediaEmergencyFetcher
except ImportError:
    # Emergency module not available - will disable emergency features
    EmergencyDataFetcher = None
    EmergencyResourcesFetcher = None
    SocialMediaEmergencyFetcher = None

# Import Nextdoor module
try:
    from nextdoor_module import NextdoorFetcher, MockNextdoorData
    NEXTDOOR_AVAILABLE = True
except ImportError:
    NextdoorFetcher = None
    MockNextdoorData = None
    NEXTDOOR_AVAILABLE = False

# Import Welfare Board modules
try:
    from parser import WelfareParser
    from validator import WelfareValidator
    from aggregator import WelfareAggregator
    from output_generator import OutputGenerator
    from file_watcher import WelfareFileWatcher
    WELFARE_BOARD_AVAILABLE = True
except ImportError:
    WelfareParser = None
    WelfareValidator = None
    WelfareAggregator = None
    OutputGenerator = None
    WelfareFileWatcher = None
    WELFARE_BOARD_AVAILABLE = False

# Import plain text generators for radio transmission
try:
    from plaintext_generators import PlainTextGenerator
    PLAINTEXT_AVAILABLE = True
except ImportError:
    PlainTextGenerator = None
    PLAINTEXT_AVAILABLE = False


# Major US cities - Top 2 cities per state + state capitals with FEMA regions
# Format: 'City, State': (latitude, longitude, FEMA_region)
MAJOR_US_CITIES = {
    # Alabama
    'Birmingham, AL': (33.5186, -86.8104, 4),
    'Montgomery, AL': (32.3792, -86.3077, 4),
    # Alaska
    'Anchorage, AK': (61.2181, -149.9003, 10),
    'Juneau, AK': (58.3019, -134.4197, 10),
    # Arizona
    'Phoenix, AZ': (33.4484, -112.0740, 9),
    'Tucson, AZ': (32.2226, -110.9747, 9),
    # Arkansas
    'Little Rock, AR': (34.7465, -92.2896, 6),
    'Fort Smith, AR': (35.3859, -94.3985, 6),
    # California
    'Los Angeles, CA': (34.0522, -118.2437, 9),
    'San Diego, CA': (32.7157, -117.1611, 9),
    'San Jose, CA': (37.3382, -121.8863, 9),
    'San Francisco, CA': (37.7749, -122.4194, 9),
    'Fresno, CA': (36.7378, -119.7871, 9),
    'Sacramento, CA': (38.5816, -121.4944, 9),
    # Colorado
    'Denver, CO': (39.7392, -104.9903, 8),
    'Colorado Springs, CO': (38.8339, -104.8214, 8),
    # Connecticut
    'Bridgeport, CT': (41.1865, -73.1952, 1),
    'Hartford, CT': (41.7658, -72.6734, 1),
    # Delaware
    'Wilmington, DE': (39.7391, -75.5398, 3),
    'Dover, DE': (39.1582, -75.5244, 3),
    # Florida
    'Jacksonville, FL': (30.3322, -81.6557, 4),
    'Miami, FL': (25.7617, -80.1918, 4),
    'Tampa, FL': (27.9506, -82.4572, 4),
    'Orlando, FL': (28.5383, -81.3792, 4),
    'Tallahassee, FL': (30.4383, -84.2807, 4),
    # Georgia
    'Atlanta, GA': (33.7490, -84.3880, 4),
    'Augusta, GA': (33.4735, -82.0105, 4),
    # Hawaii
    'Honolulu, HI': (21.3099, -157.8581, 9),
    'Hilo, HI': (19.7070, -155.0835, 9),
    # Idaho
    'Boise, ID': (43.6150, -116.2023, 10),
    'Meridian, ID': (43.6121, -116.3915, 10),
    # Illinois
    'Chicago, IL': (41.8781, -87.6298, 5),
    'Springfield, IL': (39.7817, -89.6501, 5),
    # Indiana
    'Indianapolis, IN': (39.7684, -86.1581, 5),
    'Fort Wayne, IN': (41.0793, -85.1394, 5),
    # Iowa
    'Des Moines, IA': (41.5868, -93.6250, 7),
    'Cedar Rapids, IA': (41.9779, -91.6656, 7),
    # Kansas
    'Wichita, KS': (37.6872, -97.3301, 7),
    'Topeka, KS': (39.0558, -95.6890, 7),
    # Kentucky
    'Louisville, KY': (38.2527, -85.7585, 4),
    'Lexington, KY': (38.0406, -84.5037, 4),
    # Louisiana
    'New Orleans, LA': (29.9511, -90.0715, 6),
    'Baton Rouge, LA': (30.4515, -91.1871, 6),
    # Maine
    'Portland, ME': (43.6591, -70.2568, 1),
    'Augusta, ME': (44.3106, -69.7795, 1),
    # Maryland
    'Baltimore, MD': (39.2904, -76.6122, 3),
    'Annapolis, MD': (38.9784, -76.4922, 3),
    # Massachusetts
    'Boston, MA': (42.3601, -71.0589, 1),
    'Worcester, MA': (42.2626, -71.8023, 1),
    # Michigan
    'Detroit, MI': (42.3314, -83.0458, 5),
    'Grand Rapids, MI': (42.9634, -85.6681, 5),
    # Minnesota
    'Minneapolis, MN': (44.9778, -93.2650, 5),
    'St. Paul, MN': (44.9537, -93.0900, 5),
    # Mississippi
    'Jackson, MS': (32.2988, -90.1848, 4),
    'Gulfport, MS': (30.3674, -89.0928, 4),
    # Missouri
    'Kansas City, MO': (39.0997, -94.5786, 7),
    'St. Louis, MO': (38.6270, -90.1994, 7),
    # Montana
    'Billings, MT': (45.7833, -108.5007, 8),
    'Helena, MT': (46.5891, -112.0391, 8),
    # Nebraska
    'Omaha, NE': (41.2565, -95.9345, 7),
    'Lincoln, NE': (40.8136, -96.7026, 7),
    # Nevada
    'Las Vegas, NV': (36.1699, -115.1398, 9),
    'Reno, NV': (39.5296, -119.8138, 9),
    # New Hampshire
    'Manchester, NH': (42.9956, -71.4548, 1),
    'Concord, NH': (43.2081, -71.5376, 1),
    # New Jersey
    'Newark, NJ': (40.7357, -74.1724, 2),
    'Jersey City, NJ': (40.7178, -74.0431, 2),
    # New Mexico
    'Albuquerque, NM': (35.0844, -106.6504, 6),
    'Santa Fe, NM': (35.6870, -105.9378, 6),
    # New York
    'New York, NY': (40.7128, -74.0060, 2),
    'Buffalo, NY': (42.8864, -78.8784, 2),
    'Albany, NY': (42.6526, -73.7562, 2),
    # North Carolina
    'Charlotte, NC': (35.2271, -80.8431, 4),
    'Raleigh, NC': (35.7796, -78.6382, 4),
    # North Dakota
    'Fargo, ND': (46.8772, -96.7898, 8),
    'Bismarck, ND': (46.8083, -100.7837, 8),
    # Ohio
    'Columbus, OH': (39.9612, -82.9988, 5),
    'Cleveland, OH': (41.4993, -81.6944, 5),
    'Cincinnati, OH': (39.1031, -84.5120, 5),
    # Oklahoma
    'Oklahoma City, OK': (35.4676, -97.5164, 6),
    'Tulsa, OK': (36.1540, -95.9928, 6),
    # Oregon
    'Portland, OR': (45.5152, -122.6784, 10),
    'Salem, OR': (44.9429, -123.0351, 10),
    # Pennsylvania
    'Philadelphia, PA': (39.9526, -75.1652, 3),
    'Pittsburgh, PA': (40.4406, -79.9959, 3),
    'Harrisburg, PA': (40.2732, -76.8867, 3),
    # Rhode Island
    'Providence, RI': (41.8240, -71.4128, 1),
    'Warwick, RI': (41.7001, -71.4162, 1),
    # South Carolina
    'Columbia, SC': (34.0007, -81.0348, 4),
    'Charleston, SC': (32.7765, -79.9311, 4),
    # South Dakota
    'Sioux Falls, SD': (43.5446, -96.7311, 8),
    'Pierre, SD': (44.3683, -100.3510, 8),
    # Tennessee
    'Nashville, TN': (36.1627, -86.7816, 4),
    'Memphis, TN': (35.1495, -90.0490, 4),
    # Texas
    'Houston, TX': (29.7604, -95.3698, 6),
    'San Antonio, TX': (29.4241, -98.4936, 6),
    'Dallas, TX': (32.7767, -96.7970, 6),
    'Austin, TX': (30.2672, -97.7431, 6),
    'Fort Worth, TX': (32.7555, -97.3308, 6),
    'El Paso, TX': (31.7619, -106.4850, 6),
    # Utah
    'Salt Lake City, UT': (40.7608, -111.8910, 8),
    'Provo, UT': (40.2338, -111.6585, 8),
    # Vermont
    'Burlington, VT': (44.4759, -73.2121, 1),
    'Montpelier, VT': (44.2601, -72.5754, 1),
    # Virginia
    'Virginia Beach, VA': (36.8529, -75.9780, 3),
    'Richmond, VA': (37.5407, -77.4360, 3),
    # Washington
    'Seattle, WA': (47.6062, -122.3321, 10),
    'Spokane, WA': (47.6588, -117.4260, 10),
    'Olympia, WA': (47.0379, -122.9007, 10),
    # West Virginia
    'Charleston, WV': (38.3498, -81.6326, 3),
    'Huntington, WV': (38.4192, -82.4452, 3),
    # Wisconsin
    'Milwaukee, WI': (43.0389, -87.9065, 5),
    'Madison, WI': (43.0731, -89.4012, 5),
    # Wyoming
    'Cheyenne, WY': (41.1400, -104.8202, 8),
    'Casper, WY': (42.8500, -106.3250, 8),
}

FEMA_REGIONS = {
    1: "Region 1 (New England): CT, MA, ME, NH, RI, VT",
    2: "Region 2 (New York/New Jersey): NJ, NY, PR, VI",
    3: "Region 3 (Mid-Atlantic): DC, DE, MD, PA, VA, WV",
    4: "Region 4 (Southeast): AL, FL, GA, KY, MS, NC, SC, TN",
    5: "Region 5 (Midwest): IL, IN, MI, MN, OH, WI",
    6: "Region 6 (South): AR, LA, NM, OK, TX",
    7: "Region 7 (Great Plains): IA, KS, MO, NE",
    8: "Region 8 (Rocky Mountains): CO, MT, ND, SD, UT, WY",
    9: "Region 9 (Southwest/Pacific): AZ, CA, HI, NV, Guam",
    10: "Region 10 (Northwest): AK, ID, OR, WA"
}


class WeatherFetcher:
    """Fetches weather data for US cities using NWS API"""
    
    def __init__(self):
        self.base_url = "https://api.weather.gov"
    
    def get_forecast(self, lat, lon, city_name, fema_region):
        """Get 7-day forecast for a location"""
        try:
            point_url = f"{self.base_url}/points/{lat},{lon}"
            headers = {'User-Agent': '(NewsApp, contact@example.com)'}
            
            response = requests.get(point_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            forecast_url = data['properties']['forecast']
            
            forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
            if forecast_response.status_code != 200:
                return None
            
            forecast_data = forecast_response.json()
            periods = forecast_data['properties']['periods'][:14]  # 7 days = 14 periods (day/night)
            
            return {
                'city': city_name,
                'fema_region': fema_region,
                'current': periods[0] if periods else None,
                'forecast': periods
            }
        except Exception as e:
            return None
    
    def get_all_forecasts(self, selected_regions=None, log_callback=None):
        """Get forecasts for selected FEMA regions only
        
        Args:
            selected_regions: List of region numbers to fetch (e.g., [1, 4, 5])
                             If None, fetches all regions
            log_callback: Optional callback for logging progress
        """
        # If no regions specified, fetch all
        if selected_regions is None:
            selected_regions = list(range(1, 11))
        
        # Initialize only selected regions
        forecasts_by_region = {i: [] for i in selected_regions}
        
        # Filter cities to only those in selected regions
        cities_to_fetch = {
            city: location 
            for city, location in MAJOR_US_CITIES.items() 
            if location[2] in selected_regions  # location[2] is fema_region
        }
        
        total = len(cities_to_fetch)
        if log_callback:
            log_callback(f"Fetching weather for {total} cities in {len(selected_regions)} region(s)...")
        
        for i, (city, location) in enumerate(cities_to_fetch.items(), 1):
            lat, lon, fema_region = location
            if log_callback:
                log_callback(f"  Fetching {city} ({i}/{total})...")
            forecast = self.get_forecast(lat, lon, city, fema_region)
            if forecast:
                forecasts_by_region[fema_region].append(forecast)
            time.sleep(0.3)  # Rate limiting
        
        return forecasts_by_region


class SpaceWeatherFetcher:
    """Fetches space weather and HF radio conditions from NOAA"""
    
    def __init__(self):
        self.base_url = "https://services.swpc.noaa.gov"
    
    def get_conditions(self):
        """Get comprehensive space weather data"""
        try:
            headers = {'User-Agent': '(NewsApp, contact@example.com)'}
            conditions = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
                'solar_flux': None,
                'sunspot_number': None,
                'a_index': None,
                'k_index': None,
            }
            
            # Get current solar indices
            try:
                indices_url = f"{self.base_url}/json/solar-cycle/observed-solar-cycle-indices.json"
                response = requests.get(indices_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        latest = data[-1]
                        conditions['solar_flux'] = latest.get('f10.7')
                        conditions['sunspot_number'] = latest.get('ssn')
            except:
                pass
            
            # Get K-index (planetary)
            try:
                planetary_url = f"{self.base_url}/json/planetary_k_index_1m.json"
                response = requests.get(planetary_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        latest = data[-1]
                        # Try both possible field names
                        conditions['k_index'] = latest.get('kp_index', latest.get('kp', latest.get('k_index')))
            except:
                pass
            
            # Calculate A-index from K-index
            if conditions['k_index'] is not None:
                try:
                    k = float(conditions['k_index'])
                    # Conversion table from K to A
                    if k < 1: conditions['a_index'] = 2
                    elif k < 2: conditions['a_index'] = 6
                    elif k < 3: conditions['a_index'] = 12
                    elif k < 4: conditions['a_index'] = 22
                    elif k < 5: conditions['a_index'] = 40
                    elif k < 6: conditions['a_index'] = 70
                    elif k < 7: conditions['a_index'] = 120
                    elif k < 8: conditions['a_index'] = 200
                    else: conditions['a_index'] = 300
                except:
                    pass
            
            # Get 3-day forecast
            try:
                forecast_url = f"{self.base_url}/text/3-day-forecast.txt"
                response = requests.get(forecast_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    # Get full forecast (NOAA forecasts are typically 1500-2500 chars)
                    conditions['forecast'] = response.text[:3000]
            except:
                pass
            
            # Calculate HF band conditions based on solar activity
            sfi = conditions.get('solar_flux')
            k = conditions.get('k_index')
            
            if sfi and k is not None:
                try:
                    k = float(k)
                    sfi = float(sfi)
                    
                    # Band conditions based on solar flux and geomagnetic activity
                    if k <= 2:  # Quiet
                        hf_bands = {
                            '80m': 'Good',
                            '40m': 'Good',
                            '30m': 'Good',
                            '20m': 'Excellent' if sfi > 100 else 'Good',
                            '17m': 'Excellent' if sfi > 100 else 'Good',
                            '15m': 'Excellent' if sfi > 120 else 'Good',
                            '12m': 'Good' if sfi > 120 else 'Fair',
                            '10m': 'Excellent' if sfi > 150 else 'Good' if sfi > 100 else 'Fair',
                        }
                    elif k <= 4:  # Unsettled
                        hf_bands = {
                            '80m': 'Good',
                            '40m': 'Fair',
                            '30m': 'Fair',
                            '20m': 'Good' if sfi > 100 else 'Fair',
                            '17m': 'Fair',
                            '15m': 'Fair',
                            '12m': 'Fair',
                            '10m': 'Fair' if sfi > 100 else 'Poor',
                        }
                    else:  # Disturbed
                        hf_bands = {
                            '80m': 'Fair',
                            '40m': 'Fair',
                            '30m': 'Poor',
                            '20m': 'Poor',
                            '17m': 'Poor',
                            '15m': 'Poor',
                            '12m': 'Poor',
                            '10m': 'Poor',
                        }
                except:
                    # Fallback if conversion fails
                    hf_bands = {
                        '80m': 'Good',
                        '40m': 'Good',
                        '30m': 'Good',
                        '20m': 'Good',
                        '17m': 'Fair',
                        '15m': 'Fair',
                        '12m': 'Fair',
                        '10m': 'Fair',
                    }
            else:
                # Fallback estimates if data not available
                hf_bands = {
                    '80m': 'Good',
                    '40m': 'Good',
                    '30m': 'Good',
                    '20m': 'Good',
                    '17m': 'Fair',
                    '15m': 'Fair',
                    '12m': 'Fair',
                    '10m': 'Fair',
                }
            
            conditions['hf_conditions'] = hf_bands
            conditions['band_conditions'] = hf_bands  # Alias for text generator
            
            return conditions
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M UTC")}


class NewsSource:
    """Base class for news sources"""
    def __init__(self, name, url):
        self.name = name
        self.url = url
    
    def fetch_headlines(self, max_articles=10):
        """Fetch headlines from the news source"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = self._parse_articles(soup, max_articles)
            return articles
        except Exception as e:
            return [f"Error fetching from {self.name}: {str(e)}"]
    
    def _parse_articles(self, soup, max_articles):
        """Override this method in subclasses for specific parsing"""
        # Generic headline extraction
        headlines = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4'], limit=max_articles):
            text = tag.get_text(strip=True)
            if text and len(text) > 20:  # Filter out very short text
                headlines.append(text)
        return headlines[:max_articles]


class BBCNews(NewsSource):
    def __init__(self):
        super().__init__("BBC News", "https://www.bbc.com/news")
    
    def _parse_articles(self, soup, max_articles):
        headlines = []
        # BBC specific selectors
        for article in soup.find_all(['h2', 'h3'], limit=max_articles * 2):
            text = article.get_text(strip=True)
            if text and len(text) > 20 and text not in headlines:
                headlines.append(text)
                if len(headlines) >= max_articles:
                    break
        return headlines


class APNews(NewsSource):
    def __init__(self):
        super().__init__("Associated Press", "https://apnews.com")
    
    def _parse_articles(self, soup, max_articles):
        headlines = []
        for article in soup.find_all(['h2', 'h3'], limit=max_articles * 2):
            text = article.get_text(strip=True)
            if text and len(text) > 20 and text not in headlines:
                headlines.append(text)
                if len(headlines) >= max_articles:
                    break
        return headlines


class CNNNews(NewsSource):
    def __init__(self):
        super().__init__("CNN", "https://www.cnn.com")
    
    def _parse_articles(self, soup, max_articles):
        headlines = []
        for article in soup.find_all(['h2', 'h3'], limit=max_articles * 2):
            text = article.get_text(strip=True)
            if text and len(text) > 20 and text not in headlines:
                headlines.append(text)
                if len(headlines) >= max_articles:
                    break
        return headlines


class NewsSummarizer:
    """Handles fetching and summarizing news using Claude API"""
    
    def __init__(self):
        self.sources = [
            BBCNews(),
            APNews()
        ]
        # Note: In production, this should be loaded from environment or config
        self.api_key = None
    
    def set_api_key(self, api_key):
        """Set the Anthropic API key"""
        self.api_key = api_key
    
    def fetch_all_news(self):
        """Fetch news from all sources"""
        all_news = {}
        for source in self.sources:
            all_news[source.name] = source.fetch_headlines(max_articles=15)
        return all_news
    
    def generate_summary(self, news_data):
        """Generate a summary using Claude API"""
        if not self.api_key:
            # Fallback: create a basic summary without AI
            print("INFO: No API key configured - using basic summary")
            return self._create_basic_summary(news_data)
        
        try:
            print("INFO: Generating AI summary with Claude API...")
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Prepare the news content
            news_text = ""
            for source, headlines in news_data.items():
                news_text += f"\n{source}:\n"
                for i, headline in enumerate(headlines, 1):
                    news_text += f"{i}. {headline}\n"
            
            prompt = f"""Please create a concise news summary based on these headlines from BBC News and Associated Press. 

Headlines:
{news_text}

Please provide:
1. A brief overview of the top stories (2-3 paragraphs)
2. Key topics and themes emerging from the news
3. Any important developing stories

Keep the summary informative but concise, suitable for a daily news digest."""
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            print("INFO: AI summary generated successfully")
            return message.content[0].text
        except Exception as e:
            print(f"WARNING: AI summary failed ({str(e)}) - using basic summary")
            return f"[AI summary unavailable: {str(e)}]\n\n" + self._create_basic_summary(news_data)
    
    def _create_basic_summary(self, news_data):
        """Create a basic summary without AI - just count headlines by source"""
        # Don't include headlines here - they're added separately by the text generator
        # Just provide a simple count/overview
        total_headlines = sum(len(headlines) for headlines in news_data.values())
        sources = ", ".join(news_data.keys())
        
        summary = f"Daily news digest from {sources}.\n"
        summary += f"{total_headlines} headlines retrieved.\n"
        summary += "Top stories cover breaking news, politics, world events, and more.\n\n"
        summary += "NOTE: AI summary not available. Set Anthropic API key in settings for detailed summaries."
        
        return summary


class HTMLGenerator:
    """Base class for HTML generation with common styling"""
    
    @staticmethod
    def get_base_style():
        """Return base CSS styling for all HTML reports"""
        return """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 20px;
                font-size: 28px;
            }
            h2 {
                color: #34495e;
                margin-top: 25px;
                margin-bottom: 15px;
                font-size: 20px;
                border-left: 4px solid #3498db;
                padding-left: 12px;
            }
            h3 {
                color: #555;
                margin-top: 15px;
                margin-bottom: 10px;
                font-size: 16px;
            }
            .timestamp {
                color: #7f8c8d;
                font-size: 14px;
                margin-bottom: 20px;
            }
            .section {
                margin-bottom: 30px;
            }
            .alert-critical {
                background: #fee;
                border-left: 4px solid #e74c3c;
                padding: 15px;
                margin: 10px 0;
                border-radius: 4px;
            }
            .alert-warning {
                background: #fef5e7;
                border-left: 4px solid #f39c12;
                padding: 15px;
                margin: 10px 0;
                border-radius: 4px;
            }
            .alert-info {
                background: #eaf2f8;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 10px 0;
                border-radius: 4px;
            }
            .item {
                margin: 12px 0;
                padding: 10px;
                background: #f9f9f9;
                border-radius: 4px;
            }
            .forecast-period {
                margin: 8px 0;
                padding: 8px;
                background: #f0f7ff;
                border-radius: 4px;
            }
            .tweet {
                border-left: 3px solid #1da1f2;
                padding: 12px;
                margin: 10px 0;
                background: #f8fbff;
                border-radius: 4px;
            }
            .tweet-account {
                color: #1da1f2;
                font-weight: bold;
            }
            .tweet-time {
                color: #657786;
                font-size: 13px;
            }
            a {
                color: #3498db;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            @media print {
                body { background: white; padding: 0; }
                .container { box-shadow: none; }
            }
            @media (max-width: 600px) {
                body { padding: 10px; }
                .container { padding: 15px; }
                h1 { font-size: 24px; }
            }
        </style>
        """


class NewsHTMLGenerator:
    """Generates HTML news summaries"""
    
    @staticmethod
    def create_html(filename, summary_text, news_data):
        """Create an HTML file with news summary"""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News Summary - {datetime.now().strftime("%m/%d/%Y")}</title>
    {HTMLGenerator.get_base_style()}
</head>
<body>
    <div class="container">
        <h1>📰 Daily News Summary</h1>
        <div class="timestamp">{timestamp}</div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="item">
                {summary_text.replace(chr(10), '<br>')}
            </div>
        </div>
"""
        
        # Add headlines by source
        for source_name, headlines in news_data.items():
            html += f"""
        <div class="section">
            <h2>{source_name}</h2>
"""
            for i, headline in enumerate(headlines, 1):
                html += f"""            <div class="item">
                <strong>{i}.</strong> {headline}
            </div>
"""
            html += """        </div>
"""
        
        html += """    </div>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)


class PDFGenerator:
    """Generates PDF documents from news summaries"""
    
    @staticmethod
    def create_pdf(filename, summary_text, news_data):
        """Create a PDF with the news summary"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            compress=1  # Enable compression for smaller file size
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1a1a1a',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#333333',
            spaceAfter=12,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        )
        
        # Build content
        story = []
        
        # Title
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        title = Paragraph(f"News Summary<br/>{timestamp}", title_style)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # AI Summary section
        if summary_text and not summary_text.startswith("Error"):
            story.append(Paragraph("Executive Summary", heading_style))
            # Split summary into paragraphs
            for para in summary_text.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
                    story.append(Spacer(1, 0.1*inch))
            
            story.append(PageBreak())
        
        # Headlines by source
        story.append(Paragraph("Headlines by Source", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        for source, headlines in news_data.items():
            story.append(Paragraph(source, heading_style))
            for headline in headlines:
                if not headline.startswith("Error"):
                    bullet = Paragraph(f"• {headline}", body_style)
                    story.append(bullet)
            story.append(Spacer(1, 0.15*inch))
        
        # Build PDF
        doc.build(story)


class WeatherHTMLGenerator:
    """Generates weather forecast HTML by FEMA region"""
    
    @staticmethod
    def create_html(filename, region_number, forecasts):
        """Create an HTML file with weather forecasts for a specific FEMA region"""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        region_desc = FEMA_REGIONS.get(region_number, "Unknown Region")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather - FEMA Region {region_number}</title>
    {HTMLGenerator.get_base_style()}
</head>
<body>
    <div class="container">
        <h1>🌤️ Weather Forecast - FEMA Region {region_number}</h1>
        <div class="timestamp">{timestamp}</div>
        <div class="alert-info">
            <strong>{region_desc}</strong>
        </div>
"""
        
        for forecast in forecasts:
            city = forecast['city']
            periods = forecast.get('forecast', [])
            
            html += f"""
        <div class="section">
            <h2>{city}</h2>
"""
            
            for period in periods:
                period_name = period.get('name', '')
                temp = period.get('temperature', '')
                temp_unit = period.get('temperatureUnit', 'F')
                forecast_text = period.get('shortForecast', '')
                
                html += f"""            <div class="forecast-period">
                <strong>{period_name}:</strong> {temp}°{temp_unit}, {forecast_text}
            </div>
"""
            
            html += """        </div>
"""
        
        html += """    </div>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)


class WeatherPDFGenerator:
    """Generates weather forecast PDFs by FEMA region"""
    
    @staticmethod
    def create_pdf(filename, region_number, forecasts):
        """Create a PDF with weather forecasts for a specific FEMA region"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            compress=1  # Enable compression
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=15
        )
        
        region_style = ParagraphStyle(
            'Region',
            parent=styles['Heading2'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        city_style = ParagraphStyle(
            'City',
            parent=styles['Heading2'],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=5
        )
        
        forecast_style = ParagraphStyle(
            'Forecast',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=3
        )
        
        story = []
        
        # Title
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        title = Paragraph(f"Weather Forecast - FEMA Region {region_number}<br/>{timestamp}", title_style)
        story.append(title)
        
        # Region description
        region_desc = FEMA_REGIONS.get(region_number, "Unknown Region")
        story.append(Paragraph(region_desc, region_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Add forecasts
        for i, forecast in enumerate(forecasts):
            city = forecast['city']
            periods = forecast.get('forecast', [])
            
            # City name
            story.append(Paragraph(f"<b>{city}</b>", city_style))
            
            # Show all forecast periods (7 days = 14 periods)
            for period in periods:
                period_name = period.get('name', '')
                temp = period.get('temperature', '')
                temp_unit = period.get('temperatureUnit', 'F')
                forecast_text = period.get('shortForecast', '')
                
                forecast_line = f"<b>{period_name}:</b> {temp}°{temp_unit}, {forecast_text}"
                story.append(Paragraph(forecast_line, forecast_style))
            
            story.append(Spacer(1, 0.15*inch))
            
            # Add page break every 3 cities
            if (i + 1) % 3 == 0 and i < len(forecasts) - 1:
                story.append(PageBreak())
        
        doc.build(story)


class SpaceWeatherHTMLGenerator:
    """Generates space weather HTML"""
    
    @staticmethod
    def create_html(filename, conditions):
        """Create an HTML file with space weather conditions"""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Space Weather</title>
    {HTMLGenerator.get_base_style()}
</head>
<body>
    <div class="container">
        <h1>🌞 Space Weather & HF Radio Conditions</h1>
        <div class="timestamp">{timestamp}</div>
        
        <div class="section">
            <h2>Current Solar Activity</h2>
            <div class="item">
                <strong>Solar Flux:</strong> {conditions.get('solar_flux', 'N/A')} SFU<br>
                <strong>Sunspot Number:</strong> {conditions.get('sunspot_number', 'N/A')}<br>
                <strong>A-Index:</strong> {conditions.get('a_index', 'N/A')}<br>
                <strong>K-Index:</strong> {conditions.get('k_index', 'N/A')}
            </div>
        </div>
        
        <div class="section">
            <h2>HF Radio Band Conditions</h2>
"""
        
        band_conditions = conditions.get('band_conditions', {})
        for band, condition in band_conditions.items():
            html += f"""            <div class="item">
                <strong>{band}:</strong> {condition}
            </div>
"""
        
        forecast = conditions.get('forecast', '')
        if forecast:
            html += f"""
        <div class="section">
            <h2>3-Day Forecast</h2>
            <div class="item">
                {forecast.replace(chr(10), '<br>')}
            </div>
        </div>
"""
        
        html += """    </div>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)


class SpaceWeatherPDFGenerator:
    """Generates space weather PDFs"""
    
    @staticmethod
    def create_pdf(filename, conditions):
        """Create a PDF with space weather conditions"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            compress=1  # Enable compression
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=8
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        story = []
        
        # Title
        title = Paragraph(f"Space Weather & HF Radio Conditions<br/>{conditions.get('timestamp', '')}", title_style)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Solar Activity
        story.append(Paragraph("Solar Activity", heading_style))
        
        if conditions.get('solar_flux'):
            story.append(Paragraph(f"Solar Flux (10.7 cm): {conditions['solar_flux']}", body_style))
        
        if conditions.get('sunspot_number'):
            story.append(Paragraph(f"Sunspot Number: {conditions['sunspot_number']}", body_style))
        
        story.append(Spacer(1, 0.1*inch))
        
        # HF Radio Conditions
        story.append(Paragraph("HF Radio Propagation Conditions", heading_style))
        
        hf = conditions.get('hf_conditions', {})
        for band, condition in hf.items():
            if band != 'status':
                story.append(Paragraph(f"<b>{band}:</b> {condition}", body_style))
        
        if hf.get('status'):
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"<i>{hf['status']}</i>", body_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # 3-Day Forecast
        if conditions.get('forecast_text'):
            story.append(Paragraph("3-Day Space Weather Forecast", heading_style))
            forecast_lines = conditions['forecast_text'].split('\n')
            for line in forecast_lines[:50]:  # Limit lines
                if line.strip():
                    story.append(Paragraph(line, body_style))
        
        # Error handling
        if conditions.get('error'):
            story.append(Paragraph(f"Error fetching data: {conditions['error']}", body_style))
        
        doc.build(story)


class EmergencyHTMLGenerator:
    """Generates emergency information HTML"""
    
    @staticmethod
    def create_html(filename, emergency_data, resources):
        """Create an HTML file with emergency information"""
        timestamp = emergency_data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency Information</title>
    {HTMLGenerator.get_base_style()}
</head>
<body>
    <div class="container">
        <h1>🚨 Emergency Information Report</h1>
        <div class="timestamp">{timestamp}</div>
        
        <div class="section">
            <h2>⚠️ National Weather Service Alerts</h2>
"""
        
        alerts = emergency_data.get('nws_alerts', [])
        if not alerts or (isinstance(alerts, list) and len(alerts) > 0 and alerts[0].get('error')):
            html += """            <div class="item">No active alerts or data unavailable</div>
"""
        else:
            critical_alerts = [a for a in alerts if a.get('severity') in ['Extreme', 'Severe']]
            other_alerts = [a for a in alerts if a.get('severity') not in ['Extreme', 'Severe']]
            
            if critical_alerts:
                html += """            <h3 style="color: #e74c3c;">Critical Alerts</h3>
"""
                for alert in critical_alerts[:10]:
                    event = alert.get('event', 'Unknown')
                    areas = alert.get('areas', 'Unknown')
                    headline = alert.get('headline', '')
                    severity = alert.get('severity', '')
                    
                    html += f"""            <div class="alert-critical">
                <strong>{severity.upper()}: {event}</strong><br>
                <strong>Areas:</strong> {areas}<br>
                {headline}
            </div>
"""
            
            if other_alerts:
                html += """            <h3>Other Alerts & Advisories</h3>
"""
                for alert in other_alerts[:10]:
                    event = alert.get('event', 'Unknown')
                    areas = alert.get('areas', 'Unknown')
                    html += f"""            <div class="alert-warning">
                <strong>{event}:</strong> {areas}
            </div>
"""
        
        html += """        </div>
        
        <div class="section">
            <h2>🌍 Recent Earthquakes (M4.5+, Last 7 Days)</h2>
"""
        
        quakes = emergency_data.get('usgs_earthquakes', [])
        if not quakes or (isinstance(quakes, list) and len(quakes) > 0 and quakes[0].get('error')):
            html += """            <div class="item">No significant earthquakes</div>
"""
        else:
            for quake in quakes[:15]:
                if quake.get('error'):
                    continue
                mag = quake.get('magnitude', 'Unknown')
                location = quake.get('location', 'Unknown')
                time = quake.get('time', 'Unknown')
                depth = quake.get('depth', 'Unknown')
                
                html += f"""            <div class="item">
                <strong>M{mag}</strong> - {location}<br>
                <strong>Time:</strong> {time} | <strong>Depth:</strong> {depth} km
            </div>
"""
        
        html += """        </div>
        
        <div class="section">
            <h2>🏛️ FEMA Disaster Declarations (Last 30 Days)</h2>
"""
        
        disasters = emergency_data.get('fema_disasters', [])
        if not disasters or (isinstance(disasters, list) and len(disasters) > 0 and disasters[0].get('error')):
            html += """            <div class="item">No recent disaster declarations</div>
"""
        else:
            for disaster in disasters[:15]:
                if disaster.get('error'):
                    continue
                num = disaster.get('disaster_number', 'Unknown')
                state = disaster.get('state', 'Unknown')
                incident = disaster.get('incident_type', 'Unknown')
                title = disaster.get('title', '')
                date = disaster.get('date', 'Unknown')
                
                html += f"""            <div class="item">
                <strong>{num} - {state}</strong><br>
                {incident}: {title}<br>
                <strong>Date:</strong> {date}
            </div>
"""
        
        html += """        </div>
        
        <div class="section">
            <h2>🔥 Active Fire Incidents (Last 24 Hours)</h2>
"""
        
        fires = emergency_data.get('fire_incidents', {})
        if fires.get('error'):
            html += f"""            <div class="item">Error: {fires['error']}</div>
"""
        elif fires.get('active_fires_24h'):
            html += f"""            <div class="item">
                <strong>{fires['active_fires_24h']} thermal anomalies detected</strong><br>
                {fires.get('message', '')}<br>
                <em>Source: {fires.get('source', 'Unknown')}</em>
            </div>
"""
        else:
            html += f"""            <div class="item">{fires.get('message', 'No data available')}</div>
"""
        
        html += """        </div>
    </div>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)


class EmergencyPDFGenerator:
    """Generates emergency information PDFs"""
    
    @staticmethod
    def create_pdf(filename, emergency_data, resources):
        """Create a PDF with emergency information"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            compress=1  # Enable compression
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.red
        )
        
        critical_style = ParagraphStyle(
            'Critical',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.red,
            spaceBefore=12,
            spaceAfter=8
        )
        
        warning_style = ParagraphStyle(
            'Warning',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.orange,
            spaceBefore=12,
            spaceAfter=8
        )
        
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.blue,
            spaceBefore=12,
            spaceAfter=8
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=6
        )
        
        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=4
        )
        
        story = []
        
        # Title
        timestamp = emergency_data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M"))
        title = Paragraph(f"EMERGENCY INFORMATION REPORT<br/>{timestamp}", title_style)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # NWS Alerts
        story.append(Paragraph("🚨 NATIONAL WEATHER SERVICE ALERTS", critical_style))
        alerts = emergency_data.get('nws_alerts', [])
        
        if not alerts or (isinstance(alerts, list) and len(alerts) > 0 and alerts[0].get('error')):
            story.append(Paragraph("No active alerts or data unavailable", body_style))
        else:
            critical_alerts = [a for a in alerts if a.get('severity') in ['Extreme', 'Severe']]
            other_alerts = [a for a in alerts if a.get('severity') not in ['Extreme', 'Severe']]
            
            if critical_alerts:
                story.append(Paragraph("<b>CRITICAL ALERTS:</b>", body_style))
                for alert in critical_alerts[:10]:
                    event = alert.get('event', 'Unknown')
                    areas = alert.get('areas', 'Unknown')
                    headline = alert.get('headline', '')
                    severity = alert.get('severity', '')
                    
                    alert_text = f"<b>{severity.upper()}: {event}</b><br/>"
                    alert_text += f"Areas: {areas}<br/>"
                    if headline:
                        alert_text += f"{headline}"
                    
                    story.append(Paragraph(alert_text, small_style))
                    story.append(Spacer(1, 0.05*inch))
            
            if other_alerts:
                story.append(Paragraph("<b>Other Alerts & Advisories:</b>", body_style))
                for alert in other_alerts[:10]:
                    event = alert.get('event', 'Unknown')
                    areas = alert.get('areas', 'Unknown')
                    story.append(Paragraph(f"• {event}: {areas}", small_style))
        
        story.append(Spacer(1, 0.1*inch))
        
        # Earthquakes
        story.append(Paragraph("🌍 RECENT EARTHQUAKES (M4.5+, Last 7 Days)", warning_style))
        quakes = emergency_data.get('usgs_earthquakes', [])
        
        if not quakes or (isinstance(quakes, list) and len(quakes) > 0 and quakes[0].get('error')):
            story.append(Paragraph("No significant earthquakes", body_style))
        else:
            for quake in quakes[:15]:
                if quake.get('error'):
                    continue
                mag = quake.get('magnitude', 'Unknown')
                location = quake.get('location', 'Unknown')
                time = quake.get('time', 'Unknown')
                depth = quake.get('depth', 'Unknown')
                
                quake_text = f"<b>M{mag}</b> - {location}<br/>"
                quake_text += f"Time: {time} | Depth: {depth} km"
                story.append(Paragraph(quake_text, small_style))
                story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.1*inch))
        
        # FEMA Disasters
        story.append(Paragraph("🏛️ FEMA DISASTER DECLARATIONS (Last 30 Days)", warning_style))
        disasters = emergency_data.get('fema_disasters', [])
        
        if not disasters or (isinstance(disasters, list) and len(disasters) > 0 and disasters[0].get('error')):
            story.append(Paragraph("No recent disaster declarations", body_style))
        else:
            for disaster in disasters[:15]:
                if disaster.get('error'):
                    continue
                num = disaster.get('disaster_number', 'Unknown')
                state = disaster.get('state', 'Unknown')
                incident = disaster.get('incident_type', 'Unknown')
                title = disaster.get('title', '')
                date = disaster.get('date', 'Unknown')
                
                disaster_text = f"<b>{num} - {state}</b><br/>"
                disaster_text += f"{incident}: {title}<br/>"
                disaster_text += f"Date: {date}"
                story.append(Paragraph(disaster_text, small_style))
                story.append(Spacer(1, 0.05*inch))
        
        story.append(PageBreak())
        
        # Active Fires
        story.append(Paragraph("🔥 ACTIVE FIRE INCIDENTS (Last 24 Hours)", warning_style))
        fires = emergency_data.get('fire_incidents', {})
        
        if fires.get('error'):
            story.append(Paragraph(f"Error: {fires['error']}", body_style))
        elif fires.get('active_fires_24h'):
            story.append(Paragraph(f"<b>{fires['active_fires_24h']} thermal anomalies detected</b>", body_style))
            story.append(Paragraph(fires.get('message', ''), small_style))
            story.append(Paragraph(f"Source: {fires.get('source', 'Unknown')}", small_style))
        else:
            story.append(Paragraph(fires.get('message', 'No data available'), body_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Twitter Emergency Feeds (if available)
        twitter_tweets = emergency_data.get('twitter_tweets', [])
        if twitter_tweets and not (isinstance(twitter_tweets, dict) and twitter_tweets.get('error')):
            story.append(Paragraph("🐦 OFFICIAL EMERGENCY TWEETS (Last 6 Hours)", critical_style))
            story.append(Spacer(1, 0.1*inch))
            
            for tweet in twitter_tweets[:20]:  # Limit to 20 tweets
                if tweet.get('error'):
                    continue
                
                account = tweet.get('account', 'Unknown')
                text = tweet.get('text', '')
                created = tweet.get('created_at', '')
                
                # Format the tweet
                tweet_text = f"<b>@{account}</b>"
                if created:
                    # Parse and format timestamp
                    try:
                        from dateutil import parser
                        dt = parser.parse(created)
                        time_str = dt.strftime('%I:%M %p')
                        tweet_text += f" • {time_str}"
                    except:
                        pass
                
                tweet_text += f"<br/>{text}"
                
                story.append(Paragraph(tweet_text, small_style))
                story.append(Spacer(1, 0.08*inch))
            
            story.append(Spacer(1, 0.1*inch))
        elif isinstance(twitter_tweets, dict) and twitter_tweets.get('message'):
            # Show informational message if Twitter not configured
            story.append(Paragraph("🐦 EMERGENCY TWEETS", info_style))
            story.append(Paragraph(twitter_tweets.get('message', ''), small_style))
            if twitter_tweets.get('alternative'):
                story.append(Paragraph(f"<i>{twitter_tweets.get('alternative')}</i>", small_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)


class TwitterHTMLGenerator:
    """Generates Twitter emergency feed HTML"""
    
    @staticmethod
    def create_html(filename, tweets):
        """Create an HTML file with Twitter emergency feeds"""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency Twitter Feed</title>
    {HTMLGenerator.get_base_style()}
</head>
<body>
    <div class="container">
        <h1>🐦 Emergency Twitter Feed</h1>
        <div class="timestamp">{timestamp}</div>
        
        <div class="section">
"""
        
        # Check if tweets are available
        if isinstance(tweets, dict) and tweets.get('error'):
            html += f"""            <div class="alert-warning">
                <strong>Error:</strong> {tweets.get('error', 'Unknown error')}<br>
                {tweets.get('message', '')}
            </div>
"""
            if tweets.get('details'):
                html += """            <h3>Details:</h3>
"""
                for detail in tweets['details'][:5]:
                    html += f"""            <div class="item">{detail}</div>
"""
        elif not tweets or (isinstance(tweets, dict) and tweets.get('message')):
            msg = tweets.get('message', 'No tweets available') if isinstance(tweets, dict) else 'No tweets available'
            html += f"""            <div class="item">{msg}</div>
"""
        else:
            # Display tweets
            for tweet in tweets:
                account = tweet.get('account', 'Unknown')
                text = tweet.get('text', '')
                created = tweet.get('created_at', '')
                
                # Format timestamp
                time_str = ''
                if created:
                    try:
                        from dateutil import parser
                        dt = parser.parse(created)
                        time_str = dt.strftime('%b %d, %I:%M %p')
                    except:
                        time_str = created
                
                html += f"""            <div class="tweet">
                <div class="tweet-account">@{account}</div>
                <div class="tweet-time">{time_str}</div>
                <div style="margin-top: 8px;">{text}</div>
            </div>
"""
        
        html += """        </div>
    </div>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)


class TwitterPDFGenerator:
    """Generates Twitter emergency feed PDFs"""
    
    @staticmethod
    def create_pdf(filename, tweets):
        """Create a PDF with Twitter emergency feeds"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            compress=1  # Enable compression
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#1DA1F2')  # Twitter blue
        )
        
        tweet_style = ParagraphStyle(
            'Tweet',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=10,
            leftIndent=10
        )
        
        story = []
        
        # Title
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        title = Paragraph(f"🐦 Emergency Twitter Feed<br/>{timestamp}", title_style)
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Check if tweets are available
        if isinstance(tweets, dict) and tweets.get('error'):
            story.append(Paragraph(f"<b>Error:</b> {tweets.get('error', 'Unknown error')}", tweet_style))
            if tweets.get('message'):
                story.append(Paragraph(tweets['message'], tweet_style))
            if tweets.get('details'):
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("<b>Details:</b>", tweet_style))
                for detail in tweets['details'][:5]:
                    story.append(Paragraph(f"• {detail}", tweet_style))
        elif not tweets or (isinstance(tweets, dict) and tweets.get('message')):
            msg = tweets.get('message', 'No tweets available') if isinstance(tweets, dict) else 'No tweets available'
            story.append(Paragraph(msg, tweet_style))
        else:
            # Display tweets
            for tweet in tweets:
                account = tweet.get('account', 'Unknown')
                text = tweet.get('text', '')
                created = tweet.get('created_at', '')
                
                # Format timestamp
                time_str = ''
                if created:
                    try:
                        from dateutil import parser
                        dt = parser.parse(created)
                        time_str = dt.strftime('%b %d, %I:%M %p')
                    except:
                        time_str = created
                
                # Create tweet paragraph
                tweet_text = f"<b>@{account}</b>"
                if time_str:
                    tweet_text += f" • {time_str}"
                tweet_text += f"<br/>{text}"
                
                story.append(Paragraph(tweet_text, tweet_style))
                story.append(Spacer(1, 0.15*inch))
        
        # Build PDF
        doc.build(story)



class PowerOutageFetcher:
    """Fetches power outage data from DOE/ORNL ODIN public API
    with geographical enrichment via EIA utility lookup table."""

    STATUS_URL = "https://odin.ornl.gov/odi/status"

    # EIA utility ID -> primary state of operation.
    # Built from EIA Form 861 Annual Electric Power Industry Report (public domain)
    # and cross-referenced against ODIN participating utilities.
    EIA_STATE_LOOKUP = {
        "14354": "UT", "17609": "CA", "8319":  "IA", "9991":  "MN",
        "329":   "IA", "17040": "IL", "19157": "MN", "15248": "OR",
        "5417":  "WI", "6894":  "SC", "14653": "WA", "11011": "KY",
        "16368": "MN", "12227": "MN", "2652":  "IA", "15257": "CO",
        "3644":  "WA", "12341": "IA", "13700": "MN", "3502":  "FL",
        "155":   "MN", "1884":  "MN", "19791": "VT", "15500": "WA",
        "4346":  "MN", "7887":  "GA", "3597":  "PA", "22355": "WA",
        "10799": "TN", "9837":  "NC", "8773":  "CO", "4442":  "WA",
        "40220": "IL", "38084": "MI", "5326":  "WA", "19820": "KS",
        "19189": "AZ", "13651": "KY", "5961":  "TN", "24590": "NH",
        "1613":  "SC", "14468": "MN", "20169": "WA", "18448": "WA",
        "4265":  "NM", "15845": "MN", "3249":  "NY", "3264":  "OR",
        "26939": "ND", "59013": "WA", "11804": "NY", "6782":  "MN",
        "14349": "ME", "13762": "VA", "803":   "AZ", "13573": "MA",
        "19981": "NC", "18957": "NC", "19108": "NC", "18339": "NC",
        "17572": "NC", "16101": "NC", "16496": "NC", "15671": "NC",
        "8333":  "NC", "7978":  "NC", "14717": "NC", "21632": "NC",
        "6784":  "NC", "6640":  "NC", "5656":  "NC", "3250":  "NC",
        "3107":  "NC", "240":   "NC", "2982":  "NC", "19499": "CO",
        "8901":  "TX", "5487":  "PA", "8796":  "MA", "13839": "MA",
        "16868": "WA", "12546": "MN", "12377": "MI", "20639": "MN",
        "2641":  "KS", "12470": "TN", "19156": "WY", "17267": "SD",
        "1251":  "WI", "4041":  "WA", "22822": "IN", "10000": "KS",
        "9575":  "KY", "13684": "MN", "14170": "WA", "10618": "MN",
        "12692": "MT", "1579":  "WA", "5327":  "OR", "5574":  "MN",
        "16382": "NE", "577":   "TN", "3739":  "ID", "11910": "MN",
        "19547": "HI", "14716": "PA", "20387": "PA", "18997": "OH",
        "15263": "MD", "21081": "CO", "14711": "PA", "13998": "OH",
        "12796": "WV", "12390": "PA", "9726":  "NJ", "3755":  "OH",
        "5862":  "CO", "10539": "CO", "17470": "WA", "24889": "NC",
        "13550": "OR", "3293":  "WI", "25177": "MN", "18019": "MN",
        "12651": "MN", "7460":  "MN", "7559":  "TX", "15419": "WA",
        "13758": "ID", "5202":  "AL", "11291": "NC", "10697": "MN",
        "12929": "IN", "4743":  "OR", "20996": "MN", "15023": "NC",
        "5070":  "DE", "9336":  "CO", "19266": "TN", "1889":  "NC",
        "1529":  "MN", "13955": "FL", "8786":  "SC", "15507": "TN",
        "12988": "TN", "3413":  "GA", "7140":  "FL", "6452":  "FL",
        "3366":  "IN", "3265":  "OH", "3257":  "KY", "18642": "NC",
        "5416":  "NC", "9417":  "IL", "1228":  "MO", "14232": "MO",
        "9516":  "MI", "12427": "MI", "11371": "MN", "19545": "CO",
        "18454": "NM", "4716":  "WI", "20856": "WI", "6186":  "OR",
        "18195": "ID", "5701":  "AZ", "11070": "AZ", "13610": "NV",
        "19561": "NV", "14328": "CA", "17260": "CA", "7367":  "CT",
        "8192":  "MA", "195":   "AL", "11241": "LA", "13478": "MS",
        "16572": "MS", "11957": "TX", "22500": "GA", "17543": "TX",
        "4169":  "MN", "30151": "MN", "14348": "WA", "14647": "WA",
        "30844": "OR", "20382": "PA", "31568": "OH", "6127":  "PA",
        "40229": "MI", "17718": "TX", "1430":  "WA",
    }

    # Patterns to infer state from utility name when EIA ID not in lookup.
    _NAME_PATTERNS = [
        (r'\(([A-Z]{2})\)$', None),
        (r'\bALABAMA\b', 'AL'), (r'\bALASKA\b', 'AK'),
        (r'\bARIZONA\b', 'AZ'), (r'\bARKANSAS\b', 'AR'),
        (r'\bCALIFORNIA\b', 'CA'), (r'\bCOLORADO\b', 'CO'),
        (r'\bCONNECTICUT\b', 'CT'), (r'\bDELAWARE\b', 'DE'),
        (r'\bFLORIDA\b', 'FL'), (r'\bGEORGIA\b', 'GA'),
        (r'\bHAWAII\b|\bHAWAIIAN\b', 'HI'), (r'\bIDAHO\b', 'ID'),
        (r'\bILLINOIS\b', 'IL'), (r'\bINDIANA\b', 'IN'),
        (r'\bIOWA\b', 'IA'), (r'\bKANSAS\b', 'KS'),
        (r'\bKENTUCKY\b', 'KY'), (r'\bLOUISIANA\b', 'LA'),
        (r'\bMAINE\b', 'ME'), (r'\bMARYLAND\b', 'MD'),
        (r'\bMASSACHUSETTS\b', 'MA'), (r'\bMICHIGAN\b', 'MI'),
        (r'\bMINNESOTA\b', 'MN'), (r'\bMISSISSIPPI\b', 'MS'),
        (r'\bMISSOURI\b', 'MO'), (r'\bMONTANA\b', 'MT'),
        (r'\bNEBRASKA\b', 'NE'), (r'\bNEVADA\b', 'NV'),
        (r'\bNEW HAMPSHIRE\b', 'NH'), (r'\bNEW JERSEY\b', 'NJ'),
        (r'\bNEW MEXICO\b', 'NM'), (r'\bNEW YORK\b', 'NY'),
        (r'\bNORTH CAROLINA\b', 'NC'), (r'\bNORTH DAKOTA\b', 'ND'),
        (r'\bOHIO\b', 'OH'), (r'\bOKLAHOMA\b', 'OK'),
        (r'\bOREGON\b', 'OR'), (r'\bPENNSYLVANIA\b|\bPENN\b', 'PA'),
        (r'\bRHODE ISLAND\b', 'RI'), (r'\bSOUTH CAROLINA\b', 'SC'),
        (r'\bSOUTH DAKOTA\b', 'SD'), (r'\bTENNESSEE\b', 'TN'),
        (r'\bTEXAS\b', 'TX'), (r'\bUTAH\b', 'UT'),
        (r'\bVERMONT\b', 'VT'), (r'\bVIRGINIA\b', 'VA'),
        (r'\bWASHINGTON\b', 'WA'), (r'\bWEST VIRGINIA\b', 'WV'),
        (r'\bWISCONSIN\b', 'WI'), (r'\bWYOMING\b', 'WY'),
        (r'\bPUGET\b', 'WA'), (r'\bSAN DIEGO\b', 'CA'),
        (r'\bSOUTHERN CALIFORNIA\b', 'CA'), (r'\bPACIFIC GAS\b', 'CA'),
        (r'\bNEW ENGLAND\b', 'MA'), (r'\bCHESAPEAKE\b', 'VA'),
    ]

    def get_state(self, eia_id, name):
        """Return two-letter state code for a utility, or None if unknown."""
        import re
        state = self.EIA_STATE_LOOKUP.get(str(eia_id))
        if state:
            return state
        name_upper = name.upper()
        for pattern, st in self._NAME_PATTERNS:
            m = re.search(pattern, name_upper)
            if m:
                return st if st else m.group(1)
        return None

    def get_outages(self, log_callback=None):
        """Fetch current power outage data from ODIN /odi/status."""
        import requests
        result = {
            'timestamp': __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M"),
            'total_outages': 0,
            'utility_count': 0,
            'utilities_with_outages': 0,
            'top_utilities': [],
            'states': [],
            'national_summary': '',
            'error': None
        }
        try:
            headers = {
                'User-Agent': 'EmcommBBS/1.0 (amateur radio emergency use)',
                'Accept': 'application/json'
            }
            if log_callback:
                log_callback("  - Querying ODIN API (odin.ornl.gov)...")
            resp = requests.get(self.STATUS_URL, headers=headers, timeout=20)
            if resp.status_code == 200:
                result = self._parse_response(resp.json(), result)
                if log_callback:
                    log_callback(
                        f"    \u2713 ODIN: {result['total_outages']:,} outages across "
                        f"{result['utilities_with_outages']} utilities "
                        f"in {len(result['states'])} states"
                    )
            else:
                result['error'] = f"ODIN API returned HTTP {resp.status_code}"
                if log_callback:
                    log_callback(f"    \u26a0 {result['error']}")
        except requests.exceptions.Timeout:
            result['error'] = "Request timed out after 20s"
            if log_callback:
                log_callback("    \u26a0 ODIN API timeout")
        except Exception as e:
            result['error'] = str(e)
            if log_callback:
                log_callback(f"    \u26a0 ODIN API error: {e}")
        return result

    def _parse_response(self, data, result):
        """Parse ODIN /odi/status list into structured outage data."""
        if not isinstance(data, list):
            result['error'] = "Unexpected response format from ODIN"
            return result

        state_totals = {}
        with_outages = []
        total = 0

        for utility in data:
            outages = int(utility.get('totalOutages', 0) or 0)
            eia_id  = str(utility.get('eiaId', ''))
            name    = utility.get('name', 'Unknown')
            state   = self.get_state(eia_id, name)
            total  += outages

            u_entry = {
                'name':       name,
                'outages':    outages,
                'state':      state or '??',
                'resolution': utility.get('dataResolution', ''),
            }
            if outages > 0:
                with_outages.append(u_entry)
                if state:
                    if state not in state_totals:
                        state_totals[state] = {'outages': 0, 'utilities': 0}
                    state_totals[state]['outages']   += outages
                    state_totals[state]['utilities'] += 1

        with_outages.sort(key=lambda x: x['outages'], reverse=True)
        states_list = sorted(
            [{'state': s, 'outages': v['outages'], 'utilities': v['utilities']}
             for s, v in state_totals.items()],
            key=lambda x: x['outages'], reverse=True
        )

        result['total_outages']          = total
        result['utility_count']          = len(data)
        result['utilities_with_outages'] = len(with_outages)
        result['top_utilities']          = with_outages[:15]
        result['states']                 = states_list

        if total > 0:
            top_states = ', '.join(
                f"{s['state']} ({s['outages']:,})" for s in states_list[:4]
            )
            result['national_summary'] = (
                f"{total:,} active outages across {len(with_outages)} utilities "
                f"in {len(states_list)} states. Most affected: {top_states}."
            )
        else:
            result['national_summary'] = (
                f"No significant outages reported across "
                f"{len(data)} monitored utilities."
            )
        return result

    @staticmethod
    def format_txt(outage_data):
        """Format outage data as compact plain text for radio transmission."""
        lines = []
        ts = outage_data.get('timestamp', '')
        lines.append(f"POWER OUTAGE REPORT {ts}")
        lines.append("Source: DOE/ORNL ODIN  odin.ornl.gov")
        lines.append("=" * 42)

        if outage_data.get('error'):
            lines.append(f"Data unavailable: {outage_data['error']}")
            lines.append("Check poweroutage.us for current info")
            return "\n".join(lines)

        total      = outage_data.get('total_outages', 0)
        util_count = outage_data.get('utility_count', 0)
        with_out   = outage_data.get('utilities_with_outages', 0)
        lines.append(f"TOTAL OUTAGES : {total:,}")
        lines.append(f"UTILITIES     : {with_out} reporting / {util_count} monitored")
        lines.append("")

        # Word-wrap summary at 60 chars
        summary = outage_data.get('national_summary', '')
        if summary:
            words, line = summary.split(), ""
            for word in words:
                if len(line) + len(word) + 1 > 60:
                    lines.append(line); line = word
                else:
                    line = f"{line} {word}".strip()
            if line:
                lines.append(line)
            lines.append("")

        # State summary
        states = outage_data.get('states', [])
        if states:
            lines.append("OUTAGES BY STATE:")
            lines.append(f"  {'ST':<6} {'OUTAGES':>8}  UTILS")
            lines.append("  " + "-" * 24)
            for s in states:
                lines.append(
                    f"  {s['state']:<6} {s['outages']:>8,}  {s['utilities']}"
                )
            lines.append("")

        # Top utilities with state prefix
        top = outage_data.get('top_utilities', [])
        if top:
            lines.append("TOP UTILITIES:")
            lines.append(f"  {'ST':<4} {'UTILITY':<32} {'OUTAGES':>8}")
            lines.append("  " + "-" * 46)
            for u in top:
                name = u['name'][:31]
                lines.append(f"  {u['state']:<4} {name:<32} {u['outages']:>8,}")

        lines.append("")
        lines.append("NOTE: ODIN covers participating utilities only.")
        lines.append("END POWER OUTAGE REPORT")
        return "\n".join(lines)


class NewsApp:
    """Main application GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Emcomm BBS - All-In-One Edition")
        self.root.geometry("700x650")
        
        self.summarizer = NewsSummarizer()
        self.is_running = False
        self.worker_thread = None
        self.twitter_worker_thread = None
        self.twitter_is_running = False
        # Default save directory - VarAC BBS directory
        # Create directory if it doesn't exist
        varac_dir = Path("C:/VarAC BBS")
        try:
            varac_dir.mkdir(parents=True, exist_ok=True)
            self.save_directory = str(varac_dir)
        except Exception as e:
            # Fallback to Downloads if VarAC directory can't be created
            print(f"Warning: Could not create C:/VarAC BBS directory ({e}), using Downloads")
            self.save_directory = str(Path.home() / "Downloads")
        
        # Initialize emergency fetchers if module is available
        if EmergencyDataFetcher:
            self.emergency_fetcher = EmergencyDataFetcher()
            self.emergency_enabled = True
        else:
            self.emergency_fetcher = None
            self.emergency_enabled = False
        
        self.twitter_fetcher = None  # Will be set if user provides token
        
        # Initialize Nextdoor fetcher if module is available
        if NextdoorFetcher:
            self.nextdoor_fetcher = None  # Will be set if user provides API key and ZIP codes
            self.nextdoor_enabled = NEXTDOOR_AVAILABLE
        else:
            self.nextdoor_fetcher = None
            self.nextdoor_enabled = False
        
        # Initialize Welfare Board if module is available
        if WELFARE_BOARD_AVAILABLE:
            # Configure time windows - Default to 24/7 operation
            welfare_config = {
                'time_windows': [
                    {'name': 'All Day', 'start': '00:00', 'end': '23:59'}
                ],
                'validation': {
                    'require_callsign': True,
                    'require_name': True,
                    'require_location': True,
                    'require_status': True,
                    'valid_statuses': ['SAFE', 'NEED ASSISTANCE', 'TRAFFIC']
                }
            }
            
            self.welfare_parser = WelfareParser()
            self.welfare_validator = WelfareValidator(welfare_config)
            self.welfare_aggregator = WelfareAggregator(welfare_config)
            self.welfare_output_generator = OutputGenerator(welfare_config)
            self.welfare_watcher = None
            self.welfare_enabled = True
            self.welfare_is_running = False
        else:
            self.welfare_parser = None
            self.welfare_validator = None
            self.welfare_aggregator = None
            self.welfare_output_generator = None
            self.welfare_watcher = None
            self.welfare_enabled = False
            self.welfare_is_running = False

        self.load_settings()    # Load persisted settings before building GUI
        self.setup_gui()
        self.apply_saved_settings()  # Fill widgets with loaded values
    
    def setup_gui(self):
        """Create the GUI elements with tabbed interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Emcomm BBS - Radio Optimized", 
            font=('Helvetica', 14, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Create tabbed notebook
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Main Controls
        main_tab = ttk.Frame(notebook, padding="10")
        notebook.add(main_tab, text="  Main  ")
        
        # Tab 2: Settings (API keys, directory, intervals)
        settings_tab = ttk.Frame(notebook, padding="10")
        notebook.add(settings_tab, text="  Settings  ")
        
        # Tab 3: Welfare Board (check-in monitoring)
        if self.welfare_enabled:
            welfare_tab = ttk.Frame(notebook, padding="10")
            notebook.add(welfare_tab, text="  Welfare Board  ")
        
        # Setup each tab
        self.setup_main_tab(main_tab)
        self.setup_settings_tab(settings_tab)
        if self.welfare_enabled:
            self.setup_welfare_tab(welfare_tab)
    
    def setup_main_tab(self, parent):
        """Setup the main controls tab"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)
        
        # Output Selection
        output_frame = ttk.LabelFrame(parent, text="Select Outputs to Generate", padding="10")
        output_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Initialize checkbox variables
        self.generate_news_var = tk.BooleanVar(value=True)
        self.generate_weather_var = tk.BooleanVar(value=True)
        self.generate_space_var = tk.BooleanVar(value=True)
        self.generate_emergency_var = tk.BooleanVar(value=True)
        self.generate_twitter_var = tk.BooleanVar(value=True)
        self.generate_nextdoor_var = tk.BooleanVar(value=False)
        self.generate_power_var = tk.BooleanVar(value=True)
        
        # Weather region variables (R1-R10)
        self.weather_regions = {}
        for i in range(1, 11):
            self.weather_regions[i] = tk.BooleanVar(value=(i == 4))
        
        # Left column - Main outputs
        left_col = ttk.Frame(output_frame)
        left_col.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 20))
        
        ttk.Checkbutton(left_col, text="News Summary", variable=self.generate_news_var, command=self.save_settings).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Weather with Select All/None
        weather_frame = ttk.Frame(left_col)
        weather_frame.grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(weather_frame, text="Weather Forecasts", variable=self.generate_weather_var, command=self.save_settings).pack(side=tk.LEFT)
        ttk.Button(weather_frame, text="All", command=self.select_all_regions, width=6).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(weather_frame, text="None", command=self.select_no_regions, width=6).pack(side=tk.LEFT)
        
        ttk.Checkbutton(left_col, text="Space Weather", variable=self.generate_space_var, command=self.save_settings).grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Emergency Alerts", variable=self.generate_emergency_var, command=self.save_settings).grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Power Outages", variable=self.generate_power_var, command=self.save_settings).grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Twitter Feed", variable=self.generate_twitter_var, command=self.save_settings).grid(row=5, column=0, sticky=tk.W, pady=2)
        
        # Nextdoor checkbox (if available)
        if self.nextdoor_enabled:
            ttk.Checkbutton(left_col, text="Nextdoor (Local)", variable=self.generate_nextdoor_var).grid(row=6, column=0, sticky=tk.W, pady=2)
        
        # Right column - FEMA Regions
        right_col = ttk.LabelFrame(output_frame, text="Weather Regions (FEMA)", padding="5")
        right_col.grid(row=0, column=1, sticky=(tk.W, tk.N))
        
        # Region descriptions
        region_info = {
            1: "R1: Northeast",
            2: "R2: NY/NJ",
            3: "R3: Mid-Atlantic",
            4: "R4: Southeast",
            5: "R5: Midwest",
            6: "R6: South Central",
            7: "R7: Great Plains",
            8: "R8: Mountain",
            9: "R9: Southwest",
            10: "R10: Northwest"
        }
        
        for i in range(1, 11):
            ttk.Checkbutton(right_col, text=region_info[i], variable=self.weather_regions[i], command=self.save_settings).grid(row=i-1, column=0, sticky=tk.W, pady=1)
        
        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=0, pady=(0, 10))
        
        self.start_button = ttk.Button(
            control_frame, 
            text="Start Automatic Updates", 
            command=self.start_service,
            width=22
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            control_frame, 
            text="Stop", 
            command=self.stop_service, 
            state=tk.DISABLED,
            width=10
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.manual_button = ttk.Button(
            control_frame, 
            text="Generate Now", 
            command=self.generate_now,
            width=15
        )
        self.manual_button.grid(row=0, column=2, padx=5)
        
        # Status label
        self.status_label = ttk.Label(parent, text="Ready", foreground="blue")
        self.status_label.grid(row=2, column=0, pady=(0, 10))
        
        # Log window
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="5")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initial log messages
        self.log("Emcomm BBS initialized")
        self.log(f"Save directory: {self.save_directory}")
        if not self.emergency_enabled:
            self.log("⚠ Emergency module not available")
    
    def setup_settings_tab(self, parent):
        """Setup the settings tab with API keys, directory, and intervals"""
        parent.columnconfigure(0, weight=1)
        
        # API Configuration
        api_frame = ttk.LabelFrame(parent, text="API Keys (Optional)", padding="10")
        api_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)
        
        # Anthropic API
        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.api_key_entry = ttk.Entry(api_frame, show="*", width=40)
        self.api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(api_frame, text="Set", command=self.set_api_key, width=6).grid(row=0, column=2)
        
        ttk.Label(
            api_frame, 
            text="For AI-powered news summaries (without it: headline lists only)",
            font=('Helvetica', 8),
            foreground='gray'
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(2, 10))
        
        # Twitter API section (for emergency tweets)
        if self.emergency_enabled:
            ttk.Label(api_frame, text="Twitter Bearer Token:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
            self.twitter_token_entry = ttk.Entry(api_frame, show="*", width=40)
            self.twitter_token_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
            ttk.Button(api_frame, text="Set", command=self.set_twitter_token, width=6).grid(row=2, column=2)
            
            ttk.Label(
                api_frame,
                text="For emergency tweets from official accounts (500K tweets/month free)",
                font=('Helvetica', 8),
                foreground='gray'
            ).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
            
            # Twitter handles selection
            ttk.Label(api_frame, text="Twitter Accounts:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
            self.twitter_handles_entry = ttk.Entry(api_frame, width=40)
            self.twitter_handles_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(10, 0))
            
            # Set default handles
            default_handles = "NWS,fema,USGS_Quakes,NWSAlerts,CDCgov,NHC_Atlantic"
            self.twitter_handles_entry.insert(0, default_handles)
            
            ttk.Button(api_frame, text="Update", command=self.update_twitter_handles, width=6).grid(row=4, column=2, pady=(10, 0))
            
            ttk.Label(
                api_frame,
                text="Comma-separated list, no @ symbols (e.g., NWS,fema,USGS_Quakes)",
                font=('Helvetica', 8),
                foreground='gray'
            ).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(2, 10))
        
        # Nextdoor API section (for local community posts)
        if self.nextdoor_enabled:
            ttk.Label(api_frame, text="Nextdoor API Key:").grid(row=6, column=0, sticky=tk.W, padx=(0, 5))
            self.nextdoor_key_entry = ttk.Entry(api_frame, show="*", width=40)
            self.nextdoor_key_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
            ttk.Button(api_frame, text="Set", command=self.set_nextdoor_config, width=6).grid(row=6, column=2)
            
            ttk.Label(
                api_frame,
                text="For local community posts (requires Public Agency API approval)",
                font=('Helvetica', 8),
                foreground='gray'
            ).grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
            
            # ZIP codes selection
            ttk.Label(api_frame, text="ZIP Codes:").grid(row=8, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
            self.nextdoor_zips_entry = ttk.Entry(api_frame, width=40)
            self.nextdoor_zips_entry.grid(row=8, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(10, 0))
            
            # Set default/example ZIPs
            self.nextdoor_zips_entry.insert(0, "30301,30308,30309")
            
            ttk.Button(api_frame, text="Update", command=self.set_nextdoor_config, width=6).grid(row=8, column=2, pady=(10, 0))
            
            ttk.Label(
                api_frame,
                text="Comma-separated ZIP codes to monitor (e.g., 30301,30308,30309)",
                font=('Helvetica', 8),
                foreground='gray'
            ).grid(row=9, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
        
        # Directory selection
        dir_frame = ttk.LabelFrame(parent, text="Output Location", padding="10")
        dir_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.dir_label = ttk.Label(dir_frame, text=self.save_directory, relief=tk.SUNKEN, padding=5)
        self.dir_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory, width=8).grid(row=0, column=2)
        
        # Update intervals
        interval_frame = ttk.LabelFrame(parent, text="Update Intervals", padding="10")
        interval_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(interval_frame, text="Main Reports:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.main_interval_var = tk.IntVar(value=6)
        ttk.Spinbox(interval_frame, from_=1, to=24, textvariable=self.main_interval_var, width=5).grid(row=0, column=1, padx=5)
        ttk.Label(interval_frame, text="hours").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(interval_frame, text="Twitter Feed:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.twitter_interval_var = tk.IntVar(value=6)
        ttk.Spinbox(interval_frame, from_=1, to=12, textvariable=self.twitter_interval_var, width=5).grid(row=1, column=1, padx=5, pady=(5, 0))
        ttk.Label(interval_frame, text="hours").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        
        # Welfare Board Time Windows (if enabled)
        if self.welfare_enabled:
            welfare_frame = ttk.LabelFrame(parent, text="Welfare Board Time Windows", padding="10")
            welfare_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
            
            ttk.Label(
                welfare_frame,
                text="Configure when welfare check-ins are accepted. Check-ins outside these windows will be rejected.",
                font=('Helvetica', 9),
                wraplength=550
            ).grid(row=0, column=0, columnspan=5, sticky=tk.W, pady=(0, 10))
            
            # Time window entries
            self.welfare_windows = []
            
            # Window 1
            # Window 1 - Default to 24/7 operation
            ttk.Label(welfare_frame, text="Window 1:", font=('Helvetica', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
            ttk.Label(welfare_frame, text="Name:").grid(row=1, column=1, sticky=tk.W)
            self.welfare_window1_name = ttk.Entry(welfare_frame, width=15)
            self.welfare_window1_name.insert(0, "All Day")
            self.welfare_window1_name.grid(row=1, column=2, padx=5)
            
            ttk.Label(welfare_frame, text="Start:").grid(row=1, column=3, sticky=tk.W, padx=(10, 5))
            self.welfare_window1_start = ttk.Entry(welfare_frame, width=8)
            self.welfare_window1_start.insert(0, "00:00")
            self.welfare_window1_start.grid(row=1, column=4, padx=5)
            
            ttk.Label(welfare_frame, text="End:").grid(row=1, column=5, sticky=tk.W, padx=(10, 5))
            self.welfare_window1_end = ttk.Entry(welfare_frame, width=8)
            self.welfare_window1_end.insert(0, "23:59")
            self.welfare_window1_end.grid(row=1, column=6, padx=5)
            
            # Window 2 - Disabled by default (blank name)
            ttk.Label(welfare_frame, text="Window 2:", font=('Helvetica', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
            ttk.Label(welfare_frame, text="Name:").grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
            self.welfare_window2_name = ttk.Entry(welfare_frame, width=15)
            self.welfare_window2_name.insert(0, "")  # Blank = disabled
            self.welfare_window2_name.grid(row=2, column=2, padx=5, pady=(5, 0))
            
            ttk.Label(welfare_frame, text="Start:").grid(row=2, column=3, sticky=tk.W, padx=(10, 5), pady=(5, 0))
            self.welfare_window2_start = ttk.Entry(welfare_frame, width=8)
            self.welfare_window2_start.insert(0, "08:00")
            self.welfare_window2_start.grid(row=2, column=4, padx=5, pady=(5, 0))
            
            ttk.Label(welfare_frame, text="End:").grid(row=2, column=5, sticky=tk.W, padx=(10, 5), pady=(5, 0))
            self.welfare_window2_end = ttk.Entry(welfare_frame, width=8)
            self.welfare_window2_end.insert(0, "10:00")
            self.welfare_window2_end.grid(row=2, column=6, padx=5, pady=(5, 0))
            
            # Window 3 - Disabled by default (blank name)
            ttk.Label(welfare_frame, text="Window 3:", font=('Helvetica', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
            ttk.Label(welfare_frame, text="Name:").grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
            self.welfare_window3_name = ttk.Entry(welfare_frame, width=15)
            self.welfare_window3_name.insert(0, "")  # Blank = disabled
            self.welfare_window3_name.grid(row=3, column=2, padx=5, pady=(5, 0))
            
            ttk.Label(welfare_frame, text="Start:").grid(row=3, column=3, sticky=tk.W, padx=(10, 5), pady=(5, 0))
            self.welfare_window3_start = ttk.Entry(welfare_frame, width=8)
            self.welfare_window3_start.insert(0, "14:00")
            self.welfare_window3_start.grid(row=3, column=4, padx=5, pady=(5, 0))
            
            ttk.Label(welfare_frame, text="End:").grid(row=3, column=5, sticky=tk.W, padx=(10, 5), pady=(5, 0))
            self.welfare_window3_end = ttk.Entry(welfare_frame, width=8)
            self.welfare_window3_end.insert(0, "16:00")
            self.welfare_window3_end.grid(row=3, column=6, padx=5, pady=(5, 0))
            
            # Apply button
            ttk.Button(
                welfare_frame,
                text="Apply Time Windows",
                command=self.apply_welfare_windows,
                width=20
            ).grid(row=4, column=0, columnspan=7, pady=(15, 5))
            
            ttk.Label(
                welfare_frame,
                text="Format: HH:MM (24-hour). Leave name blank to disable a window.",
                font=('Helvetica', 8),
                foreground='gray'
            ).grid(row=5, column=0, columnspan=7, sticky=tk.W, pady=(5, 0))

            # Register vars for save_settings()
            self._time_window_vars = [
                (self.welfare_window1_name, self.welfare_window1_start, self.welfare_window1_end),
                (self.welfare_window2_name, self.welfare_window2_start, self.welfare_window2_end),
                (self.welfare_window3_name, self.welfare_window3_start, self.welfare_window3_end),
            ]
    
    def apply_welfare_windows(self):
        """Apply welfare board time window configuration"""
        try:
            windows = []
            
            # Window 1
            name1 = self.welfare_window1_name.get().strip()
            if name1:
                windows.append({
                    'name': name1,
                    'start': self.welfare_window1_start.get().strip(),
                    'end': self.welfare_window1_end.get().strip()
                })
            
            # Window 2
            name2 = self.welfare_window2_name.get().strip()
            if name2:
                windows.append({
                    'name': name2,
                    'start': self.welfare_window2_start.get().strip(),
                    'end': self.welfare_window2_end.get().strip()
                })
            
            # Window 3
            name3 = self.welfare_window3_name.get().strip()
            if name3:
                windows.append({
                    'name': name3,
                    'start': self.welfare_window3_start.get().strip(),
                    'end': self.welfare_window3_end.get().strip()
                })
            
            if not windows:
                messagebox.showwarning("Warning", "At least one time window must be configured.")
                return
            
            # Validate time format
            import re
            time_pattern = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
            for window in windows:
                if not time_pattern.match(window['start']) or not time_pattern.match(window['end']):
                    messagebox.showerror("Error", f"Invalid time format in {window['name']}. Use HH:MM (24-hour).")
                    return
            
            # Update welfare config
            welfare_config = {
                'time_windows': windows,
                'validation': {
                    'require_callsign': True,
                    'require_name': True,
                    'require_location': True,
                    'require_status': True,
                    'valid_statuses': ['SAFE', 'NEED ASSISTANCE', 'TRAFFIC']
                }
            }
            
            # Reinitialize aggregator with new config
            self.welfare_aggregator = WelfareAggregator(welfare_config)
            self.welfare_validator = WelfareValidator(welfare_config)
            self.welfare_output_generator = OutputGenerator(welfare_config)
            
            # Log the new configuration
            self.log(f"✓ Welfare Board time windows updated: {len(windows)} window(s)")
            for w in windows:
                self.log(f"  • {w['name']}: {w['start']}-{w['end']}")
            
            # Update the current window display if on welfare tab
            self.update_welfare_window()
            
            # Also log to welfare board if available
            if hasattr(self, 'welfare_log_text'):
                self.welfare_log(f"✓ Time windows updated: {len(windows)} window(s)")
                for w in windows:
                    self.welfare_log(f"  • {w['name']}: {w['start']}-{w['end']}")
            
            messagebox.showinfo("Success", f"Time windows updated!\n\nActive windows:\n" + 
                              "\n".join([f"• {w['name']}: {w['start']}-{w['end']}" for w in windows]))
            self.save_settings()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply time windows: {e}")
    
    def setup_welfare_tab(self, parent):
        """Setup the Welfare Board tab"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)
        
        # Folder Configuration frame
        folder_frame = ttk.LabelFrame(parent, text="Folder Configuration", padding="10")
        folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        
        # Monitor folder (incoming files)
        ttk.Label(folder_frame, text="Monitor Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Default welfare directory - VarAC Files location
        default_welfare_dir = Path(r"C:\Users\Facundo\Dropbox (Personal)\Ham Radio\Digital Modes\VarAC\Files in")
        if not default_welfare_dir.exists():
            # Fallback if VarAC path doesn't exist
            default_welfare_dir = Path("data/input")
        
        self.welfare_monitor_label = ttk.Label(folder_frame, text=str(default_welfare_dir), foreground="blue")
        self.welfare_monitor_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Button(folder_frame, text="Browse", command=self.set_welfare_folder, width=10).grid(row=0, column=2, padx=(10, 0))
        
        # Archive folder (processed files)
        ttk.Label(folder_frame, text="Archive Folder:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # Default archive directory
        default_archive_dir = Path(r"C:\Users\Facundo\Dropbox (Personal)\Ham Radio\Digital Modes\VarAC\Files in\welfare_archive")
        if not hasattr(self, 'welfare_archive_dir'):
            self.welfare_archive_dir = str(default_archive_dir)
        
        self.welfare_archive_label = ttk.Label(folder_frame, text=self.welfare_archive_dir, foreground="blue")
        self.welfare_archive_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(folder_frame, text="Browse", command=self.set_welfare_archive_folder, width=10).grid(row=1, column=2, padx=(10, 0), pady=(5, 0))
        
        # Error folder (invalid files)
        ttk.Label(folder_frame, text="Error Folder:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # Default error directory
        default_error_dir = Path(r"C:\Users\Facundo\Dropbox (Personal)\Ham Radio\Digital Modes\VarAC\Files in\welfare_error")
        if not hasattr(self, 'welfare_error_dir'):
            self.welfare_error_dir = str(default_error_dir)
        
        self.welfare_error_label = ttk.Label(folder_frame, text=self.welfare_error_dir, foreground="blue")
        self.welfare_error_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(folder_frame, text="Browse", command=self.set_welfare_error_folder, width=10).grid(row=2, column=2, padx=(10, 0), pady=(5, 0))
        
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Current Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Current Window:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.welfare_window_label = ttk.Label(status_frame, text="None", foreground="gray")
        self.welfare_window_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(status_frame, text="Check-ins:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.welfare_checkin_label = ttk.Label(status_frame, text="0", foreground="green", font=('Helvetica', 12, 'bold'))
        self.welfare_checkin_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=2, column=0, pady=(0, 10))
        
        self.welfare_start_button = ttk.Button(
            control_frame,
            text="▶ Start Monitoring",
            command=self.start_welfare_monitoring,
            width=20
        )
        self.welfare_start_button.grid(row=0, column=0, padx=5)
        
        self.welfare_stop_button = ttk.Button(
            control_frame,
            text="⏹ Stop",
            command=self.stop_welfare_monitoring,
            state=tk.DISABLED,
            width=15
        )
        self.welfare_stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            control_frame,
            text="🌐 View Board",
            command=self.view_welfare_board,
            width=15
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            control_frame,
            text="📄 Template",
            command=self.open_welfare_template,
            width=15
        ).grid(row=0, column=3, padx=5)
        
        # Log window
        log_frame = ttk.LabelFrame(parent, text="Welfare Check-in Activity Log", padding="5")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.welfare_log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, wrap=tk.WORD)
        self.welfare_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initial message
        self.welfare_log("Welfare Board ready")
        self.welfare_log("Click 'Start Monitoring' to begin watching for check-ins")
        
        # Update current window periodically
        self.update_welfare_window()
    
    # ── Settings persistence ──────────────────────────────────────────────────

    def _settings_path(self):
        """Return path to the user config file (same folder as the script)."""
        return Path(__file__).parent / "emcomm_bbs_config.json"

    def save_settings(self):
        """Persist all user-configurable settings to emcomm_bbs_config.json."""
        # Twitter handles
        try:
            twitter_handles = self.twitter_handles_entry.get().strip()
        except Exception:
            twitter_handles = ""

        # Nextdoor key and ZIP codes
        try:
            nextdoor_key = self.nextdoor_key_entry.get().strip()
        except Exception:
            nextdoor_key = ""
        try:
            nextdoor_zips = self.nextdoor_zips_entry.get().strip()
        except Exception:
            nextdoor_zips = ""

        # Time windows
        time_windows = []
        try:
            for name_var, start_var, end_var in self._time_window_vars:
                name  = name_var.get().strip()
                start = start_var.get().strip()
                end   = end_var.get().strip()
                if name:
                    time_windows.append({"name": name, "start": start, "end": end})
        except Exception:
            pass

        # Checkboxes (actual var names are generate_*_var)
        def _get_var(name):
            v = getattr(self, name, None)
            return bool(v.get()) if v else True

        config = {
            "save_directory":    self.save_directory,
            "anthropic_api_key": self.summarizer.api_key or "",
            "twitter_token":     getattr(self, "_twitter_token", ""),
            "twitter_handles":   twitter_handles,
            "nextdoor_key":      nextdoor_key,
            "nextdoor_zips":     nextdoor_zips,
            "time_windows":      time_windows,
            "weather_regions":   self._get_selected_regions(),
            "checkboxes": {
                "news":      _get_var("generate_news_var"),
                "weather":   _get_var("generate_weather_var"),
                "space":     _get_var("generate_space_var"),
                "emergency": _get_var("generate_emergency_var"),
                "twitter":   _get_var("generate_twitter_var"),
                "power":     _get_var("generate_power_var"),
                "nextdoor":  _get_var("generate_nextdoor_var"),
            }
        }
        try:
            with open(self._settings_path(), "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.log(f"⚠ Could not save settings: {e}")

    def _get_selected_regions(self):
        """Return list of selected FEMA region numbers."""
        selected = []
        try:
            for i in range(1, 11):
                if self.weather_regions[i].get():
                    selected.append(i)
        except Exception:
            pass
        return selected

    def select_all_regions(self):
        """Select all weather regions"""
        for i in range(1, 11):
            self.weather_regions[i].set(True)
        self.log("Selected all weather regions")
        self.save_settings()

    def select_no_regions(self):
        """Deselect all weather regions"""
        for i in range(1, 11):
            self.weather_regions[i].set(False)
        self.log("Deselected all weather regions")
        self.save_settings()

    def select_directory(self):
        """Select save directory"""
        directory = filedialog.askdirectory(initialdir=self.save_directory)
        if directory:
            self.save_directory = directory
            self.dir_label.config(text=directory)
            self.log(f"Save directory changed to: {directory}")
            self.save_settings()

    def cleanup_old_files(self):
        """Delete old TXT files - keeps only the newest set"""
        try:
            file_prefixes = ['news_', 'wx_R', 'space_', 'emergency_', 'tweets_']
            files_deleted = 0
            for filename in os.listdir(self.save_directory):
                if filename.endswith('.txt'):
                    if any(filename.startswith(p) for p in file_prefixes):
                        filepath = os.path.join(self.save_directory, filename)
                        try:
                            os.remove(filepath)
                            files_deleted += 1
                        except:
                            pass
            if files_deleted > 0:
                self.log(f"✓ Removed {files_deleted} old file(s) - keeping only newest set")
        except Exception as e:
            self.log(f"Warning: Could not clean up old files: {e}")

    def load_settings(self):
        """Load saved settings from emcomm_bbs_config.json on startup."""
        path = self._settings_path()
        if not path.exists():
            return  # First run — nothing to load
        try:
            with open(path) as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load saved settings ({e})")
            return

        # Restore save directory
        saved_dir = config.get("save_directory", "")
        if saved_dir and Path(saved_dir).exists():
            self.save_directory = saved_dir

        # Restore Anthropic API key
        api_key = config.get("anthropic_api_key", "")
        if api_key:
            self.summarizer.set_api_key(api_key)
            self._saved_api_key = api_key          # used to pre-fill the entry widget

        # Restore Twitter token
        token = config.get("twitter_token", "")
        if token:
            self._saved_twitter_token = token       # used to pre-fill and re-apply

        # Store everything else for apply_saved_settings() called after GUI is built
        self._saved_config = config

    def apply_saved_settings(self):
        """Called after GUI is built — fills widgets with persisted values."""
        cfg = getattr(self, "_saved_config", {})
        if not cfg:
            return

        # API key entry
        try:
            saved_key = getattr(self, "_saved_api_key", "")
            if saved_key:
                self.api_key_entry.insert(0, saved_key)
        except Exception:
            pass

        # Twitter token entry + handles + re-apply fetcher
        try:
            token = getattr(self, "_saved_twitter_token", "")
            handles_str = cfg.get("twitter_handles", "")
            if token:
                self.twitter_token_entry.insert(0, token)
                self._twitter_token = token
            if handles_str:
                self.twitter_handles_entry.delete(0, tk.END)
                self.twitter_handles_entry.insert(0, handles_str)
            if token and SocialMediaEmergencyFetcher:
                handles = [h.strip() for h in handles_str.split(",") if h.strip()] if handles_str else None
                self.twitter_fetcher = SocialMediaEmergencyFetcher(token, handles)
        except Exception:
            pass

        # Nextdoor key and ZIP codes
        try:
            nd_key = cfg.get("nextdoor_key", "")
            nd_zips = cfg.get("nextdoor_zips", "")
            if nd_key:
                self.nextdoor_key_entry.insert(0, nd_key)
            if nd_zips:
                self.nextdoor_zips_entry.delete(0, tk.END)
                self.nextdoor_zips_entry.insert(0, nd_zips)
            if nd_key and nd_zips and NextdoorFetcher:
                zip_codes = [z.strip() for z in nd_zips.split(",") if z.strip()]
                self.nextdoor_fetcher = NextdoorFetcher(nd_key, zip_codes)
        except Exception:
            pass

        # Save directory label
        try:
            self.dir_label.config(text=self.save_directory)
        except Exception:
            pass

        # Weather region checkboxes — first clear all, then restore saved selection
        try:
            saved_regions = cfg.get("weather_regions", [])
            if saved_regions:
                for i in range(1, 11):
                    self.weather_regions[i].set(i in saved_regions)
        except Exception:
            pass

        # Output checkboxes (vars are named generate_*_var)
        try:
            boxes = cfg.get("checkboxes", {})
            for key, var_name in [
                ("news",      "generate_news_var"),
                ("weather",   "generate_weather_var"),
                ("space",     "generate_space_var"),
                ("emergency", "generate_emergency_var"),
                ("twitter",   "generate_twitter_var"),
                ("power",     "generate_power_var"),
                ("nextdoor",  "generate_nextdoor_var"),
            ]:
                if key in boxes and hasattr(self, var_name):
                    getattr(self, var_name).set(bool(boxes[key]))
        except Exception:
            pass

        # Time windows
        try:
            windows = cfg.get("time_windows", [])
            for i, win in enumerate(windows[:3]):
                name_var, start_var, end_var = self._time_window_vars[i]
                name_var.delete(0, tk.END)
                name_var.insert(0, win.get("name", ""))
                start_var.delete(0, tk.END)
                start_var.insert(0, win.get("start", "00:00"))
                end_var.delete(0, tk.END)
                end_var.insert(0, win.get("end", "23:59"))
        except Exception:
            pass

    # ── End settings persistence ──────────────────────────────────────────────

    def browse_directory(self):
        """Browse for save directory"""
        directory = filedialog.askdirectory(initialdir=self.save_directory)
        if directory:
            self.save_directory = directory
            self.dir_label.config(text=directory)
            self.log(f"Save directory changed to: {directory}")
            self.save_settings()

    def set_api_key(self):
        """Set the Anthropic API key"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            self.summarizer.set_api_key(api_key)
            self.log("✓ Anthropic API key set (AI summaries enabled)")
            self.save_settings()
        else:
            self.log("Please enter an API key")
    
    def set_twitter_token(self):
        """Set the Twitter bearer token"""
        if not self.emergency_enabled:
            self.log("Emergency module not available")
            return
        
        token = self.twitter_token_entry.get().strip()
        if not token:
            self.log("Please enter a Twitter bearer token")
            return
        
        try:
            # Get custom handles if specified
            handles_str = self.twitter_handles_entry.get().strip()
            custom_handles = None
            if handles_str:
                custom_handles = [h.strip() for h in handles_str.split(',') if h.strip()]
            
            # Create the Twitter fetcher
            self.twitter_fetcher = SocialMediaEmergencyFetcher(token, custom_handles)
            self.log("✓ Twitter bearer token set")
            
            if custom_handles:
                self.log(f"  Monitoring {len(custom_handles)} accounts: {', '.join(custom_handles[:5])}{'...' if len(custom_handles) > 5 else ''}")
            
            # Auto-enable Twitter checkbox
            self.generate_twitter_var.set(True)
            self._twitter_token = token
            self.save_settings()

        except Exception as e:
            self.log(f"✗ Error setting Twitter token: {e}")
            self.twitter_fetcher = None
    
    def update_twitter_handles(self):
        """Update the list of Twitter handles to monitor"""
        if not self.emergency_enabled:
            self.log("Emergency module not available")
            return
        
        handles_str = self.twitter_handles_entry.get().strip()
        if not handles_str:
            self.log("Please enter at least one Twitter handle")
            return
        
        # Parse handles
        custom_handles = [h.strip() for h in handles_str.split(',') if h.strip()]
        
        if not custom_handles:
            self.log("No valid handles found")
            return
        
        # Update the fetcher if it exists
        if self.twitter_fetcher:
            try:
                token = self.twitter_token_entry.get().strip()
                if token:
                    self.twitter_fetcher = SocialMediaEmergencyFetcher(token, custom_handles)
                    self.log(f"✓ Updated Twitter handles: monitoring {len(custom_handles)} accounts")
                    self.log(f"  Accounts: {', '.join(custom_handles[:8])}{'...' if len(custom_handles) > 8 else ''}")
                    self.save_settings()
                else:
                    self.log("Please set Twitter token first")
            except Exception as e:
                self.log(f"Error updating handles: {e}")
        else:
            self.log(f"Twitter handles saved ({len(custom_handles)} accounts). Set token to enable.")
            self.log(f"  Accounts: {', '.join(custom_handles[:8])}{'...' if len(custom_handles) > 8 else ''}")
    
    def set_nextdoor_config(self):
        """Configure Nextdoor API key and ZIP codes"""
        if not self.nextdoor_enabled:
            self.log("Nextdoor module not available")
            return
        
        api_key = self.nextdoor_key_entry.get().strip()
        zips_str = self.nextdoor_zips_entry.get().strip()
        
        # Parse ZIP codes
        zip_codes = [z.strip() for z in zips_str.split(',') if z.strip()]
        
        if not api_key and not zip_codes:
            self.log("⚠ Please enter Nextdoor API key and ZIP codes")
            return
        
        if not api_key:
            self.log("⚠ Please enter Nextdoor API key")
            return
        
        if not zip_codes:
            self.log("⚠ Please enter at least one ZIP code")
            return
        
        try:
            # Create Nextdoor fetcher
            self.nextdoor_fetcher = NextdoorFetcher(api_key, zip_codes)
            self.log(f"✓ Nextdoor configured: monitoring {len(zip_codes)} ZIP code(s)")
            self.log(f"  ZIP codes: {', '.join(zip_codes)}")

            # Enable the checkbox automatically
            self.generate_nextdoor_var.set(True)
            self.save_settings()
            
        except Exception as e:
            self.log(f"✗ Error configuring Nextdoor: {e}")
            self.nextdoor_fetcher = None
    
    def setup_main_tab(self, parent):
        """Setup the main controls tab"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)
        
        # Output Selection
        output_frame = ttk.LabelFrame(parent, text="Select Outputs to Generate", padding="10")
        output_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Initialize checkbox variables
        self.generate_news_var = tk.BooleanVar(value=True)
        self.generate_weather_var = tk.BooleanVar(value=True)
        self.generate_space_var = tk.BooleanVar(value=True)
        self.generate_emergency_var = tk.BooleanVar(value=True)
        self.generate_twitter_var = tk.BooleanVar(value=True)
        self.generate_nextdoor_var = tk.BooleanVar(value=False)  # Default off
        self.generate_power_var = tk.BooleanVar(value=True)
        
        # Weather region variables (R1-R10)
        self.weather_regions = {}
        for i in range(1, 11):
            self.weather_regions[i] = tk.BooleanVar(value=(i == 4))
        
        # Left column - Main outputs
        left_col = ttk.Frame(output_frame)
        left_col.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 20))
        
        ttk.Checkbutton(left_col, text="News Summary", variable=self.generate_news_var, command=self.save_settings).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Weather with Select All/None
        weather_frame = ttk.Frame(left_col)
        weather_frame.grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(weather_frame, text="Weather Forecasts", variable=self.generate_weather_var, command=self.save_settings).pack(side=tk.LEFT)
        ttk.Button(weather_frame, text="Select All", command=self.select_all_regions, width=10).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(weather_frame, text="None", command=self.select_no_regions, width=6).pack(side=tk.LEFT)
        
        ttk.Checkbutton(left_col, text="Space Weather", variable=self.generate_space_var, command=self.save_settings).grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Emergency Alerts", variable=self.generate_emergency_var, command=self.save_settings).grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Power Outages", variable=self.generate_power_var, command=self.save_settings).grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Twitter Feed", variable=self.generate_twitter_var, command=self.save_settings).grid(row=5, column=0, sticky=tk.W, pady=2)
        
        # Nextdoor checkbox (if available)
        if self.nextdoor_enabled:
            ttk.Checkbutton(left_col, text="Nextdoor (Local)", variable=self.generate_nextdoor_var).grid(row=6, column=0, sticky=tk.W, pady=2)
        
        # Right column - FEMA Regions
        right_col = ttk.LabelFrame(output_frame, text="Weather Regions (FEMA)", padding="5")
        right_col.grid(row=0, column=1, sticky=(tk.W, tk.N))
        
        # Region descriptions
        region_info = {
            1: "R1: Northeast (ME,NH,VT,MA,CT,RI)",
            2: "R2: NY/NJ (NY,NJ,PR,VI)",
            3: "R3: Mid-Atlantic (PA,MD,DE,VA,WV,DC)",
            4: "R4: Southeast (AL,FL,GA,KY,MS,NC,SC,TN)",
            5: "R5: Midwest (IL,IN,MI,MN,OH,WI)",
            6: "R6: South Central (AR,LA,NM,OK,TX)",
            7: "R7: Great Plains (IA,KS,MO,NE)",
            8: "R8: Mountain (CO,MT,ND,SD,UT,WY)",
            9: "R9: Southwest (AZ,CA,NV,HI)",
            10: "R10: Northwest (AK,ID,OR,WA)"
        }
        
        for i in range(1, 11):
            ttk.Checkbutton(right_col, text=region_info[i], variable=self.weather_regions[i], command=self.save_settings).grid(row=i-1, column=0, sticky=tk.W, pady=1)
        
        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=0, pady=(0, 10))
        
        self.start_button = ttk.Button(
            control_frame, 
            text="Start Automatic Updates", 
            command=self.start_service,
            width=22
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            control_frame, 
            text="Stop", 
            command=self.stop_service, 
            state=tk.DISABLED,
            width=10
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.manual_button = ttk.Button(
            control_frame, 
            text="Generate Now", 
            command=self.generate_now,
            width=15
        )
        self.manual_button.grid(row=0, column=2, padx=5)
        
        # Status label
        self.status_label = ttk.Label(parent, text="Ready", foreground="blue")
        self.status_label.grid(row=2, column=0, pady=(0, 10))
        
        # Log window
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="5")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initial log messages
        self.log("Emcomm BBS initialized")
        self.log(f"Save directory: {self.save_directory}")
        if not self.emergency_enabled:
            self.log("⚠ Emergency module not available")
        self.log("Click 'Generate Now' to create all PDFs, or 'Start' for automatic 6-hour updates.")
    
    def log(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def generate_summary_pdf(self):
        """Generate a news summary TXT file (optimized for radio transmission)"""
        try:
            # Cleanup old files first
            self.cleanup_old_files()
            
            self.log("Fetching news from sources...")
            self.status_label.config(text="Fetching news...")
            
            # Fetch news
            news_data = self.summarizer.fetch_all_news()
            
            # Count total headlines
            total_headlines = sum(len(h) for h in news_data.values())
            self.log(f"Fetched {total_headlines} headlines from {len(news_data)} sources")
            
            # Generate summary
            self.log("Generating summary...")
            self.status_label.config(text="Generating summary...")
            summary_text = self.summarizer.generate_summary(news_data)
            
            # Log summary info for debugging
            if summary_text:
                summary_preview = summary_text[:100].replace('\n', ' ')
                self.log(f"Summary generated ({len(summary_text)} chars): {summary_preview}...")
                if "AI summary not available" in summary_text or "NOTE:" in summary_text:
                    self.log("⚠ Using basic summary (AI not available)")
                else:
                    self.log("✓ Using AI-generated summary")
            else:
                self.log("⚠ Warning: No summary text generated!")
            
            # Create TXT with shorter filename: news_MMDD_HHMM.txt
            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            filename = os.path.join(self.save_directory, f"news_{short_name}.txt")
            
            self.log("Creating news TXT...")
            self.status_label.config(text="Creating TXT...")
            PlainTextGenerator.create_news_txt(filename, summary_text, news_data)
            
            # Get file size
            file_size = os.path.getsize(filename)
            self.log(f"✓ News TXT saved: news_{short_name}.txt ({file_size:,} bytes)")
            self.status_label.config(text=f"TXT created: news_{short_name}.txt")
            
            return True
        except Exception as e:
            self.log(f"✗ Error generating news summary: {str(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()[:500]}")
            self.status_label.config(text="Error occurred")
            return False
    
    def generate_weather_pdf(self):
        """Generate weather forecast TXT files by FEMA region (optimized for radio)"""
        try:
            # Get list of selected regions
            selected_regions = [i for i in range(1, 11) if self.weather_regions[i].get()]
            
            if not selected_regions:
                self.log("⚠ No weather regions selected - skipping weather generation")
                return False
            
            self.log(f"Fetching weather for {len(selected_regions)} selected region(s): {selected_regions}")
            self.status_label.config(text="Fetching weather...")
            
            # Only fetch weather for selected regions (saves API calls!)
            weather_fetcher = WeatherFetcher()
            forecasts_by_region = weather_fetcher.get_all_forecasts(
                selected_regions=selected_regions,
                log_callback=self.log
            )
            
            if not forecasts_by_region:
                self.log("No weather data available")
                return False
            
            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            
            # Create a TXT file for each selected FEMA region
            txts_created = 0
            total_size = 0
            for region_num in selected_regions:
                forecasts = forecasts_by_region.get(region_num, [])
                if forecasts:
                    filename = os.path.join(self.save_directory, f"wx_R{region_num}_{short_name}.txt")
                    
                    self.log(f"Creating weather TXT for FEMA Region {region_num}...")
                    PlainTextGenerator.create_weather_txt(
                        filename, region_num, forecasts, FEMA_REGIONS.get(region_num, "")
                    )
                    
                    file_size = os.path.getsize(filename)
                    total_size += file_size
                    self.log(f"✓ Weather TXT saved: wx_R{region_num}_{short_name}.txt ({file_size:,} bytes, {len(forecasts)} cities)")
                    txts_created += 1
            
            if txts_created > 0:
                self.log(f"✓ Created {txts_created} weather TXT files (total: {total_size:,} bytes)")
            else:
                self.log("⚠ No weather data retrieved for selected regions")
            
            return True
        except Exception as e:
            self.log(f"✗ Error generating weather TXT: {str(e)}")
            return False
    
    def generate_space_weather_pdf(self):
        """Generate space weather TXT file (optimized for radio)"""
        try:
            self.log("Fetching space weather data...")
            self.status_label.config(text="Fetching space weather...")
            
            space_fetcher = SpaceWeatherFetcher()
            conditions = space_fetcher.get_conditions()
            
            # Create TXT with shorter filename: space_MMDD_HHMM.txt
            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            filename = os.path.join(self.save_directory, f"space_{short_name}.txt")
            
            self.log("Creating space weather TXT...")
            PlainTextGenerator.create_space_txt(filename, conditions)
            
            file_size = os.path.getsize(filename)
            self.log(f"✓ Space weather TXT saved: space_{short_name}.txt ({file_size:,} bytes)")
            
            return True
        except Exception as e:
            self.log(f"✗ Error generating space weather TXT: {str(e)}")
            return False
    
    def generate_emergency_pdf(self):
        """Generate emergency information PDF"""
        if not self.emergency_enabled:
            self.log("Emergency module not available - skipping")
            return False
        
        try:
            self.log("Fetching emergency data...")
            self.status_label.config(text="Fetching emergency alerts...")
            
            # Fetch emergency data with timeout protection
            import time
            start_time = time.time()
            
            self.log("  - Fetching NWS alerts...")
            emergency_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'nws_alerts': [],
                'usgs_earthquakes': [],
                'fema_disasters': [],
                'fire_incidents': {},
                'twitter_tweets': []
            }
            
            # Fetch each data source individually with error handling
            try:
                emergency_data['nws_alerts'] = self.emergency_fetcher.get_nws_alerts()
                self.log(f"    ✓ Got {len(emergency_data['nws_alerts'])} alerts")
            except Exception as e:
                self.log(f"    ⚠ NWS alerts error: {str(e)}")
            
            try:
                self.log("  - Fetching earthquake data...")
                emergency_data['usgs_earthquakes'] = self.emergency_fetcher.get_recent_earthquakes()
                self.log(f"    ✓ Got {len(emergency_data['usgs_earthquakes'])} earthquakes")
            except Exception as e:
                self.log(f"    ⚠ USGS error: {str(e)}")
            
            try:
                self.log("  - Fetching FEMA disasters...")
                emergency_data['fema_disasters'] = self.emergency_fetcher.get_fema_disasters()
                self.log(f"    ✓ Got {len(emergency_data['fema_disasters'])} disasters")
            except Exception as e:
                self.log(f"    ⚠ FEMA error: {str(e)}")
            
            try:
                self.log("  - Fetching wildfire data...")
                emergency_data['fire_incidents'] = self.emergency_fetcher.get_active_fires()
                self.log("    ✓ Got fire data")
            except Exception as e:
                self.log(f"    ⚠ Fire data error: {str(e)}")
            
            # Fetch Twitter emergency tweets if configured
            if self.twitter_fetcher:
                try:
                    self.log("  - Fetching emergency tweets...")
                    self.log(f"    Twitter fetcher configured: {self.twitter_fetcher is not None}")
                    emergency_data['twitter_tweets'] = self.twitter_fetcher.get_emergency_tweets()
                    
                    if isinstance(emergency_data['twitter_tweets'], list):
                        self.log(f"    ✓ Got {len(emergency_data['twitter_tweets'])} tweets")
                    elif isinstance(emergency_data['twitter_tweets'], dict):
                        if emergency_data['twitter_tweets'].get('error'):
                            self.log(f"    ⚠ Twitter error: {emergency_data['twitter_tweets'].get('error')}")
                            if emergency_data['twitter_tweets'].get('details'):
                                for detail in emergency_data['twitter_tweets']['details'][:3]:
                                    self.log(f"      - {detail}")
                        else:
                            self.log(f"    ⚠ Twitter returned: {emergency_data['twitter_tweets'].get('message', 'Unknown response')}")
                except Exception as e:
                    self.log(f"    ⚠ Twitter exception: {str(e)}")
                    import traceback
                    self.log(f"    Traceback: {traceback.format_exc()[:200]}")
                    emergency_data['twitter_tweets'] = {
                        'error': str(e),
                        'message': 'Could not fetch tweets - check token and connection',
                        'alternative': 'Check Twitter/X directly for emergency updates'
                    }
            else:
                self.log("  - Twitter not configured")
                self.log("    To enable: Add Twitter bearer token and click 'Set Token'")
                emergency_data['twitter_tweets'] = {
                    'message': 'Twitter integration not configured',
                    'alternative': 'Add Twitter bearer token in settings to enable real-time tweets'
                }
            
            elapsed = time.time() - start_time
            self.log(f"  Emergency data fetched in {elapsed:.1f}s")
            
            # Get emergency resources
            resources = EmergencyResourcesFetcher.get_emergency_resources()
            
            # Create TXT with shorter filename: emergency_MMDD_HHMM.txt
            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            filename = os.path.join(self.save_directory, f"emergency_{short_name}.txt")
            
            self.log("Creating emergency TXT...")
            self.status_label.config(text="Creating emergency TXT...")
            PlainTextGenerator.create_emergency_txt(filename, emergency_data)
            
            file_size = os.path.getsize(filename)
            self.log(f"✓ Emergency TXT saved: emergency_{short_name}.txt ({file_size:,} bytes)")
            self.status_label.config(text=f"Emergency TXT created: emergency_{short_name}.txt")
            
            return True
        except Exception as e:
            self.log(f"✗ Error generating emergency HTML: {str(e)}")
            self.status_label.config(text="Error in emergency HTML")
            return False
    
    def generate_twitter_pdf(self):
        """Generate Twitter emergency feed TXT file"""
        if not self.twitter_fetcher:
            self.log("Twitter not configured - skipping Twitter TXT")
            return False
        
        try:
            self.log("Fetching emergency tweets...")
            self.status_label.config(text="Fetching tweets...")
            
            tweets = self.twitter_fetcher.get_emergency_tweets()
            
            if isinstance(tweets, list):
                self.log(f"  ✓ Got {len(tweets)} tweets")
            elif isinstance(tweets, dict) and tweets.get('error'):
                self.log(f"  ⚠ Twitter error: {tweets.get('error')}")
            
            # Create TXT with shorter filename: tweets_MMDD_HHMM.txt
            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            filename = os.path.join(self.save_directory, f"tweets_{short_name}.txt")
            
            self.log("Creating Twitter TXT...")
            self.status_label.config(text="Creating Twitter TXT...")
            PlainTextGenerator.create_tweets_txt(filename, tweets)
            
            file_size = os.path.getsize(filename)
            self.log(f"✓ Twitter TXT saved: tweets_{short_name}.txt ({file_size:,} bytes)")
            self.status_label.config(text=f"Twitter TXT created: tweets_{short_name}.txt")
            
            return True
        except Exception as e:
            self.log(f"✗ Error generating Twitter TXT: {str(e)}")
            import traceback
            self.log(f"  Traceback: {traceback.format_exc()[:300]}")
            self.status_label.config(text="Error in Twitter TXT")
            return False
    
    def generate_power_outage(self):
        """Fetch power outage data from DOE EAGLE-I and save as TXT"""
        try:
            self.log("Fetching power outage data from DOE EAGLE-I...")
            self.status_label.config(text="Fetching power outage data...")

            fetcher = PowerOutageFetcher()
            outage_data = fetcher.get_outages(log_callback=self.log)

            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            filename = os.path.join(self.save_directory, f"power_outages_{short_name}.txt")

            txt_content = PowerOutageFetcher.format_txt(outage_data)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(txt_content)

            file_size = os.path.getsize(filename)
            self.log(f"✓ Power Outage TXT saved: power_outages_{short_name}.txt ({file_size:,} bytes)")
            self.status_label.config(text=f"Power outage report created: power_outages_{short_name}.txt")
            return True
        except Exception as e:
            self.log(f"✗ Error generating power outage report: {str(e)}")
            self.status_label.config(text="Error in power outage report")
            return False

    def generate_nextdoor(self):
        """Generate Nextdoor community posts TXT file"""
        if not self.nextdoor_fetcher:
            self.log("Nextdoor not configured - skipping Nextdoor TXT")
            return False
        
        try:
            self.log("Fetching local Nextdoor posts...")
            self.status_label.config(text="Fetching Nextdoor posts...")
            
            posts = self.nextdoor_fetcher.get_local_posts()
            
            if isinstance(posts, list):
                self.log(f"  ✓ Got {len(posts)} posts from {len(self.nextdoor_fetcher.zip_codes)} ZIP code(s)")
                
                # Show statistics
                stats = self.nextdoor_fetcher.get_statistics(posts)
                if stats:
                    critical = stats['by_urgency'].get('critical', 0)
                    high = stats['by_urgency'].get('high', 0)
                    medium = stats['by_urgency'].get('medium', 0)
                    self.log(f"  Critical: {critical}, High: {high}, Medium: {medium}")
                    
            elif isinstance(posts, dict) and posts.get('error'):
                self.log(f"  ⚠ Nextdoor error: {posts.get('error')}")
                if posts.get('message'):
                    self.log(f"  {posts['message']}")
                return False
            
            # Create TXT with shorter filename: nextdoor_MMDD_HHMM.txt
            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            filename = os.path.join(self.save_directory, f"nextdoor_{short_name}.txt")
            
            self.log("Creating Nextdoor TXT...")
            self.status_label.config(text="Creating Nextdoor TXT...")
            PlainTextGenerator.create_nextdoor_txt(
                filename, 
                posts, 
                self.nextdoor_fetcher.zip_codes
            )
            
            file_size = os.path.getsize(filename)
            self.log(f"✓ Nextdoor TXT saved: nextdoor_{short_name}.txt ({file_size:,} bytes)")
            self.status_label.config(text=f"Nextdoor TXT created: nextdoor_{short_name}.txt")
            
            return True
        except Exception as e:
            self.log(f"✗ Error generating Nextdoor TXT: {str(e)}")
            import traceback
            self.log(f"  Traceback: {traceback.format_exc()[:300]}")
            self.status_label.config(text="Error in Nextdoor TXT")
            return False
    
    def generate_all(self):
        """Generate selected reports based on checkbox selections"""
        self.log("=" * 50)
        self.log("Starting generation of selected reports...")
        
        # Check which outputs are selected
        outputs_to_generate = []
        if self.generate_news_var.get():
            outputs_to_generate.append("News")
        if self.generate_weather_var.get():
            outputs_to_generate.append("Weather")
        if self.generate_space_var.get():
            outputs_to_generate.append("Space")
        if self.generate_emergency_var.get():
            outputs_to_generate.append("Emergency")
        if self.generate_power_var.get():
            outputs_to_generate.append("Power Outages")
        if self.generate_twitter_var.get():
            outputs_to_generate.append("Twitter")
        if self.generate_nextdoor_var.get():
            outputs_to_generate.append("Nextdoor")
        
        if not outputs_to_generate:
            self.log("⚠ No outputs selected! Please select at least one output to generate.")
            return
        
        self.log(f"Generating: {', '.join(outputs_to_generate)}")
        
        # Generate news
        if self.generate_news_var.get():
            self.generate_summary_pdf()
        else:
            self.log("⊘ Skipping News (not selected)")
        
        # Generate weather  
        if self.generate_weather_var.get():
            # Check if any regions are selected
            selected_regions = sum(1 for i in range(1, 11) if self.weather_regions[i].get())
            if selected_regions > 0:
                self.log(f"Weather: {selected_regions} regions selected")
                self.generate_weather_pdf()
            else:
                self.log("⊘ Skipping Weather (no regions selected)")
        else:
            self.log("⊘ Skipping Weather (not selected)")
        
        # Generate space weather
        if self.generate_space_var.get():
            self.generate_space_weather_pdf()
        else:
            self.log("⊘ Skipping Space Weather (not selected)")
        
        # Generate emergency info
        if self.generate_emergency_var.get():
            if self.emergency_enabled:
                self.generate_emergency_pdf()
            else:
                self.log("⚠ Emergency module not available")
        else:
            self.log("⊘ Skipping Emergency Alerts (not selected)")
        
        # Generate power outage report
        if self.generate_power_var.get():
            self.generate_power_outage()
        else:
            self.log("⊘ Skipping Power Outages (not selected)")

        # Generate Twitter feed - SMART DETECTION to avoid duplicates
        if self.generate_twitter_var.get():
            # Check if we should generate tweets here or let twitter worker handle it
            main_interval = self.main_interval_var.get()
            twitter_interval = self.twitter_interval_var.get()
            
            if main_interval == twitter_interval:
                # Intervals match - generate tweets here (twitter worker will skip)
                if self.twitter_fetcher:
                    self.log("Twitter: Generating (intervals match - main worker handles)")
                    self.generate_twitter_pdf()
                else:
                    self.log("⚠ Twitter not configured - skipping")
            else:
                # Intervals differ - let twitter worker handle it
                self.log(f"⊘ Skipping Twitter (handled by separate worker: every {twitter_interval}h)")
        else:
            self.log("⊘ Skipping Twitter Feed (not selected)")
        
        # Generate Nextdoor posts (local community)
        if self.generate_nextdoor_var.get():
            if self.nextdoor_fetcher:
                self.log("Nextdoor: Generating local community posts")
                self.generate_nextdoor()
            else:
                self.log("⚠ Nextdoor not configured - skipping")
        else:
            self.log("⊘ Skipping Nextdoor Posts (not selected)")
        
        self.log("Selected reports generated!")
        self.log("=" * 50)
    
    def generate_now(self):
        """Generate all reports immediately"""
        self.manual_button.config(state=tk.DISABLED)
        
        def run():
            self.generate_all()
            self.manual_button.config(state=tk.NORMAL)
        
        threading.Thread(target=run, daemon=True).start()
    
    def start_service(self):
        """Start the automatic generation service"""
        self.is_running = True
        self.twitter_is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        main_interval_hours = self.main_interval_var.get()
        twitter_interval_hours = self.twitter_interval_var.get()
        
        # Explain smart detection to user
        if main_interval_hours == twitter_interval_hours:
            self.log(f"Service started. All reports every {main_interval_hours}h (intervals match - optimized)")
        else:
            self.log(f"Service started. Main reports every {main_interval_hours}h, Twitter every {twitter_interval_hours}h (separate schedules)")
        
        self.status_label.config(text="Service running - Generation in progress...")
        
        def worker():
            while self.is_running:
                # Generate all reports immediately on start
                self.generate_all()
                
                if not self.is_running:
                    break
                
                # Wait for configured interval
                main_interval_seconds = main_interval_hours * 3600
                iterations = main_interval_seconds // 10  # Check every 10 seconds
                self.log(f"Next main generation in {main_interval_hours} hours.")
                
                for i in range(iterations):
                    if not self.is_running:
                        break
                    remaining = main_interval_seconds - (i * 10)
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60
                    self.status_label.config(text=f"Service running - Next main in {hours}h {minutes}m")
                    time.sleep(10)
        
        def twitter_worker():
            """Separate worker for Twitter feed updates"""
            if not self.twitter_fetcher:
                return
            
            # Check if twitter checkbox is even selected
            if not self.generate_twitter_var.get():
                self.log("Twitter worker: Twitter feed not selected - worker inactive")
                return
            
            while self.twitter_is_running:
                # Smart detection: only generate if intervals differ
                main_interval = self.main_interval_var.get()
                twitter_interval = self.twitter_interval_var.get()
                
                if main_interval == twitter_interval:
                    # Intervals match - main worker handles it, we skip
                    self.log(f"Twitter worker: Intervals match ({twitter_interval}h) - main worker handles tweets")
                    # Sleep for the interval and check again
                    twitter_interval_seconds = twitter_interval_hours * 3600
                    iterations = twitter_interval_seconds // 10
                    
                    for i in range(iterations):
                        if not self.twitter_is_running:
                            break
                        time.sleep(10)
                    continue
                
                # Intervals differ - we handle twitter updates
                self.log(f"Twitter worker: Generating (every {twitter_interval}h, main every {main_interval}h)")
                self.generate_twitter_pdf()
                
                if not self.twitter_is_running:
                    break
                
                # Wait for configured Twitter interval
                twitter_interval_seconds = twitter_interval_hours * 3600
                iterations = twitter_interval_seconds // 10
                self.log(f"Next Twitter update in {twitter_interval_hours} hours.")
                
                for i in range(iterations):
                    if not self.twitter_is_running:
                        break
                    time.sleep(10)
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
        
        if self.twitter_fetcher:
            self.twitter_worker_thread = threading.Thread(target=twitter_worker, daemon=True)
            self.twitter_worker_thread.start()
    
    def stop_service(self):
        """Stop the automatic generation service"""
        self.is_running = False
        self.twitter_is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("Service stopped.")
        self.status_label.config(text="Service stopped")
    
    # Welfare Board Methods
    def welfare_log(self, message):
        """Add message to welfare board log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        self.welfare_log_text.insert(tk.END, log_message)
        self.welfare_log_text.see(tk.END)
        self.welfare_log_text.update()
    
    def set_welfare_folder(self):
        """Set welfare board input folder"""
        folder = filedialog.askdirectory(initialdir=".")
        if folder:
            self.welfare_monitor_label.config(text=folder)
            self.welfare_log(f"Monitor folder set to: {folder}")
    
    def set_welfare_archive_folder(self):
        """Set welfare board archive folder"""
        folder = filedialog.askdirectory(initialdir=self.welfare_archive_dir)
        if folder:
            self.welfare_archive_dir = folder
            self.welfare_archive_label.config(text=folder)
            self.welfare_log(f"Archive folder set to: {folder}")
    
    def set_welfare_error_folder(self):
        """Set welfare board error folder"""
        folder = filedialog.askdirectory(initialdir=self.welfare_error_dir)
        if folder:
            self.welfare_error_dir = folder
            self.welfare_error_label.config(text=folder)
            self.welfare_log(f"Error folder set to: {folder}")
    
    def start_welfare_monitoring(self):
        """Start monitoring for welfare check-ins"""
        try:
            if self.welfare_is_running:
                return
            
            input_dir = Path(self.welfare_monitor_label.cget("text"))
            
            # Create directory if it doesn't exist
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Log current configuration
            self.welfare_log("✓ Started monitoring for welfare check-ins")
            self.welfare_log(f"  Watching: {input_dir}")
            self.welfare_log(f"  Time windows configured: {len(self.welfare_aggregator.time_windows)}")
            for tw in self.welfare_aggregator.time_windows:
                self.welfare_log(f"    • {tw['name']}: {tw['start']}-{tw['end']}")
            
            # Check current window
            from datetime import datetime
            current_time = datetime.now()
            self.welfare_log(f"  Current time: {current_time.strftime('%H:%M:%S')}")
            
            window_info = self.welfare_aggregator.get_current_window()
            if window_info:
                self.welfare_log(f"  ✓ Active window: {window_info['name']} ({window_info['start']}-{window_info['end']})")
            else:
                self.welfare_log(f"  ⚠ No active window right now - check-ins will be rejected until a window is active")
            
            # Start file watcher
            self.welfare_watcher = WelfareFileWatcher(input_dir, self.process_welfare_file)
            self.welfare_watcher.start()
            
            self.welfare_is_running = True
            self.welfare_start_button.config(state=tk.DISABLED)
            self.welfare_stop_button.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
            self.welfare_log(f"✗ Error starting: {e}")
    
    def stop_welfare_monitoring(self):
        """Stop welfare monitoring"""
        if self.welfare_watcher:
            self.welfare_watcher.stop()
            self.welfare_watcher = None
        
        self.welfare_is_running = False
        self.welfare_start_button.config(state=tk.NORMAL)
        self.welfare_stop_button.config(state=tk.DISABLED)
        
        self.welfare_log("⏹ Stopped monitoring")
    
    def process_welfare_file(self, filepath):
        """Process a newly received welfare check-in file"""
        try:
            # Check if file still exists (might have been moved already)
            if not filepath.exists():
                # File was already processed - this is normal, don't log it
                # (File watcher can trigger multiple times for the same file)
                return
            
            self.welfare_log(f"📥 New file: {filepath.name}")
            
            # Parse file
            parsed_data = self.welfare_parser.parse_file(filepath)
            if not parsed_data:
                self.welfare_log(f"  ✗ Failed to parse file")
                if filepath.exists():  # Check again before moving
                    self.move_welfare_to_error(filepath, "Parse failed")
                return
            
            # Validate
            is_valid, errors = self.welfare_validator.validate(parsed_data)
            if not is_valid:
                self.welfare_log(f"  ✗ Validation failed:")
                for error in errors:
                    self.welfare_log(f"    • {error}")
                if filepath.exists():  # Check before moving
                    self.move_welfare_to_error(filepath, f"Validation: {'; '.join(errors)}")
                return
            
            self.welfare_log(f"  ✓ Valid check-in from {parsed_data['callsign']}")
            
            # Add to aggregator
            success, message, window_info = self.welfare_aggregator.add_checkin(parsed_data)
            
            if not success:
                # Check if it's a true duplicate (identical content)
                if "identical" in message.lower():
                    self.welfare_log(f"  ℹ {message}")
                    self.welfare_log(f"  → Discarding redundant check-in (no new information)")
                    if filepath.exists():
                        self.move_welfare_to_archive(filepath)  # Archive, not error
                else:
                    # Other failure (no active window, etc.)
                    self.welfare_log(f"  ⚠ {message}")
                    
                    # Log current time and windows for debugging
                    from datetime import datetime
                    current_time = datetime.now()
                    self.welfare_log(f"  ℹ Current time: {current_time.strftime('%H:%M:%S')}")
                    self.welfare_log(f"  ℹ Configured windows: {len(self.welfare_aggregator.time_windows)}")
                    for tw in self.welfare_aggregator.time_windows:
                        self.welfare_log(f"    • {tw['name']}: {tw['start']}-{tw['end']}")
                    
                    if filepath.exists():
                        self.move_welfare_to_error(filepath, message)
                return
            
            # Success - either new check-in or update
            if "Updated" in message:
                self.welfare_log(f"  🔄 {message}")  # Update indicator
            else:
                self.welfare_log(f"  ✓ {message}")  # New check-in
            
            # Get all check-ins for this window
            checkins = self.welfare_aggregator.get_window_checkins(window_info['key'])
            
            # Generate outputs in same directory as news, weather, tweets, etc.
            output_dir = Path(self.save_directory)
            
            # Update output generator config
            self.welfare_output_generator.config = {
                'directories': {'output': str(output_dir)},
                'output': {
                    'generate_text': True,
                    'generate_html': True,
                    'generate_csv': True,
                    'html_auto_refresh': 30
                }
            }
            self.welfare_output_generator.output_dir = output_dir
            
            generated = self.welfare_output_generator.generate_all(window_info, checkins)
            
            if generated:
                self.welfare_log(f"  ✓ Generated {len(generated)} output files:")
                for file_type, filepath in generated.items():
                    self.welfare_log(f"    • {file_type.upper()}: {Path(filepath).name}")
            
            # Move to archive
            self.move_welfare_to_archive(filepath)
            
            # Update display
            self.update_welfare_checkin_count()
            
        except Exception as e:
            self.welfare_log(f"  ✗ Error processing file: {e}")
            import traceback
            self.welfare_log(f"  {traceback.format_exc()[:200]}")
            self.move_welfare_to_error(filepath, str(e))
    
    def move_welfare_to_archive(self, filepath):
        """Move processed welfare file to archive"""
        try:
            # Use user-selected archive folder
            archive_dir = Path(self.welfare_archive_dir)
            archive_dir.mkdir(parents=True, exist_ok=True)
            dest = archive_dir / filepath.name
            
            # Add timestamp if file exists
            if dest.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                dest = archive_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"
            
            shutil.move(str(filepath), str(dest))
            self.welfare_log(f"  📦 Archived: {dest.name}")
        except Exception as e:
            self.welfare_log(f"  ⚠ Archive failed: {e}")
    
    def move_welfare_to_error(self, filepath, reason):
        """Move invalid welfare file to error directory"""
        try:
            # Use user-selected error folder
            error_dir = Path(self.welfare_error_dir)
            error_dir.mkdir(parents=True, exist_ok=True)
            dest = error_dir / filepath.name
            
            # Add timestamp if file exists
            if dest.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                dest = error_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"
            
            shutil.move(str(filepath), str(dest))
            
            # Write error log
            error_log = dest.with_suffix('.error.txt')
            error_log.write_text(f"Error: {reason}\nTime: {datetime.now()}\n")
            
            self.welfare_log(f"  ⚠ Moved to error folder: {reason}")
        except Exception as e:
            self.welfare_log(f"  ✗ Error move failed: {e}")
    
    def update_welfare_window(self):
        """Update current welfare time window display"""
        if not self.welfare_enabled:
            return
        
        current_time = datetime.now()
        window_info = self.welfare_aggregator.get_current_window()
        
        if window_info:
            self.welfare_window_label.config(
                text=f"{window_info['name']} ({window_info['start']}-{window_info['end']}) - Active now!",
                foreground="green"
            )
        else:
            # Show current time and next window
            time_str = current_time.strftime('%H:%M')
            self.welfare_window_label.config(
                text=f"No active window (current time: {time_str})",
                foreground="gray"
            )
        
        # Schedule next update
        self.root.after(60000, self.update_welfare_window)  # Every minute
    
    def update_welfare_checkin_count(self):
        """Update welfare check-in counter"""
        window_info = self.welfare_aggregator.get_current_window()
        if window_info:
            count = self.welfare_aggregator.get_window_count(window_info['key'])
            self.welfare_checkin_label.config(text=str(count))
    
    def view_welfare_board(self):
        """Open HTML welfare board in browser"""
        import webbrowser
        
        # Look in same directory as other outputs
        output_dir = Path(self.save_directory)
        html_file = output_dir / 'welfare_board.html'
        
        if html_file.exists():
            webbrowser.open(html_file.as_uri())
            self.welfare_log("🌐 Opened welfare board in browser")
        else:
            messagebox.showinfo("Info", "No welfare board generated yet. Start monitoring to collect check-ins.")
    
    def open_welfare_template(self):
        """Open welfare template file"""
        import sys
        import subprocess
        
        template_file = Path('welfare_checkin_template.txt')
        
        if not template_file.exists():
            # Create default template
            template_content = """CALLSIGN: 

NAME: 

LOCATION: 

STATUS: (SAFE / NEED ASSISTANCE / TRAFFIC)

MESSAGE:

"""
            template_file.write_text(template_content)
        
        # Open in default text editor
        try:
            if sys.platform == 'win32':
                import os
                os.startfile(template_file)
            elif sys.platform == 'darwin':
                subprocess.call(['open', template_file])
            else:
                subprocess.call(['xdg-open', template_file])
            
            self.welfare_log("📄 Opened template file")
        except Exception as e:
            self.welfare_log(f"⚠ Could not open template: {e}")


def main():
    root = tk.Tk()
    app = NewsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
