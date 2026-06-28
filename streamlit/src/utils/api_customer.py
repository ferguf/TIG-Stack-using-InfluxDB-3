import uuid
import requests
import pandas as pd
from typing import Optional, List, Dict, Union
import streamlit as st
# --- location: src.utils.api_customer ---
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
    """
    POST a new logical connection to FastAPI.
    Features G -> Mbps translation (10G -> 10000) and dynamic connector tables.
    """
    import requests
    import streamlit as st
    from src.utils.api_customer import API_URL

    try:
        url = f"{API_URL}/fabric_connections/"
        
        # Safe Cast: "10G" -> "10000" (Megabits)
        bw_str = str(payload.get("bandwidth", "0")).upper().replace("G", "000")
        bw_val = int(bw_str) if bw_str.isdigit() else 0

        # Safe Cast: "UNTAGGED" -> 0
        vlan_str = str(payload.get("vlan_id", "0")).upper()
        vlan_val = 0 if vlan_str in ["UNTAGGED", "NONE", ""] else int(vlan_str)
        
        api_payload = {
            "connection_name": payload.get("connection_name"),
            "service_id": payload.get("service_id"),
            "connector_a_id": payload.get("connector_a_id"),
            "connector_b_id": payload.get("connector_b_id"),
            # Dynamic table mapping: Accepts 'interface' or 'ports' from the UI form
            "connector_a_table": payload.get("connector_a_table", "ports"),
            "connector_b_table": payload.get("connector_b_table", "ports"),
            "connection_status": payload.get("status", "Staged"),
            "vrf_name": payload.get("vrf_name"),
            "service_bw": bw_val,
            "s_vlan": vlan_val,
            "health_status": 1
        }

        resp = requests.post(url, json=api_payload, timeout=10)
        
        if resp.status_code == 500:
            st.error(f"💥 Database/Backend Error: {resp.text}")
            return {}

        resp.raise_for_status()
        return resp.json()

    except Exception as e:
        st.error(f"❌ Failed to commit connection: {str(e)}")
        return {}

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
    
def post_vrf_intent(payload: dict) -> dict:
    """Alias for post_fabric_service to match Workflow Manager naming."""
    return post_fabric_service(payload)

