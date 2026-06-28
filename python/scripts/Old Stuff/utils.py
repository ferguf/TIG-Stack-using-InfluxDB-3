"""File Name: 'utils.py' and version'1.0.3' date: 'November 27, 2025 1:21 PM MST' """
import re
from typing import Any

def get_next_lag_index(cur: Any, device_id: int) -> int:
    """Finds the highest existing integer index (XX) from port_names starting with 'ae' for a device."""
    query = """
        SELECT MAX(CAST(substring(port_name from 3) AS INTEGER))
        FROM ports 
        WHERE device_id = %s AND port_name ~ 'ae\d+';
    """
    cur.execute(query, (device_id,))
    max_index = cur.fetchone()[0]
                
    return (max_index if max_index is not None else -1) + 1

def is_lag_name_unique(cur: Any, device_id: int, lag_name: str) -> bool:
    """Checks if a given port_name already exists for the device."""
    query = "SELECT 1 FROM ports WHERE device_id = %s AND port_name = %s;"
    cur.execute(query, (device_id, lag_name))
    return cur.fetchone() is None

def extract_speed_in_mbps(speed_str: str) -> int:
    """Converts speed strings (e.g., '10G', '1G', '100M') to Mbps for calculation."""
    speed_str = speed_str.strip().upper()
    match = re.match(r'(\d+)([GMK])', speed_str)
    if not match:
        return 0
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == 'G':
        return value * 1000  # GB to MB
    elif unit == 'M':
        return value         # MB is already MB
    elif unit == 'K':
        return value // 1000 # KB to MB (or just 0 for practical network speeds)
    return 0
    
def format_mbps_to_network_speed(mbps: int) -> str:
    """Converts total Mbps back to a common network speed format (e.g., 1000M -> 1G)."""
    if mbps >= 1000:
        if mbps % 1000 == 0:
            return f"{mbps // 1000}G"
        else:
            return f"{mbps / 1000:.1f}G"
    return f"{mbps}M"