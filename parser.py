"""
Welfare Board - Parser Module
Extracts structured data from welfare check-in text files
"""

import re
from datetime import datetime
from pathlib import Path


class WelfareParser:
    """Parse welfare check-in template files"""
    
    # Field patterns for parsing
    FIELD_PATTERNS = {
        'callsign': r'CALLSIGN:\s*(.+)',
        'name': r'NAME:\s*(.+)',
        'location': r'LOCATION:\s*(.+)',
        'status': r'STATUS:\s*(.+)',
        'power': r'POWER:\s*(.+)',
        'message': r'MESSAGE:\s*(.+)',
    }

    VALID_POWER_STATUSES = ['ON', 'OFF', 'GENERATOR']
    
    def __init__(self):
        """Initialize parser"""
        pass
    
    def parse_file(self, filepath):
        """
        Parse a welfare check-in file
        
        Args:
            filepath: Path to the welfare check-in file
            
        Returns:
            dict: Parsed data with fields:
                - callsign
                - name
                - location
                - status
                - message
                - filename
                - received_time
            None if parsing fails
        """
        try:
            filepath = Path(filepath)
            
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract fields
            parsed_data = {
                'filename': filepath.name,
                'received_time': datetime.now(),
                'file_path': str(filepath)
            }
            
            # Parse each field
            for field_name, pattern in self.FIELD_PATTERNS.items():
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    parsed_data[field_name] = value if value else None
                else:
                    parsed_data[field_name] = None
            
            # Special handling for MESSAGE field (can be multi-line)
            message_match = re.search(r'MESSAGE:\s*(.+?)(?=\n\s*$|\Z)', content, re.IGNORECASE | re.DOTALL)
            if message_match:
                parsed_data['message'] = message_match.group(1).strip()
            
            return parsed_data
            
        except Exception as e:
            print(f"Error parsing file {filepath}: {e}")
            return None
    
    def extract_callsign(self, text):
        """
        Extract callsign from text using various patterns
        
        Args:
            text: Text to search
            
        Returns:
            str: Extracted callsign or None
        """
        # Try explicit CALLSIGN: field first
        match = re.search(r'CALLSIGN:\s*([A-Z0-9]{3,7})', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # Try to find callsign-like patterns
        match = re.search(r'\b([A-Z]{1,2}[0-9][A-Z]{1,3})\b', text)
        if match:
            return match.group(1).upper()
        
        return None
    
    def parse_status(self, status_text):
        """
        Normalize status field
        
        Args:
            status_text: Raw status text
            
        Returns:
            str: Normalized status
        """
        if not status_text:
            return None
        
        status_upper = status_text.upper().strip()
        
        # Map variations to standard statuses
        status_map = {
            'OK': 'SAFE',
            'OKAY': 'SAFE',
            'GOOD': 'SAFE',
            'ALL CLEAR': 'SAFE',
            'SAFE': 'SAFE',
            'NEED HELP': 'NEED ASSISTANCE',
            'HELP': 'NEED ASSISTANCE',
            'EMERGENCY': 'NEED ASSISTANCE',
            'NEED ASSISTANCE': 'NEED ASSISTANCE',
            'ASSISTANCE': 'NEED ASSISTANCE',
            'TRAFFIC': 'TRAFFIC',
            'MESSAGE': 'TRAFFIC',
            'MESSAGES': 'TRAFFIC',
        }
        
        for key, value in status_map.items():
            if key in status_upper:
                return value
        
        return status_text.upper()
    
    def format_for_display(self, parsed_data):
        """
        Format parsed data for display
        
        Args:
            parsed_data: Dictionary of parsed fields
            
        Returns:
            str: Formatted text representation
        """
        if not parsed_data:
            return "Invalid data"
        
        output = []
        output.append("─" * 50)
        output.append(f"CALLSIGN: {parsed_data.get('callsign', 'Unknown')}")
        output.append(f"NAME: {parsed_data.get('name', 'Unknown')}")
        output.append(f"LOCATION: {parsed_data.get('location', 'Unknown')}")
        output.append(f"STATUS: {parsed_data.get('status', 'Unknown')}")
        
        message = parsed_data.get('message', '')
        if message:
            output.append(f"MESSAGE: {message}")
        
        received = parsed_data.get('received_time')
        if received:
            output.append(f"RECEIVED: {received.strftime('%H:%M:%S')}")
        
        output.append("─" * 50)
        
        return '\n'.join(output)


if __name__ == '__main__':
    # Test the parser
    parser = WelfareParser()
    
    # Create test file
    test_content = """CALLSIGN: KD8XXX
NAME: John Smith  
LOCATION: Atlanta, GA
STATUS: SAFE
MESSAGE: All systems operational, power restored at 18:00.
Weather conditions improving.
"""
    
    test_file = Path('test_welfare.txt')
    test_file.write_text(test_content)
    
    # Parse it
    result = parser.parse_file(test_file)
    if result:
        print("Parse successful!")
        print(parser.format_for_display(result))
    else:
        print("Parse failed!")
    
    # Cleanup
    test_file.unlink()
