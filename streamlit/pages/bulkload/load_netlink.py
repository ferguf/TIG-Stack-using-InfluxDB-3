import streamlit as st
import pandas as pd
import requests
import re
import uuid
from src.utils.api_network import (
    get_device_by_name,
    get_port_by_device_name,
    get_network_links_detail,
    post_network_link,
    put_network_link,
    delete_network_link,
    API_URL
)
from src.ui_components import UI
from src.utils.file_utils import MessageHandler

# ==========================================
# 1. API RESOLVERS & CACHING
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def resolve_location_id(location_identifier: str):
    """Cached API Lookup for Location UUIDs to prevent N+1 API flooding."""
    if not location_identifier or str(location_identifier).lower() == 'nan':
        return None
        
    identifier = str(location_identifier).strip()
    url = f"{API_URL}/locations/name/{identifier}" 
    
    try:
        response = requests.get(url, headers={'accept': 'application/json'}, timeout=5)
        if response.status_code == 200:
            loc_data = response.json()
            if isinstance(loc_data, dict):
                return str(loc_data.get("location_id", loc_data.get("id", "")))
            elif isinstance(loc_data, list) and len(loc_data) > 0:
                return str(loc_data[0].get("location_id", loc_data[0].get("id", "")))
        return None
    except Exception as e:
        print(f"Location resolution failed for {identifier}: {e}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def resolve_port_id(device_name: str, port_name: str):
    """Cached API Lookup for Port UUIDs to prevent N+1 API flooding."""
    if not device_name or not port_name:
        return None
    try:
        port_data = get_port_by_device_name(str(device_name).strip(), str(port_name).strip())
        return str(port_data.get("port_id")) if isinstance(port_data, dict) else None
    except Exception:
        return None

# ==========================================
# 2. BUSINESS LOGIC & HELPERS
# ==========================================

def determine_device_vendor(chassis: str) -> str:
    """Determines the device vendor based on chassis model regex matching."""
    if not chassis or str(chassis).strip() == "" or str(chassis).lower() == "nan":
        return "Unknown"
        
    chassis_str = str(chassis).strip().upper()
    
    if re.match(r'^MX.*|^M.*|^VRR.*', chassis_str): return "Juniper"
    if re.match(r'^7750.*|^7950.*', chassis_str): return "Nokia"
    if re.match(r'^ASR.*', chassis_str): return "Cisco"
    return "Unknown"

def determine_network_asn(owner: str) -> str:
    """Maps device owner to the appropriate Autonomous System Number (ASN)."""
    if not owner or str(owner).lower() == "nan":
        return "Unknown"
        
    owner_map = {
        "QCC": "AS209",
        "L3": "AS3356",
        "TWTC-JUNIPER": "AS3549",
        "LC": "AS22561",
        "GBLX": "AS3549"
    }
    return owner_map.get(str(owner).strip().upper(), "Unknown")

def determine_link_type(dev_a: str, dev_b: str) -> str:
    """Analyzes router hostnames to determine if the link is Intra-Pop or Inter-Pop."""
    if not dev_a or not dev_b or 'nan' in [str(dev_a).lower(), str(dev_b).lower()]:
        return "Unknown"
        
    def extract_pop(hostname: str) -> str:
        h = hostname.strip().upper()
        # Handle dot notation (e.g., SDR1.NYC6)
        if '.' in h:
            return h.split('.')[1]
        # Handle hyphen notation (e.g., BTV1-AR1, NYC6-AR1)
        if '-' in h:
            return h.split('-')[0]
        return h

    try:
        pop_a = extract_pop(str(dev_a))
        pop_b = extract_pop(str(dev_b))
        return "Intra-Pop" if pop_a == pop_b else "Inter-Pop"
    except Exception:
        return "Unknown"

def analyze_topology_devices(df: pd.DataFrame) -> list:
    """Extracts a unique, deduplicated list of all device hostnames from the CSV."""
    if 'router' in df.columns and 'adj_router' in df.columns:
        sources = df['router'].dropna().unique().tolist()
        dests = df['adj_router'].dropna().unique().tolist()
    elif 'device_a' in df.columns and 'device_b' in df.columns:
        sources = df['device_a'].dropna().unique().tolist()
        dests = df['device_b'].dropna().unique().tolist()
    else:
        return []

    unique_devices = list(set(sources + dests))
    return [str(d).strip() for d in unique_devices if str(d).strip()]

def verify_devices_in_db(unique_devices: list) -> pd.DataFrame:
    """Checks the extracted unique devices against the active NDT node database."""
    verification_data = []
    total_devices = len(unique_devices)
    
    if total_devices > 0:
        progress_bar = st.progress(0, text="Initiating device verification...")
        
        for i, device in enumerate(unique_devices):
            progress_bar.progress((i) / total_devices, text=f"Verifying device: {device}")
            device_data = get_device_by_name(device)
            exists = device_data is not None
            
            device_uuid = "N/A"
            if exists and isinstance(device_data, dict):
                device_uuid = str(device_data.get('id', device_data.get('device_id', device_data.get('uuid', ''))))
            
            verification_data.append({
                "Hostname": device,
                "Device_ID": device_uuid,
                "Status": "✅ Verified" if exists else "❌ Not in database",
                "Exists": exists
            })
            
        progress_bar.empty()
        
    return pd.DataFrame(verification_data)

def verify_topology_ports(df_raw: pd.DataFrame, df_device_status: pd.DataFrame) -> pd.DataFrame:
    """Extracts unique ports, maps bandwidth, and checks database existence."""
    dev_id_map = dict(zip(df_device_status['Hostname'], df_device_status['Device_ID']))
    port_meta_map = {}
    
    for _, row in df_raw.iterrows():
        bw = row.get('bandwidth_kbps', 100000000) 
        dev_a, port_a = str(row.get('device_a', '')).strip(), str(row.get('port_a', '')).strip()
        dev_b, port_b = str(row.get('device_b', '')).strip(), str(row.get('port_b', '')).strip()
        
        if dev_a and port_a and dev_a != 'nan':
            if (dev_a, port_a) not in port_meta_map:
                alias = f"IS-IS Link to {dev_b} [{port_b}]" if dev_b and dev_b != 'nan' else "Auto-provisioned Interface"
                port_meta_map[(dev_a, port_a)] = {"speed": bw, "alias": alias}
                
        if dev_b and port_b and dev_b != 'nan':
            if (dev_b, port_b) not in port_meta_map:
                alias = f"IS-IS Link to {dev_a} [{port_a}]" if dev_a and dev_a != 'nan' else "Auto-provisioned Interface"
                port_meta_map[(dev_b, port_b)] = {"speed": bw, "alias": alias}
            
    port_data = []
    total_ports = len(port_meta_map)
    
    if total_ports > 0:
        progress_bar = st.progress(0, text="Initiating port verification...")
        for i, ((device, port), meta) in enumerate(port_meta_map.items()):
            progress_bar.progress((i) / total_ports, text=f"Verifying port: {device} [{port}]")
            port_id = resolve_port_id(device, port)
            exists = port_id is not None
            port_data.append({
                "Hostname": device, "Device_ID": dev_id_map.get(device),
                "Port": port, "Speed": meta["speed"], "Alias": meta["alias"],
                "Port_ID": port_id, "Status": "✅ Verified" if exists else "❌ Missing Port",
                "Exists": exists
            })
        progress_bar.empty()
        
    return pd.DataFrame(port_data)

# ==========================================
# 3. API ORCHESTRATORS (POST ACTIONS)
# ==========================================

def post_device_to_db(device_intent: dict) -> dict:
    """Strictly mapped payload for POST /devices/"""
    chassis_str = str(device_intent.get("chassis", "Unknown")).strip()
    pop_str = str(device_intent.get("pop", "Unknown")).strip()
    owner_str = str(device_intent.get("owner", "Unknown")).strip()
    
    clli_str = str(device_intent.get("clli_code", pop_str)).strip()
    loc_id = resolve_location_id(clli_str) or resolve_location_id(pop_str)

    payload = {
        "device_name": str(device_intent.get("hostname", "")).strip(),
        "device_role": str(device_intent.get("type", "EDGE")),
        "device_model": chassis_str,
        "device_vendor": determine_device_vendor(chassis_str), 
        "nos_version": "Unknown",
        "availability_zone": pop_str,
        "lifecycle_status": "Active",
        "planning_status": "Active",
        "health_status": 4,
        "network": determine_network_asn(owner_str),
        "location_id": loc_id, 
        "location": pop_str,
        "floor": "Unknown",
        "aisle": "Unknown",
        "rack": "Unknown",
        "device_description": f"Owner: {owner_str} | Auto-provisioned via Link Staging Gateway"
    }
    
    url = f"{API_URL}/devices/" 
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json() if response.status_code in [200, 201] else {}
    except Exception as e:
        print(f"Failed to post device to {url}: {e}")
        return {}

def post_device_port(port_intent: dict, status_override: str = "Active") -> dict:
    """Strictly mapped payload for POST /ports/{device_id}"""
    port_id = port_intent.get("port_id") or str(uuid.uuid4())
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
    
    url = f"{API_URL}/ports/{device_id}"
    try:
        response = requests.post(url, json=api_payload, timeout=5)
        return response.json() if response.status_code in [200, 201] else {}
    except Exception as e:
        print(f"Failed to post port to {url}: {e}")
        return {}

# ==========================================
# 4. BATCH LINK PROCESSING
# ==========================================

def add_bulk_process(adds, ctx):
    """
    Processes bulk additions for network links with canonical endpoint ordering.
    Prevents A<->B duplicate links by always sorting endpoint UUIDs before ingest.
    Seeds the link_health_status to 0 (Provisioning) to align with the telemetry engine.
    Flushes ingestion state and forces an instant UI refresh.
    """
    import streamlit as st
    from src.utils.api_network import post_network_link

    # Normalize input into list-of-dicts
    records = adds.to_dict(orient="records") if hasattr(adds, "to_dict") else adds

    success_count = 0
    error_count = 0

    for row in records:
        # Extract raw port IDs
        a_raw = str(row.get("a_port_id", "")).strip()
        b_raw = str(row.get("b_port_id", "")).strip()

        # Skip invalid rows
        if not a_raw or not b_raw:
            print(f"Skipping row with missing ports: {row}")
            error_count += 1
            continue

        # ⭐ CANONICAL ORDERING — THE FIX ⭐
        endpoint_a, endpoint_b = sorted([a_raw, b_raw])

        payload = {
            "endpoint_a": endpoint_a,
            "endpoint_a_type": "port",
            "endpoint_b": endpoint_b,
            "endpoint_b_type": "port",
            "link_type": str(row.get("link_type", "Intra-Pop")),
            "description": str(row.get("description", "")),
            "channel": int(row.get("channel", 64)),
            "frequency": float(row.get("frequency", 0.0)),
            "link_health_status": 0  # <--- Seeds explicitly to 'Provisioning / Planning'
        }

        try:
            result = post_network_link(payload)
            if result:
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"Bulk Link API Exception on row: {e}")
            error_count += 1

    # UI + state refresh
    if success_count > 0:
        st.toast(f"✅ Successfully provisioned {success_count} links.", icon="✅")

        if "FabricStateManager" not in st.session_state:
            st.session_state["FabricStateManager"] = {}
        st.session_state["FabricStateManager"]["links_stale"] = True

        st.session_state[f"{ctx}_df"] = None
        st.session_state[f"{ctx}_preview"] = None
        st.session_state[f"{ctx}_verified"] = False
        st.session_state[f"{ctx}_file_id"] = None

        st.cache_data.clear()
        st.rerun()

    if error_count > 0:
        st.toast(f"⚠️ Failed to provision {error_count} links.", icon="⚠️")

