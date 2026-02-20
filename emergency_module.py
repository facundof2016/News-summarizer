"""
Emergency Information Module
Fetches critical emergency data for local/regional awareness
"""

import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json


class EmergencyDataFetcher:
    """Fetches emergency and alert information from multiple sources"""
    
    def __init__(self):
        self.user_agent = {'User-Agent': '(EmergencyApp, contact@example.com)'}
    
    def get_all_emergency_data(self, user_state=None):
        """Fetch all emergency-related data"""
        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'nws_alerts': self.get_nws_alerts(user_state),
            'usgs_earthquakes': self.get_recent_earthquakes(),
            'fema_disasters': self.get_fema_disasters(),
            'fire_incidents': self.get_active_fires()
        }
        return data
    
    def get_nws_alerts(self, state=None):
        """Get National Weather Service active alerts"""
        try:
            if state:
                url = f"https://api.weather.gov/alerts/active?area={state}"
            else:
                url = "https://api.weather.gov/alerts/active"
            
            response = requests.get(url, headers=self.user_agent, timeout=10)
            if response.status_code == 200:
                data = response.json()
                alerts = []
                for feature in data.get('features', [])[:20]:  # Limit to 20
                    props = feature.get('properties', {})
                    alerts.append({
                        'event': props.get('event'),
                        'severity': props.get('severity'),
                        'urgency': props.get('urgency'),
                        'areas': props.get('areaDesc'),
                        'headline': props.get('headline'),
                        'description': props.get('description', '')[:1500],  # Increased from 500 to 1500
                        'effective': props.get('effective'),
                        'expires': props.get('expires')
                    })
                return alerts
            return []
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_recent_earthquakes(self):
        """Get recent significant earthquakes from USGS"""
        try:
            # Earthquakes M4.5+ in last 7 days
            url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                quakes = []
                for feature in data.get('features', [])[:15]:
                    props = feature.get('properties', {})
                    coords = feature.get('geometry', {}).get('coordinates', [])
                    quakes.append({
                        'magnitude': props.get('mag'),
                        'location': props.get('place'),
                        'time': datetime.fromtimestamp(props.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M UTC'),
                        'depth': coords[2] if len(coords) > 2 else None,
                        'url': props.get('url')
                    })
                return quakes
            return []
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_cdc_info(self):
        """Get CDC outbreak and health alert information"""
        # Note: CDC doesn't have a simple public API, so we get general status
        try:
            info = {
                'message': 'Check CDC.gov for latest outbreak information',
                'resources': [
                    'Outbreak updates: https://www.cdc.gov/outbreaks/',
                    'Travel health: https://wwwnc.cdc.gov/travel/notices',
                    'Emergency preparedness: https://emergency.cdc.gov/'
                ]
            }
            return info
        except Exception as e:
            return {'error': str(e)}
    
    def get_fema_disasters(self):
        """Get FEMA disaster declarations"""
        try:
            url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
            params = {
                '$filter': f"declarationDate ge '{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}'",
                '$orderby': 'declarationDate desc',
                '$top': '20'
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                disasters = []
                for item in data.get('DisasterDeclarationsSummaries', []):
                    disasters.append({
                        'disaster_number': item.get('disasterNumber'),
                        'state': item.get('state'),
                        'declaration_type': item.get('declarationType'),
                        'incident_type': item.get('incidentType'),
                        'title': item.get('declarationTitle'),
                        'date': item.get('declarationDate'),
                        'incident_begin': item.get('incidentBeginDate')
                    })
                return disasters
            return []
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_air_quality_alerts(self):
        """Get air quality alerts from AirNow"""
        try:
            # This would need AirNow API key for full functionality
            # Returning placeholder for now
            return {
                'message': 'Check AirNow.gov for current air quality in your area',
                'url': 'https://www.airnow.gov/',
                'note': 'Air quality data available with API key'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_active_fires(self):
        """Get active wildfire information"""
        try:
            # NASA FIRMS provides fire data
            url = "https://firms.modaps.eosdis.nasa.gov/api/country/csv/MODIS_NRT/USA/1"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                lines = response.text.split('\n')
                if len(lines) > 1:
                    fire_count = len(lines) - 2  # Minus header and empty line
                    return {
                        'active_fires_24h': fire_count,
                        'message': f'{fire_count} thermal anomalies detected in last 24 hours',
                        'source': 'NASA FIRMS',
                        'note': 'Includes wildfires and other heat sources',
                        'url': 'https://firms.modaps.eosdis.nasa.gov/map/'
                    }
            return {'message': 'No data available'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_power_outage_summary(self):
        """Get power outage summary information"""
        # Note: No single national API, individual utilities have their own
        return {
            'message': 'Check local utility websites for outage information',
            'resources': [
                'PowerOutage.us - National map',
                'Your local utility website',
                'FEMA emergency updates'
            ],
            'note': 'Real-time outage data requires utility-specific APIs'
        }
    
    def get_eas_messages(self):
        """Get Emergency Alert System messages"""
        # EAS messages are typically broadcast-only
        # IPAWS (Integrated Public Alert & Warning System) info
        return {
            'message': 'EAS alerts delivered via broadcast and wireless',
            'resources': [
                'FEMA IPAWS: https://www.fema.gov/emergency-managers/practitioners/integrated-public-alert-warning-system',
                'Enable Wireless Emergency Alerts on your phone',
                'Monitor NOAA Weather Radio'
            ],
            'note': 'Check local emergency management websites for current alerts'
        }


class SocialMediaEmergencyFetcher:
    """
    Fetches emergency information from social media
    Note: Twitter API requires authentication and has rate limits
    """
    
    def __init__(self, twitter_bearer_token=None, custom_accounts=None):
        self.twitter_token = twitter_bearer_token
        
        # Use custom accounts if provided, otherwise use defaults
        if custom_accounts and isinstance(custom_accounts, list) and len(custom_accounts) > 0:
            self.emergency_accounts = custom_accounts
        else:
            # Default emergency accounts
            self.emergency_accounts = [
                'NWS',           # National Weather Service
                'fema',          # FEMA
                'USGS_Quakes',   # USGS Earthquakes
                'NWSAlerts',     # NWS Alerts
                'CDCgov',        # CDC
                'NHC_Atlantic',  # National Hurricane Center
                'USGSBigQuakes', # USGS Big Earthquakes
                'FBI',           # FBI
                'DHSgov',        # Dept of Homeland Security
                'EPA',           # EPA
                'USCG',          # Coast Guard
                'USNationalGuard', # National Guard
            ]
    
    def get_emergency_tweets(self):
        """
        Get recent tweets from emergency agencies
        Requires Twitter API v2 bearer token
        """
        if not self.twitter_token:
            return {
                'error': 'Twitter API token not configured',
                'message': 'To enable Twitter feeds, add a Twitter API bearer token',
                'instructions': [
                    '1. Sign up for Twitter API at https://developer.twitter.com/',
                    '2. Create a project and get bearer token',
                    '3. Add token to the app configuration',
                    '4. Free tier allows 500,000 tweets/month'
                ],
                'alternative': 'Check these accounts directly on Twitter/X'
            }
        
        try:
            headers = {
                'Authorization': f'Bearer {self.twitter_token}',
                'User-Agent': 'EmergencyNewsApp/1.0'
            }
            tweets = []
            errors = []
            
            # Get tweets from each account
            for account in self.emergency_accounts:
                try:
                    url = f"https://api.twitter.com/2/tweets/search/recent"
                    params = {
                        'query': f'from:{account}',
                        'max_results': 10,
                        'tweet.fields': 'created_at,text,author_id',
                        'expansions': 'referenced_tweets.id',
                        'max_results': 10
                    }
                    
                    response = requests.get(url, headers=headers, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        tweet_count = 0
                        for tweet in data.get('data', []):
                            # Get full text - Twitter API v2 should give us complete text
                            tweet_text = tweet.get('text', '')
                            
                            # Debug logging to check for truncation
                            if len(tweet_text) > 0:
                                tweet_count += 1
                                # Check if tweet appears truncated (ends with ellipsis or is suspiciously short)
                                is_truncated = tweet_text.endswith('…') or tweet_text.endswith('...')
                                if is_truncated:
                                    print(f"DEBUG: Tweet from @{account} may be truncated (ends with ellipsis): {len(tweet_text)} chars")
                            
                            # Note: If text ends with '…' or is exactly 280 chars, 
                            # it might be truncated, but API v2 should handle this
                            tweets.append({
                                'account': account,
                                'text': tweet_text,
                                'created_at': tweet.get('created_at', ''),
                            })
                        
                        if tweet_count > 0:
                            print(f"DEBUG: Fetched {tweet_count} tweets from @{account}, avg length: {sum(len(t['text']) for t in tweets[-tweet_count:]) // tweet_count if tweet_count > 0 else 0} chars")
                    elif response.status_code == 401:
                        errors.append(f"Authentication failed - check token")
                        break  # Don't continue if auth fails
                    elif response.status_code == 429:
                        errors.append(f"Rate limit exceeded")
                        break
                    else:
                        errors.append(f"{account}: HTTP {response.status_code}")
                    
                    # Small delay to avoid rate limits
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    errors.append(f"{account}: {str(e)}")
                    continue
            
            if tweets:
                return tweets
            elif errors:
                return {
                    'error': 'Failed to retrieve tweets',
                    'details': errors,
                    'message': 'Check token and rate limits at developer.twitter.com'
                }
            else:
                return {
                    'message': 'No recent tweets from emergency accounts',
                    'note': 'Accounts may not have posted in last 7 days'
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Twitter API error - check token and connection'
            }


class EmergencyResourcesFetcher:
    """Provides emergency preparedness resources and checklists"""
    
    @staticmethod
    def get_emergency_resources():
        """Get emergency preparedness information"""
        return {
            'emergency_contacts': {
                '911': 'Fire, Medical, Police Emergency',
                '311': 'Non-emergency city services',
                'poison_control': '1-800-222-1222',
                'disaster_distress': '1-800-985-5990',
                'red_cross': '1-800-RED-CROSS (1-800-733-2767)'
            },
            'supply_checklist': [
                'Water (1 gallon per person per day for 3 days)',
                'Non-perishable food (3-day supply)',
                'Battery or hand-crank radio',
                'Flashlight and extra batteries',
                'First aid kit',
                'Whistle for signaling',
                'Dust masks or N95 respirators',
                'Plastic sheeting and duct tape',
                'Moist towelettes and garbage bags',
                'Wrench or pliers (to turn off utilities)',
                'Manual can opener',
                'Local maps',
                'Cell phone with chargers and backup battery'
            ],
            'important_documents': [
                'Insurance policies',
                'Identification documents',
                'Bank account records',
                'Credit card account numbers',
                'Medical information',
                'Copies stored in waterproof container'
            ],
            'family_plan': [
                'Establish meeting places',
                'Out-of-area emergency contact',
                'Evacuation routes',
                'Pet care plan',
                'Special needs considerations'
            ]
        }


# Example usage and data priorities
EMERGENCY_INFO_PRIORITIES = {
    'critical': [
        'NWS severe weather alerts',
        'FEMA disaster declarations',
        'USGS significant earthquakes (M5.0+)',
        'Active fire incidents',
        'Air quality emergencies (AQI > 200)'
    ],
    'important': [
        'Power outage information',
        'CDC outbreak notices',
        'All NWS alerts',
        'Earthquakes M4.0+',
        'Emergency agency social media'
    ],
    'awareness': [
        'Space weather impacts',
        'HF radio conditions',
        'General preparedness',
        'Resource availability',
        'Weather forecasts'
    ]
}
