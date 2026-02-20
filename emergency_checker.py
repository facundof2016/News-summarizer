#!/usr/bin/env python3
"""
Standalone Emergency Information Checker
Quick way to check current emergency conditions
"""

import sys
import os

# Add current directory to path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emergency_module import EmergencyDataFetcher, EmergencyResourcesFetcher
from datetime import datetime
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_alerts(alerts):
    """Print weather alerts"""
    if not alerts:
        print("  No active alerts")
        return
    
    if isinstance(alerts, list) and len(alerts) > 0 and alerts[0].get('error'):
        print(f"  Error: {alerts[0]['error']}")
        return
    
    for alert in alerts[:10]:  # Limit to 10 most recent
        if alert.get('error'):
            print(f"  Error: {alert['error']}")
            continue
            
        severity = alert.get('severity', 'Unknown')
        event = alert.get('event', 'Unknown Event')
        areas = alert.get('areas', 'Unknown Area')
        headline = alert.get('headline', '')
        
        # Color code based on severity
        if severity == 'Extreme':
            prefix = "🔴 EXTREME"
        elif severity == 'Severe':
            prefix = "🟠 SEVERE"
        elif severity == 'Moderate':
            prefix = "🟡 MODERATE"
        else:
            prefix = "ℹ️  INFO"
        
        print(f"\n  {prefix}: {event}")
        print(f"  Area: {areas}")
        if headline:
            print(f"  {headline}")


def print_earthquakes(quakes):
    """Print recent earthquakes"""
    if not quakes:
        print("  No significant earthquakes in past 7 days")
        return
    
    if isinstance(quakes, list) and len(quakes) > 0 and quakes[0].get('error'):
        print(f"  Error: {quakes[0]['error']}")
        return
    
    for quake in quakes[:10]:
        if quake.get('error'):
            print(f"  Error: {quake['error']}")
            continue
            
        mag = quake.get('magnitude', 'Unknown')
        location = quake.get('location', 'Unknown Location')
        time = quake.get('time', 'Unknown Time')
        depth = quake.get('depth', 'Unknown')
        
        print(f"\n  M{mag} - {location}")
        print(f"  Time: {time}")
        print(f"  Depth: {depth} km")


def print_disasters(disasters):
    """Print FEMA disasters"""
    if not disasters:
        print("  No recent disaster declarations")
        return
    
    if isinstance(disasters, list) and len(disasters) > 0 and disasters[0].get('error'):
        print(f"  Error: {disasters[0]['error']}")
        return
    
    for disaster in disasters[:10]:
        if disaster.get('error'):
            print(f"  Error: {disaster['error']}")
            continue
            
        num = disaster.get('disaster_number', 'Unknown')
        state = disaster.get('state', 'Unknown')
        incident = disaster.get('incident_type', 'Unknown')
        title = disaster.get('title', '')
        date = disaster.get('date', 'Unknown')
        
        print(f"\n  {num} - {state}")
        print(f"  Type: {incident}")
        print(f"  {title}")
        print(f"  Date: {date}")


def print_fire_info(fire_data):
    """Print fire information"""
    if fire_data.get('error'):
        print(f"  Error: {fire_data['error']}")
        return
    
    if fire_data.get('active_fires_24h'):
        print(f"\n  Active thermal anomalies: {fire_data['active_fires_24h']}")
        print(f"  {fire_data.get('message', '')}")
        print(f"  Source: {fire_data.get('source', 'Unknown')}")
        print(f"  Note: {fire_data.get('note', '')}")
    else:
        print(f"  {fire_data.get('message', 'No data available')}")


def print_resources(resources):
    """Print emergency resources"""
    contacts = resources.get('emergency_contacts', {})
    
    print("\n  EMERGENCY PHONE NUMBERS:")
    for name, number in contacts.items():
        print(f"    {number}: {contacts[name]}")
    
    print("\n  SUPPLY CHECKLIST (Top 10):")
    for i, item in enumerate(resources.get('supply_checklist', [])[:10], 1):
        print(f"    {i}. {item}")


def main():
    """Main function to run emergency checks"""
    print("\n" + "=" * 70)
    print("  EMERGENCY INFORMATION CHECKER")
    print("  " + datetime.now().strftime("%B %d, %Y at %I:%M %p"))
    print("=" * 70)
    
    # Check if user wants a specific state
    user_state = None
    if len(sys.argv) > 1:
        user_state = sys.argv[1].upper()
        print(f"\n  Filtering for state: {user_state}")
    
    print("\n  Fetching data from emergency sources...")
    print("  (This may take 30-60 seconds)")
    
    # Initialize fetcher
    fetcher = EmergencyDataFetcher()
    
    # Fetch all data
    print("\n  📡 Connecting to data sources...")
    
    try:
        # 1. Weather Alerts
        print_section("🌪️  NATIONAL WEATHER SERVICE ALERTS")
        print("  Fetching NWS alerts...")
        alerts = fetcher.get_nws_alerts(user_state)
        print_alerts(alerts)
        
        # 2. Earthquakes
        print_section("🌍 RECENT EARTHQUAKES (M4.5+ Last 7 Days)")
        print("  Fetching USGS data...")
        quakes = fetcher.get_recent_earthquakes()
        print_earthquakes(quakes)
        
        # 3. FEMA Disasters
        print_section("🏛️  FEMA DISASTER DECLARATIONS (Last 30 Days)")
        print("  Fetching FEMA data...")
        disasters = fetcher.get_fema_disasters()
        print_disasters(disasters)
        
        # 4. Wildfires
        print_section("🔥 ACTIVE FIRE INCIDENTS (Last 24 Hours)")
        print("  Fetching NASA FIRMS data...")
        fires = fetcher.get_active_fires()
        print_fire_info(fires)
        
        # 5. Air Quality
        print_section("💨 AIR QUALITY INFORMATION")
        air_quality = fetcher.get_air_quality_alerts()
        print(f"  {air_quality.get('message', 'No data available')}")
        if air_quality.get('url'):
            print(f"  Check: {air_quality['url']}")
        
        # 6. Power Outages
        print_section("⚡ POWER OUTAGE INFORMATION")
        outages = fetcher.get_power_outage_summary()
        print(f"  {outages.get('message', 'No data available')}")
        if outages.get('resources'):
            for resource in outages['resources']:
                print(f"    • {resource}")
        
        # 7. Emergency Resources
        print_section("📋 EMERGENCY PREPAREDNESS RESOURCES")
        resources = EmergencyResourcesFetcher.get_emergency_resources()
        print_resources(resources)
        
        # Summary
        print_section("✅ DATA FETCH COMPLETE")
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("  All available emergency data retrieved successfully.")
        print("\n  💡 TIP: Run with state code for filtered alerts")
        print("     Example: python emergency_checker.py CA")
        print("     Example: python emergency_checker.py TX")
        print("\n" + "=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Interrupted by user")
        print("=" * 70 + "\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n  ❌ ERROR: {e}")
        print("=" * 70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