def update_bulk_process(upds, ctx):
    """Placeholder for link bulk updates."""
    import streamlit as st
    st.toast("Update link logic coming online soon.", icon="🛠️")
def update_bulk_process(upds, ctx):
    """Placeholder for link bulk updates."""
    st.toast("Update link logic coming online soon.", icon="🛠️")

def delete_bulk_process(rows, ctx):
    """Processes DELETE operations."""
    success_count = 0
    df_temp = st.session_state[f"{ctx}_preview"].copy()
    existing_links = get_network_links_detail() or []
    link_id_map = {l.get('link_id'): l for l in existing_links if l.get('link_id')}
    
    for row in rows:
        ln_id = row.get("Link_ID")
        idx_list = df_temp.index[df_temp['Link_ID'] == ln_id].tolist() if ln_id else []
        if not link_id_map.get(ln_id):
            for i in idx_list: df_temp.at[i, 'Status'] = "❌ not found"
            continue

        if delete_network_link(ln_id):
            success_count += 1
            for i in idx_list: df_temp.at[i, 'Status'] = "✅ Success"
        else:
            for i in idx_list: df_temp.at[i, 'Status'] = "❌ Error"

    st.session_state[f"{ctx}_preview"] = df_temp
    if 'FabricStateManager' in st.session_state: st.session_state['FabricStateManager']['links_stale'] = True
    return success_count

