import uuid
import requests
import pandas as pd
from typing import Optional, List, Dict, Union
import streamlit as st

# --- Global Configuration ---
API_URL = "http://fastapi:8000"

# ----------------------------------------------------------------------
# 1. CRUD CUSTOMER SERVICES
# ----------------------------------------------------------------------

def get_customers() -> pd.DataFrame:
    """Fetch all customers from FastAPI and return as DataFrame."""
    try:
        resp = requests.get(f"{API_URL}/customers/summary")
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Error fetching customers: {e}")
        return pd.DataFrame()

def post_customer(customer_name: str, account_id: str) -> dict:
    """Create a new customer via FastAPI."""
    payload = {
        "customer_name": customer_name,
        "account_id": account_id,
    }
    resp = requests.post(f"{API_URL}/customers/", json=payload)
    resp.raise_for_status()
    return resp.json()

def update_customer(customer_id: str, account_id: str, customer_name: str) -> dict:
    """Update a customer via FastAPI."""
    payload = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "account_id": account_id,
    }
    resp = requests.put(f"{API_URL}/customers/{customer_id}", json=payload)
    resp.raise_for_status()
    return resp.json()

def delete_customer(customer_id: str) -> dict:
    """Delete a customer via FastAPI."""
    resp = requests.delete(f"{API_URL}/customers/{customer_id}")
    resp.raise_for_status()
    return resp.json()


# ----------------------------------------------------------------------
# 2. CRUD FABRIC SERVICES
# ----------------------------------------------------------------------

def get_fabric_services(customer_id: str) -> pd.DataFrame:
    """Fetch fabric services for a specific customer."""
    try:
        url = f"{API_URL}/fabric_services/customer/{customer_id}"
        resp = requests.get(url)
        
        if resp.status_code == 404:
            return pd.DataFrame()
            
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            return pd.DataFrame()
            
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Error fetching fabric services: {e}")
        return pd.DataFrame()

def post_fabric_service(payload: dict) -> dict:
    """Create a new fabric service."""
    url = f"{API_URL}/fabric_services/"
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()

def update_fabric_service(service_id: str, payload: dict) -> dict:
    """Update a fabric service via PUT."""
    try:
        url = f"{API_URL}/fabric_services/{service_id}"
        resp = requests.put(url, json=payload)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"Update Service Error: {e.response.text}")
        raise e

def delete_fabric_service(service_id: str) -> bool:
    """Delete a fabric service."""
    url = f"{API_URL}/fabric_services/{service_id}"
    resp = requests.delete(url)
    resp.raise_for_status()
    return True

