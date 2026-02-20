"""
Welfare Board - Aggregator Module
Groups welfare check-ins by time windows
"""

from datetime import datetime, time, timedelta
from pathlib import Path
import json


class WelfareAggregator:
    """Aggregate welfare check-ins by time window"""
    
    def __init__(self, config=None):
        """
        Initialize aggregator
        
        Args:
            config: Configuration dictionary with time_windows
        """
        self.config = config or {}
        self.time_windows = self.config.get('time_windows', [])
        self.checkins = {}  # {window_key: [checkins]}
        
    def get_current_window(self, check_time=None):
        """
        Determine which time window a check-in belongs to
        
        Args:
            check_time: datetime object (default: now)
            
        Returns:
            dict: Window info or None if no active window
                {
                    'name': 'Evening Net',
                    'start': '19:00',
                    'end': '21:00',
                    'key': '2024-12-16_1900-2100'
                }
        """
        if check_time is None:
            check_time = datetime.now()
        
        current_time = check_time.time()
        current_date = check_time.date()
        
        for window in self.time_windows:
            start_time = datetime.strptime(window['start'], '%H:%M').time()
            end_time = datetime.strptime(window['end'], '%H:%M').time()
            
            # Check if current time falls within window
            if start_time <= current_time <= end_time:
                window_key = self._create_window_key(current_date, window)
                return {
                    'name': window.get('name', f"{window['start']}-{window['end']}"),
                    'start': window['start'],
                    'end': window['end'],
                    'key': window_key,
                    'date': current_date
                }
        
        return None
    
    def _create_window_key(self, date, window):
        """
        Create unique key for a time window
        
        Args:
            date: Date object
            window: Window definition dict
            
        Returns:
            str: Unique key like "2024-12-16_1900-2100"
        """
        start = window['start'].replace(':', '')
        end = window['end'].replace(':', '')
        return f"{date.isoformat()}_{start}-{end}"
    
    def add_checkin(self, parsed_data, check_time=None):
        """
        Add a check-in to the appropriate time window with intelligent duplicate handling
        
        Compares new check-ins against existing ones:
        - If content is identical: Reject as duplicate
        - If content differs: Append as update, preserve history
        
        Args:
            parsed_data: Parsed check-in data
            check_time: When check-in was received (default: now)
            
        Returns:
            tuple: (success, message, window_info)
        """
        if check_time is None:
            check_time = parsed_data.get('received_time', datetime.now())
        
        # Get current window
        window_info = self.get_current_window(check_time)
        
        if not window_info:
            return False, "No active time window for this check-in", None
        
        window_key = window_info['key']
        
        # Initialize window if needed
        if window_key not in self.checkins:
            self.checkins[window_key] = []
        
        # Check for existing check-ins from this callsign
        callsign = parsed_data.get('callsign', '').upper()
        existing_index = None
        existing_checkin = None
        
        for i, existing in enumerate(self.checkins[window_key]):
            if existing.get('callsign', '').upper() == callsign:
                existing_index = i
                existing_checkin = existing
                break
        
        if existing_checkin:
            # Found existing check-in - compare content
            is_duplicate = self._is_content_identical(existing_checkin, parsed_data)
            
            if is_duplicate:
                # Truly duplicate - same content, reject
                return False, f"Duplicate: {callsign} - identical check-in already exists", window_info
            else:
                # Content differs - this is an UPDATE
                # Build a new history entry from the existing check-in's current state
                new_history_entry = {
                    'status': existing_checkin.get('status'),
                    'message': existing_checkin.get('message'),
                    'received_time': existing_checkin.get('received_time')
                }
                # Carry forward the full history chain and append the current state
                existing_history = existing_checkin.get('history', [])
                parsed_data['history'] = existing_history + [new_history_entry]
                parsed_data['update_number'] = existing_checkin.get('update_number', 0) + 1
                parsed_data['first_checkin_time'] = existing_checkin.get('first_checkin_time',
                                                                         existing_checkin.get('received_time'))
                
                # Replace existing check-in with updated version
                self.checkins[window_key][existing_index] = parsed_data
                
                return True, f"Updated {callsign} in {window_info['name']} (update #{parsed_data['update_number']})", window_info
        
        # New check-in (no existing record)
        parsed_data['update_number'] = 0
        parsed_data['first_checkin_time'] = parsed_data.get('received_time', datetime.now())
        self.checkins[window_key].append(parsed_data)
        
        return True, f"Added {callsign} to {window_info['name']}", window_info
    
    def _is_content_identical(self, existing, new):
        """
        Compare two check-ins to determine if content is identical
        
        Compares: NAME, LOCATION, STATUS, MESSAGE
        Ignores: received_time, update_number, history fields
        
        Args:
            existing: Existing check-in dict
            new: New check-in dict
            
        Returns:
            bool: True if content is identical
        """
        # Fields to compare
        compare_fields = ['name', 'location', 'status', 'message']
        
        for field in compare_fields:
            existing_value = existing.get(field, '').strip()
            new_value = new.get(field, '').strip()
            
            # Normalize empty values
            if not existing_value:
                existing_value = ''
            if not new_value:
                new_value = ''
            
            if existing_value != new_value:
                return False  # Content differs
        
        return True  # All fields match - truly duplicate
    
    def get_window_checkins(self, window_key):
        """
        Get all check-ins for a specific window
        
        Args:
            window_key: Window key
            
        Returns:
            list: Check-ins for that window
        """
        return self.checkins.get(window_key, [])
    
    def get_all_windows(self):
        """
        Get all active windows with check-ins
        
        Returns:
            dict: {window_key: checkins}
        """
        return self.checkins
    
    def get_window_count(self, window_key):
        """
        Get count of check-ins for a window
        
        Args:
            window_key: Window key
            
        Returns:
            int: Number of check-ins
        """
        return len(self.checkins.get(window_key, []))
    
    def get_status_counts(self, window_key):
        """
        Get count of each status for a window
        
        Args:
            window_key: Window key
            
        Returns:
            dict: {status: count}
        """
        checkins = self.checkins.get(window_key, [])
        status_counts = {}
        
        for checkin in checkins:
            status = checkin.get('status', 'Unknown').upper()
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return status_counts
    
    def sort_checkins(self, checkins, sort_by='received_time'):
        """
        Sort check-ins by specified field
        
        Args:
            checkins: List of check-ins
            sort_by: Field to sort by (default: received_time)
            
        Returns:
            list: Sorted check-ins
        """
        return sorted(checkins, key=lambda x: x.get(sort_by, datetime.min))
    
    def clear_window(self, window_key):
        """
        Clear all check-ins for a window
        
        Args:
            window_key: Window key to clear
        """
        if window_key in self.checkins:
            del self.checkins[window_key]
    
    def clear_all(self):
        """Clear all check-ins"""
        self.checkins = {}
    
    def save_state(self, filepath):
        """
        Save aggregator state to file
        
        Args:
            filepath: Path to save file
        """
        try:
            state = {}
            for window_key, checkins in self.checkins.items():
                # Convert datetime objects to strings
                serializable_checkins = []
                for checkin in checkins:
                    serializable = checkin.copy()
                    if 'received_time' in serializable and isinstance(serializable['received_time'], datetime):
                        serializable['received_time'] = serializable['received_time'].isoformat()
                    serializable_checkins.append(serializable)
                state[window_key] = serializable_checkins
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def load_state(self, filepath):
        """
        Load aggregator state from file
        
        Args:
            filepath: Path to load from
        """
        try:
            if not Path(filepath).exists():
                return False
            
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # Convert date strings back to datetime objects
            for window_key, checkins in state.items():
                for checkin in checkins:
                    if 'received_time' in checkin and isinstance(checkin['received_time'], str):
                        checkin['received_time'] = datetime.fromisoformat(checkin['received_time'])
                self.checkins[window_key] = checkins
            
            return True
        except Exception as e:
            print(f"Error loading state: {e}")
            return False
    
    def get_summary(self):
        """
        Get summary of all windows
        
        Returns:
            list: Summary information for each window
        """
        summary = []
        
        for window_key, checkins in self.checkins.items():
            # Parse window key to get date and times
            parts = window_key.split('_')
            date_str = parts[0]
            time_range = parts[1] if len(parts) > 1 else 'Unknown'
            
            status_counts = self.get_status_counts(window_key)
            
            summary.append({
                'window_key': window_key,
                'date': date_str,
                'time_range': time_range,
                'total_checkins': len(checkins),
                'status_counts': status_counts,
                'callsigns': [c.get('callsign', 'Unknown') for c in checkins]
            })
        
        return summary