def build_preview_dataframe(df_norm, existing_links):
    """Enriches CSV data with UUIDs using O(1) hash map lookups."""
    preview_data = []
    link_map = {}
    
    if existing_links:
        for link in existing_links:
            a_id, b_id = link.get('a_port_id'), link.get('b_port_id')
            if a_id and b_id:
                link_map[(a_id, b_id)], link_map[(b_id, a_id)] = link, link 
    
    for _, row in df_norm.iterrows():
        dev_a, port_a = str(row.get('device_a', '')).strip(), str(row.get('port_a', '')).strip()
        dev_b, port_b = str(row.get('device_b', '')).strip(), str(row.get('port_b', '')).strip()
        
        id_a, id_b = resolve_port_id(dev_a, port_a), resolve_port_id(dev_b, port_b)
        match = link_map.get((id_a, id_b))

        status = "❌ Missing Port" if not id_a or not id_b else ("✅ Link verified" if match else "🔍 link not found")
        found_link_id = match.get('link_id') if match else None

        preview_data.append({
            "Action": str(row.get('Action', 'ADD')).upper(), 
            "Status": status, "device_a": dev_a, "port_a": port_a, "a_port_id": id_a,  
            "device_b": dev_b, "port_b": port_b, "b_port_id": id_b,  
            "link_type": str(row.get('link_type', 'Physical')), "channel": row.get('channel', 0),
            "frequency": row.get('frequency', 0.0), "description": str(row.get('description', '')),
            "Link_ID": found_link_id
        })
        
    return pd.DataFrame(preview_data)

