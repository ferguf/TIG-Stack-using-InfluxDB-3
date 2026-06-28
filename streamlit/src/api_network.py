# src/utils/api_network.py
import streamlit as st
import requests
import uuid
from typing import List, Dict, Optional

API_URL = "http://fastapi:8000"
TIMEOUT = 5

def get_devices() -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/devices/", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"API Error (get_devices): {e}")
        return []

def get_ports_by_device_name(device_name: str) -> Optional[Dict]:
    try:
        response = requests.get(
            f"{API_URL}/ports/name/{device_name}",
            headers={'accept': 'application/json'},
            timeout=TIMEOUT
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"API Get Error: {e}")
        return None

def post_device(payload: Dict) -> Optional[Dict]:
    try:
        resp = requests.post(f"{API_URL}/devices/", json=payload, timeout=TIMEOUT)
        return resp.json() if resp.status_code in [200, 201] else None
    except Exception: return None

def post_device_ports(device_id: str, ports_list: List[Dict]) -> bool:
    try:
        resp = requests.post(f"{API_URL}/ports/bulk/{device_id}", json=ports_list, timeout=TIMEOUT)
        return resp.status_code in [200, 201]
    except Exception: return False

def update_device(device_id: str, payload: Dict) -> Optional[Dict]:
    try:
        resp = requests.put(f"{API_URL}/devices/{device_id}", json=payload, timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else None
    except Exception: return None

def get_device_location(device_id: str) -> Optional[Dict]:
    try:
        resp = requests.get(f"{API_URL}/locations/device/{device_id}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else None
    except Exception: return None

def get_site_details(short_name: str) -> Optional[Dict]:
    try:
        resp = requests.get(f"{API_URL}/locations/shortName/{short_name}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else None
    except Exception: return None

def get_devices_by_location(location_code: str) -> Optional[Dict]:
    try:
        resp = requests.get(f"{API_URL}/devices/location/{location_code}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else None
    except Exception: return None

def get_ports_by_device(device_id: str) -> Optional[Dict]:
    try:
        resp = requests.get(f"{API_URL}/ports/device/{device_id}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else None
    except Exception: return None

def get_devices_by_short_name(short_name: str) -> List[Dict]:
    try:
        clean_name = str(short_name).strip().lower()
        resp = requests.get(f"{API_URL}/devices/location/{clean_name}", timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else [data]
        return []
    except Exception as e:
        print(f"API Error (get_devices_by_short_name): {e}")
        return []

def save_device_location(payload: Dict, exists: bool) -> Optional[Dict]:
    try:
        url = f"{API_URL}/locations/device"
        if exists:
            resp = requests.put(f"{url}/{payload['device_id']}", json=payload, timeout=TIMEOUT)
        else:
            resp = requests.post(url, json=payload, timeout=TIMEOUT)
        return resp.json() if resp.status_code in [200, 201] else None
    except Exception: return None

def post_network_link(payload: dict) -> Optional[Dict]:
    try:
        resp = requests.post(f"{API_URL}/networkLinks/", json=payload, timeout=TIMEOUT)
        return resp.json() if resp.status_code in [200, 201] else None
    except Exception as e:
        print(f"API Error (post_network_link): {e}")
        return None

def get_lag_network_links() -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/networkLinks/lag", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"Error fetching LAG links: {e}")
        return []

def update_port(port_id: str, payload: dict) -> Optional[Dict]:
    try:
        response = requests.put(f"{API_URL}/ports/id/{port_id}", json=payload, timeout=TIMEOUT)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"API Error (update_port): {e}")
        return None

def delete_network_link(link_id: str) -> bool:
    try:
        response = requests.delete(f"{API_URL}/networkLinks/{link_id}", timeout=TIMEOUT)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"API Delete Error: {e}")
        return False

def get_network_links_detail_by_device(device_id: str):
    try:
        response = requests.get(f"{API_URL}/networkLinks/detail/device/{device_id}", timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching detailed links: {e}")
        return []