def get_fabric_service_details(service_id: str) -> dict:
    """
    Fetches the comprehensive topology of a Fabric Service, 
    including nested fabric_connections and fabric_ports.
    """
    import requests
    # Replace API_URL with your actual variable/import if needed
    url = f"{API_URL}/fabric_services/detail/{service_id}" 
    
    try:
        response = requests.get(url, headers={'accept': 'application/json'}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch service details for {service_id}: {e}")
        return {}
# ----------------------------------------------------------------------
# 3. CRUD FABRIC CONNECTIONS
# ----------------------------------------------------------------------


def get_connections_by_service(service_id: str) -> list:
    """Helper for selection components; returns list instead of DataFrame."""
    if not service_id:
        return []
    try:
        response = requests.get(f"{API_URL}/fabric_connections/service/{service_id}")
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else [data]
        return []
    except Exception:
        return []

def get_fabric_connections(service_id: str) -> pd.DataFrame:
    """Fetch connections for a specific service."""
    try:
        url = f"{API_URL}/fabric_connections/service/{service_id}"
        resp = requests.get(url, headers={'accept': 'application/json'})
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Connection Fetch Error: {e}")
        return pd.DataFrame()

def post_fabric_connection(payload: dict) -> dict:
    """Create a new connection."""
    url = f"{API_URL}/fabric_connections/"
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()

def update_fabric_connection(connection_id: str, payload: dict) -> dict:
    """Update a connection via PUT."""
    if not connection_id or connection_id == "None":
        raise ValueError("Invalid Connection ID provided.")
    url = f"{API_URL}/fabric_connections/{connection_id}"
    resp = requests.put(url, json=payload)
    resp.raise_for_status()
    return resp.json()

def delete_fabric_connection(connection_id: str) -> bool:
    """Delete a connection."""
    url = f"{API_URL}/fabric_connections/{connection_id}"
    resp = requests.delete(url)
    resp.raise_for_status()
    return True

# ----------------------------------------------------------------------
# 4. FABRIC PORTS & INVENTORY
# ----------------------------------------------------------------------

def get_ports_by_customer(customer_id: str) -> pd.DataFrame:
    """Fetch ports assigned to a specific customer."""
    try:
        url = f"{API_URL}/ports/customer/{customer_id}"
        resp = requests.get(url, headers={'accept': 'application/json'})
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Error fetching customer ports: {e}")
        return pd.DataFrame()

def get_ports_by_device(device_id: str) -> pd.DataFrame:
    """Fetches all ports for a specific device (inventory lookup)."""
    try:
        resp = requests.get(f"{API_URL}/ports/device/{device_id}")
        resp.raise_for_status()
        return pd.DataFrame(resp.json())
    except Exception as e:
        print(f"Error fetching device ports: {e}")
        return pd.DataFrame()

def get_port_by_id(port_id: str) -> Optional[dict]:
    """Fetch full details for a specific port UUID."""
    try:
        resp = requests.get(f"{API_URL}/ports/port/{port_id}")
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None

def update_port_assignment(port_id: str, payload: dict) -> dict:
    """Updates port metadata (e.g., assigning to customer)."""
    resp = requests.put(f"{API_URL}/ports/id/{port_id}", json=payload)
    resp.raise_for_status()
    return resp.json()

def assign_port_to_customer(port_id: str, customer_id: str) -> bool:
    """Shortcut helper to link a port to a customer."""
    payload = {"customer_id": customer_id} # Fixed typo from 'cusotmer_id'
    resp = requests.put(f"{API_URL}/ports/id/{port_id}", json=payload)
    return resp.status_code == 200

def unassign_port(port_id: str) -> dict:
    """Resets the port to an unassigned, physical, and available state."""
    payload = {
        "customer_id": None,
        "port_type": "Physical",
        "port_service_status": "Available"
    }
    url = f"{API_URL}/ports/id/{port_id}"
    resp = requests.put(url, json=payload, headers={'accept': 'application/json'})
    resp.raise_for_status()
    return resp.json()


# ----------------------------------------------------------------------
# 5. DEVICE & LOCATION SERVICES
# ----------------------------------------------------------------------

def get_all_devices() -> list:
    """Fetches list of network devices (raw JSON)."""
    resp = requests.get(f"{API_URL}/devices")
    resp.raise_for_status()
    return resp.json()

def get_devices() -> pd.DataFrame:
    """Fetches all devices and returns as DataFrame."""
    resp = requests.get(f"{API_URL}/devices/")
    resp.raise_for_status()
    data = resp.json()
    return pd.DataFrame(data if isinstance(data, list) else [data])

def get_devices_by_roles(roles: List[str]) -> list:
    """Fetches devices matching specific roles (e.g., ['VAR', 'ES'])."""
    role_str = ",".join(roles)
    resp = requests.get(f"{API_URL}/devices?roles={role_str}")
    resp.raise_for_status()
    return resp.json()

def get_locations() -> list:
    """Fetch all location records."""
    resp = requests.get(f"{API_URL}/locations/")
    resp.raise_for_status()
    return resp.json()

def post_location(location_data: dict) -> dict:
    """Create a new site location."""
    resp = requests.post(f"{API_URL}/locations/", json=location_data)
    resp.raise_for_status()
    return resp.json()

def get_location_details(short_name: str) -> Optional[Dict]:
    """
    Fetches facility/CLLI information based on the site short name (e.g., 'den1').
    
    Args:
        short_name (str): The shorthand identifier for the location.
        
    Returns:
        Optional[Dict]: The JSON response containing location details, or None if failed.
    """
    try:
        # Clean the input to match API expectations (lowercase, no spaces)
        clean_name = str(short_name).strip().lower()
        
        url = f"{API_URL}/locations/shortName/{clean_name}"
        response = requests.get(url, timeout=5)
        
        # Raise an exception for 4XX or 5XX errors
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        # Log error or handle gracefully in UI
        print(f"Error fetching location for {short_name}: {e}")
        return None