# ==========================================
# 5. UI VIEWS & DASHBOARDS
# ==========================================

def render_verification_gateway(df_raw: pd.DataFrame, ctx: str) -> bool:
    """
    Renders the Node & Port Verification UI with inline auto-provisioning mechanics.
    Performs a bidirectional sweep to guarantee the staging table populates correctly.
    """
    import streamlit as st
    import pandas as pd
    from src.ui_components import UI
    
    # ==========================================
    # PHASE 1: NODE VERIFICATION
    # ==========================================
    st.write("### 🔍 Phase 1: Node Verification")
    
    with st.spinner("Analyzing topology for unique nodes..."):
        unique_nodes = analyze_topology_devices(df_raw)
        
    if not unique_nodes:
        st.warning("No recognizable device columns found in the CSV.")
        return False

    with st.spinner("Cross-referencing NDT database..."):
        df_device_status = verify_devices_in_db(unique_nodes)
    
    st.dataframe(
        df_device_status[['Hostname', 'Device_ID', 'Status']], 
        use_container_width=True,
        hide_index=True
    )
    
    missing_devices = df_device_status[~df_device_status['Exists']]
    
    if not missing_devices.empty:
        st.error(f"⚠️ **Topology Integrity Block:** {len(missing_devices)} nodes required by this CSV do not exist.")
        
        # Robust Bidirectional Scanning for Staging Execution
        missing_hostnames = missing_devices['Hostname'].astype(str).str.strip().tolist()
        staging_rows = []
        raw_intents = [] # Tracks parameters for the inline post execution loop
        
        for host in missing_hostnames:
            host_upper = host.upper()
            
            # 1. Look for matches on the A-Side Naming Conventions
            a_match = df_raw[
                df_raw.get('router', pd.Series()).astype(str).str.strip().str.upper() == host_upper
            ]
            if a_match.empty:
                a_match = df_raw[
                    df_raw.get('device_a', pd.Series()).astype(str).str.strip().str.upper() == host_upper
                ]
                
            if not a_match.empty:
                r = a_match.iloc[0]
                chassis = str(r.get('chassis', 'Unknown')).strip()
                owner = str(r.get('owner', 'Unknown')).strip()
                pop = str(r.get('pop', 'Unknown')).strip()
                role = str(r.get('type', 'EDGE')).strip()
                
                staging_rows.append({
                    "device_name": host, "device_role": role, "device_model": chassis,
                    "device_vendor": determine_device_vendor(chassis), "availability_zone": pop,
                    "lifecycle_status": "Active", "planning_status": "Active", "health_status": 4,
                    "network": determine_network_asn(owner), "location": pop,
                    "floor": "Unknown", "aisle": "Unknown", "rack": "Unknown",
                    "device_description": "Auto-provisioned via Link Staging Gateway"
                })
                raw_intents.append({"hostname": host, "pop": pop, "type": role, "chassis": chassis, "owner": owner})
                continue
            
            # 2. Look for matches on the B-Side (Adjacent) Naming Conventions
            b_match = df_raw[
                df_raw.get('adj_router', pd.Series()).astype(str).str.strip().str.upper() == host_upper
            ]
            if b_match.empty:
                b_match = df_raw[
                    df_raw.get('device_b', pd.Series()).astype(str).str.strip().str.upper() == host_upper
                ]
                
            if not b_match.empty:
                r = b_match.iloc[0]
                chassis = str(r.get('adj_router_chassis', r.get('chassis', 'Unknown'))).strip()
                owner = str(r.get('adj_router_owner', r.get('owner', 'Unknown'))).strip()
                pop = str(r.get('pop', 'Unknown')).strip() 
                role = str(r.get('adj_router_type', r.get('type', 'EDGE'))).strip()
                
                staging_rows.append({
                    "device_name": host, "device_role": role, "device_model": chassis,
                    "device_vendor": determine_device_vendor(chassis), "availability_zone": pop,
                    "lifecycle_status": "Active", "planning_status": "Active", "health_status": 4,
                    "network": determine_network_asn(owner), "location": pop,
                    "floor": "Unknown", "aisle": "Unknown", "rack": "Unknown",
                    "device_description": "Auto-provisioned via Link Staging Gateway"
                })
                raw_intents.append({"hostname": host, "pop": pop, "type": role, "chassis": chassis, "owner": owner})

        staged_nodes = pd.DataFrame(staging_rows)
        st.session_state["pending_provisioning"] = staged_nodes
        
        st.write("#### 📋 Staging Table: Missing Node Details")
        if not staged_nodes.empty:
            st.dataframe(staged_nodes, use_container_width=True)
            
            # Injected Inline Provisioning Action Button
            if UI.button(f"➕ Auto-Provision {len(staged_nodes)} Missing Nodes", color="green", key=f"{ctx}_inline_prov_nodes"):
                with st.spinner("Executing direct node provisioning sequence..."):
                    for intent in raw_intents:
                        post_device_to_db(intent)
                st.cache_data.clear()
                st.rerun()
        else:
            st.warning("Could not extract row details for the missing nodes. Verify CSV column formatting.")
            
        if 'FabricStateManager' in st.session_state: 
            st.session_state['FabricStateManager']['topology_ready'] = False
        return False 
    else:
        st.success("✅ All topology nodes verified.")

    # ==========================================
    # PHASE 1.5: PORT VERIFICATION & PROVISIONING
    # ==========================================
    st.divider()
    st.write("### 🔌 Phase 1.5: Port Verification")
    with st.spinner("Analyzing required interfaces..."):
        df_port_status = verify_topology_ports(df_raw, df_device_status)
        
    if df_port_status.empty: 
        return True

    st.dataframe(df_port_status[['Hostname', 'Port', 'Speed', 'Alias', 'Status']], use_container_width=True, hide_index=True)
    missing_ports = df_port_status[~df_port_status['Exists']]
    
    if not missing_ports.empty:
        st.warning(f"⚠️ {len(missing_ports)} interfaces missing from database.")
        if UI.button(f"➕ Auto-Provision {len(missing_ports)} Missing Ports", color="blue", key=f"{ctx}_prov_ports"):
            with st.spinner("Provisioning missing interfaces..."):
                for _, row in missing_ports.iterrows():
                    intent = {
                        "device_id": row["Device_ID"], "port": row["Port"],
                        "speed": row.get("Speed", 100000000), "alias": row.get("Alias", "Auto-provisioned Interface"),
                        "admin_status": "up", "port_health_status": 1
                    }
                    post_device_port(intent)
                st.cache_data.clear()
                st.rerun()
                
        if 'FabricStateManager' in st.session_state: 
            st.session_state['FabricStateManager']['topology_ready'] = False
        return False
    else:
        st.success("✅ All topology interfaces verified in database. Ready for Link Stitching.")
        if 'FabricStateManager' in st.session_state: 
            st.session_state['FabricStateManager']['topology_ready'] = True
        return True

