"""
Welfare Board - Output Generator Module
Generates text, HTML, and CSV output files
"""

from datetime import datetime
from pathlib import Path
import csv


class OutputGenerator:
    """Generate various output formats for welfare board"""
    
    def __init__(self, config=None):
        """
        Initialize output generator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.output_config = self.config.get('output', {})
        self.output_dir = Path(self.config.get('directories', {}).get('output', 'data/output'))
        
    def generate_all(self, window_info, checkins):
        """
        Generate all enabled output formats
        
        Args:
            window_info: Window information dict
            checkins: List of check-ins for this window
            
        Returns:
            dict: Paths to generated files
        """
        generated_files = {}
        
        if self.output_config.get('generate_text', True):
            text_file = self.generate_text(window_info, checkins)
            if text_file:
                generated_files['text'] = text_file
        
        if self.output_config.get('generate_html', True):
            html_file = self.generate_html(window_info, checkins)
            if html_file:
                generated_files['html'] = html_file
        
        if self.output_config.get('generate_csv', True):
            csv_file = self.generate_csv(window_info, checkins)
            if csv_file:
                generated_files['csv'] = csv_file
        
        return generated_files
    
    def generate_text(self, window_info, checkins):
        """
        Generate plain text welfare board - OPTIMIZED FOR PACKET RADIO
        Minimal formatting, maximum information density
        
        Args:
            window_info: Window information
            checkins: List of check-ins
            
        Returns:
            Path: Path to generated file
        """
        try:
            # Create filename
            date_str = window_info['date'].strftime('%Y-%m-%d')
            time_range = window_info['start'].replace(':', '') + '-' + window_info['end'].replace(':', '')
            filename = f"welfare_{date_str}_{time_range}.txt"
            filepath = self.output_dir / filename
            
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate compact content
            lines = []
            
            # Header - compact
            lines.append(f"WELFARE BOARD {date_str} {window_info['start']}-{window_info['end']}")
            lines.append(f"Total:{len(checkins)} Gen:{datetime.now().strftime('%H:%M')}")
            
            # Status summary - one line
            status_counts = {}
            for checkin in checkins:
                status = checkin.get('status', 'UNK')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                # Abbreviate status for compactness
                status_abbrev = {
                    'SAFE': 'OK',
                    'NEED ASSISTANCE': 'NEED',
                    'TRAFFIC': 'TRAF'
                }
                summary_parts = []
                for status, count in sorted(status_counts.items()):
                    abbrev = status_abbrev.get(status, status[:4])
                    summary_parts.append(f"{abbrev}:{count}")
                lines.append(" ".join(summary_parts))
            
            # Power status summary
            power_counts = {}
            for checkin in checkins:
                pwr = checkin.get('power')
                if pwr:
                    pwr = pwr.upper()
                    power_counts[pwr] = power_counts.get(pwr, 0) + 1
            if power_counts:
                pwr_parts = [f"PWR-{k}:{v}" for k, v in sorted(power_counts.items())]
                lines.append(" ".join(pwr_parts))
            
            lines.append("")  # Blank line before check-ins
            
            # Individual check-ins - ultra-compact format with update tracking
            for i, checkin in enumerate(sorted(checkins, key=lambda x: x.get('received_time', datetime.min)), 1):
                # One-line format: #N CALL NAME LOC STAT TIME [UPD]
                callsign = checkin.get('callsign', 'UNK')
                name = checkin.get('name', 'Unknown')
                location = checkin.get('location', 'Unknown')
                status = checkin.get('status', 'Unknown')
                
                # Abbreviate status
                status_abbrev = {
                    'SAFE': 'OK',
                    'NEED ASSISTANCE': 'NEED',
                    'TRAFFIC': 'TRAF'
                }
                status_short = status_abbrev.get(status, status[:4])
                
                received = checkin.get('received_time')
                
                # Format: #N CALL(NAME) LOC [UPD#]
                update_num = checkin.get('update_number', 0)
                update_indicator = f" [UPD{update_num}]" if update_num > 0 else ""
                power = checkin.get('power', '').upper() if checkin.get('power') else None
                power_str = f" PWR:{power}" if power else ""
                lines.append(f"{i}. {callsign}({name}) {location}{power_str}{update_indicator}")

                # Build timestamped history: most recent first
                # Current entry is first
                current_time = received.strftime('%H:%M') if received else '??:??'
                current_status = status_short
                current_message = checkin.get('message', '').strip()

                def render_history_entry(time_str, stat_str, msg_str):
                    """Render one history line with wrapped message."""
                    header = f"   {time_str} {stat_str}"
                    entry_lines = [header]
                    if msg_str:
                        for orig_line in msg_str.splitlines():
                            orig_line = orig_line.strip()
                            if not orig_line:
                                continue
                            while len(orig_line) > 54:
                                entry_lines.append(f"        {orig_line[:54]}")
                                orig_line = orig_line[54:]
                            entry_lines.append(f"        {orig_line}")
                    return entry_lines

                lines.extend(render_history_entry(current_time, current_status, current_message))

                # Then older entries in reverse order (most recent history entry next)
                history = checkin.get('history', [])
                for hist in reversed(history):
                    hist_received = hist.get('received_time')
                    hist_time = hist_received.strftime('%H:%M') if isinstance(hist_received, datetime) else str(hist_received)[:5] if hist_received else '??:??'
                    hist_status_raw = hist.get('status', '')
                    hist_status = status_abbrev.get(hist_status_raw, hist_status_raw[:4]) if hist_status_raw else '??'
                    hist_message = hist.get('message', '').strip()
                    lines.extend(render_history_entry(hist_time, hist_status, hist_message))
            
            lines.append("")  # Blank line at end
            lines.append(f"END {datetime.now().strftime('%H:%M')}")
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return filepath
            
        except Exception as e:
            print(f"Error generating text output: {e}")
            return None
    
    def generate_html(self, window_info, checkins):
        """
        Generate HTML welfare board with auto-refresh
        
        Args:
            window_info: Window information
            checkins: List of check-ins
            
        Returns:
            Path: Path to generated file
        """
        try:
            # Create filename
            filename = "welfare_board.html"
            filepath = self.output_dir / filename
            
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Auto-refresh interval
            refresh_seconds = self.output_config.get('html_auto_refresh', 30)
            
            # Status summary
            status_counts = {}
            for checkin in checkins:
                status = checkin.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Generate HTML
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{refresh_seconds}">
    <title>Amateur Radio Welfare Board</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #00ff00;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #0a0a0a;
            padding: 30px;
            border: 2px solid #00ff00;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
        }}
        h1 {{
            text-align: center;
            color: #00ff00;
            text-transform: uppercase;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .header-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #0f0f0f;
            border: 1px solid #00ff00;
        }}
        .info-item {{
            padding: 10px;
        }}
        .info-label {{
            color: #00aa00;
            font-weight: bold;
        }}
        .status-summary {{
            margin: 20px 0;
            padding: 15px;
            background-color: #0f0f0f;
            border: 1px solid #00ff00;
        }}
        .status-counts {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .status-count {{
            padding: 8px 15px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .status-safe {{
            background-color: #004400;
            color: #00ff00;
        }}
        .status-assistance {{
            background-color: #440000;
            color: #ff0000;
        }}
        .status-traffic {{
            background-color: #444400;
            color: #ffff00;
        }}
        .update-badge {{
            display: inline-block;
            background-color: #0066ff;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .status-change {{
            color: #ffaa00;
            font-style: italic;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .checkin {{
            margin: 20px 0;
            padding: 20px;
            background-color: #0f0f0f;
            border-left: 5px solid #00ff00;
        }}
        .checkin.updated {{
            border-left-color: #0066ff;
        }}
        .checkin-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #004400;
        }}
        .callsign {{
            font-size: 1.3em;
            font-weight: bold;
            color: #00ff00;
        }}
        .received-time {{
            color: #00aa00;
        }}
        .checkin-field {{
            margin: 8px 0;
        }}
        .field-label {{
            color: #00aa00;
            font-weight: bold;
            display: inline-block;
            width: 100px;
        }}
        .status-indicator {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 3px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .message-box {{
            margin-top: 10px;
            padding: 10px;
            background-color: #050505;
            border-left: 3px solid #00aa00;
            font-style: italic;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #00ff00;
            color: #00aa00;
        }}
        @media print {{
            body {{ background-color: white; color: black; }}
            .container {{ background-color: white; border-color: black; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 Amateur Radio Welfare Board 📡</h1>
        
        <div class="header-info">
            <div class="info-item">
                <div class="info-label">Date:</div>
                <div>{window_info['date'].strftime('%A, %B %d, %Y')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Time Window:</div>
                <div>{window_info['name']}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Period:</div>
                <div>{window_info['start']} - {window_info['end']}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Total Check-ins:</div>
                <div>{len(checkins)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Last Updated:</div>
                <div>{datetime.now().strftime('%H:%M:%S')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Auto-Refresh:</div>
                <div>Every {refresh_seconds} seconds</div>
            </div>
        </div>
        
        <div class="status-summary">
            <div class="info-label">Status Summary:</div>
            <div class="status-counts">
"""
            
            for status, count in sorted(status_counts.items()):
                status_class = 'safe' if status == 'SAFE' else ('assistance' if 'ASSISTANCE' in status else 'traffic')
                html += f'                <div class="status-count status-{status_class}">{status}: {count}</div>\n'
            
            html += """            </div>
        </div>
        
        <h2 style="color: #00aa00; margin-top: 30px;">Check-ins:</h2>
"""
            
            # Individual check-ins
            for i, checkin in enumerate(sorted(checkins, key=lambda x: x.get('received_time', datetime.min)), 1):
                status = checkin.get('status', 'Unknown')
                status_class = 'safe' if status == 'SAFE' else ('assistance' if 'ASSISTANCE' in status else 'traffic')
                
                received = checkin.get('received_time')
                received_str = received.strftime('%H:%M:%S') if received else 'Unknown'
                
                # Check if this is an update
                update_num = checkin.get('update_number', 0)
                is_updated = update_num > 0
                update_class = " updated" if is_updated else ""
                update_badge = f'<span class="update-badge">UPDATE #{update_num}</span>' if is_updated else ''
                
                html += f"""        <div class="checkin{update_class}">
            <div class="checkin-header">
                <div>
                    <span style="color: #00aa00;">#{i}</span>
                    <span class="callsign">{checkin.get('callsign', 'Unknown')}</span>
                    {update_badge}
                </div>
                <div class="received-time">{received_str}</div>
            </div>
            
            <div class="checkin-field">
                <span class="field-label">NAME:</span>
                {checkin.get('name', 'Unknown')}
            </div>
            
            <div class="checkin-field">
                <span class="field-label">LOCATION:</span>
                {checkin.get('location', 'Unknown')}
            </div>
            
            <div class="checkin-field">
                <span class="field-label">STATUS:</span>
                <span class="status-indicator status-{status_class}">{status}</span>
"""

                # Show status change if updated
                if is_updated:
                    prev_status = checkin.get('previous_status', '')
                    if prev_status and prev_status != status:
                        html += f"""                <div class="status-change">Previously: {prev_status}</div>
"""

                # Power field
                power = checkin.get('power', '').upper() if checkin.get('power') else None
                if power:
                    power_color = '#ff4444' if power == 'OFF' else ('#ffaa00' if power == 'GENERATOR' else '#00ff00')
                    html += f"""            <div class="checkin-field">
                <span class="field-label">POWER:</span>
                <span style="color:{power_color}; font-weight:bold;">{power}</span>
            </div>
"""

                html += """            </div>
"""

                message = checkin.get('message', '')
                if message:
                    html += f"""            
            <div class="message-box">
                <strong>MESSAGE:</strong><br>
                {message}
            </div>
"""

                html += "        </div>\n"
            
            html += f"""        
        <div class="footer">
            <p>Generated by Amateur Radio Welfare Board System</p>
            <p>This page auto-refreshes every {refresh_seconds} seconds</p>
        </div>
    </div>
</body>
</html>"""
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return filepath
            
        except Exception as e:
            print(f"Error generating HTML output: {e}")
            return None
    
    def generate_csv(self, window_info, checkins):
        """
        Generate CSV export of check-ins
        
        Args:
            window_info: Window information
            checkins: List of check-ins
            
        Returns:
            Path: Path to generated file
        """
        try:
            # Create filename
            date_str = window_info['date'].strftime('%Y-%m-%d')
            time_range = window_info['start'].replace(':', '') + '-' + window_info['end'].replace(':', '')
            filename = f"welfare_{date_str}_{time_range}.csv"
            filepath = self.output_dir / filename
            
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Date', 'Window', 'Callsign', 'Name', 'Location', 'Status',
                             'Power', 'Message', 'Received_Time', 'Update_Number', 'Previous_Status']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for checkin in sorted(checkins, key=lambda x: x.get('received_time', datetime.min)):
                    received = checkin.get('received_time')
                    received_str = received.strftime('%H:%M:%S') if received else ''
                    
                    update_num = checkin.get('update_number', 0)
                    prev_status = checkin.get('previous_status', '') if update_num > 0 else ''
                    
                    writer.writerow({
                        'Date': window_info['date'].strftime('%Y-%m-%d'),
                        'Window': f"{window_info['start']}-{window_info['end']}",
                        'Callsign': checkin.get('callsign', ''),
                        'Name': checkin.get('name', ''),
                        'Location': checkin.get('location', ''),
                        'Status': checkin.get('status', ''),
                        'Power': checkin.get('power', '').upper() if checkin.get('power') else '',
                        'Message': checkin.get('message', ''),
                        'Received_Time': received_str,
                        'Update_Number': update_num,
                        'Previous_Status': prev_status
                    })
            
            return filepath
            
        except Exception as e:
            print(f"Error generating CSV output: {e}")
            return None


if __name__ == '__main__':
    # Test the output generator
    from datetime import datetime, date
    
    config = {
        'output': {
            'generate_text': True,
            'generate_html': True,
            'generate_csv': True,
            'html_auto_refresh': 30
        },
        'directories': {
            'output': 'test_output'
        }
    }
    
    generator = OutputGenerator(config)
    
    # Test data
    window_info = {
        'name': 'Evening Net',
        'start': '19:00',
        'end': '21:00',
        'date': date.today(),
        'key': f"{date.today()}_1900-2100"
    }
    
    checkins = [
        {
            'callsign': 'KD8XXX',
            'name': 'John Smith',
            'location': 'Atlanta, GA',
            'status': 'SAFE',
            'message': 'All systems operational',
            'received_time': datetime.now()
        },
        {
            'callsign': 'W1ABC',
            'name': 'Jane Doe',
            'location': 'Boston, MA',
            'status': 'SAFE',
            'message': 'Everything OK here',
            'received_time': datetime.now()
        }
    ]
    
    # Generate all outputs
    generated = generator.generate_all(window_info, checkins)
    print("Generated files:")
    for format_type, filepath in generated.items():
        print(f"  {format_type}: {filepath}")
