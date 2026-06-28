import ipaddress
import pandas as pd
import streamlit as st
import base64
import os
def get_topology_schema(svc_type: str, mcgw_mode: str = "Physical"):
    """
    Standardizes the DB Table mapping to satisfy 'chk_connector_table_values'.
    Returns: (A_Table, B_Table, Description)
    """
    svc_type = svc_type.upper().replace(" ", "")
    
    # Layer 3 / VRF Logic
    if any(x in svc_type for x in ["IPVPN", "IP-VPN", "DIA", "IOD"]):
        return "interface", "ports", "L3 VRF Attachment"
    
    # MCGW Logic
    if "MCGW" in svc_type:
        if "Cloud" in mcgw_mode:
            return "cloud_connections", "interface", "L3 Cloud-to-Interface"
        return "interface", "ports", "L3 Port-to-Interface"

    # Layer 2 / Ethernet Logic
    if any(x in svc_type for x in ["EPL", "EVPL", "EP-LAN", "EVP-LAN"]):
        return "ports", "ports", "L2 Fabric Stitch"

    return "interface", "ports", "Generic Connection"

def mask_to_cidr(mask_str: str) -> int:
    """Converts dotted-decimal mask (255.255.255.252) to CIDR (30)."""
    import ipaddress
    try:
        return ipaddress.IPv4Network(f"0.0.0.0/{mask_str}").prefixlen
    except Exception:
        return 30 # Fallback for typical point-to-point links

def initialize_provisioning_queues():
    """
    Initializes the three-tier queue system:
    1. Port Queue: Active form staging for Physical Ports.
    2. Interface Queue: Active form staging for Logical Interfaces.
    3. Stager Queue: Persistent ledger of POSTed items to drive Connections.
    """
    import streamlit as st
    
    # The 'Form' Queues (Cleared after every POST)
    if "payload" not in st.session_state:
        st.session_state.payload = {
            "service_context": {
                "children": {
                    "ports": [],      # The Port Queue
                    "interfaces": []   # The Interface Queue
                }
            }
        }
    
    # The 'Persistent' Ledger (Lives until the Connection is finished)
    if "stager_queue" not in st.session_state:
        st.session_state.stager_queue = {
            "ports": [],
            "interfaces": [],
            "connections": []
        }

def initialize_fabric_session():
    """
    Initializes the three-tiered JSON queue system in st.session_state.
    
    1. Port Queue (payload): Volatile form staging for Step 2.
    2. Interface Queue (payload): Volatile form staging for Step 3.
    3. Stager Queue: Persistent JSON ledger used to drive Step 5 connections.
    """
    import streamlit as st

    # --- THE FORM QUEUES (Volatile Staging) ---
    if "payload" not in st.session_state:
        st.session_state.payload = {
            "service_context": {
                "children": {
                    "ports": [],      # Active Port Queue
                    "interfaces": []   # Active Interface Queue
                }
            }
        }

    # --- THE STAGER QUEUE JSON (Persistent Results) ---
    if "stager_queue" not in st.session_state:
        st.session_state.stager_queue = {
            "ports": [],
            "interfaces": [],
            "connections": []
        }
    
def commit_queue_to_stager(tier: str):
    """
    Transfers data from the volatile Form Queues to the persistent Stager Queue.
    Typically called immediately after a successful API POST.
    
    Args:
        tier (str): 'ports' or 'interfaces'
    """
    import streamlit as st

    # 1. Access the Queues
    form_queue = st.session_state.payload["service_context"]["children"].get(tier, [])
    stager = st.session_state.stager_queue.get(tier)

    if not form_queue:
        return False

    # 2. Update the Stager with the Queue data
    # We use extend to handle multiple items provisioned in one step
    stager.extend(form_queue)

    # 3. Clear the Form Queue (Tier 5 Debugger will now show 0 for this tier)
    st.session_state.payload["service_context"]["children"][tier] = []
    
    return True

def get_stager_context():
    """
    Retrieves the current state of the Stager Queue to drive 
    Fabric Connection logic (Step 5) and Routing (Step 4).
    
    Returns:
        tuple: (list_of_staged_ports, list_of_staged_interfaces)
    """
    import streamlit as st

    stager = st.session_state.get("stager_queue", {})
    
    staged_ports = stager.get("ports", [])
    staged_intfs = stager.get("interfaces", [])

    return staged_ports, staged_intfs