if __name__ == '__main__':
    # Test the aggregator
    config = {
        'time_windows': [
            {'name': 'Morning Net', 'start': '08:00', 'end': '10:00'},
            {'name': 'Evening Net', 'start': '19:00', 'end': '21:00'}
        ]
    }
    
    aggregator = WelfareAggregator(config)
    
    # Simulate check-ins
    test_checkin1 = {
        'callsign': 'KD8XXX',
        'name': 'John Smith',
        'location': 'Atlanta, GA',
        'status': 'SAFE',
        'message': 'All clear',
        'received_time': datetime.now().replace(hour=19, minute=15)
    }
    
    test_checkin2 = {
        'callsign': 'W1ABC',
        'name': 'Jane Doe',
        'location': 'Boston, MA',
        'status': 'SAFE',
        'message': 'Everything OK',
        'received_time': datetime.now().replace(hour=19, minute=30)
    }
    
    # Add check-ins
    success1, msg1, window1 = aggregator.add_checkin(test_checkin1, test_checkin1['received_time'])
    print(f"Check-in 1: {msg1}")
    
    success2, msg2, window2 = aggregator.add_checkin(test_checkin2, test_checkin2['received_time'])
    print(f"Check-in 2: {msg2}")
    
    # Print summary
    print("\nSummary:")
    for window_summary in aggregator.get_summary():
        print(f"  {window_summary['time_range']}: {window_summary['total_checkins']} check-ins")
        print(f"    Callsigns: {', '.join(window_summary['callsigns'])}")
