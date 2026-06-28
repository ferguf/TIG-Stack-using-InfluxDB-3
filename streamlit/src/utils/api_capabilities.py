import requests
import pandas as pd

# Global Configuration
API_URL = "http://fastapi:8000"

# =========================================================
# 1. READ OPERATIONS (GET)
# =========================================================

def get_ref_services() -> pd.DataFrame:
    """Fetch all Master Template services."""
    try:
        resp = requests.get(f"{API_URL}/api/v1/capabilities/reference/services")
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Error fetching ref services: {e}")
        return pd.DataFrame()

def get_location_capabilities(location_id: str) -> dict:
    """Fetch aggregated capabilities for a physical location."""
    try:
        resp = requests.get(f"{API_URL}/api/v1/capabilities/location/{location_id}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching location capabilities: {e}")
        return {}

# =========================================================
# 2. CREATE OPERATIONS (POST)
# =========================================================

def post_ref_service(payload: dict) -> dict:
    """Create a new Master Template service."""
    resp = requests.post(f"{API_URL}/api/v1/capabilities/reference/services", json=payload)
    if resp.status_code != 201:
        raise Exception(f"Backend Error: {resp.text}")
    return resp.json()

def post_hardware_profile(payload: dict) -> dict:
    """Create a new Hardware Profile (Role + Model)."""
    resp = requests.post(f"{API_URL}/api/v1/capabilities/profiles", json=payload)
    if resp.status_code != 201:
        raise Exception(f"Backend Error: {resp.text}")
    return resp.json()

def post_profile_service(profile_id: str, payload: dict) -> dict:
    """Map a service capability to a hardware profile."""
    resp = requests.post(f"{API_URL}/api/v1/capabilities/profiles/{profile_id}/services", json=payload)
    if resp.status_code != 201:
        raise Exception(f"Backend Error: {resp.text}")
    return resp.json()

# =========================================================
# 3. UPDATE & DELETE (Stubs for consistency)
# =========================================================

# Note: You can add these as you expand the backend router endpoints
def delete_ref_service(service_id: str) -> dict:
    """Delete a service from the Master Template."""
    resp = requests.delete(f"{API_URL}/api/v1/capabilities/reference/services/{service_id}")
    resp.raise_for_status()
    return resp.json()