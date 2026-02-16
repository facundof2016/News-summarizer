#!/usr/bin/env python3
"""
News Summarizer Desktop App
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
    
    def get_all_forecasts(self, log_callback=None):
        """Get forecasts for all major cities, organized by FEMA region"""
        forecasts_by_region = {i: [] for i in range(1, 11)}
        
        total = len(MAJOR_US_CITIES)
        for i, (city, location) in enumerate(MAJOR_US_CITIES.items(), 1):
            lat, lon, fema_region = location
            if log_callback:
                log_callback(f"Fetching weather for {city} ({i}/{total})...")
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


class NewsApp:
    """Main application GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("News Summarizer - All-In-One Edition")
        self.root.geometry("700x650")
        
        self.summarizer = NewsSummarizer()
        self.is_running = False
        self.worker_thread = None
        self.twitter_worker_thread = None
        self.twitter_is_running = False
        self.save_directory = str(Path.home() / "Downloads")
        
        # Initialize emergency fetchers if module is available
        if EmergencyDataFetcher:
            self.emergency_fetcher = EmergencyDataFetcher()
            self.emergency_enabled = True
        else:
            self.emergency_fetcher = None
            self.emergency_enabled = False
        
        self.twitter_fetcher = None  # Will be set if user provides token
        
        self.setup_gui()
    
    def setup_gui(self):
        """Create the GUI elements"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="All-In-One: News • Weather • Space • Emergency", 
            font=('Helvetica', 14, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # API Key section
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration (Optional)", padding="10")
        api_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.api_key_entry = ttk.Entry(api_frame, show="*", width=40)
        self.api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(api_frame, text="Set Key", command=self.set_api_key).grid(row=0, column=2)
        
        info_label = ttk.Label(
            api_frame, 
            text="Note: API key enables AI-powered summaries. Without it, you'll get headline lists only.",
            font=('Helvetica', 8),
            foreground='gray'
        )
        info_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Twitter API section (for emergency tweets)
        if self.emergency_enabled:
            ttk.Label(api_frame, text="Twitter Bearer Token:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
            self.twitter_token_entry = ttk.Entry(api_frame, show="*", width=40)
            self.twitter_token_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(10, 0))
            
            ttk.Button(api_frame, text="Set Token", command=self.set_twitter_token).grid(row=2, column=2, pady=(10, 0))
            
            twitter_info = ttk.Label(
                api_frame,
                text="Optional: Adds emergency tweets from official accounts. Free tier: 500K tweets/month.",
                font=('Helvetica', 8),
                foreground='gray'
            )
            twitter_info.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
            
            # Twitter handles selection
            ttk.Label(api_frame, text="Twitter Handles:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
            self.twitter_handles_entry = ttk.Entry(api_frame, width=40)
            self.twitter_handles_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(10, 0))
            
            # Set default handles
            default_handles = "NWS,fema,USGS_Quakes,NWSAlerts,CDCgov,NHC_Atlantic"
            self.twitter_handles_entry.insert(0, default_handles)
            
            ttk.Button(api_frame, text="Update Handles", command=self.update_twitter_handles).grid(row=4, column=2, pady=(10, 0))
            
            handles_info = ttk.Label(
                api_frame,
                text="Comma-separated list (no @ symbols). Example: NWS,fema,USGS_Quakes",
                font=('Helvetica', 8),
                foreground='gray'
            )
            handles_info.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Directory selection
        dir_frame = ttk.LabelFrame(main_frame, text="Save Location", padding="10")
        dir_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.dir_label = ttk.Label(dir_frame, text=self.save_directory, relief=tk.SUNKEN, anchor=tk.W)
        self.dir_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dir_frame, text="Browse...", command=self.select_directory).grid(row=0, column=2)
        
        # Update intervals
        interval_frame = ttk.LabelFrame(main_frame, text="Update Intervals", padding="10")
        interval_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(interval_frame, text="Main Reports (News/Weather/Space/Emergency):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.main_interval_var = tk.IntVar(value=6)
        main_interval_spin = ttk.Spinbox(interval_frame, from_=1, to=24, textvariable=self.main_interval_var, width=5)
        main_interval_spin.grid(row=0, column=1, padx=5)
        ttk.Label(interval_frame, text="hours").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(interval_frame, text="Twitter Feed:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.twitter_interval_var = tk.IntVar(value=6)
        twitter_interval_spin = ttk.Spinbox(interval_frame, from_=1, to=12, textvariable=self.twitter_interval_var, width=5)
        twitter_interval_spin.grid(row=1, column=1, padx=5, pady=(5, 0))
        ttk.Label(interval_frame, text="hours").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        
        # Output Selection
        output_frame = ttk.LabelFrame(main_frame, text="Select Outputs to Generate", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Initialize checkbox variables
        self.generate_news_var = tk.BooleanVar(value=True)
        self.generate_weather_var = tk.BooleanVar(value=True)
        self.generate_space_var = tk.BooleanVar(value=True)
        self.generate_emergency_var = tk.BooleanVar(value=True)
        self.generate_twitter_var = tk.BooleanVar(value=True)
        
        # Weather region variables (R1-R10)
        self.weather_regions = {}
        for i in range(1, 11):
            self.weather_regions[i] = tk.BooleanVar(value=True)
        
        # Left column - Main outputs
        left_col = ttk.Frame(output_frame)
        left_col.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 20))
        
        ttk.Checkbutton(left_col, text="News Summary", variable=self.generate_news_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Weather with Select All/None
        weather_frame = ttk.Frame(left_col)
        weather_frame.grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(weather_frame, text="Weather Forecasts", variable=self.generate_weather_var).pack(side=tk.LEFT)
        ttk.Button(weather_frame, text="Select All", command=self.select_all_regions, width=10).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(weather_frame, text="None", command=self.select_no_regions, width=6).pack(side=tk.LEFT)
        
        ttk.Checkbutton(left_col, text="Space Weather", variable=self.generate_space_var).grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Emergency Alerts", variable=self.generate_emergency_var).grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_col, text="Twitter Feed", variable=self.generate_twitter_var).grid(row=4, column=0, sticky=tk.W, pady=2)
        
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
            ttk.Checkbutton(right_col, text=region_info[i], variable=self.weather_regions[i]).grid(row=i-1, column=0, sticky=tk.W, pady=1)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(
            control_frame, 
            text="Start Automatic Updates", 
            command=self.start_service
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            control_frame, 
            text="Stop", 
            command=self.stop_service, 
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.manual_button = ttk.Button(
            control_frame, 
            text="Generate Now", 
            command=self.generate_now
        )
        self.manual_button.grid(row=0, column=2, padx=5)
        
        # Status/Log area
        log_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Startup message
        startup_msg = "All-In-One App Ready! Generates: News • Weather • Space Weather"
        if self.emergency_enabled:
            startup_msg += " • Emergency Alerts"
        self.log(startup_msg)
        self.log("Click 'Generate Now' to create all PDFs, or 'Start' for automatic 6-hour updates.")
    
    def log(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def set_api_key(self):
        """Set the API key"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            self.summarizer.set_api_key(api_key)
            self.log("API key configured successfully.")
            self.status_label.config(text="API key set - AI summaries enabled")
        else:
            self.log("Please enter a valid API key.")
    
    def set_twitter_token(self):
        """Set Twitter API bearer token"""
        if not self.emergency_enabled:
            self.log("Emergency module not available")
            return
        
        token = self.twitter_token_entry.get().strip()
        if token and SocialMediaEmergencyFetcher:
            try:
                # Get custom handles from entry field
                handles_str = self.twitter_handles_entry.get().strip()
                if handles_str:
                    # Parse comma-separated handles
                    custom_handles = [h.strip() for h in handles_str.split(',') if h.strip()]
                    self.twitter_fetcher = SocialMediaEmergencyFetcher(token, custom_handles)
                    self.log("Twitter API bearer token configured successfully.")
                    self.log(f"Token starts with: {token[:20]}...")
                    self.log(f"Monitoring {len(custom_handles)} Twitter accounts: {', '.join(custom_handles[:5])}{'...' if len(custom_handles) > 5 else ''}")
                else:
                    self.twitter_fetcher = SocialMediaEmergencyFetcher(token)
                    self.log("Twitter API bearer token configured with default accounts.")
                    self.log(f"Token starts with: {token[:20]}...")
                self.status_label.config(text="Twitter API set - Emergency tweets enabled")
            except Exception as e:
                self.log(f"Error setting Twitter token: {e}")
        else:
            self.log("Please enter a valid Twitter bearer token.")
    
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
                else:
                    self.log("Please set Twitter token first")
            except Exception as e:
                self.log(f"Error updating handles: {e}")
        else:
            self.log(f"Twitter handles saved ({len(custom_handles)} accounts). Set token to enable.")
            self.log(f"  Accounts: {', '.join(custom_handles[:8])}{'...' if len(custom_handles) > 8 else ''}")
    
    def select_all_regions(self):
        """Select all weather regions"""
        for i in range(1, 11):
            self.weather_regions[i].set(True)
        self.log("Selected all weather regions")
    
    def select_no_regions(self):
        """Deselect all weather regions"""
        for i in range(1, 11):
            self.weather_regions[i].set(False)
        self.log("Deselected all weather regions")
    
    def select_directory(self):
        """Select save directory"""
        directory = filedialog.askdirectory(initialdir=self.save_directory)
        if directory:
            self.save_directory = directory
            self.dir_label.config(text=directory)
            self.log(f"Save directory changed to: {directory}")
    
    def cleanup_old_files(self):
        """Delete old TXT files - keeps only the newest set"""
        try:
            # Delete all old report files to keep only the newest set
            file_prefixes = ['news_', 'wx_R', 'space_', 'emergency_', 'tweets_']
            files_deleted = 0
            
            for filename in os.listdir(self.save_directory):
                if filename.endswith('.txt'):
                    # Check if it's one of our report files
                    is_report_file = any(filename.startswith(prefix) for prefix in file_prefixes)
                    
                    if is_report_file:
                        filepath = os.path.join(self.save_directory, filename)
                        try:
                            os.remove(filepath)
                            files_deleted += 1
                        except:
                            pass  # File might be in use
            
            if files_deleted > 0:
                self.log(f"✓ Removed {files_deleted} old file(s) - keeping only newest set")
        except Exception as e:
            self.log(f"Warning: Could not clean up old files: {e}")
    
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
            self.log("Fetching weather forecasts...")
            self.status_label.config(text="Fetching weather...")
            
            weather_fetcher = WeatherFetcher()
            forecasts_by_region = weather_fetcher.get_all_forecasts(log_callback=self.log)
            
            if not forecasts_by_region:
                self.log("No weather data available")
                return False
            
            timestamp = datetime.now()
            short_name = timestamp.strftime("%m%d_%H%M")
            
            # Create a TXT file for each selected FEMA region
            txts_created = 0
            total_size = 0
            for region_num in range(1, 11):
                # Check if this region is selected
                if not self.weather_regions[region_num].get():
                    continue  # Skip unselected regions
                
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
                self.log("⚠ No weather regions selected - no files created")
            
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
        if self.generate_twitter_var.get():
            outputs_to_generate.append("Twitter")
        
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
        
        # Generate Twitter feed (separate file)
        if self.generate_twitter_var.get():
            if self.twitter_fetcher:
                self.generate_twitter_pdf()
            else:
                self.log("⚠ Twitter not configured - skipping")
        else:
            self.log("⊘ Skipping Twitter Feed (not selected)")
        
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
        
        self.log(f"Service started. Main reports every {main_interval_hours}h, Twitter every {twitter_interval_hours}h.")
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
            
            while self.twitter_is_running:
                # Generate Twitter PDF immediately on start
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


def main():
    root = tk.Tk()
    app = NewsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
