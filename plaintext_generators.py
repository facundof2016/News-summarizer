# Plain Text Generators for Low-Bandwidth Radio Transmission
# Optimized for ABSOLUTE MINIMUM file size

"""
Plain text generators that create ultra-compact files suitable for 
radio transmission over low-bandwidth links.

File size comparison:
- PDF (compressed): 50 KB
- HTML: 80 KB  
- Plain Text: 5-8 KB (90% smaller!)
"""

from datetime import datetime


class PlainTextGenerator:
    """Generates ultra-compact plain text reports for radio transmission"""
    
    @staticmethod
    def create_news_txt(filename, summary_text, news_data):
        """Create minimal news text file"""
        timestamp = datetime.now().strftime("%m/%d %H:%M")
        
        lines = []
        lines.append(f"NEWS {timestamp}")
        lines.append("=" * 40)
        
        # Summary (compact)
        if summary_text and summary_text.strip():
            lines.append("SUMMARY:")
            lines.append(summary_text.strip())
            lines.append("")
        
        # Headlines by source (very compact)
        for source, headlines in news_data.items():
            lines.append(f"{source}:")
            for i, headline in enumerate(headlines[:10], 1):  # Limit to 10
                lines.append(f"{i}. {headline}")
            lines.append("")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    @staticmethod
    def create_weather_txt(filename, region_number, forecasts, region_desc):
        """Create minimal weather text file"""
        timestamp = datetime.now().strftime("%m/%d %H:%M")
        
        lines = []
        lines.append(f"WX R{region_number} {timestamp}")
        lines.append(region_desc)
        lines.append("=" * 40)
        
        for forecast in forecasts:
            city = forecast['city']
            periods = forecast.get('forecast', [])[:4]  # Only next 2 days (4 periods)
            
            lines.append(city)
            for period in periods:
                name = period.get('name', '')[:3]  # "Today" -> "Tod"
                temp = period.get('temperature', '')
                wx = period.get('shortForecast', '')
                
                # Ultra compact: "Tod 65F Sunny"
                lines.append(f"{name} {temp}F {wx}")
            lines.append("")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    @staticmethod
    def create_space_txt(filename, conditions):
        """Create minimal space weather text file"""
        timestamp = datetime.now().strftime("%m/%d %H:%M")
        
        lines = []
        lines.append(f"SPACE {timestamp}")
        lines.append("=" * 40)
        
        lines.append(f"SFI:{conditions.get('solar_flux', 'N/A')}")
        lines.append(f"SSN:{conditions.get('sunspot_number', 'N/A')}")
        lines.append(f"A:{conditions.get('a_index', 'N/A')}")
        lines.append(f"K:{conditions.get('k_index', 'N/A')}")
        lines.append("")
        
        # Band conditions
        band_conditions = conditions.get('band_conditions', {})
        if band_conditions:
            lines.append("BANDS:")
            for band, cond in band_conditions.items():
                lines.append(f"{band}: {cond}")
        else:
            lines.append("BANDS: No data available")
        
        # Add forecast if available
        forecast = conditions.get('forecast', '')
        if forecast:
            lines.append("")
            lines.append("FORECAST:")
            
            # Process all forecast lines (no limit - we want the complete forecast!)
            forecast_lines = forecast.split('\n')
            
            for line in forecast_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Word wrap long lines at ~75 characters
                if len(line) <= 75:
                    lines.append(line)
                else:
                    # Word wrap the line
                    words = line.split()
                    current_line = ""
                    
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 75:
                            current_line += (word + " ")
                        else:
                            if current_line:
                                lines.append(current_line.rstrip())
                            current_line = word + " "
                    
                    if current_line:
                        lines.append(current_line.rstrip())
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    @staticmethod
    def create_emergency_txt(filename, emergency_data):
        """Create minimal emergency text file"""
        timestamp = emergency_data.get('timestamp', datetime.now().strftime("%m/%d %H:%M"))
        
        lines = []
        lines.append(f"EMRG {timestamp}")
        lines.append("=" * 40)
        
        # NWS Alerts (show complete information)
        alerts = emergency_data.get('nws_alerts', [])
        if alerts and not (isinstance(alerts, list) and len(alerts) > 0 and alerts[0].get('error')):
            lines.append("ALERTS:")
            alert_count = 0
            for alert in alerts[:15]:  # Show up to 15 alerts (increased from 10)
                event = alert.get('event', 'Unknown Event')
                areas = alert.get('areas', 'Unknown Area')
                severity = alert.get('severity', '')
                headline = alert.get('headline', '')
                description = alert.get('description', '')
                effective = alert.get('effective', '')
                expires = alert.get('expires', '')
                
                # Mark critical alerts with !
                severity_marker = "!" if severity in ['Extreme', 'Severe'] else " "
                
                # Format: [!] Event - Areas
                alert_header = f"{severity_marker} {event} - {areas}"
                
                # Word wrap the header if needed
                if len(alert_header) <= 75:
                    lines.append(alert_header)
                else:
                    # Word wrap long alert headers
                    words = alert_header.split()
                    current_line = ""
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 75:
                            current_line += (word + " ")
                        else:
                            if current_line:
                                lines.append(current_line.rstrip())
                            current_line = "  " + word + " "  # Indent continuation
                    if current_line:
                        lines.append(current_line.rstrip())
                
                # Add timing if available
                if effective or expires:
                    timing_parts = []
                    if effective:
                        # Extract just the date/time, not full ISO format
                        try:
                            eff_time = effective.split('T')[1][:5] if 'T' in effective else effective
                            eff_date = effective.split('T')[0] if 'T' in effective else ''
                            timing_parts.append(f"From {eff_date} {eff_time}")
                        except:
                            timing_parts.append(f"From {effective}")
                    if expires:
                        try:
                            exp_time = expires.split('T')[1][:5] if 'T' in expires else expires
                            exp_date = expires.split('T')[0] if 'T' in expires else ''
                            timing_parts.append(f"Until {exp_date} {exp_time}")
                        except:
                            timing_parts.append(f"Until {expires}")
                    
                    if timing_parts:
                        timing_line = "  " + " ".join(timing_parts)
                        lines.append(timing_line)
                
                # Add headline if available (provides critical details)
                if headline and headline != event:
                    # Indent and word wrap the headline
                    headline_words = headline.split()
                    current_line = "  "
                    for word in headline_words:
                        if len(current_line) + len(word) + 1 <= 75:
                            current_line += (word + " ")
                        else:
                            if len(current_line.strip()) > 0:
                                lines.append(current_line.rstrip())
                            current_line = "  " + word + " "
                    if len(current_line.strip()) > 0:
                        lines.append(current_line.rstrip())
                
                # Add description (the actual alert text - important for Special Weather Statements!)
                if description:
                    # Clean up the description - remove excessive whitespace
                    description = ' '.join(description.split())
                    
                    # Word wrap the description
                    desc_words = description.split()
                    current_line = "  "
                    line_count = 0
                    max_desc_lines = 8  # Limit description to 8 lines to keep file size reasonable
                    
                    for word in desc_words:
                        if line_count >= max_desc_lines:
                            lines.append("  [...]")
                            break
                        
                        if len(current_line) + len(word) + 1 <= 75:
                            current_line += (word + " ")
                        else:
                            if len(current_line.strip()) > 0:
                                lines.append(current_line.rstrip())
                                line_count += 1
                            current_line = "  " + word + " "
                    
                    if len(current_line.strip()) > 0 and line_count < max_desc_lines:
                        lines.append(current_line.rstrip())
                
                lines.append("")  # Blank line between alerts
                alert_count += 1
            
            if alert_count == 0:
                lines.append("  None active")
        
        # Earthquakes (show complete information)
        quakes = emergency_data.get('usgs_earthquakes', [])
        if quakes and not (isinstance(quakes, list) and len(quakes) > 0 and quakes[0].get('error')):
            lines.append("")
            lines.append("QUAKES:")
            for quake in quakes[:10]:  # Show up to 10 (increased from 5)
                if not quake.get('error'):
                    mag = quake.get('magnitude', '')
                    loc = quake.get('location', '')
                    time = quake.get('time', '')
                    depth = quake.get('depth', '')
                    
                    # Format: M6.2 Location (Time, Depth)
                    quake_line = f"M{mag} {loc}"
                    if time or depth:
                        details = []
                        if time:
                            details.append(time)
                        if depth:
                            details.append(f"{depth}km")
                        quake_line += f" ({', '.join(details)})"
                    
                    # Word wrap if needed
                    if len(quake_line) <= 75:
                        lines.append(quake_line)
                    else:
                        words = quake_line.split()
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) + 1 <= 75:
                                current_line += (word + " ")
                            else:
                                if current_line:
                                    lines.append(current_line.rstrip())
                                current_line = "  " + word + " "  # Indent continuation
                        if current_line:
                            lines.append(current_line.rstrip())
        
        # FEMA Disasters (show complete information)
        disasters = emergency_data.get('fema_disasters', [])
        if disasters and not (isinstance(disasters, list) and len(disasters) > 0 and disasters[0].get('error')):
            lines.append("")
            lines.append("FEMA:")
            for disaster in disasters[:5]:  # Show up to 5
                if not disaster.get('error'):
                    num = disaster.get('disaster_number', '')
                    state = disaster.get('state', '')
                    inc = disaster.get('incident_type', '')
                    title = disaster.get('title', '')
                    date = disaster.get('date', '')
                    
                    # Format: DR-1234 ST Type: Title (Date)
                    disaster_line = f"{num} {state} {inc}"
                    if title:
                        disaster_line += f": {title}"
                    if date:
                        disaster_line += f" ({date})"
                    
                    # Word wrap if needed
                    if len(disaster_line) <= 75:
                        lines.append(disaster_line)
                    else:
                        words = disaster_line.split()
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) + 1 <= 75:
                                current_line += (word + " ")
                            else:
                                if current_line:
                                    lines.append(current_line.rstrip())
                                current_line = "  " + word + " "  # Indent continuation
                        if current_line:
                            lines.append(current_line.rstrip())
        
        # Fires (compact)
        fires = emergency_data.get('fire_incidents', {})
        if fires.get('active_fires_24h'):
            lines.append("")
            lines.append(f"FIRES: {fires['active_fires_24h']} active")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    @staticmethod
    def create_tweets_txt(filename, tweets):
        """Create minimal tweets text file"""
        timestamp = datetime.now().strftime("%m/%d %H:%M")
        
        lines = []
        lines.append(f"TWEETS {timestamp}")
        lines.append("=" * 40)
        
        if isinstance(tweets, dict) and tweets.get('error'):
            lines.append(f"ERR: {tweets.get('error', 'Unknown')}")
            if tweets.get('details'):
                lines.append("")
                lines.append("Details:")
                for detail in tweets.get('details', [])[:3]:
                    lines.append(f"  {detail}")
        elif isinstance(tweets, dict) and tweets.get('message'):
            lines.append(tweets.get('message', 'No tweets available'))
        elif isinstance(tweets, list) and len(tweets) > 0:
            lines.append(f"Total: {len(tweets)} tweets")
            lines.append("")
            for tweet in tweets[:20]:  # Show up to 20 tweets
                acct = tweet.get('account', 'Unknown')
                text = tweet.get('text', '')
                
                # Show full tweet text - no truncation
                # Word wrap at ~75 chars for readability
                lines.append(f"@{acct}:")
                
                if len(text) > 75:
                    # Word wrap at ~75 chars
                    words = text.split()
                    current_line = "  "  # Start with indent
                    
                    for word in words:
                        # Handle very long words (URLs, hashtags, etc.)
                        if len(word) > 70:
                            # If we have content, flush it first
                            if len(current_line.strip()) > 0:
                                lines.append(current_line.rstrip())
                            # Put long word on its own line
                            lines.append(f"  {word}")
                            current_line = "  "
                        elif len(current_line) + len(word) + 1 <= 75:
                            current_line += (word + " ")
                        else:
                            # Line is full, flush it
                            if len(current_line.strip()) > 0:
                                lines.append(current_line.rstrip())
                            current_line = "  " + word + " "
                    
                    # Flush any remaining text
                    if len(current_line.strip()) > 0:
                        lines.append(current_line.rstrip())
                else:
                    # Short tweet - single line
                    lines.append(f"  {text}")
                
                lines.append("")  # Blank line after tweet
        else:
            lines.append("No tweets available")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


# Size estimation for radio transmission:
#
# News:      5-8 KB  (was 50 KB PDF) - 90% smaller
# Weather:   2-4 KB per region (was 60 KB PDF) - 93% smaller  
# Space:     0.5-1 KB (was 30 KB PDF) - 97% smaller
# Emergency: 2-3 KB (was 40 KB PDF) - 93% smaller
# Tweets:    2-4 KB (was 25 KB PDF) - 90% smaller
#
# TOTAL per set: ~20-30 KB (was 635 KB PDF)
# COMPRESSION RATIO: 95% smaller!
#
# For radio transmission at 1200 baud (typical packet radio):
# - PDF set (635 KB): ~70 minutes transmission time
# - TXT set (25 KB): ~3 minutes transmission time
# 
# 23x faster transmission!
