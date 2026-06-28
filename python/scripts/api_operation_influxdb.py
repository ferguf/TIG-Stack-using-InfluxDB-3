"""
File Name: api_operation_influxdb.py
Version: 2.0.0 - REST API Implementation (No gRPC)
"""
import requests
import logging
import pandas as pd
from scripts.db_config import INFLUX_TOKEN, INFLUX_DB

logger = logging.getLogger(__name__)

def _fetch_telemetry_v2(query: str):
    """
    Fetches telemetry data using the InfluxDB 3 REST API.
    Bypasses the 'Ghost 443' gRPC bug.
    """
    # InfluxDB 3 SQL Query Endpoint
    url = "http://influxdb3-core:8181/api/v3/query"
    
    headers = {
        "Authorization": f"Token {INFLUX_TOKEN.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json" 
    }
    
    payload = {
        "query": query,
        "database": INFLUX_DB
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"InfluxDB REST Error ({response.status_code}): {response.text}")
            return []

        # InfluxDB 3 returns a list of JSON objects for queries
        data = response.json()
        
        if not data:
            return []
            
        df = pd.DataFrame(data)
        
        # Format timestamps
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            
        return df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"REST API Query Execution Error: {e}")
        return []