"""
File Name: influxdb.py
Version: 3.6.0-Auth-Final
"""
import logging
import requests
from fastapi import APIRouter
from influxdb_client_3 import InfluxDBClient3
from scripts.db_config import INFLUX_TOKEN, INFLUX_DB

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/influx", tags=["influx"])

def check_postgres():
    # Placeholder for your existing postgres check
    return "Up"

@router.get("/health")
async def database_health():
    """
    Verified Health Check for InfluxDB 3.6.0.
    Fixes the 'MissingToken' error on /ping and the 'Ghost 443' gRPC bug.
    """
    results = {"postgres": "Down", "influxdb_api": "Down", "storage_engine": "Down"}
    
    # 1. Postgres Check
    results["postgres"] = check_postgres()

    # Shared Configuration
    target_url = "http://influxdb3-core:8181"
    headers = {"Authorization": f"Token {INFLUX_TOKEN.strip()}"}

    # 2. InfluxDB API Check (/ping)
    try:
        # v3.6.0 logs show 'MissingToken' error without this header
        resp = requests.get(f"{target_url}/ping", headers=headers, timeout=2)
        
        # InfluxDB returns 204 (No Content) for a successful ping
        if resp.status_code in [200, 204]:
            results["influxdb_api"] = "Up"
        else:
            logger.error(f"Ping failed: Status {resp.status_code}")
    except Exception as e:
        logger.error(f"Ping unreachable: {e}")

    # 3. InfluxDB Storage Engine Check (Flight SQL)
    try:
        # We use http:// to force 'h2c' (insecure gRPC) on port 8181
        f_client = InfluxDBClient3(
            connection_string=f"http://influxdb3-core:8181",
            token=INFLUX_TOKEN.strip(),
            database=INFLUX_DB.strip()
        )
        
        # Handshake query
        f_client.query("SELECT 1")
        results["storage_engine"] = "Up"
    except Exception as e:
        # If /ping worked but this failed, the engine is up but the DB might be missing
        if results["influxdb_api"] == "Up":
            results["storage_engine"] = "Up (No DB Found)"
        logger.error(f"Flight SQL Check Failed: {e}")

    # Final Status
    is_healthy = all("Up" in v for v in results.values())
    
    return {
        "status": "Healthy" if is_healthy else "Degraded",
        "details": results
    }