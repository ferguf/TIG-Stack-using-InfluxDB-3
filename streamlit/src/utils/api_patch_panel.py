import requests
import streamlit as st
from src.utils.file_utils import MessageHandler

API_URL = "http://fastapi:8000"

def get_port_by_device_name(device_name: str, port_name: str):
    """GET /ports/{device_name}/port/{port_name}"""
    url = f"{API_URL}/ports/{device_name}/port/{port_name}"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        response = requests.get(url, headers={'accept': 'application/json'}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            port_id = data.get('port_id')
            MessageHandler.add(f"✅ Side B Port Found: {port_name} (ID: {port_id})", "success", category="API")
            return port_id
        MessageHandler.add(f"⚠️ Side B Not Found: {device_name}/{port_name} (HTTP {response.status_code})", "warning", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ API Exception: {str(e)}", "error", category="API")
        return None

def get_patch_panel_port_uuid(device_name: str, port_name: str):
    """GET /patchPanels/device/{device_name}/port/{port_name}"""
    url = f"{API_URL}/patchPanels/device/{device_name}/port/{port_name}"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            uuid = response.json().get("patch_panel_port_id")
            MessageHandler.add(f"✅ Side A Port Found: {port_name} (ID: {uuid})", "success", category="API")
            return uuid
        MessageHandler.add(f"⚠️ Side A Not Found: {device_name}/{port_name} (HTTP {response.status_code})", "warning", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ API Exception: {str(e)}", "error", category="API")
        return None


def update_panel_port(port_id: str, payload: dict):
    """
    PATCH /patchPanels/{port_id}
    Updates Side A with the Side B connection info.
    """
    url = f"{API_URL}/patchPanels/port/{port_id}"
    
    try:
        # We use PATCH now to support the 'exclude_unset=True' backend logic
        response = requests.patch(
            url, 
            json=payload, 
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            return True, "Success"
        
        # Log detailed error if the 500 error persists
        error_detail = response.json().get('detail', 'Unknown Error')
        return False, f"HTTP {response.status_code}: {error_detail}"
        
    except Exception as e:
        return False, str(e)

    
def get_panel_ports(device_id: str):
    """GET /patchPanels/device/{device_id}"""
    url = f"{API_URL}/patchPanels/device/{device_id}"
    MessageHandler.add(f"📡 API REQ: GET {url}", "info", category="API")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            MessageHandler.add(f"✅ Retrieved {len(data)} ports for device {device_id}", "success", category="API")
            return data
        return []
    except Exception as e:
        MessageHandler.add(f"❌ API Error fetching ports: {str(e)}", "error", category="API")
        return []

def post_panel_port(payload: dict):
    """POST /patchPanels/"""
    url = f"{API_URL}/patchPanels/"
    MessageHandler.add(f"📡 API REQ: POST {url} | Payload: {payload}", "info", category="API")
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code in [200, 201]:
            MessageHandler.add("✅ New Port Created Successfully", "success", category="API")
            return True, "OK"
        
        reason = response.json().get('detail', response.text) if response.status_code != 500 else "NULL UUID/DB Error"
        MessageHandler.add(f"❌ POST Failed: {reason}", "error", category="API")
        return False, f"HTTP {response.status_code} - {reason}"
    except Exception as e:
        MessageHandler.add(f"❌ POST Conn Error: {str(e)}", "error", category="API")
        return False, f"Conn Error: {str(e)}"
    
def delete_panel_port(port_id: str):
    """DELETE /patchPanels/{port_id}"""
    url = f"{API_URL}/patchPanels/{port_id}"
    MessageHandler.add(f"📡 API REQ: DELETE {url}", "info", category="API")
    try:
        response = requests.delete(url, timeout=5)
        if response.status_code == 200:
            MessageHandler.add(f"🗑️ Port {port_id} deleted", "success", category="API")
            return True, response.text
        MessageHandler.add(f"❌ Delete Failed: HTTP {response.status_code}", "error", category="API")
        return False, response.text
    except Exception as e:
        MessageHandler.add(f"❌ Delete Conn Error: {str(e)}", "error", category="API")
        return False, str(e)


def get_patch_panels_for_device_name(device_name: str):
    """
    Specifically for Side A / Passive Gear.
    Returns the patch panel object based on a name string.
    """
    url = f"{API_URL}/patchPanels/deviceName/{device_name}"
    MessageHandler.add(f"📡 API REQ (PP Search): GET {url}", "info", category="API")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        MessageHandler.add(f"⚠️ Patch Panel '{device_name}' not found.", "warning", category="API")
        return None
    except Exception as e:
        MessageHandler.add(f"❌ PP API Error: {str(e)}", "error", category="API")
        return None

def get_patch_panel_port_by_name(device_name: str, port_name: str):
    """GET /patchPanels/device/{device_name}/portName/{port_name}"""
    try:
        response = requests.get(
            f"{API_URL}/patchPanels/deviceName/{device_name}/portName/{port_name}",
            headers={'accept': 'application/json'}
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        st.error(f"API Get Error: {e}")
        return None
 
# --- Aliases for Backward Compatibility ---
delete_patch_panel = delete_panel_port
update_patch_panel = update_panel_port