"""File Name: 'port_utils.py' and version '1.0.7' date: 'November 27, 2025 1:36 PM MST' """
import re
from psycopg2 import Error

def extract_speed_in_mbps(speed_str: str) -> int:
    """Converts a network speed string (e.g., '10G', '100M') to Mbps."""
    if not speed_str:
        return 0
    
    match = re.match(r'(\d+)([GM])', speed_str.upper())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'G':
            return value * 1000
        elif unit == 'M':
            return value
    return 0

def format_mbps_to_network_speed(mbps: int) -> str:
    """Converts speed in Mbps back to a human-readable string (e.g., '10000' -> '10G')."""
    if mbps >= 1000 and mbps % 1000 == 0:
        return f"{mbps // 1000}G"
    return f"{mbps}M"

def is_lag_name_unique(cur, device_id: str, lag_name: str) -> bool:
    """Checks if a given LAG name already exists on the device."""
    query = "SELECT port_id FROM ports WHERE device_id = %s AND port_name = %s;"
    try:
        cur.execute(query, (device_id, lag_name))
        return cur.fetchone() is None
    except Error as e:
        print(f"Error checking LAG name uniqueness: {e}")
        return False