def post_port_intent(customer_id: str, port_intent: dict, status_override: str = "Staged") -> dict:
    """
    Finalized Step 2 Orchestrator (Standalone Version).
    Strictly maps the provided UI intent object to the Galileo API Model.
    Contains NO state-transition logic.
    """
    import requests
    # Restored your original direct import structure
    from src.utils.api_customer import API_URL 

    port_id = port_intent.get("port_id")
    
    # Mapping the Intent Object directly to the Database schema
    api_payload = {
        "device_id": port_intent.get("device_id"),
        "port_name": port_intent.get("port"),           
        "port_speed": port_intent.get("speed"),         
        "port_description": port_intent.get("alias"),   
        "port_optic": port_intent.get("optics"),        
        "port_tagging": port_intent.get("port_tagging"), 
        "admin_status": port_intent.get("admin_status"), 
        "customer_id": customer_id,                
        "port_service_status": status_override,
        
        # Explicitly passing health from the UI payload, defaulting to 4 if missing
        "port_health_status": port_intent.get("port_health_status", 4), 
        
        "port_type": "fabric port"
    }

    target_url = f"{API_URL}/ports/id/{port_id}"
    
    try:
        # Note: Using PUT as this resource exists but is being updated with intent
        response = requests.put(target_url, json=api_payload, timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Failed to provision {port_intent.get('port', 'Unknown')}: {e.response.text}")

def post_static_route_intent(payload: dict) -> Optional[dict]:
    """
    POST a static route intent to FastAPI.
    Forcing 'prefix_mask' to string to satisfy API validation.
    """
    try:
        url = f"{API_URL}/interface/staticRoute"
        
        # Build a clean payload to strip out UI-only keys like 'display_cidr'
        api_payload = {
            "interface_id": payload.get("interface_id"),
            "ip_prefix": payload.get("ip_prefix"),
            "prefix_mask": str(payload.get("prefix_mask")), # FORCE STRING HERE
            "next_hop_ip": payload.get("next_hop_ip"),
            "metric": int(payload.get("metric", 0)),
            "community": payload.get("community", "")
        }
        
        resp = requests.post(url, json=api_payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"❌ Static Route API Error: {e}")
        return None

def post_bgp_peer_intent(payload: dict) -> Optional[dict]:
    """
    POST a BGP neighbor intent to FastAPI.
    Forcing list-type for policies to satisfy the 422 error.
    """
    import requests
    import streamlit as st
    
    try:
        url = f"{API_URL}/interface/bgpNeighbor"
        
        # Helper to ensure policy is always a list
        def ensure_list(val):
            if isinstance(val, list):
                return val
            return [str(val)] if val else ["ALLOW_ALL"]

        api_payload = {
            "interface_id": payload.get("interface_id"),
            "neighbor_ip": payload.get("neighbor_ip"),
            "local_ip": payload.get("local_ip"),
            "remote_asn": int(payload.get("remote_asn", 64512)),
            "local_asn": int(payload.get("local_asn", 1)),
            "session_type": payload.get("session_type", "EBGP"),
            "description": payload.get("description", ""),
            # FORCE LISTS HERE
            "import_policy": ensure_list(payload.get("import_policy")),
            "export_policy": ensure_list(payload.get("export_policy")),
            "multihop": int(payload.get("multihop", 0)),
            "auth": bool(payload.get("auth", False)),
            "bfd": bool(payload.get("bfd", False)),
            "bfd_interval": int(payload.get("bfd_interval", 500)),
            "bfd_multiple": int(payload.get("bfd_multiple", 3))
        }
        
        resp = requests.post(url, json=api_payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"❌ BGP API Error: {e}")
        return None

def get_cloud_partners():
    """Fetches valid cloud partners from the Galileo DB."""
    try:
        resp = requests.get(f"{API_URL}/cloudPartner/")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Error fetching cloud partners: {e}")
        return []
    
def get_cloud_partners():
    """Fetches dynamic partner list from Galileo DB."""
    try:
        # Matches your CURL: GET /cloudPartner/
        resp = requests.get(f"{API_URL}/cloudPartner/", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"📡 API Connection Error: {e}")
        return []

def post_cloud_intent(peering_intent: dict) -> dict:
    """
    POST a cloud connection intent to the Galileo API.
    Ensures the service_id is explicitly stringified to prevent 422 errors.
    
    Args:
        peering_intent (dict): Dictionary containing partner_id, service_id, 
                               connection_name, service_type, region, and service_bw.
    
    Returns:
        dict: The JSON response from the API or an empty dict on failure.
    """
    import requests
    import streamlit as st
    from src.utils.api_customer import API_URL

    # 1. ANCHOR RESOLUTION
    service_id = peering_intent.get("service_id") or st.session_state.get("payload", {}).get("service_id")

    if not service_id:
        print("❌ CRITICAL: No service_id found. Aborting POST.")
        return {}

    # 2. PAYLOAD CONSTRUCTION
    api_payload = {
        "partner_id": peering_intent.get("partner_id"),
        "service_id": str(service_id),
        "connection_name": peering_intent.get("connection_name"),
        "service_type": peering_intent.get("service_type", "Layer3"),
        "service_status": "Planned",
        "region": peering_intent.get("region"),
        "service_bw": int(peering_intent.get("service_bw", 1000)),
        "redundancy_model": peering_intent.get("redundancy_model", "Single"),
        "description": peering_intent.get("description", "Galileo Provisioned")
    }

    # 3. API TRANSMISSION
    try:
        url = f"{API_URL}/cloudPartner/connection/"
        resp = requests.post(url, json=api_payload, timeout=15)
        
        if resp.status_code == 422:
            print(f"💥 Validation Error (422): {resp.json()}")
        
        resp.raise_for_status()
        return resp.json()
        
    except Exception as e:
        print(f"❌ API Call Failed: {e}")
        return {}

def get_optics_options(speed: str) -> list:
    """Returns valid transceiver types based on port speed."""
    speed_map = {
        "1G": ["1000Base-LX", "1000Base-SX", "1000Base-T"],
        "10G": ["10GBase-LR", "10GBase-SR", "10GBase-ER"],
        "100G": ["100GBase-LR4", "100GBase-SR4", "100GBase-CWDM4"]
    }
    for key in speed_map:
        if key in speed: return speed_map[key]
    return ["Standard-SFP", "Standard-QSFP"]

def post_interface_intent(payload: dict) -> dict:
    """
    POST a logical interface intent to FastAPI.
    Anchors the interface to both a physical port_id and a parent service_id.
    """
    import requests
    import uuid
    from datetime import datetime
    import streamlit as st
    from src.utils.api_customer import API_URL

    # Retrieve the service_id anchor from the global payload
    # This satisfies the FastAPI ResponseModel requirement
    # Map UI internal state to the DB schema
    api_ready_payload = {
        "interface_id": payload.get("interface_id") or str(uuid.uuid4()),
        "service_id": payload.get("service_id"),
        "port_id": payload.get("port_id"), 
        "ckt_id": payload.get("ckt_id", "PENDING"),
        "description": payload.get("alias", "Provisioned via Galileo"),
        "interface_name": payload.get("alias"),
        "interface_type": "Fabric Interface",
        "svlan_id": int(payload.get("vlan_id") or 0),
        "status": "Staged",
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        url = f"{API_URL}/interface/"
        resp = requests.post(url, json=api_ready_payload, timeout=10)
        
        # Capture specific backend validation errors before raising
        if resp.status_code == 500:
            st.error(f"💥 Backend Interface Error: {resp.text}")
            return {}

        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Failed to provision interface {payload.get('alias')}: {e}")
        return {}
    except Exception as e:
        st.error(f"❌ Connection Error: {str(e)}")
        return {}

def post_interface_ip(payload: dict) -> bool:
    """
    POSTs an IP assignment to a logical interface.
    ALIGNED: Matches FastAPI Pydantic requirements for types and mandatory fields.
    """
    import requests
    import streamlit as st
    from src.utils.api_customer import API_URL

    try:
        url = f"{API_URL}/interface/ipAddress/"
        
        # Build the final payload to ensure correct types
        api_ready_payload = {
            "interface_id": str(payload.get("interface_id")),
            "lumen_ip_address": str(payload.get("lumen_ip_address")),
            "customer_ip_address": str(payload.get("customer_ip_address")),
            "network_mask_cidr": int(payload.get("network_mask_cidr", 30)),
            "bring_your_own_ip": bool(payload.get("bring_your_own_ip", False))
        }

        resp = requests.post(url, json=api_ready_payload, timeout=5)
        
        if resp.status_code == 422:
            st.error(f"❌ API Validation Error: {resp.json().get('detail')}")
            return False
            
        resp.raise_for_status()
        return True
    except Exception as e:
        st.error(f"❌ IP Assignment API Failed: {e}")
        return False

def get_all_interfaces() -> pd.DataFrame:
    """Fetch all interfaces from the API."""
    try:
        resp = requests.get(f"{API_URL}/interface/")
        resp.raise_for_status()
        return pd.DataFrame(resp.json())
    except Exception as e:
        st.error(f"Error fetching interfaces: {e}")
        return pd.DataFrame()

def get_interface_detail(interface_id: str) -> dict:
    """Fetch detailed view of an interface including nested objects."""
    try:
        resp = requests.get(f"{API_URL}/interface/detail/{interface_id}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Error fetching interface detail: {e}")
        return {}

def get_fabric_service_detail(service_id: str) -> dict:
    """Fetch detailed view of a fabric service including nested connections."""
    try:
        resp = requests.get(f"{API_URL}/fabric_services/detail/{service_id}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Error fetching fabric service detail: {e}")
        return {}

def provision_service_changes(service_id: str, payload: dict) -> bool:
    """
    API Plumbing: Pushes the staged JSON payload to the Galileo Controller.
    This effectively 'commits' the ports/connections in the queue.
    """
    import requests

    try:
        # Construct the endpoint - adjust path as per your Controller API
        url = f"{API_URL}/services/{service_id}/provision"
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code in [200, 201, 202]:
            return True
        else:
            print(f"Provisioning Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Connection Exception in provision_service_changes: {e}")
        return False

def get_bgp_policies(customer_id: str) -> list:
    """
    Fetches all BGP policies for a given customer.
    Note: Ensure your FastAPI backend has an endpoint for /customer/{id}
    """
    target_url = f"{API_URL}/interface/routingPolicy/customer/{customer_id}"
    
    try:
        response = requests.get(target_url, timeout=10)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Fetch Error: {str(e)}")
        return []

def get_bgp_policy_by_id(policy_id: str) -> List[dict]:
    """
    Fetches the full sequence of terms for a specific policy_id.
    Endpoint: GET /interface/routingPolicy/{policy_id}
    """
    target_url = f"{API_URL}/interface/routingPolicy/{policy_id}"
    
    try:
        response = requests.get(target_url, timeout=10)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch BGP policy {policy_id}: {str(e)}")
        return []

def post_bgp_policy(policy_terms: List[dict]) -> List[dict]:
    """
    Creates a new BGP Policy (Bulk Terms).
    Endpoint: POST /interface/routingPolicy
    """
    target_url = f"{API_URL}/interface/routingPolicy"
    
    # Ensure payload is a list for the FastAPI validator
    if not isinstance(policy_terms, list):
        policy_terms = [policy_terms]
    
    try:
        response = requests.post(target_url, json=policy_terms, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        error_detail = response.text if 'response' in locals() else str(e)
        st.error(f"Failed to create routing policy: {error_detail}")
        raise Exception(f"POST Error: {error_detail}")

def put_bgp_policy(policy_id: str, policy_terms: List[dict]) -> List[dict]:
    """
    Updates an existing BGP Policy via replacement strategy.
    Endpoint: PUT /interface/routingPolicy/{policy_id}
    """
    target_url = f"{API_URL}/interface/routingPolicy/{policy_id}"
    
    if not isinstance(policy_terms, list):
        policy_terms = [policy_terms]
        
    try:
        response = requests.put(target_url, json=policy_terms, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        error_detail = response.text if 'response' in locals() else str(e)
        st.error(f"Failed to update routing policy {policy_id}: {error_detail}")
        raise Exception(f"PUT Error: {error_detail}")

def put_bgp_policy(payload: list, policy_id: str) -> list:
    """
    Updates an existing BGP routing policy.
    Endpoint: PUT /interface/routingPolicy/{policy_id}
    """
    target_url = f"{API_URL}/interface/routingPolicy/{policy_id}"
    
    try:
        response = requests.put(target_url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"PUT Error (Policy {policy_id}): {str(e)}")


def delete_bgp_policy(policy_id: str) -> bool:
    """
    Deletes all terms associated with a routing policy UUID.
    Endpoint: DELETE /interface/routingPolicy/{policy_id}
    """
    target_url = f"{API_URL}/interface/routingPolicy/{policy_id}"
    
    try:
        response = requests.delete(target_url, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        error_detail = response.text if 'response' in locals() else str(e)
        st.error(f"Failed to delete policy {policy_id}: {error_detail}")
        return False

def get_bgp_policies_by_service(fabric_service_id: str) -> list:
    """
    Fetches all BGP routing policies associated with a specific fabric service ID.
    Endpoint: GET /interface/routingPolicy/fabricService/{fabric_service_id}
    """
    target_url = f"{API_URL}/interface/routingPolicy/fabricService/{fabric_service_id}"
    
    try:
        response = requests.get(target_url, timeout=10)
        # 404 simply means no policies are attached to this service yet
        if response.status_code == 404:
            return []
            
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Fetch Error (Service {fabric_service_id}): {str(e)}")
        return []

def clear_service_queue(service_id: str) -> bool:
    """
    API Plumbing: Tells the Controller to discard all 'staged' or 'pending' 
    records for a specific service ID.
    """
    import requests
    from src.utils.api_config import API_BASE_URL

    try:
        # Endpoint to flush the pending manifest/intent
        url = f"{API_BASE_URL}/services/{service_id}/queue/clear"
        
        response = requests.delete(url, timeout=10)
        
        return response.status_code == 200
    except Exception as e:
        print(f"Connection Exception in clear_service_queue: {e}")
        return False