def deduplicate_staging_links(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicates network links in a DataFrame by treating A->B and B->A as identical paths.
    Creates a canonical sorted key for each link and drops duplicates based on that key.
    """
    import pandas as pd
    
    if df is None or df.empty:
        return df
        
    # Create a copy to avoid SettingWithCopyWarning
    df_clean = df.copy()
    
    def generate_canonical_key(row):
        # Format: "DEVICE::PORT" - fallback to empty strings to prevent sorting errors
        a_side = f"{row.get('device_a', '')}::{row.get('port_a', '')}".upper()
        b_side = f"{row.get('device_b', '')}::{row.get('port_b', '')}".upper()
        
        # Sorting guarantees A->B and B->A produce the exact same tuple
        return tuple(sorted([a_side, b_side]))
        
    # Apply the canonical key, drop duplicates keeping the first occurrence, then clean up
    df_clean['_canonical_key'] = df_clean.apply(generate_canonical_key, axis=1)
    df_clean = df_clean.drop_duplicates(subset=['_canonical_key'], keep='first')
    df_clean = df_clean.drop(columns=['_canonical_key'])
    
    # Reset index to ensure clean Row_IDs later
    return df_clean.reset_index(drop=True)


def render_node_provisioning_dashboard():
    """Unified Node Provisioning Dashboard."""
    st.subheader("🚀 Bulk Node Provisioning")
    if "provisioning_log" not in st.session_state: st.session_state["provisioning_log"] = pd.DataFrame(columns=["Hostname", "Status", "Message"])
    
    pending_df = st.session_state.get("pending_provisioning")
    if pending_df is not None and not pending_df.empty:
        st.success("✅ Staging data found from previous analysis.")
        if st.button("📥 Load Staged Data into Form"):
            st.session_state["node_input_text"] = "\n".join(pending_df['device_name'].astype(str).tolist())
            st.rerun()

    with st.expander("➕ Add Missing Nodes", expanded=True):
        raw_input = st.text_area("Paste hostnames to provision:", value=st.session_state.get("node_input_text", ""), key="node_input_text")
        pop_default = st.text_input("Default PoP/Site ID", value="PHX")
        
        if st.button("🚀 Execute Batch Provisioning", type="primary"):
            hostnames = [h.strip() for h in raw_input.split('\n') if h.strip()]
            for host in hostnames:
                # If staged data exists, use it. Otherwise rely on defaults.
                row_intent = {"hostname": host, "pop": pop_default, "type": "EDGE", "chassis": "MX480", "owner": "QCC"}
                if pending_df is not None and host in pending_df['device_name'].values:
                    match_row = pending_df[pending_df['device_name'] == host].iloc[0]
                    row_intent = match_row.to_dict()
                    row_intent['hostname'] = host # Map device_name back to hostname for the orchestrator
                    
                with st.status(f"Provisioning {host}...", expanded=False) as s:
                    result = post_device_to_db(row_intent)
                    if result:
                        new_row = {"Hostname": host, "Status": "✅ Success", "Message": "Provisioned"}
                        s.update(label=f"Provisioned {host}", state="complete", expanded=False)
                    else:
                        new_row = {"Hostname": host, "Status": "❌ Failed", "Message": "API Error"}
                        s.update(label=f"Failed {host}", state="error", expanded=False)
                    
                    st.session_state["provisioning_log"] = pd.concat([st.session_state["provisioning_log"], pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

    st.write("### 📋 Provisioning Status History")
    if not st.session_state["provisioning_log"].empty:
        st.dataframe(st.session_state["provisioning_log"], use_container_width=True, hide_index=True)
        if st.button("🧹 Clear Log"):
            st.session_state["provisioning_log"] = pd.DataFrame(columns=["Hostname", "Status", "Message"])
            st.rerun()
    else:
        st.info("No provisioning history found.")

def render_netlink_view():
    """Main UI View for Netlink operations."""
    import streamlit as st
    import pandas as pd
    import time

    st.title("🌐 Netlink Connection Manager")
    MessageHandler.render(key_suffix="nl_view")
    
    ctx = "nl_v21" 
    if f"{ctx}_verified" not in st.session_state: st.session_state[f"{ctx}_verified"] = False
    if f"{ctx}_preview" not in st.session_state: st.session_state[f"{ctx}_preview"] = None

    def clear_staging():
        st.session_state[f"{ctx}_df"], st.session_state[f"{ctx}_preview"], st.session_state[f"{ctx}_verified"], st.session_state[f"{ctx}_file_id"] = None, None, False, None

    db_links = get_network_links_detail() or []

    st.subheader("📥 Bulk Ingestion")
    uploaded_file = st.file_uploader("Upload Network Link CSV", type=["csv"], key=f"{ctx}_uploader")

    if uploaded_file:
        if st.session_state.get(f"{ctx}_file_id") != uploaded_file.file_id:
            df_raw = pd.read_csv(uploaded_file)
            df_raw.columns = [c.lower().strip() for c in df_raw.columns]
            
            df_raw = df_raw.dropna(how='all')
            df_raw = df_raw.dropna(subset=['router']) if 'router' in df_raw.columns else df_raw.dropna(subset=['device_a'])
            
            preview_init = df_raw.copy()
            
            if 'router' in preview_init.columns:
                preview_init['device_a'], preview_init['port_a'] = preview_init['router'], preview_init['isis_interface']
                preview_init['device_b'], preview_init['port_b'] = preview_init['adj_router'], preview_init['adj_interface']
                preview_init['link_type'] = preview_init.apply(lambda r: determine_link_type(r.get('device_a'), r.get('device_b')), axis=1)
                preview_init['description'] = preview_init.apply(lambda r: f"{r.get('device_a')}.{r.get('port_a')}::{r.get('device_b')}.{r.get('port_b')}", axis=1)
                preview_init['channel'], preview_init['frequency'] = 64, 0.0

            preview_init['Action'] = preview_init['action'].str.upper() if 'action' in preview_init.columns else "ADD"
            preview_init['Status'], preview_init['Link_ID'] = "⚪ Not Verified", None
            
            st.session_state[f"{ctx}_df"], st.session_state[f"{ctx}_file_id"], st.session_state[f"{ctx}_preview"], st.session_state[f"{ctx}_verified"] = preview_init, uploaded_file.file_id, preview_init, False

        if st.session_state.get(f"{ctx}_df") is not None:
            if not render_verification_gateway(st.session_state[f"{ctx}_df"], ctx): st.stop() 

        # ==========================================
        # PHASE 2: LINK STITCHING (With Progress)
        # ==========================================
        st.write("### 🔗 Phase 2: Link Stitching")
        c_v1, c_v2 = st.columns([1, 3])
        with c_v1:
            if UI.button("🔍 Verify Link Logic", color="orange", key="btn_verify"):
                raw_df = st.session_state.get(f"{ctx}_df")
                
                if raw_df is not None:
                    total_links = len(raw_df)
                    if total_links > 0:
                        stitch_pb = st.progress(0, text="Initiating link stitching verification...")
                        
                        for i, row in raw_df.iterrows():
                            a_dev = row.get("device_a", "Unknown")
                            z_dev = row.get("device_b", "Unknown")
                            stitch_pb.progress(i / total_links, text=f"Stitching Path: {a_dev} ↔ {z_dev}")
                            time.sleep(0.02) # Brief buffer for smooth UI rendering
                            
                        stitch_pb.progress(1.0, text="Finalizing preview matrix...")
                        
                        # Execute the core batch build logic
                        st.session_state[f"{ctx}_preview"] = build_preview_dataframe(raw_df, db_links)
                        stitch_pb.empty()
                
                st.session_state[f"{ctx}_verified"] = True
                st.rerun()
        
        # ==========================================
        # PHASE 3: DB INSERTION (With Progress)
        # ==========================================
        df_preview = st.session_state.get(f"{ctx}_preview")
        if df_preview is not None and st.session_state.get(f"{ctx}_verified"):
            st.write("### ⚡ Link DB Insertion")
            c1, c2, c3, c4 = st.columns(4)
            adds = df_preview[df_preview['Action'] == 'ADD'].to_dict('records')
            upds = df_preview[df_preview['Action'] == 'UPDATE'].to_dict('records')
            dels = df_preview[df_preview['Action'] == 'DELETE'].to_dict('records')

            with c1:
                if len(adds) > 0 and UI.button(f"➕ Add ({len(adds)})", color="green", key="b_add"):
                    pb = st.progress(0, text="Staging additions...")
                    for i, row in enumerate(adds):
                        desc = row.get("description", f"Link Index {i}")
                        pb.progress(i / len(adds), text=f"Preparing Add: {desc}")
                        time.sleep(0.01)
                    pb.progress(1.0, text="Committing additions to database...")
                    add_bulk_process(adds, ctx)
                    pb.empty()

            with c2:
                if len(upds) > 0 and UI.button(f"🔄 Update ({len(upds)})", color="blue", key="b_upd"):
                    pb = st.progress(0, text="Staging updates...")
                    for i, row in enumerate(upds):
                        desc = row.get("description", f"Link Index {i}")
                        pb.progress(i / len(upds), text=f"Preparing Update: {desc}")
                        time.sleep(0.01)
                    pb.progress(1.0, text="Committing updates to database...")
                    update_bulk_process(upds, ctx)
                    pb.empty()
                    st.rerun()

            with c3:
                if len(dels) > 0 and UI.button(f"🗑️ Delete ({len(dels)})", color="red", key="b_del"):
                    pb = st.progress(0, text="Staging deletions...")
                    for i, row in enumerate(dels):
                        desc = row.get("description", f"Link Index {i}")
                        pb.progress(i / len(dels), text=f"Preparing Delete: {desc}")
                        time.sleep(0.01)
                    pb.progress(1.0, text="Committing deletions to database...")
                    delete_bulk_process(dels, ctx)
                    pb.empty()
                    st.rerun()

            with c4:
                if UI.button("🧹 Clear", key="btn_clear"): 
                    clear_staging()
                    st.rerun()

            st.divider()
            st.subheader("📋 Preview Staging Table")
            df_preview['Row_ID'] = df_preview.index.astype(str)
            display_cols = ["Action", "Status", "link_type", "device_a", "port_a", "a_port_id", "device_b", "port_b", "b_port_id", "channel", "frequency", "description", "Link_ID", "Row_ID"]
            available_cols = [c for c in display_cols if c in df_preview.columns]
            UI.render_selectable_table(df_preview[available_cols], f"{ctx}_table", "Row_ID")

    st.divider()
    st.subheader("🗄️ Active Netlink Inventory")
    if db_links:
        df_active = pd.DataFrame(db_links)
        df_active['Source'] = df_active['a_device_name'] + " [" + df_active['a_port_name'] + "]"
        df_active['Dest'] = df_active['b_device_name'] + " [" + df_active['b_port_name'] + "]"
        cols = ["Source", "Dest", "link_type", "channel", "frequency", "link_id"]
        selection = UI.render_selectable_table(df_active[cols], "active_inv", "link_id")
        if selection and UI.button("🗑️ Delete Selected", color="red", key="del_one"):
            if delete_network_link(selection['link_id']): 
                st.toast("Deleted")
                st.rerun()
    else:
        st.info("No active network links found.")