def hydrate_stager_from_api(tier: str, record: dict):
    """
    Hydrates the Stager Queue with a confirmed record from the API.
    
    Args:
        tier (str): 'ports' or 'interfaces'
        record (dict): The JSON object returned by the API after a successful POST.
    """
    import streamlit as st

    if "stager_queue" not in st.session_state:
        st.session_state.stager_queue = {"ports": [], "interfaces": [], "connections": []}

    # Append the live record (containing the new UUIDs) to the persistent ledger
    st.session_state.stager_queue[tier].append(record)

def calculate_ip_assignment(byoip: bool, prefix: int, version: str = "v4", manual_cidr: str = ""):
    """
    Unified IP Calculator. 
    Handles both manual BYOIP parsing and automated Lumen Pool allocation.
    """
    import streamlit as st
    import ipaddress

    # --- BRANCH 1: BYOIP (Manual Entry) ---
    if byoip:
        try:
            if not manual_cidr:
                return "Pending Input", "Pending Input", "Pending Input"
                
            net = ipaddress.ip_network(manual_cidr.strip(), strict=False)
            hosts = list(net.hosts())

            if len(hosts) >= 2:
                pe_ip, ce_ip = str(hosts[0]), str(hosts[1])
            else:
                # Handle /31 or /127 
                pe_ip, ce_ip = str(net[0]), str(net[1])

            mask = str(net.netmask) if version == "v4" else str(net.prefixlen)
            return pe_ip, ce_ip, mask
            
        except Exception:
            return "Invalid Subnet", "Invalid", "Invalid"

    # --- BRANCH 2: LUMEN ASSIGNED (Auto-Allocation) ---
    base_pool_str = "2001:db8::/48" if version == "v6" else "8.56.0.0/16"
    pool = ipaddress.ip_network(base_pool_str)

    # Count consumed IPs to find the next available subnet block
    live_manifest = st.session_state.get("live_manifest", {})
    live_intfs = live_manifest.get("fabric_interfaces", [])
    staged_payload = st.session_state.get("payload", {})
    staged_intfs = staged_payload.get("service_context", {}).get("children", {}).get("interfaces", [])

    if version == "v4":
        consumed = [i.get("ipv4_address") for i in live_intfs if i.get("ipv4_address")]
        consumed += [i.get("ipv4_lumen") for i in staged_intfs if i.get("ipv4_lumen")]
    else:
        consumed = [i.get("ipv6_address") for i in live_intfs if i.get("ipv6_address")]
        consumed += [i.get("v6_lumen") for i in staged_intfs if i.get("v6_lumen")]

    current_index = len(consumed)

    try:
        available_subnets = pool.subnets(new_prefix=prefix)
        # Fast-forward to the unconsumed index
        target_net = next((sn for i, sn in enumerate(available_subnets) if i == current_index), None)
        
        if not target_net:
            return "Pool Exhausted", "Invalid", "Invalid"

        hosts = list(target_net.hosts())
        if len(hosts) >= 2:
            pe_ip, ce_ip = str(hosts[0]), str(hosts[1])
        else:
            pe_ip, ce_ip = str(target_net[0]), str(target_net[1])

        mask = str(target_net.netmask) if version == "v4" else str(target_net.prefixlen)
        return pe_ip, ce_ip, mask
        
    except Exception as e:
        return f"Error: {str(e)}", "Invalid", "Invalid"

def get_base64_image(image_path):
    """
    Converts a local image file to a Base64 data URI.
    Returns None if the file is not found or fails to encode.
    """
    if not os.path.exists(image_path):
        return None  
        
    try:
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None
    
