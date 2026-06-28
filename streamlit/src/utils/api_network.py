
import logging
logger = logging.getLogger(__name__)
import uuid
import requests
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
# Add this near the top of src/utils/api_network.py
from src.utils.file_utils import MessageHandler

API_URL = "http://fastapi:8000"

def get_devices() -> List[Dict]:
    """GET /devices/ - Fetches list of all hardware."""
    url = f"{API_URL}/devices/"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            MessageHandler.add(f"✅ Retrieved {len(data)} devices", "success", category="API")
            return data
        MessageHandler.add(f"⚠️ Failed to fetch devices: HTTP {resp.status_code}", "warning", category="API")
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Exception (get_devices): {str(e)}", "error", category="API")
        return []

def get_device_by_name(device_name: str):
    """GET /devices/{device_name}"""
    url = f"{API_URL}/devices/name/{device_name}"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        response = requests.get(url, headers={'accept': 'application/json'}, timeout=5)
        if response.status_code == 200:
            MessageHandler.add(f"✅ Device {device_name} metadata retrieved", "success", category="API")
            return response.json()
        MessageHandler.add(f"⚠️ Device {device_name} not found (HTTP {response.status_code})", "warning", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ API Error fetching device {device_name}: {e}", "error", category="API")
        return None
    
def get_device_by_id(device_id: str):
    """GET /devices/{device_id}"""
    url = f"{API_URL}/devices/{device_id}"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        response = requests.get(url, headers={'accept': 'application/json'}, timeout=5)
        if response.status_code == 200:
            MessageHandler.add(f"✅ Device {device_id} metadata retrieved", "success", category="API")
            return response.json()
        MessageHandler.add(f"⚠️ Device {device_id} not found (HTTP {response.status_code})", "warning", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ API Error fetching device {device_id}: {e}", "error", category="API")
        return None

def post_device(payload: dict):
    """POST /devices/ - Creates a new device shell."""
    url = f"{API_URL}/devices/"
    MessageHandler.add(f"📡 API REQ: POST {url} | Payload: {payload}", "info", category="API")
    try:
        response = requests.post(
            url,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            json=payload,
            timeout=5
        )
        if response.status_code in [200, 201]:
            data = response.json()
            MessageHandler.add(f"✅ Device Created: {data.get('device_name')} (ID: {data.get('device_id')})", "success", category="API")
            return data
        
        err_msg = f"HTTP {response.status_code} - {response.text}"
        MessageHandler.add(f"❌ Device Creation Failed: {err_msg}", "error", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ Network Error during creation: {e}", "error", category="API")
        return None

def update_device(device_id: str, payload: dict):
    """PUT /devices/{device_id}"""
    url = f"{API_URL}/devices/{device_id}"
    MessageHandler.add(f"📡 API REQ: PUT {url} | Payload: {payload}", "info", category="API")
    try:
        payload["device_id"] = device_id
        response = requests.put(
            url,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            MessageHandler.add(f"✅ Device {device_id} updated successfully", "success", category="API")
            return True
        MessageHandler.add(f"❌ Update Failed for {device_id}: HTTP {response.status_code}", "error", category="API")
        return False
    except Exception as e:
        MessageHandler.add(f"❌ API Update Error: {e}", "error", category="API")
        return False

def delete_device(device_id: str):
    """DELETE /devices/{device_id}"""
    url = f"{API_URL}/devices/{device_id}"
    MessageHandler.add(f"📡 API REQ: DELETE {url}", "info", category="API")
    try:
        response = requests.delete(url, headers={'accept': 'application/json'}, timeout=5)
        success = response.status_code in [200, 204]
        if success:
            MessageHandler.add(f"🗑️ Device {device_id} deleted successfully", "success", category="API")
        else:
            MessageHandler.add(f"❌ Delete Failed for {device_id}: HTTP {response.status_code}", "error", category="API")
        return success
    except Exception as e:
        MessageHandler.add(f"❌ API Delete Error: {e}", "error", category="API")
        return False

def get_port_by_device_name(device_name: str, port_name: str):
    """GET /ports/device/{device_name}/port/{port_name}"""
    url = f"{API_URL}/ports/device/{device_name}/port/{port_name}"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        response = requests.get(url, headers={'accept': 'application/json'}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            MessageHandler.add(f"✅ Active Port Found: {port_name} (ID: {data.get('port_id')})", "success", category="API")
            return data
        
        MessageHandler.add(f"⚠️ Active Port Not Found: {device_name}/{port_name} (HTTP {response.status_code})", "warning", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ API Port Lookup Error: {e}", "error", category="API")
        return None
  
def post_device_ports(device_id: str, ports_list: List[Dict]) -> bool:
    try:
        resp = requests.post(f"{API_URL}/ports/bulk/{device_id}", json=ports_list)
        return resp.status_code in [200, 201]
    except: return False
    
def post_device_port(port_intent: dict, status_override: str = "Active") -> dict:
    """
    Finalized Step 2 Orchestrator (Standalone Version).
    Strictly maps the provided UI intent object to the Galileo API Model.
    POSTs to the device-specific port collection endpoint.
    """
    import requests
    import uuid
    from src.utils.api_customer import API_URL 

    # Generate a new UUID if one isn't explicitly provided
    port_id = port_intent.get("port_id") or str(uuid.uuid4())
    
    # Isolate device_id for routing
    device_id = str(port_intent.get("device_id", ""))
    
    api_payload = {
        "port_id": port_id,
        "mac_address": "unknown",  
        "port_name": str(port_intent.get("port", "")),
        "port_speed": str(port_intent.get("speed", "100000")),
        "device_id": device_id,
        "port_description": str(port_intent.get("alias", "")),
        "port_optic": "unknown",
        "port_tagging": "untagged",
        "port_cktid": "N/A",
        "customer_id": None,       
        "port_service_status": status_override,
        "port_type": "Infrastructure",
        "port_health_status": int(port_intent.get("port_health_status", 4)),
        "admin_status": str(port_intent.get("admin_status", "up")).lower(),
        "oper_status": "down"      
    }
    
    # --- FIX: Target the endpoint using the device_id as the path parameter ---
    url = f"{API_URL}/ports/{device_id}"
    
    try:
        response = requests.post(url, json=api_payload, timeout=5)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"API Error {response.status_code} on {url}: {response.text}")
            return {}
    except Exception as e:
        print(f"Failed to post port to {url}: {e}")
        return {}
    
def update_device(device_id: str, payload: dict):
    """PUT /devices/{device_id} - Corrected to use requests directly"""
    url = f"{API_URL}/devices/{device_id}"
    MessageHandler.add(f"📡 API REQ: PUT {url}", "info", category="API")
    try:
        # Ensure ID is in payload as per your existing requirement
        payload["device_id"] = device_id
        response = requests.put(
            url,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            MessageHandler.add(f"✅ Device {device_id} updated successfully", "success", category="API")
            return True
        MessageHandler.add(f"❌ Update Failed for {device_id}: HTTP {response.status_code}", "error", category="API")
        return False
    except Exception as e:
        MessageHandler.add(f"❌ API Update Error: {e}", "error", category="API")
        return False

def delete_device(device_id: str):
    """DELETE /devices/{device_id} - Corrected to use requests directly"""
    url = f"{API_URL}/devices/{device_id}"
    MessageHandler.add(f"📡 API REQ: DELETE {url}", "info", category="API")
    try:
        response = requests.delete(url, headers={'accept': 'application/json'}, timeout=5)
        success = response.status_code in [200, 204]
        if success:
            MessageHandler.add(f"🗑️ Device {device_id} deleted successfully", "success", category="API")
        else:
            MessageHandler.add(f"❌ Delete Failed for {device_id}: HTTP {response.status_code}", "error", category="API")
        return success
    except Exception as e:
        MessageHandler.add(f"❌ API Delete Error: {e}", "error", category="API")
        return False

def get_devices_by_short_name(short_name: str) -> List[Dict]:
    """
    Fetches all devices for a site. Ensures the return is always a list.
    """
    try:
        clean_name = str(short_name).strip().lower()
        url = f"{API_URL}/devices/location/{clean_name}"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            # Guard: If API returns a single dict instead of a list, wrap it.
            return data if isinstance(data, list) else [data]
        
        return []
    except Exception as e:
        print(f"API Error: {e}")
        return []
  
def get_ports_by_device(device_id: str) -> Optional[Dict]:
    try:
        resp = requests.get(f"{API_URL}/ports/device/{device_id}")
        return resp.json() if resp.status_code == 200 else None
    except: return None

def get_devices_by_short_name(short_name: str) -> List[Dict]:
    """
    Fetches all devices for a site. Ensures the return is always a list.
    """
    try:
        clean_name = str(short_name).strip().lower()
        url = f"{API_URL}/devices/location/{clean_name}"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            # Guard: If API returns a single dict instead of a list, wrap it.
            return data if isinstance(data, list) else [data]
        
        return []
    except Exception as e:
        print(f"API Error: {e}")
        return []
    
def get_site_details_by_shortname(short_name: str):
    """Fetches facility info based on shortName (e.g., den1)"""
    try:
        clean_name = str(short_name).strip().lower()
        resp = requests.get(f"{API_URL}/locations/shortName/{clean_name}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None

def get_location_by_id(location_id: str):
    """Fetches facility info based on location UUID."""
    try:
        clean_id = str(location_id).strip()
        resp = requests.get(f"{API_URL}/locations/{clean_id}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None

def fetch_master_dashboard(network_name: str) -> list:
    """Fetches the nested God Mode dashboard payload based on network name."""
    try:
        clean_name = str(network_name).strip().upper()
        # Adjust the path below if your API_URL already includes '/inventory'
        resp = requests.get(f"{API_URL}/inventory/networkLinks/dashboard/master/{clean_name}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []

def fetch_locations_by_network(network_name: str) -> list:
    """Fetches all valid PoP locations for a given network."""
    try:
        clean_name = str(network_name).strip().upper()
        resp = requests.get(f"{API_URL}/locations/by-network/{clean_name}", timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else []
        return []
    except Exception:
        return []

def fetch_topology_links(network_name: str, pop: str = None, link_type: str = None) -> list:
    """Fetches network topology links dynamically based on network name and filters."""
    try:
        clean_name = str(network_name).strip().upper()
        params = {"network": clean_name}
        
        # Dynamically append the PoP filter
        if pop and pop != "-- Global Backbone --":
            params["pop"] = str(pop).strip().upper()
            
        # Dynamically append the Link Type filter
        if link_type:
            params["link_type"] = str(link_type).strip()

        resp = requests.get(f"{API_URL}/networkLinks/detail/filter", params=params, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else []
        return []
    except Exception:
        return []

def get_network_devices(network_name: str) -> list:
    """Fetches all devices for a specific network (e.g., AS3356)."""
    import requests
    import streamlit as st
    
    url = f"{API_URL}/devices/network/{network_name}"
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error (Network Devices): {e}")
        return []
    
def get_device_location(device_id: str):
    """Fetches the location assignment for a specific device."""
    import requests
    try:
        clean_id = str(device_id).strip()
        # Note: Adjust the /devices/ route if your FastAPI endpoint differs
        resp = requests.get(f"{API_URL}/devices/{clean_id}/location", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None
  
def get_site_details_by_shortname(short_name: str):
    """Fetches facility info based on shortName (e.g., den1)"""
    try:
        clean_name = str(short_name).strip().lower()
        resp = requests.get(f"{API_URL}/locations/shortName/{clean_name}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None

def save_device_location(payload: Dict, exists: bool) -> Optional[Dict]:
    try:
        url = f"{API_URL}/locations/device"
        if exists:
            resp = requests.put(f"{url}/{payload['device_id']}", json=payload)
        else:
            resp = requests.post(url, json=payload)
        return resp.json() if resp.status_code in [200, 201] else None
    except: return None

def get_network_links() -> list:
    """GET /networkLinks/ - Fetches all registered connections."""
    url = f"{API_URL}/networkLinks/"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            MessageHandler.add(f"✅ Retrieved {len(data)} netlinks", "success", category="API")
            return data
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Error (get_links): {e}", "error", category="API")
        return []

def get_network_links_detail() -> list:
    """
    GET /networkLinks/detail
    Fetches links with joined Port and Device names from the backend.
    """
    url = f"{API_URL}/networkLinks/detail"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            MessageHandler.add(f"✅ Retrieved {len(data)} detailed netlinks", "success", category="API")
            return data
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Error (get_links_detail): {e}", "error", category="API")
        return []

def get_network_link_by_id(netlink_id: str) -> dict:
    """GET /networkLinks/{netlink_id} - Fetches a specific connection."""
    url = f"{API_URL}/networkLinks/{netlink_id}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        MessageHandler.add(f"❌ API Error (get_link_by_id): {e}", "error", category="API")
        return None

def post_network_link(payload: dict):
    """POST /networkLinks/ - Creates a new link record."""
    url = f"{API_URL}/networkLinks/"
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.json() if resp.status_code in [200, 201] else None
    except Exception as e:
        MessageHandler.add(f"❌ API Error (post): {e}", "error", category="API")
        return None

def put_network_link(netlink_id: str, payload: dict):
    """PUT /networkLinks/{netlink_id} - Updates an existing link."""
    url = f"{API_URL}/networkLinks/{netlink_id}"
    try:
        resp = requests.put(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        MessageHandler.add(f"❌ API Error (put): {e}", "error", category="API")
        return False

def delete_network_link(netlink_id: str):
    """DELETE /networkLinks/{netlink_id} - Removes a link."""
    url = f"{API_URL}/networkLinks/{netlink_id}"
    try:
        resp = requests.delete(url, timeout=5)
        return resp.status_code in [200, 204]
    except Exception as e:
        MessageHandler.add(f"❌ API Error (delete): {e}", "error", category="API")
        return False

def get_galileo_nodes() -> list:
    """
    GET /galileo/nodes
    Fetches city hubs (NYC1, DEN1, SFO1) with device 'backpacks' for Beck topology.
    """
    url = f"{API_URL}/galileo/nodes"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            MessageHandler.add(f"✅ Retrieved {len(data)} Galileo nodes", "success", category="API")
            return data
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Error (get_galileo_nodes): {e}", "error", category="API")
        return []

def get_galileo_links() -> list:
    """
    GET /galileo/links
    Fetches the inter-city connectivity fabric (fiber spans) for Beck topology.
    """
    url = f"{API_URL}/galileo/links"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            MessageHandler.add(f"✅ Retrieved {len(data)} Galileo links", "success", category="API")
            return data
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Error (get_galileo_links): {e}", "error", category="API")
        return []

def get_network_summary_grouped() -> dict:
    """
    GET /inventory/network/summary/grouped
    Fetches the hierarchical network summary including devices, 
    locations, ports, and links.
    """
    url = f"{API_URL}/inventory/network/summary/grouped"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Calculate total metric count for logging
            total_items = sum(len(v) for v in data.values() if isinstance(v, list))
            MessageHandler.add(f"✅ Retrieved {total_items} grouped inventory metrics", "success", category="API")
            return data
        
        MessageHandler.add(f"⚠️ Unexpected status {resp.status_code} for network summary", "warning", category="API")
        return {}
    except Exception as e:
        MessageHandler.add(f"❌ API Error (get_network_summary_grouped): {e}", "error", category="API")
        return {}

def get_global_traffic_summary() -> dict:
    """
    NDT API Layer: Fetches the macro-level global traffic summary.
    """
    url = f"{API_URL}/traffic/summary/global"
    
    try:
        response = requests.get(url, headers={"accept": "application/json"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"NDT Fabric Error - Failed to fetch global traffic summary: {e}")
        return {}

def get_regional_detail_summary(report_date: str = "2026-04-23", pop_limit: int = 50, router_limit: int = 50) -> dict:
    """
    NDT API Layer: Fetches the deep regional topology and PoP details.
    """
    url = f"{API_URL}/traffic/regions/detail"
    params = {
        "report_date": report_date,
        "pop_limit": pop_limit,
        "router_limit": router_limit
    }
    
    try:
        response = requests.get(url, params=params, headers={"accept": "application/json"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"NDT Fabric Error - Failed to fetch regional detail summary: {e}")
        return {}

def get_pop_summary(pop_id: str, report_date: str = "2026-04-23", router_limit: int = 50) -> dict:
    """
    NDT API Layer: Fetches the aggregate summary for a specific PoP.
    Endpoint: /traffic/pops/{pop_id}/summary
    """
    url = f"{API_URL}/traffic/pops/{pop_id.lower()}/summary"
    params = {
        "report_date": report_date,
        "router_limit": router_limit
    }
    
    try:
        response = requests.get(url, params=params, headers={"accept": "application/json"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"NDT Fabric Error - Failed to fetch PoP summary for {pop_id}: {e}")
        return {}

def get_pop_to_pop_summary(pop_id: str, limit: int = 25) -> list:
    """
    NDT API Layer: Fetches targeted PoP-to-PoP bi-directional flow telemetry.
    """
    url = f"{API_URL}/traffic/pop2pop/{pop_id}"
    params = {"limit": limit}
    
    try:
        response = requests.get(url, params=params, headers={"accept": "application/json"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"NDT Fabric Error - Failed to fetch pop-to-pop telemetry for {pop_id}: {e}")
        return []

def get_router_summary(report_date: str = "2026-04-23", limit: int = 20, sort: str = "egress_total") -> list:
    """
    NDT API Layer: Fetches the top N routers based on traffic volume for a specific date.
    Endpoint: /traffic/routers
    """
    url = f"{API_URL}/traffic/routers"
    params = {
        "report_date": report_date,
        "limit": limit,
        "sort": sort,
        "order": "desc"
    }
    
    try:
        response = requests.get(url, params=params, headers={"accept": "application/json"}, timeout=15)
        response.raise_for_status()
        # Returns the raw JSON list from the FastAPI backend
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"NDT Fabric Error - Failed to fetch router leaderboard for {report_date}: {e}")
        return []

def get_router_detail(router_id: str, report_date: str = "2026-04-21", egress_limit: int = 25, ingress_limit: int = 25) -> dict:
    """
    NDT API Layer: Fetches detailed router-to-router ingress/egress flows for a specific chassis.
    Endpoint: /traffic/router/{router_id}/detail
    """
    # Force lower case on the router ID to ensure URL consistency
    safe_router_id = router_id.lower()
    url = f"{API_URL}/traffic/router/{safe_router_id}/detail"
    
    params = {
        "report_date": report_date,
        "egress_limit": egress_limit,
        "ingress_limit": ingress_limit
    }
    
    try:
        response = requests.get(url, params=params, headers={"accept": "application/json"}, timeout=15)
        response.raise_for_status()
        
        # Returns the raw JSON payload (summary, egress_flows, ingress_flows)
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"NDT Fabric Error - Failed to fetch node details for {safe_router_id} on {report_date}: {e}")
        # Return an empty dictionary so the upstream data controller handles it gracefully
        return {}
    
def get_normalized_inventory_df(payload: dict, target_key: str) -> pd.DataFrame:
    """
    Safely extracts a list of dictionaries from a JSON payload and converts it to a DataFrame.
    """
    if not payload:
        return pd.DataFrame()

    # 1. Handle if the API wraps the response in a 'data' or 'results' key
    if "data" in payload and isinstance(payload["data"], dict):
        base_data = payload["data"]
    elif "results" in payload and isinstance(payload["results"], dict):
        base_data = payload["results"]
    else:
        base_data = payload

    # 2. Extract the specific target array (e.g., "device_location")
    extracted_list = base_data.get(target_key, [])

    # 3. Convert to DataFrame
    if isinstance(extracted_list, list) and len(extracted_list) > 0:
        return pd.DataFrame(extracted_list)
    else:
        # Return empty dataframe if key is missing or list is empty
        return pd.DataFrame()