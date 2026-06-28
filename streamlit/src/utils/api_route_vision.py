import random
import uuid
import requests
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from src.utils.file_utils import MessageHandler

# Configuration - Using the fastpi:8000 hostname for container-to-container comms
API_URL = "http://fastapi:8000"

# --- HELPER UTILITIES ---

def process_routing_dataframe(data: List[Dict]) -> pd.DataFrame:
    """
    Utility to convert API list response into a pandas DataFrame.
    """
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def get_route_vision_data() -> List[Dict]:
    """
    Alias for get_route_vision_all. 
    Required to satisfy imports in route_vision.py.
    """
    return get_route_vision_all()

# --- READ OPERATIONS ---

def get_route_vision_all() -> List[Dict]:
    """GET /routeVision/ - Fetches all routing records across the fabric."""
    url = f"{API_URL}/routeVision/"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            MessageHandler.add(f"✅ Retrieved {len(data)} routing records", "success", category="API")
            return data
        MessageHandler.add(f"⚠️ Failed to fetch routes: HTTP {resp.status_code}", "warning", category="API")
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Exception (get_route_vision_all): {str(e)}", "error", category="API")
        return []

def get_route_vision_by_service(service_id: str) -> List[Dict]:
    """GET /routeVision/{service_id} - Fetches routes for a specific customer service."""
    url = f"{API_URL}/routeVision/{service_id}"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        resp = requests.get(url, headers={'accept': 'application/json'}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            MessageHandler.add(f"✅ Service {service_id}: {len(data)} routes retrieved", "success", category="API")
            return data
        MessageHandler.add(f"⚠️ No routes found for service {service_id} (HTTP {resp.status_code})", "warning", category="API")
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Error fetching routes for {service_id}: {e}", "error", category="API")
        return []

# --- WRITE OPERATIONS ---

def post_route_vision_batch(service_id: str, payload: List[Dict]):
    """POST /routeVision/{service_id} - Provisions a list of routes."""
    url = f"{API_URL}/routeVision/{service_id}"
    MessageHandler.add(f"📡 API REQ: POST {url} | Batch Size: {len(payload)}", "info", category="API")
    try:
        resp = requests.post(
            url,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            json=payload,
            timeout=5
        )
        if resp.status_code in [200, 201]:
            data = resp.json()
            MessageHandler.add(f"✅ Provisioning Success: {len(payload)} routes for {service_id}", "success", category="API")
            return data
        
        MessageHandler.add(f"❌ Provisioning Failed: HTTP {resp.status_code} - {resp.text}", "error", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ Network Error during route provisioning: {e}", "error", category="API")
        return None

def put_route_vision_entry(service_id: str, route_id: str, payload: Dict):
    """PUT /routeVision/{service_id}/{route_id} - Updates a specific route."""
    url = f"{API_URL}/routeVision/{service_id}/{route_id}"
    MessageHandler.add(f"📡 API REQ: PUT {url}", "info", category="API")
    try:
        resp = requests.put(
            url,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            json=payload,
            timeout=5
        )
        if resp.status_code == 200:
            MessageHandler.add(f"✅ Route {route_id} updated successfully", "success", category="API")
            return resp.json()
        
        MessageHandler.add(f"❌ Update Failed: HTTP {resp.status_code}", "error", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ API Error updating route {route_id}: {e}", "error", category="API")
        return None

def delete_route_vision_by_service(service_id: str):
    """DELETE /routeVision/{service_id} - Removes a single route for a service."""
    url = f"{API_URL}/routeVision/{service_id}"
    MessageHandler.add(f"📡 API REQ: DELETE {url}", "info", category="API")
    try:
        resp = requests.delete(url, timeout=5)
        if resp.status_code in [200, 204]:
            MessageHandler.add(f"🗑️ Route for service {service_id} successfully deleted", "success", category="API")
            return True
        MessageHandler.add(f"⚠️ Delete failed: HTTP {resp.status_code}", "warning", category="API")
        return False
    except Exception as e:
        MessageHandler.add(f"❌ API Error deleting route for {service_id}: {e}", "error", category="API")
        return False

# --- NEW INJECTION LOGIC ---

import random
# Ensure post_route_vision_batch and MessageHandler are imported!
def provision_test_data(service_id: str):
    """
    Generates and provisions a realistic dual-stack routing table.
    Target Mix: ~80% IPv4, ~20% IPv6.
    Protocol Mix: 80% BGP, 20% Static within each family.
    Uses realistic Direct /30 (IPv4) and /64 (IPv6) anchor links.
    """
    import random
    
    routes = []
    
    # ==========================================
    # 1. IPv4 GENERATION (~80% of total routes)
    # ==========================================
    num_v4_directs = random.randint(3, 4)
    
    for d in range(num_v4_directs):
        base_oct = random.randint(10, 250)
        provider_ip = f"172.16.{base_oct}.1"
        customer_ip = f"172.16.{base_oct}.2"
        
        # 🟢 FIX: Changed ip_next_hop from "Attached" to "0.0.0.0" for inet compatibility
        routes.append({
            "fabric_service_id": service_id, "fabric_connection_id": None,
            "ip_prefix": f"172.16.{base_oct}.0/30", "ip_next_hop": "0.0.0.0",
            "route_type": "DIRECT", "route_status": "Active", "route_target": "3549:110001",
            "route_distinguisher": f"{provider_ip}:110001", "bgp_asn": None, "bgp_as_path": "", "bgp_community": ""
        })

        protocol = random.choices(["BGP", "STATIC"], weights=[0.8, 0.2])[0]
        
        if protocol == "BGP":
            for _ in range(random.randint(15, 25)):
                bgp_prefix = f"10.{random.randint(0,255)}.{random.randint(0,255)}.0/{random.randint(16,29)}"
                peer_asn = random.randint(64500, 65000)
                routes.append({
                    "fabric_service_id": service_id, "fabric_connection_id": None,
                    "ip_prefix": bgp_prefix, "ip_next_hop": customer_ip,
                    "route_type": "BGP", "route_status": "Active", "route_target": "3549:110001",
                    "route_distinguisher": f"{provider_ip}:110001", "bgp_asn": peer_asn, 
                    "bgp_as_path": f"3549 {peer_asn}", "bgp_community": "3549:100"
                })
        else:
            for _ in range(random.randint(1, 3)):
                static_prefix = f"192.168.{random.randint(0,255)}.0/{random.randint(24,28)}"
                routes.append({
                    "fabric_service_id": service_id, "fabric_connection_id": None,
                    "ip_prefix": static_prefix, "ip_next_hop": customer_ip,
                    "route_type": "STATIC", "route_status": "Active", "route_target": "3549:110001",
                    "route_distinguisher": f"{provider_ip}:110001", "bgp_asn": None, 
                    "bgp_as_path": "", "bgp_community": ""
                })

    # ==========================================
    # 2. IPv6 GENERATION (~20% of total routes)
    # ==========================================
    num_v6_directs = random.randint(1, 2)
    
    for d in range(num_v6_directs):
        subnet_hex = hex(random.randint(4096, 65535))[2:] 
        provider_ipv6 = f"2001:db8:ffff:{subnet_hex}::1"
        customer_ipv6 = f"2001:db8:ffff:{subnet_hex}::2"
        rd_v4_id = f"192.168.1.{d + 200}"
        
        # 🟢 FIX: Changed ip_next_hop from "Attached" to "::" (IPv6 equivalent of 0.0.0.0)
        routes.append({
            "fabric_service_id": service_id, "fabric_connection_id": None,
            "ip_prefix": f"2001:db8:ffff:{subnet_hex}::/64", "ip_next_hop": "::",
            "route_type": "DIRECT", "route_status": "Active", "route_target": "3549:110001",
            "route_distinguisher": f"{rd_v4_id}:110001", "bgp_asn": None, "bgp_as_path": "", "bgp_community": ""
        })

        protocol = random.choices(["BGP", "STATIC"], weights=[0.8, 0.2])[0]
        
        if protocol == "BGP":
            for _ in range(random.randint(6, 12)):
                mask = random.choice([48, 56, 64])
                cust_net = hex(random.randint(1, 65535))[2:]
                peer_asn = random.randint(64500, 65000)
                routes.append({
                    "fabric_service_id": service_id, "fabric_connection_id": None,
                    "ip_prefix": f"2001:db8:{cust_net}::/{mask}", "ip_next_hop": customer_ipv6,
                    "route_type": "BGP", "route_status": "Active", "route_target": "3549:110001",
                    "route_distinguisher": f"{rd_v4_id}:110001", "bgp_asn": peer_asn, 
                    "bgp_as_path": f"3549 {peer_asn}", "bgp_community": "3549:1000"
                })
        else:
            for _ in range(random.randint(1, 2)):
                mask = random.choice([48, 64])
                static_net = hex(random.randint(1, 65535))[2:]
                routes.append({
                    "fabric_service_id": service_id, "fabric_connection_id": None,
                    "ip_prefix": f"2001:db8:dddd:{static_net}::/{mask}", "ip_next_hop": customer_ipv6,
                    "route_type": "STATIC", "route_status": "Active", "route_target": "3549:110001",
                    "route_distinguisher": f"{rd_v4_id}:110001", "bgp_asn": None, 
                    "bgp_as_path": "", "bgp_community": ""
                })

    # ==========================================
    # 3. METRICS & BATCH PUSH
    # ==========================================
    v4_count = sum(1 for r in routes if '.' in r['ip_prefix'])
    v6_count = sum(1 for r in routes if ':' in r['ip_prefix'])
    total_generated = len(routes)
    
    try:
        MessageHandler.add(f"🏗️ Generated {total_generated} test routes ({v4_count} IPv4 | {v6_count} IPv6) for service {service_id}", "info", category="Provisioning")
    except NameError:
        pass 
    
    return post_route_vision_batch(service_id, routes)