def validate_port_rules(row, active_port_ids, service_type):
    """
    Business logic for Lumen Fabric port eligibility.
    Reflects DB: EPL (All-2-1-bundled), Fabric (Staged/Active + Tagging rules).
    """
    port_id = row.get('port_id')
    # Normalize status for consistent comparison
    port_status = str(row.get('port_service_status', 'Available')).strip().lower()
    port_tagging = str(row.get('port_tagging', 'untagged')).strip().lower()
    
    # 1. Check if already assigned to this specific service
    if port_id in active_port_ids:
        return "✅ Currently Assigned"

    # 2. Logic for EPL Service Type
    if service_type == "EPL":
        if port_tagging == "all-2-1-bundled":
            return "🟢 Available (EPL)"
        return "❌ EPL Requires All-2-1-bundled"

    # 3. Logic for Fabric/MCGW Service Type
    # Rule: untagged must be Staged
    if port_tagging == "untagged":
        if port_status == "staged":
            return "🟢 Available (Staged)"
        return f"❌ Untagged must be Staged (Current: {port_status.capitalize()})"

    # Rule: Tagged must be Active or Staged
    if port_tagging == "tagged":
        if port_status in ["active", "staged"]:
            return f"🟢 Available ({port_status.capitalize()})"
        return f"❌ Tagged must be Active/Staged (Current: {port_status.capitalize()})"

    # Catch-all for All-2-1-bundled ports appearing in a non-EPL context
    if port_tagging == "all-2-1-bundled":
        return "⚠️ Reserved for EPL"

    return "❌ Ineligible Configuration"

def format_network_date(dt_str):
    """Normalizes ISO strings to 'YYYY-MM-DD HH:MM' format."""
    if not dt_str: return "N/A"
    try:
        import pandas as pd
        return pd.to_datetime(dt_str).strftime('%Y-%m-%d %H:%M')
    except:
        return dt_str
    
def handle_stitching_orchestration(selected_a: pd.Series, selected_b: pd.Series, connection_intent: dict):
    """
    Step 5 Orchestration Sequence:
    1. Activate Interface (Side A) -> Status change only.
    2. Activate Port (Side B) -> port_service_status change only.
    3. Create Fabric Connection -> Full payload commit.
    """
    import streamlit as st
    import requests
    import pandas as pd
    from src.utils.api_customer import API_URL, post_fabric_connection

    with st.status("🚀 Orchestrating Fabric Provisioning...", expanded=True) as status:
        try:
            # --- PRE-FLIGHT CHECK: Verify ID presence ---
            # Using .get() ensures we don't crash if the column was stripped by the UI
            intf_id = selected_a.get('interface_id')
            port_id = selected_b.get('port_id')

            if not intf_id or not port_id:
                missing = []
                if not intf_id: missing.append("interface_id")
                if not port_id: missing.append("port_id")
                st.error(f"❌ Critical Data Missing: {', '.join(missing)}")
                return

            # --- STEP 1: ACTIVATE INTERFACE (SIDE A) ---
            st.write(f"🔄 Activating Interface: `{selected_a.get('interface_name', 'Francis')}`...")
            # Targeted PUT to promotion endpoint
            resp_a = requests.put(f"{API_URL}/interface/{intf_id}", json={"status": "Active"})
            resp_a.raise_for_status()

            # --- STEP 2: ACTIVATE PORT (SIDE B) ---
            # Check current status from the series
            current_port_status = str(selected_b.get('port_service_status', 'Staged')).lower()
            
            if current_port_status == "staged":
                st.write(f"🔌 Activating Physical Port: `{selected_b.get('port_name', 'ae0')}`...")
                # Targeted update to avoid overwriting physical optics/speed data
                resp_b = requests.put(
                    f"{API_URL}/ports/id/{port_id}", 
                    json={"port_service_status": "Active"}
                )
                resp_b.raise_for_status()
            else:
                st.write(f"✅ Port `{selected_b.get('port_name')}` is already Active.")

            # --- STEP 3: CREATE FABRIC CONNECTION ---
            st.write(f"🔗 Committing Stitch: `{connection_intent['connection_name']}`...")
            
            # Ensure the API payload has the correct ID anchors before submission
            connection_intent['connector_a_id'] = intf_id
            connection_intent['connector_b_id'] = port_id
            
            # Clean payload for API (removing UI-only anchors like customer_id)
            api_payload = {k: v for k, v in connection_intent.items() if k != "customer_id"}
            
            # Leveraging your post_fabric_connection method
            post_fabric_connection(api_payload)

            status.update(label="✅ Fabric Stitching Successful!", state="complete")
            st.toast(f"Connection {connection_intent['connection_name']} is now Active.")
            
            # Reset intent queue and trigger refresh to update Document 1 & 2 in Digital Twin
            st.session_state.payload["service_context"]["children"]["fabric_connections"] = []
            st.rerun()

        except Exception as e:
            status.update(label="❌ Orchestration Failed", state="error")
            st.error(f"Provisioning Error: {str(e)}")