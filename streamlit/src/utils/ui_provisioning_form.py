from plotly import data
import streamlit as st
import pandas as pd
import random
import ipaddress
from src.api_client import get_all_devices, get_ports_by_device, get_fabric_services


def _execute_pattern_ui(payload: dict, a_table: str, b_table: str, label: str):
    import streamlit as st
    import pandas as pd
    
    live = st.session_state.live_manifest
    children = payload.get("service_context", {}).get("children", {})
    
    # Helper to fetch data based on table name
    def get_options(table_name):
        if table_name == "ports":
            return {f"Port: {p['port_name']}": p['port_id'] for p in live.get("fabric_ports", [])}
        if table_name == "interfaces":
            return {f"Intf: {i['interface_name']}": i['interface_id'] for i in live.get("fabric_interfaces", [])}
        if table_name == "cloud_connections":
            return {f"Cloud: {c['connection_name']}": c['cloud_connection_id'] for c in live.get("cloud_connections", [])}
        return {}

    a_options = get_options(a_table)
    b_options = get_options(b_table)

    if not a_options or not b_options:
        st.warning(f"⚠️ Prerequisites for {label} missing in the Live Manifest.")
        return

    with st.container(border=True):
        st.caption(f"Pattern: **{label}**")
        c1, c2 = st.columns(2)
        
        side_a = c1.selectbox(f"Select {a_table.title()}", options=list(a_options.keys()), key="side_a")
        # Filter Z-side only if tables are the same (E-Line case)
        z_options = [k for k in b_options.keys() if b_options[k] != a_options.get(side_a)] if a_table == b_table else list(b_options.keys())
        side_b = c2.selectbox(f"Select {b_table.title()}", options=z_options, key="side_b")
        
        conn_name = st.text_input("Connection Name", value=f"CX-{payload.get('service_context', {}).get('service_type')}")

        if st.button("🔗 Queue Fabric Connection", use_container_width=True, type="primary"):
            new_conn = {
                "service_id": payload.get("service_id"),
                "connection_name": conn_name.strip(),
                "connector_a_id": a_options[side_a],
                "connector_a_table": a_table,
                "connector_b_id": b_options[side_b],
                "connector_b_table": b_table,
                "service_bw": 1000,
                "connection_status": "Planned"
            }
            children.setdefault("fabric_connections", []).append(new_conn)
            st.toast("Fabric connection staged.")
            st.rerun()

def add_port_to_queue_callback():
    """
    Logic: Executes BEFORE the UI reruns. 
    Updates the master JSON and hydrates the Success Message.
    """
    import streamlit as st
    from src.api_client import get_ports_by_device

    # 1. Path Safety - Ensure the nested JSON structure is ready
    if "payload" not in st.session_state:
        return
    
    ctx = st.session_state.payload.setdefault("service_context", {})
    children = ctx.setdefault("children", {})
    ports_list = children.setdefault("ports", [])

    # 2. Get Selection Data from Widget Keys
    target_dev = st.session_state.get("f_dev")
    sel_port = st.session_state.get("f_port")
    all_devices = st.session_state.get("all_devices_cache")

    if target_dev and sel_port and all_devices:
        try:
            # 3. Hydrate IDs and Technical Specs from Cache/API
            dev_rec = next(d for d in all_devices if d['device_name'] == target_dev)
            ports_df = get_ports_by_device(dev_rec['device_id'])
            port_rec = ports_df[ports_df['port_name'] == sel_port].iloc[0].to_dict()

            # 4. Construct the Port Object
            new_port = {
                "port_id": str(port_rec['port_id']),
                "device_id": str(port_rec['device_id']),
                "device": target_dev,
                "port": sel_port,
                "speed": st.session_state.get("f_spd"),
                "optics": st.session_state.get("f_opt"),
                "alias": st.session_state.get("f_alias") or f"{target_dev}:{sel_port}",
                "status": "Staged",
                "admin_status": st.session_state.get("f_admin", "Up").lower()
            }

            # 5. Commit to Master Payload
            st.session_state.payload["service_context"]["children"]["ports"].append(new_port)
            st.session_state.port_success_msg = f"Port {sel_port} added to manifest."
            
        except Exception as e:
            st.error(f"Hydration Error: {str(e)}")

def render_fabric_port_form(fs_detail: dict, namespace: str = "wizard"):
    """
    Renders the physical port configuration form.
    Optimized to centralize business rules, tagging, and COS classification logic.
    Includes an escape hatch to bypass provisioning and move to the next step.
    """
    import streamlit as st
    import pandas as pd
    import datetime
    from src.utils.api_customer import get_all_devices, get_ports_by_device
    from src.utils.ui_provisioning_form import get_optics_options

    # --- 1. CONTEXT & CAPACITY ENGINE ---
    svc_id = fs_detail.get("service_id")
    svc_type = str(fs_detail.get("service_type", "IPVPN")).upper().replace("EPLAN", "EP-LAN").replace("EVP-LLAN", "EVP-LAN")
    
    # Isolation: Only ports assigned to THIS specific service count toward live capacity
    live_ports = [p for p in fs_detail.get("fabric_ports", []) if svc_id in (p.get("fabric_service_ids") or [])]
    
    # Staging Queue
    payload = st.session_state.setdefault("payload", {"service_context": {"children": {"ports": []}}})
    ports_manifest = payload["service_context"]["children"].setdefault("ports", [])
    
    total_ports = len(live_ports) + len(ports_manifest)

    # --- THE CENTRALIZED RULE ENGINE ---
    rule_map = {
        "IPVPN":   {"max": 1, "tags": ["Untagged/Single Service", "Tagged / MultiService "], "cap": "L3 Attachment: 1 handoff per site.", "cos": ["6Q DSCP", "6Q 802.1p"]},
        "MCGW":    {"max": 1, "tags": ["Untagged/Single Service", "Tagged / MultiService "], "cap": "Cloud Gateway: 1 handoff per site.", "cos": ["6Q DSCP", "6Q 802.1p"]},
        "EPL":     {"max": 2, "tags": ["All-2-1-bundled"], "cap": "Point-to-Point: Exactly 2 symmetric ports.", "cos": ["Single Service BE", "Single Service Dedicate"]},
        "EVPL":    {"max": 50, "tags": ["All-2-1-bundled", "Tagged / MultiService "], "cap": "Virtual: Up to 50 ports (Tagged).", "cos": ["Single Service BE", "Single Service Dedicate"]},
        "EP-LAN":  {"max": 50, "tags": ["All-2-1-bundled"], "cap": "Multipoint: Up to 50 ports (Bundled).", "cos": ["6Q DSCP", "6Q 802.1p", "3Q DSCP", "3Q 802.1p", "Single Service BE", "Single Service Dedicate"]},
        "EVP-LAN": {"max": 50, "tags": ["All-2-1-bundled", "Tagged / MultiService "], "cap": "Virtual Multipoint: Up to 50 ports.", "cos": ["6Q DSCP", "6Q 802.1p", "3Q DSCP", "3Q 802.1p", "Single Service BE", "Single Service Dedicate"]},
        "IOD":     {"max": 1, "tags": ["Untagged/Single Service", "Tagged / MultiService "], "cap": "Internet on Demand: 1 handoff per site.", "cos": ["Single Service BE"]}
    }
    
    # Safety fallback
    default_rule = {"max": 1, "tags": ["Untagged/Single Service"], "cap": "Standard Attachment.", "cos": ["Single Service BE"]}
    current_rule = rule_map.get(svc_type, default_rule)
    is_locked = total_ports >= current_rule["max"]

    # --- 2. HARDWARE DISCOVERY ---
    all_devices = get_all_devices()
    target_devs = [d['device_name'] for d in all_devices if d.get('device_role') in ["VAR", "ES"]]

    # --- 3. UI: CONFIGURATION FORM ---
    with st.container(border=True):
        st.subheader(f"✨ Configure Physical Port: {fs_detail.get('service_name')}")
        st.caption(current_rule["cap"])
        
        # --- BILLING & PRICING INFO ---
        st.info("""
        ℹ️ **Billing & Activation:** The port will start billing once the port status is **Active**, or on the scheduled **Port Activation Date** (the port will automatically become active on this assigned date).
        
        **Port Charges (MRC):**
        * **1G:** $500
        * **10G:** $800
        * **100G:** $1,200
        * **400G:** $1,500
        """)
        
        if is_locked:
            st.info(f"ℹ️ Capacity reached ({current_rule['max']} ports). Move to the next step or clear the queue.")

        l, r = st.columns(2)
        with l:
            target_dev = st.selectbox("1️⃣ Host Device", options=target_devs, key=f"f_dev_{namespace}", disabled=is_locked)
            
            # Nested Data Fetch
            dev_rec = next((d for d in all_devices if d['device_name'] == target_dev), None)
            ports_df = get_ports_by_device(dev_rec['device_id']) if dev_rec else pd.DataFrame()
            
            speeds = sorted(ports_df['port_speed'].unique().tolist()) if not ports_df.empty else ["Unknown"]
            sel_speed = st.radio("2️⃣ Speed", options=speeds, horizontal=True, key=f"f_spd_{namespace}", disabled=is_locked)
            
            filtered_ports = ports_df[ports_df['port_speed'] == sel_speed] if not ports_df.empty else pd.DataFrame()
            avail_ports = filtered_ports['port_name'].tolist() if not filtered_ports.empty else ["No Ports Found"]
            st.selectbox("3️⃣ Available Ports", options=avail_ports, key=f"f_port_{namespace}", disabled=is_locked)

        with r:
            st.text_input("Alias", placeholder="e.g., SITE-A-Handoff", key=f"f_alias_{namespace}", disabled=is_locked)
            st.radio("🔦 Optics", options=get_optics_options(sel_speed), horizontal=True, key=f"f_opt_{namespace}", disabled=is_locked)
            
            # Tagging: Pulled directly from the centralized rule map
            tag_options = current_rule["tags"]
            selected_tag = st.radio("🏷️ Tagging", options=tag_options, key=f"f_tag_{namespace}", disabled=is_locked or len(tag_options) == 1)
            
            # --- DYNAMIC COS CLASSIFICATION LOGIC ---
            cos_options = current_rule.get("cos", [])
            
            if cos_options:
                # Determine if the physical port lacks a VLAN header
                is_untagged = "Untagged" in selected_tag or "All-2-1-bundled" in selected_tag
                
                # Rule: 802.1p strictly requires a VLAN tag. If untagged, filter those options out.
                if is_untagged:
                    filtered_cos = [cos for cos in cos_options if "802.1p" not in cos]
                    help_txt = "Untagged/Bundled ports cannot support 802.1p classification." if len(filtered_cos) < len(cos_options) else None
                else:
                    filtered_cos = cos_options
                    help_txt = None
                    
                st.radio(
                    "🚦 COS Classification", 
                    horizontal=True,
                    options=filtered_cos, 
                    key=f"f_cos_{namespace}", 
                    disabled=is_locked or len(filtered_cos) == 1,
                    help=help_txt
                )
            
            st.radio("Admin Status", ["Up", "Down"], horizontal=True, key=f"f_admin_{namespace}", disabled=is_locked)
            
            # Date Picker defaulting to today
            st.date_input("📅 Delivery Date", value=datetime.date.today(), key=f"f_date_{namespace}", disabled=is_locked)

        st.divider()

        # --- 4. ACTION LOGIC ---
        c_add, c_skip = st.columns(2)
        
        with c_add:
            if not is_locked:
                if st.button("➕ Add Port to Queue", type="primary", use_container_width=True, key=f"btn_add_{namespace}"):
                    if dev_rec and not filtered_ports.empty:
                        selected_port_name = st.session_state[f"f_port_{namespace}"]
                        port_rec = filtered_ports[filtered_ports['port_name'] == selected_port_name].iloc[0]
                        
                        # Mapping tag display to DB value
                        tag_db_map = {"Untagged/Single Service": "Untagged", "Tagged / MultiService ": "Tagged"}
                        raw_tag = st.session_state[f"f_tag_{namespace}"]
                        
                        new_port = {
                            "port_id": str(port_rec['port_id']),
                            "device_id": str(port_rec['device_id']),
                            "device": target_dev,
                            "port": selected_port_name,
                            "speed": sel_speed,
                            "optics": st.session_state[f"f_opt_{namespace}"],
                            "port_tagging": tag_db_map.get(raw_tag, raw_tag),
                            "alias": st.session_state[f"f_alias_{namespace}"] or f"{target_dev}:{selected_port_name}",
                            "status": "Staged",
                            "admin_status": st.session_state[f"f_admin_{namespace}"].lower(),
                            "delivery_date": str(st.session_state[f"f_date_{namespace}"])
                        }
                        
                        # Append the COS classification if present
                        cos_val = st.session_state.get(f"f_cos_{namespace}")
                        if cos_val:
                            new_port["cos_classification"] = cos_val
                            
                        st.session_state.payload["service_context"]["children"]["ports"].append(new_port)
                        st.rerun()
            else:
                if st.button("🗑️ Clear Local Staging Queue", type="secondary", use_container_width=True, key=f"btn_clear_{namespace}"):
                    st.session_state.payload["service_context"]["children"]["ports"] = []
                    st.rerun()

        with c_skip:
            # Escape Hatch: Move to Step 3 (Logic/Interfaces) without forcing a port commit
            if st.button("⏭️ Skip to Logic / Next Step", type="secondary", use_container_width=True, key=f"btn_skip_{namespace}"):
                st.session_state.prov_step = 3
                st.rerun()

    # --- 5. MANIFEST VIEW ---
    st.subheader(f"📋 Staging Manifest ({len(ports_manifest)} ports queued)")
    if ports_manifest:
        st.data_editor(pd.DataFrame(ports_manifest), use_container_width=True, hide_index=True, key=f"sync_{namespace}")

def on_service_type_change():
    """
    Callback triggered when the 'Type' dropdown changes.
    Ensures state is synchronized before the next render cycle.
    Updated to use 'service_context' instead of 'vrf'.
    """
    selected_type = st.session_state.service_type_selector
    
    # Initialize service_context if not present
    if "payload" in st.session_state:
        if selected_type == "MCGW":
            st.session_state.payload["service_context"]["type"] = "MCGW"
            st.session_state.payload["service_context"]["flavor"] = "Full"
        else:
            st.session_state.payload["service_context"]["type"] = selected_type
            st.session_state.payload["service_context"]["flavor"] = ""
            
def on_flavor_change():
    """
    Syncs the MCGW flavor (Full/Limited).
    Automatically triggers a rerun to update Reference Architecture.
    """
    new_flavor = st.session_state.mcgw_flavor_selector
    if "payload" in st.session_state:
        st.session_state.payload["service_context"]["flavor"] = new_flavor
        
    # =====================================================================
    # 1. SERVICE-SPECIFIC SUB-METHODS (The Customization Zones)
    # =====================================================================

def _render_ipvpn_context(data: dict, is_existing: bool, c_col):
    """Specific fields for Layer 3 IP-VPN."""
    data['type'] = "IPVPN"  
    
    if is_existing:
        c_col.text_input("Route Target", value=data.get('rt', ''), disabled=True) 
    else:
        if not data.get('rt') or data.get('rt') == "3549:10000":
            data['rt'] = f"3549:100{random.randint(1000, 9999)}"
        data['rt'] = c_col.text_input("Route Target", value=data.get('rt'), key="svc_rt_input")

def _render_mcgw_context(data: dict, is_existing: bool, c_col):
    """Specific fields for Multi-Cloud Gateway."""
    import streamlit as st
    import random
    
    data['type'] = "MCGW"  
    
    if is_existing:
        c_col.text_input("Route Target", value=data.get('rt', ''), disabled=True) 
    else:
        if not data.get('rt') or data.get('rt') == "3549:10000":
            data['rt'] = f"3549:100{random.randint(1000, 9999)}"
        data['rt'] = c_col.text_input("Route Target", value=data.get('rt'), key="svc_mcgw_rt_input")
    
    if not is_existing:
        st.divider()
        st.markdown("##### ⚙️ MCGW Specifications")
        c1, c2 = st.columns(2)
        
        # 1. Render the Flavor selector first
        data['flavor'] = c1.radio("MCGW Flavor", ["Full", "Limited"], horizontal=True, key="mcgw_flavor_selector")
        
        # 2. Conditionally render the Service BW selector and corresponding pricing
        if data['flavor'] == "Full":
            data['mcgw_bw'] = c2.radio("Service BW", ["10G", "20G", "Unlimited"], horizontal=True, key="mcgw_bw_selector")
            
            # Dynamic pricing info for Full Flavor
            if data['mcgw_bw'] == "10G":
                st.info("ℹ️ **Pricing:** 10G Full MCGW is $1,000 / MRC")
            elif data['mcgw_bw'] == "20G":
                st.info("ℹ️ **Pricing:** 20G Full MCGW is $1,500 / MRC")
            elif data['mcgw_bw'] == "Unlimited":
                st.info("ℹ️ **Pricing:** Unlimited Full MCGW is $2,000 / MRC")
                
        else:
            # Clear out the bandwidth data if "Limited" is selected so it doesn't submit stale data
            data['mcgw_bw'] = None
            
            # Pricing info for Limited Flavor
            st.info("ℹ️ **Pricing:** There is no charge for the Limited bandwidth MCGW. MCGW is limted to a single Port and a Single Cloud Connection, and does not support advanced features such as Dynamic Path Selection or Active/Active. This is ideal for customers who want the MCGW architecture but have a single primary workload in the cloud and want to minimize costs.")

        # 3. Global Billing Trigger Note
        st.info("⏳ **Billing Trigger:** MCGW billing wiil NOT start when you provision the MCGW .  Billing will start once a fabric connection or a cloud is attached to the MCGW.")

def _render_evpl_context(data: dict, is_existing: bool, c_col):
    """Specific fields for Ethernet Private Line (Port-Based)."""
    data['type'] = "EPL"  
    data['rt'] = ""       
    
    if not is_existing:
        st.divider()
        st.markdown("##### ⚙️ E-line EVPL Specifications")
        c1, c2 = st.columns(2)
        data['mtu'] = c1.selectbox("MTU Size", options=[1500, 9000], index=1, key="epl_mtu")
        data['sla'] = c2.selectbox("Class of Service", options=["Basic", "Enhanced", "Premium"], key="epl_sla")

def _render_epl_context(data: dict, is_existing: bool, c_col):
    """Specific fields for Ethernet Private Line (Port-Based)."""
    data['type'] = "EPL"  
    data['rt'] = ""       
    
    if not is_existing:
        st.divider()
        st.markdown("##### ⚙️ E-line EPL Specifications")
        c1, c2 = st.columns(2)
        data['mtu'] = c1.selectbox("MTU Size", options=[1500, 9000], index=1, key="epl_mtu")
        data['sla'] = c2.selectbox("Class of Service", options=["Premium"], key="epl_sla")

def _render_elan_context(data: dict, is_existing: bool):
    """Specific fields for E-LAN (Multipoint)."""
    import streamlit as st
    
    data['rt'] = ""
    
    # Set a default type if one isn't already present
    if 'type' not in data or data['type'] not in ["EP-LAN", "EVP-LAN"]:
        data['type'] = "EP-LAN"
    
    if not is_existing:
        st.divider()
        st.markdown("##### ⚙️ E-LAN Specifications")
        c1, c2 = st.columns(2)
        
        # --- 1. LAN Type Selection ---
        type_opts = ["EP-LAN", "EVP-LAN"]
        type_idx = type_opts.index(data['type']) if data['type'] in type_opts else 0
        
        data['type'] = c1.radio(
            "LAN Type", 
            options=type_opts, 
            index=type_idx,
            horizontal=True, 
            key="elan_type_selector"
        )
        
        # --- 2. Class of Service ---
        # THE FIX: Ensure these are strings wrapped in quotes!
        sla_opts = ["6Q-Multi-COS", "3Q-Multi-COS", "Basic", "Enhanced", "Premium"]
        
        # Determine index dynamically to preserve state. Default to "Basic" (index 2) if empty.
        sla_idx = sla_opts.index(data.get('sla', "Basic")) if data.get('sla') in sla_opts else 2
        
        data['sla'] = c2.radio(
            "Class of Service", 
            options=sla_opts, 
            index=sla_idx, 
            key="elan_sla_selector"
        )
        
        # --- 3. Multi-COS Templates & Policing Rules ---
        # THE FIX: Ensure quotes are here as well.
        if data['sla'] in ["6Q-Multi-COS", "3Q-Multi-COS"]:
            
            # Template Selector with state retention
            policy_opts = ["Premium+ Template", "Policed Premium+ Template"]
            policy_idx = policy_opts.index(data.get('premium_plus_policy', "Premium+ Template")) if data.get('premium_plus_policy') in policy_opts else 0
            
            data['premium_plus_policy'] = st.selectbox(
                "Multi-COS Template", 
                options=policy_opts,
                index=policy_idx,
                help="Classification protocol (DSCP/802.1p) will be assigned individually per port. This is assigned at the port based on the Customer requirement, tagging selection in the port form. Policing is applied at the E-LAN level, not per port.",
                key="elan_policy_selector"
            )
            
            # Dynamic Policy Rules & Policing Percentage
            if data['premium_plus_policy'] == "Policed Premium+ Template":
                st.info("ℹ️ **Policed Policy:** Premium+ tier traffic across this E-LAN will be strictly policed to a percentage of the total service bandwidth.")
                
                pct_opts = [10, 25]
                pct_idx = pct_opts.index(data.get('premium_plus_policing_pct', 10)) if data.get('premium_plus_policing_pct') in pct_opts else 0
                
                data['premium_plus_policing_pct'] = st.radio(
                    "Premium+ Egress Traffic Policing Limit",
                    options=pct_opts,
                    index=pct_idx,
                    format_func=lambda x: f"{x}% of Service BW",
                    horizontal=True,
                    key="elan_global_policing"
                )
            else:
                st.info("ℹ️ **Non-Policed Policy:** Premium+ tier traffic across this E-LAN allows up to 100% of the service bandwidth.")
                data['premium_plus_policing_pct'] = None
                
        else:
            # Clear out the template and policing data entirely if they select a standard SLA
            data['premium_plus_policy'] = None
            data['premium_plus_policing_pct'] = None

def _render_iod_context(data: dict, is_existing: bool, c_col):
    """Specific fields for Internet on Demand."""
    data['type'] = "IOD"   
    data['rt'] = ""
    
    if not is_existing:
        st.divider()
        st.markdown("##### ⚙️ IOD Specifications")
        c1, c2 = st.columns(2)
        data['billing_tier'] = c1.selectbox("Billing Tier", options=["Flat Rate", "Burstable (95th Percentile)"], key="iod_billing")

    # =====================================================================
    # 2. THE MAIN DELEGATOR FORM
    # =====================================================================

def render_service_context_form(data: dict, customer_id: str, test_callback=None):
    """
    Step 1 Form Delegator.
    Fixed to allow Greenfield architecture selection (e.g., EPL) and 
    handle the 'Zero Services' scenario.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.api_customer import get_fabric_services

    # --- 1. DATA ACQUISITION & INITIAL STATE ---
    all_services = get_fabric_services(customer_id)
    
    # Determine if we even CAN do Brownfield
    has_existing = False
    if isinstance(all_services, pd.DataFrame) and not all_services.empty:
        has_existing = True
    elif isinstance(all_services, list) and len(all_services) > 0:
        has_existing = True

    # Force Greenfield if no services exist
    if not has_existing:
        data['mode'] = "New Fabric Service"
        is_existing = False
    else:
        is_existing = data.get("mode") != "New Fabric Service"

    # --- 2. BRANCHED UI LOGIC ---
    if is_existing:
        # --- BROWNFIELD: SEARCH & SELECT ---
        services_list = all_services.to_dict('records') if isinstance(all_services, pd.DataFrame) else all_services
        supported_types = ['IPVPN', 'MCGW', 'IP-VPN', 'EPL', 'EVPL', 'ELAN', 'IOD']
        services_list = [s for s in services_list if s.get('service_type') in supported_types]

        svc_map = {f"{s.get('service_name')} ({s.get('service_type')})": s for s in services_list}
        
        sel_label = st.selectbox(
            "🔍 Search Established Fabric Services", 
            options=list(svc_map.keys()), 
            key="br_selectbox"
        )
        
        if sel_label:
            selected = svc_map[sel_label]
            data.update({
                "service_id": selected.get("service_id"),
                "name": selected.get("service_name"),
                "alias": selected.get("service_alias"),
                "type": selected.get("service_type"), 
                "rt": selected.get("route_target", "")
            })
    else:
        # --- GREENFIELD: INITIALIZE NEW ---
        if not has_existing:
            st.info("💡 **New Customer Detected:** No existing fabric services found. Starting Greenfield provisioning.")
        
        data['mode'] = "New Fabric Service"
        data.pop("service_id", None)
        
        supported_types = ['IPVPN', 'MCGW', 'EPL', 'EVPL', 'ELAN', 'IOD']
        
        # 🛑 THE FIX: Allow the user to select 'EPL' (or others) from scratch
        data['type'] = st.selectbox(
            "Select Service Architecture", 
            options=supported_types, 
            index=supported_types.index(data.get('type', 'IPVPN')) if data.get('type') in supported_types else 0,
            key="gf_type_select"
        )

    # --- 3. COMMON INTERFACE ---
    svc_type = str(data.get('type', 'IPVPN')).strip()
    st.divider()
    
    c1, c2 = st.columns(2)
    key_suffix = "bf" if is_existing else "gf"
    
    data['alias'] = c1.text_input(
        "Service Alias / Name", 
        value=data.get('alias', ''), 
        key=f"svc_alias_{key_suffix}",
        placeholder="e.g. Backbone_EPL_West"
    )
    data['name'] = data['alias']
    
    # Read-only display confirms what the system is about to build
    c2.text_input("Confirmed Architecture", value=svc_type, disabled=True, key=f"svc_type_display_{key_suffix}")

    # --- 4. ARCHITECTURE DISPATCH ---
    # Now that svc_type can dynamically be 'EPL', this dispatch will route correctly.
    if svc_type in ["IPVPN", "IP-VPN"]:
        _render_ipvpn_context(data, is_existing, c2)
    elif svc_type == "MCGW":
        _render_mcgw_context(data, is_existing, c2)
    elif svc_type == "EPL":
        _render_epl_context(data, is_existing, c2)
    elif svc_type == "EVPL":
        _render_evpl_context(data, is_existing, c2)
    elif svc_type == "ELAN":
        _render_elan_context(data, is_existing)
    elif svc_type == "IOD":
        _render_iod_context(data, is_existing, c2)

    if test_callback:
        if st.button("🧪 Run API Mapping Test"):
            test_callback()

    # --- 5. EXECUTION ---
    st.divider()
    # 🛑 THE FIX: Updated to width="stretch" to clear console warnings
    if st.button("🚀 Provision Fabric Service", type="primary", width="stretch"):
        if not data.get('alias'):
            st.error("A Service Alias is required to initialize the NDT.")
            return

        from src.utils.service_wizards import provision_fabric_service_api
        
        with st.spinner("🛰️ Provisioning Service in Fabric..."):
            new_id = provision_fabric_service_api(customer_id, data)
            if new_id:
                data['service_id'] = new_id
                st.session_state['prov_data'] = data   
                st.session_state['prov_step'] = "SUCCESS" 
                st.session_state['selected_svc_id'] = new_id
                st.rerun()

def render_interface_build_form(l3_data: dict, calc_func, namespace: str = "wizard"):
    """
    Stabilized Interface Builder.
    Defaults to Lumen-Assigned Auto-Allocation with an optional BYOIP override.
    Includes a visual manifest queue and an escape hatch to skip to Routing.
    """
    import streamlit as st
    import pandas as pd
    
    q_len = len(l3_data.get("interfaces", []))
    is_locked = (q_len >= 1)

    with st.container(border=True):
        st.subheader("➕ Create New Interface")
        if is_locked:
            st.success("✅ Interface Staged. Proceed to Routing configuration.")
        else:
            st.info("Build the interface configuration. Once added, Routing forms will appear.")

        c1, c2 = st.columns(2)
        alias = c1.text_input("Interface Alias", placeholder="WAN-Primary-Link", key=f"intf_alias_{namespace}", disabled=is_locked)
        vlan_mode = c2.radio("VLAN Tagging", ["Tagged", "Untagged"], horizontal=True, key=f"vlan_mode_radio_{namespace}", disabled=is_locked)
        vlan_id = c2.number_input("VLAN ID", 1, 4094, 100, key=f"vlan_id_input_{namespace}", disabled=is_locked) if vlan_mode == "Tagged" else None

        st.divider()
        
        col_v6, col_byoip = st.columns(2)
        enable_v6 = col_v6.checkbox("Enable IPv6 (Dual-Stack)", value=False, key=f"v6_enable_check_{namespace}", disabled=is_locked)
        
        # Enforce value=False so it always defaults to Lumen IPs
        byoip = col_byoip.toggle("Override with BYOIP", value=False, key=f"byoip_toggle_{namespace}", disabled=is_locked)
        
        v4_manual = ""
        v6_manual = ""
        prefix_choice = 30

        if byoip:
            st.warning("⚠️ **BYOIP Mode:** You are overriding automatic IP allocation.")
            man_v4, man_v6 = st.columns(2)
            v4_manual = man_v4.text_input("IPv4 Subnet/Mask", value="192.168.1.0/30", key=f"v4_manual_input_{namespace}", disabled=is_locked)
            if enable_v6:
                v6_manual = man_v6.text_input("IPv6 Subnet/Mask", value="2001:db8::/126", key=f"v6_manual_input_{namespace}", disabled=is_locked)
        else:
            st.markdown("##### 🏢 Lumen-Assigned Pool Allocation (Default)")
            prefix_choice = st.radio("Select Prefix Size", [30, 29, 28], horizontal=True, key=f"prefix_radio_{namespace}", disabled=is_locked)

        st.divider()
        
        # Pass all 4 arguments to the calculator to prevent TypeErrors
        v4_lumen, v4_customer, v4_mask = calc_func(byoip=byoip, prefix=prefix_choice, version="v4", manual_cidr=v4_manual)
        v6_lumen, v6_customer, v6_mask = (None, None, None)
        
        if enable_v6:
            v6_lumen, v6_customer, v6_mask = calc_func(byoip=byoip, prefix=126, version="v6", manual_cidr=v6_manual)

        res_v4, res_v6 = st.columns(2)
        with res_v4:
            st.markdown("**IPv4 Assignment**")
            st.code(f"PE: {v4_lumen}\nCE: {v4_customer}\nMsk: {v4_mask}", language="text")
        with res_v6:
            if enable_v6:
                st.markdown("**IPv6 Assignment**")
                st.code(f"PE: {v6_lumen}\nCE: {v6_customer}\nMsk: /{v6_mask}", language="text")
            else:
                st.caption("IPv6 Not Configured")

        # --- DYNAMIC BUTTON LOGIC ---
        c_action, c_skip = st.columns(2)
        
        with c_action:
            if not is_locked:
                if st.button("➕ Add Interface to Queue", use_container_width=True, type="secondary", key=f"btn_add_intf_{namespace}"):
                    if alias and v4_lumen not in ["Invalid", "Invalid Subnet", "Pool Exhausted", "Pending Input"]:
                        l3_data["interfaces"].append({
                            "alias": alias,
                            "vlan_id": vlan_id,
                            "ipv4_lumen": v4_lumen, 
                            "ipv4_customer": v4_customer, 
                            "ipv4_mask": v4_mask,
                            "v6_lumen": v6_lumen,
                            "v6_customer": v6_customer,
                            "v6_mask": v6_mask,
                            "is_dual_stack": enable_v6,
                            "routing": {"bgp": [], "static": []},
                            "ckt_id": "PENDING"
                        })
                        st.toast(f"Interface {alias} added to queue.")
                        st.rerun()
                    else:
                        st.error("Missing alias or invalid IP configuration.")
            else:
                if st.button("🗑️ Clear Interface Queue", use_container_width=True, type="secondary", key=f"btn_clr_intf_{namespace}"):
                    l3_data["interfaces"] = []
                    st.rerun()

        with c_skip:
            # Escape Hatch: Move to Step 4 (Routing)
            if st.button("⏭️ Skip to Routing / Next Step", type="secondary", use_container_width=True, key=f"btn_skip_intf_{namespace}"):
                st.session_state.prov_step = 4
                st.rerun()

    # --- SECTION B: THE MANIFEST ---
    st.subheader(f"📋 Interface Manifest ({q_len} Staged)")
    
    # Define columns to show in the table
    display_cols = ["alias", "vlan_id", "ipv4_lumen", "ipv4_customer", "is_dual_stack"]
    
    # Build dataframe
    view_df = pd.DataFrame(l3_data.get("interfaces", []))
    if view_df.empty:
        view_df = pd.DataFrame(columns=display_cols)
        
    st.data_editor(
        view_df[display_cols] if not view_df.empty else view_df, 
        use_container_width=True, 
        hide_index=True, 
        key=f"i_sync_{q_len}_{namespace}"
    )

def render_l2_interface_build_form(l2_data: dict, namespace: str = "wizard_l2"):
    """
    Stabilized Layer 2 Interface Builder (E-LAN / VPLS).
    Stages a pure L2 broadcast domain so it can be assigned a UUID and 
    referenced during the multipoint stitching phase.
    """
    import streamlit as st
    import pandas as pd
    
    # Initialize the list if it doesn't exist
    if "interfaces" not in l2_data:
        l2_data["interfaces"] = []
        
    q_len = len(l2_data.get("interfaces", []))
    is_locked = (q_len >= 1)

    with st.container(border=True):
        st.subheader("➕ Create New L2 Interface")
        if is_locked:
            st.success("✅ L2 Interface Staged. Proceed to Stitching configuration.")
        else:
            st.info("Build the L2 domain configuration. Once added, you can stitch multiple physical ports to it.")

        # --- ROW 1: CORE IDENTITY ---
        c1, c2 = st.columns(2)
        alias = c1.text_input("Interface Alias / Domain Name", placeholder="E-LAN-Primary", key=f"intf_alias_{namespace}", disabled=is_locked)
        
        vlan_mode = c2.radio("VLAN Tagging", ["Tagged", "Untagged"], horizontal=True, key=f"vlan_mode_radio_{namespace}", disabled=is_locked)
        vlan_id = c2.number_input("VLAN ID", 1, 4094, 100, key=f"vlan_id_input_{namespace}", disabled=is_locked) if vlan_mode == "Tagged" else None

        st.divider()
        
        # --- ROW 2: L2 SPECIFICS ---
        c3, c4 = st.columns(2)
        mtu = c3.selectbox("MTU Size (Bytes)", options=[1500, 9000], index=1, key=f"mtu_select_{namespace}", disabled=is_locked)
        cos = c4.selectbox("Class of Service", options=["Best Effort", "Business Critical", "Real-Time"], index=0, key=f"cos_select_{namespace}", disabled=is_locked)

        st.divider()
        
        # --- DYNAMIC BUTTON LOGIC ---
        c_action, c_skip = st.columns(2)
        
        with c_action:
            if not is_locked:
                if st.button("➕ Add L2 Interface to Queue", use_container_width=True, type="secondary", key=f"btn_add_intf_{namespace}"):
                    if alias:
                        l2_data["interfaces"].append({
                            "alias": alias,
                            "vlan_mode": vlan_mode,
                            "vlan_id": vlan_id,
                            "mtu": mtu,
                            "cos": cos,
                            "routing": None, # Explicitly null for pure L2
                            "ckt_id": "PENDING"
                        })
                        st.toast(f"L2 Interface {alias} added to queue.")
                        st.rerun()
                    else:
                        st.error("Missing alias.")
            else:
                if st.button("🗑️ Clear Interface Queue", use_container_width=True, type="secondary", key=f"btn_clr_intf_{namespace}"):
                    l2_data["interfaces"] = []
                    st.rerun()

        with c_skip:
            # Escape Hatch: Move to Step 4 (Stitching)
            # Assuming step 4 is your stitching step for L2 flows
            if st.button("⏭️ Skip to Stitching / Next Step", type="secondary", use_container_width=True, key=f"btn_skip_intf_{namespace}"):
                st.session_state.prov_step = 4
                st.rerun()

    # --- SECTION B: THE MANIFEST ---
    st.subheader(f"📋 L2 Interface Manifest ({q_len} Staged)")
    
    # Define columns to show in the table
    display_cols = ["alias", "vlan_mode", "vlan_id", "mtu", "cos"]
    
    # Build dataframe
    view_df = pd.DataFrame(l2_data.get("interfaces", []))
    if view_df.empty:
        view_df = pd.DataFrame(columns=display_cols)
        
    st.data_editor(
        view_df[display_cols] if not view_df.empty else view_df, 
        use_container_width=True, 
        hide_index=True, 
        key=f"i_sync_{q_len}_{namespace}"
    )

def render_static_route_form(placeholder_dict: dict, target_intf: dict):
    """
    Unified Static Route Form with verification manifest.
    """
    import streamlit as st
    import ipaddress
    import pandas as pd

    alias_pfx = f"st_{target_intf.get('alias', 'unk')}".replace(" ", "_")
    v4_next_hop = target_intf.get('ipv4_customer')
    v6_next_hop = target_intf.get('v6_customer')

    with st.container(border=True):
        st.markdown("##### 📍 Add Static Route")
        version = "IPv4"
        if target_intf.get('is_dual_stack'):
            version = st.radio("Family", ["IPv4", "IPv6"], horizontal=True, key=f"{alias_pfx}_ver_toggle")
        
        current_nh = v4_next_hop if version == "IPv4" else v6_next_hop
        dest = st.text_input(f"{version} Destination (CIDR)", placeholder="10.0.0.0/24", key=f"{alias_pfx}_{version}_dest")
        
        if current_nh:
            st.info(f"**Next-Hop (Auto-detected):** `{current_nh}`")

        if st.button(f"➕ Add {version} Route", key=f"{alias_pfx}_{version}_btn", use_container_width=True, type="secondary"):
            if dest and current_nh:
                try:
                    net = ipaddress.ip_network(dest.strip(), strict=False)
                    # Initialize nested dicts if missing
                    routing_data = target_intf.setdefault("routing", {"bgp": [], "static": []})
                    
                    routing_data["static"].append({
                        "ip_prefix": str(net.network_address), 
                        "prefix_mask": int(net.prefixlen), 
                        "next_hop_ip": current_nh, 
                        "display_cidr": str(net),
                        "family": version
                    })
                    st.toast(f"Route {dest} added to staging.")
                    st.rerun()
                except ValueError:
                    st.error("Invalid CIDR format. Please check the destination prefix.")
            else:
                st.warning("Destination and Next-Hop are required.")

    # --- Static Route Queue View ---
    static_queue = target_intf.get("routing", {}).get("static", [])
    if static_queue:
        st.markdown("###### 📋 Staged Static Routes")
        st.dataframe(pd.DataFrame(static_queue)[["display_cidr", "next_hop_ip", "family"]], use_container_width=True, hide_index=True)

def render_bgp_peer_form(placeholder_dict: dict, target_intf: dict):
    """
    Unified BGP Form with verification manifest.
    """
    import streamlit as st
    import pandas as pd

    pfx = f"bgp_{target_intf.get('alias', 'unk')}".replace(" ", "_")
    enable_v6 = target_intf.get('is_dual_stack', False)

    with st.container(border=True):
        st.markdown("##### 🤝 Add BGP Neighbor")
        version = "IPv4"
        if enable_v6:
            version = st.radio("Address Family", ["IPv4", "IPv6"], horizontal=True, key=f"{pfx}_ver")
        
        is_v6 = version == "IPv6"
        # Peer IP is the PE side, Local IP is the CE side
        peer_ip_val = target_intf.get('v6_lumen' if is_v6 else 'ipv4_lumen', '')
        local_ip_val = target_intf.get('v6_customer' if is_v6 else 'ipv4_customer', '')

        c1, c2 = st.columns(2)
        with c1:
            lumen_as = st.text_input("Lumen AS", value="1", key=f"{pfx}_las")
            neighbor_ip = st.text_input(f"Neighbor {version} (PE)", value=peer_ip_val, key=f"{pfx}_{version}_nip")
        with c2:
            cust_as = st.text_input("Customer AS", value="64512", key=f"{pfx}_cas")
            local_ip = st.text_input(f"Local {version} (CE)", value=local_ip_val, key=f"{pfx}_{version}_lip")

        st.divider()
        b_col, h_col = st.columns(2)
        bfd_on = b_col.toggle("Enable BFD", value=False, key=f"{pfx}_bfd")
        mhop_on = h_col.toggle("Enable Multihop", value=False, key=f"{pfx}_mhop")

        if st.button(f"➕ Add {version} Neighbor", use_container_width=True, type="secondary", key=f"{pfx}_btn"):
            if neighbor_ip and lumen_as and cust_as:
                # Initialize nested dicts if missing
                routing_data = target_intf.setdefault("routing", {"bgp": [], "static": []})
                
                routing_data["bgp"].append({
                    "family": version,
                    "neighbor_ip": neighbor_ip,
                    "local_ip": local_ip,
                    "lumen_as": lumen_as,
                    "customer_as": cust_as,
                    "bfd_enabled": bfd_on,
                    "multihop": mhop_on
                })
                st.toast(f"BGP {version} Neighbor staged.")
                st.rerun()
            else:
                st.error("Lumen AS, Customer AS, and Neighbor IP are required.")

    # --- BGP Peer Queue View ---
    bgp_queue = target_intf.get("routing", {}).get("bgp", [])
    if bgp_queue:
        st.markdown("###### 📋 Staged BGP Peers")
        st.dataframe(pd.DataFrame(bgp_queue)[["family", "neighbor_ip", "lumen_as", "customer_as"]], use_container_width=True, hide_index=True)

def get_optics_options(speed: str) -> list:
    """Returns the appropriate optics list based on port speed."""
    mapping = {
        "1G": ["SX (Multimode)", "LX (Single-mode)"],
        "10G": ["SR (Multimode)", "LR (Single-mode)"],
        "100G": [
            "LR4 (10km - 4 Lane)", 
            "LR1 (10km - Single Lambda)", 
            "FR1 (2km)", 
            "DR1 (500m)"
        ],
        "400G": [
            "FR4 (2km)", 
            "LR4 (10km)"
        ]
    }
    speed_key = speed.upper().replace("BPS", "").replace(" ", "").strip()
    return mapping.get(speed_key, ["Standard (Generic)"])

def render_cloud_provisioning_form(fs_detail: dict, namespace: str = "wizard"):
    """
    Renders the Cloud Provisioning form (Step 4).
    Uses a 'namespace' variable to allow the form to be rendered multiple times
    on the same page without Streamlit key collisions.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.api_customer import get_cloud_partners, post_cloud_intent
    
    # 1. INITIALIZE QUEUE IN SESSION STATE
    if "cloud_queue" not in st.session_state:
        st.session_state.cloud_queue = []

    # 2. EXTRACT ANCHOR
    service_id = fs_detail.get("service_id")
    if not service_id:
        st.error("⛔ Error: Fabric Service ID missing from manifest.")
        return
    
    # 3. DATA HYDRATION (Dynamic DB Lookup)
    db_partners = get_cloud_partners()
    if not db_partners:
        st.warning("⚠️ No Cloud Partners available in the Galileo inventory.")
        return

    partner_names = sorted(list(set(p['partner_name'] for p in db_partners)))
    partner_options = ["None"] + partner_names

    # 4. CONFIGURATION FORM UI
    with st.container(border=True):
        st.markdown("#### 🚀 Stage New Cloud Interconnect")
        st.caption(f"Relational Anchor (service_id): **{service_id}**")
        
        c1, c2 = st.columns(2, gap="large")
        
        with c1:
            st.markdown("**1. Provider Selection**")
            # THE FIX: Add the namespace to the key
            selected_partner_name = st.selectbox("Cloud Provider", options=partner_options, key=f"c_prov_{service_id}_{namespace}")
            is_none = (selected_partner_name == "None")
            
            if not is_none:
                regions = sorted(list(set(p['region'] for p in db_partners if p['partner_name'] == selected_partner_name)))
                selected_region = st.radio("Target Cloud Region", options=regions, horizontal=True, key=f"c_reg_{service_id}_{namespace}")
            else:
                st.info("⏭️ Select a provider to begin.")
                selected_region = None

        with c2:
            if not is_none:
                st.markdown("**2. Capacity & Identity**")
                services = [p for p in db_partners if p['partner_name'] == selected_partner_name and p['region'] == selected_region]
                service_map = {f"{s['service_type']} ({s['partnership_level']})": s for s in services}
                
                selected_service_label = st.selectbox("Service Profile", options=list(service_map.keys()), key=f"c_svc_{service_id}_{namespace}")
                chosen_partner = service_map[selected_service_label]
                
                tiers = chosen_partner.get("bandwidth_tiers", [1, 2, 5, 10]) 
                tier_labels = [f"{t}G" for t in tiers]
                
                selected_tier_label = st.select_slider("Select Bandwidth Tier", options=tier_labels, key=f"c_bw_{service_id}_{namespace}")
                bandwidth_int = int(selected_tier_label.replace("G", ""))
                
                peering_id = st.text_input("Cloud Connection Identifier", placeholder="e.g., AWS Account ID or GCP Key", key=f"c_id_{service_id}_{namespace}")
            else:
                st.caption("Parameters will appear once a provider is selected.")

        st.divider()

        # --- ACTION 1: ADD TO STAGING QUEUE ---
        btn_label = "➕ Add to Provisioning Queue" if not is_none else "⏭️ Skip Cloud Peering"
        if st.button(btn_label, use_container_width=True, type="secondary", key=f"btn_add_{service_id}_{namespace}"):
            if is_none:
                st.toast("Skipping cloud peering configuration.")
            elif peering_id:
                peering_intent = {
                    "service_id": service_id,
                    "partner_id": chosen_partner['partner_id'],
                    "provider": selected_partner_name,
                    "region": selected_region,
                    "connection_name": f"{selected_partner_name}-{selected_region}-{peering_id[:6]}",
                    "service_type": chosen_partner['service_type'],
                    "service_bw": bandwidth_int * 1000, 
                    "identifier": peering_id,
                    "description": f"Queued Staging: {peering_id}",
                    "status": "Staged"
                }
                st.session_state.cloud_queue.append(peering_intent)
                st.toast(f"Queued {selected_partner_name} connection @ {selected_tier_label}.")
                st.rerun()
            else:
                st.error("⚠️ Connection Identifier is required to stage a VXC.")

    # 5. QUEUE MANAGEMENT & COMMIT VIEW
    q_len = len(st.session_state.cloud_queue)
    if q_len > 0:
        st.write("---")
        st.markdown(f"##### 🛒 Cloud Staging Queue ({q_len})")
        
        df_queue = pd.DataFrame(st.session_state.cloud_queue)
        st.dataframe(
            df_queue[["provider", "region", "connection_name", "service_bw", "identifier", "status"]], 
            use_container_width=True, 
            hide_index=True
        )

        col_clear, col_prov = st.columns([1, 2])
        
        if col_clear.button("🗑️ Clear Queue", use_container_width=True, key=f"btn_clear_{service_id}_{namespace}"):
            st.session_state.cloud_queue = []
            st.rerun()

        if col_prov.button("🚀 PROVISION ALL QUEUED VXCs", use_container_width=True, type="primary", key=f"btn_prov_{service_id}_{namespace}"):
            success_count = 0
            
            with st.spinner(f"Provisioning {q_len} cloud connections..."):
                for intent in st.session_state.cloud_queue:
                    response = post_cloud_intent(intent)
                    if response:
                        success_count += 1
                        staged_node = {
                            "interface_id": f"PENDING-{intent['identifier'][:4]}",
                            "interface_name": intent["connection_name"],
                            "interface_type": intent["service_type"],
                            "service_bw_mbps": intent["service_bw"],
                            "status": "Provisioning",
                            "ckt_id": "VXC-BUILD"
                        }
                        if "fabric_interfaces" not in fs_detail:
                            fs_detail["fabric_interfaces"] = []
                        fs_detail["fabric_interfaces"].append(staged_node)

            if success_count > 0:
                st.success(f"✅ Successfully provisioned {success_count} VXCs to the Galileo Controller.")
                st.session_state.cloud_queue = [] 
            else:
                st.error("❌ Provisioning failed. Check Galileo API logs.")

def _fabric_connection_provisioning_ui(payload: dict, a_table: str, b_table: str, label: str, customer_ports_df: pd.DataFrame):
    """
    Step 5 UI Executor: 
    Binds Side A (from Service Detail) to Side B (from Customer Inventory).
    """
    import streamlit as st
    import pandas as pd
    
    # JSON #1: Live Service Detail
    live = st.session_state.live_manifest 
    children = payload.get("service_context", {}).get("children", {})
    
    # --- 🛰️ DYNAMIC HYDRATION LOGIC ---
    def get_verified_options(table_name):
        # 1. SIDE A: Interfaces (Rules: Must be Staged)
        if table_name == "interfaces":
            valid_intfs = [
                i for i in live.get("fabric_interfaces", []) 
                if i.get("service_status") == "Staged"
            ]
            return {f"Intf: {i['interface_name']}": i['interface_id'] for i in valid_intfs}

        # 2. SIDE B: Ports (Rules: Staged/Untagged OR Active/Tagged)
        if table_name == "ports":
            mask = (
                ((customer_ports_df['port_service_status'] == 'Staged') & (customer_ports_df['port_tagging'] == 'Untagged')) |
                ((customer_ports_df['port_service_status'] == 'Active') & (customer_ports_df['port_tagging'] == 'Tagged'))
            )
            valid_ports = customer_ports_df[mask]
            return {
                f"Port: {p['port_name']} ({p['port_tagging']})": p['port_id'] 
                for _, p in valid_ports.iterrows()
            }

        # 3. SIDE B: Cloud Connections (Rule: Must be Live)
        if table_name == "cloud_connections":
            return {
                f"Cloud: {c['connection_name']}": c['cloud_connection_id'] 
                for c in live.get("cloud_connections", [])
            }
        return {}

    # Hydrate the options
    a_options = get_verified_options(a_table)
    b_options = get_verified_options(b_table)

    # --- 🏗️ UI RENDERING ---
    if not a_options or not b_options:
        st.warning(f"⚠️ Prerequisites for {label} missing. Check status of Ports and Interfaces.")
        return

    with st.container(border=True):
        st.caption(f"Stitching Pattern: **{label}**")
        c1, c2 = st.columns(2)
        
        # Side A Selection (Interfaces)
        side_a = c1.selectbox(f"Select {a_table.title()}", options=list(a_options.keys()), key="f_side_a")
        
        # Side B Selection (Ports/Cloud)
        z_options = [k for k in b_options.keys() if b_options[k] != a_options.get(side_a)] if a_table == b_table else list(b_options.keys())
        side_b = c2.selectbox(f"Select {b_table.title()}", options=z_options, key="f_side_b")
        
        bw = st.select_slider("Assigned Bandwidth", options=["10M", "100M", "1000M"], value="1000M")
        conn_name = st.text_input("Connection Identifier", value=f"CX-{side_a}")

        if st.button("🔗 Queue Fabric Connection", use_container_width=True, type="primary"):
            new_conn = {
                "service_id": payload.get("service_id"),
                "connection_name": conn_name.strip(),
                "connector_a_id": a_options[side_a],
                "connector_a_table": a_table,
                "connector_b_id": b_options[side_b],
                "connector_b_table": b_table,
                "service_bw": int(bw.replace("M", "")),
                "connection_status": "Planned"
            }
            children.setdefault("fabric_connections", []).append(new_conn)
            st.toast("Connection staged in intent payload.")
            st.rerun()

def render_l3_connection_form(manager):
    """
    Form for L3 Services: Binding Interface (A) to Peering Session (B).
    """
    import streamlit as st
    import pandas as pd

    # FIX: Use .get() access for the service_type
    svc_type = manager.get("service_context", {}).get("service_type", "Unknown")
    
    st.subheader("🔗 L3 Fabric Attachment")
    st.info(f"Binding logic for {svc_type}: Map logical Interface to Cloud Provider.")
    
    # Rest of your code using manager.get("service_context")...
    children = manager.get("service_context", {}).get("children", {})

    interfaces = children.get("interfaces", [])
    peerings = children.get("cloud_peerings", [])

    # Map aliases/names to their provisioned Database IDs
    intf_map = {i['alias']: i.get('interface_id') for i in interfaces if i.get('interface_id')}
    peer_map = {
        f"{p.get('provider', 'Cloud')} ({p.get('identifier', 'Unknown')})": p.get('cloud_connection_id') 
        for p in peerings if p.get('cloud_connection_id')
    }

    if not intf_map or not peer_map:
        st.warning("⚠️ Prerequisites missing: Ensure a provisioned Interface (Step 3) and an active Peering Session (Step 4) are queued.")
        return

    with st.container(border=True):
        c1, c2 = st.columns(2)
        side_a_alias = c1.selectbox("Select Side A (Local Interface)", options=list(intf_map.keys()))
        side_b_alias = c2.selectbox("Select Side B (Cloud Endpoint)", options=list(peer_map.keys()))
        
        bw = st.select_slider("Handoff Bandwidth", options=["10M", "50M", "100M", "500M", "1000M", "10000M"])
        bw_int = int(bw.replace("M", ""))
        
        conn_name = st.text_input("Connection Name", value=f"L3-{side_a_alias}-to-Cloud")
        
        if st.button("🔗 Queue Fabric Attachment", use_container_width=True, type="secondary"):
            if not conn_name:
                st.error("Connection Name is required.")
            else:
                # Align perfectly with the API schema!
                new_attach = {
                    "service_id": manager.payload.get("service_id"),
                    "connection_name": conn_name.strip(),
                    "connector_a_id": intf_map[side_a_alias],
                    "connector_a_table": "interfaces",
                    "connector_b_id": peer_map[side_b_alias],
                    "connector_b_table": "cloud_connections",
                    "connection_status": "Planned",
                    "service_bw": bw_int,
                    "health_status": 4
                }
                
                # Append to the main queue
                children.setdefault("fabric_connections", []).append(new_attach)
                st.toast(f"Linked {side_a_alias} to {side_b_alias}")
                st.rerun()

    # Display Queue
    conn_list = children.get("fabric_connections", [])
    if conn_list:
        st.divider()
        st.markdown(f"### 📋 Queued L3 Attachments ({len(conn_list)})")
        display_df = pd.DataFrame(conn_list)[["connection_name", "connector_a_id", "connector_b_id", "service_bw", "connection_status"]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

def render_eline_connection_form(manager):
    """
    Form for E-Line Services: Binding Port A to Port Z.
    """
    import streamlit as st
    import pandas as pd

    # FIX: Dictionary access
    svc_context = manager.get("service_context", {})
    svc_type = svc_context.get("service_type", "E-Line")
    
    st.subheader("🔗 E-Line P2P Attachment (EVC)")
    st.info("Mapping Side A Physical Port to Side Z Remote Physical Port.")
    
    ports = manager.payload.get("service_context", {}).get("children", {}).get("ports", [])
    port_options = {p['alias']: p['port_id'] for p in ports if p.get('port_id')}

    if len(port_options) < 2:
        st.warning("⚠️ **Prerequisites Missing:** An E-Line requires exactly TWO provisioned physical ports. Please ensure two ports are committed in Step 2 before building the EVC.")
        return

    with st.container(border=True):
        st.markdown("##### 📍 Stitch Ethernet Virtual Circuit")
        
        c1, c2 = st.columns(2)
        with c1:
            a_alias = st.selectbox("A-Side Port (UNI-A)", options=list(port_options.keys()), key="eline_a")
            service_bw = st.number_input("EVC Bandwidth (Mbps)", min_value=10, value=1000)
        
        with c2:
            b_options = [k for k in port_options.keys() if k != a_alias]
            
            if not b_options:
                st.error("No valid Z-Side ports available.")
                return
                
            b_alias = st.selectbox("Z-Side Port (UNI-Z)", options=b_options, key="eline_b")
            conn_name = st.text_input("Circuit ID / Name", value=f"EVC_{a_alias}_to_{b_alias}")

        if st.button("➕ Queue EVC", use_container_width=True, type="secondary"):
            if not conn_name.strip():
                st.error("❌ EVC Name cannot be blank.")
            else:
                # --- NEW: Extract the Service Alias for the VRF Name field ---
                svc_alias = manager.payload.get("service_context", {}).get("alias", "E-Line-Service")

                new_evc = {
                    "service_id": manager.payload.get("service_id"),
                    "connection_name": conn_name.strip(),
                    "connector_a_id": port_options[a_alias],
                    "connector_a_table": "ports",          
                    "connector_b_id": port_options[b_alias],
                    "connector_b_table": "ports",          
                    "connection_status": "Planned",
                    "service_bw": int(service_bw),
                    "health_status": 4,
                    
                    # --- THE FIX: Map the Alias to the VRF Name ---
                    "vrf_name": svc_alias 
                }
                
                manager.payload["service_context"]["children"]["fabric_connections"].append(new_evc)
                st.toast(f"✅ Queued EVC: {conn_name}", icon="🔗")
                st.rerun()


    conn_list = manager.payload["service_context"]["children"].get("fabric_connections", [])
    if conn_list:
        st.divider()
        st.markdown(f"### 📋 Queued EVCs ({len(conn_list)})")
        
        display_df = pd.DataFrame(conn_list)[["connection_name", "connector_a_id", "connector_b_id", "service_bw", "connection_status"]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

def render_generic_connection_form(manager):
    """Fallback form for unsupported or generic service types."""
    st.warning(f"No specialized attachment logic defined for {manager.service_type}.")
    
    # src/utils/ui_provisioning_form.py

def render_fabric_connection_form(compat_payload: dict, manager_payload: dict):
    """
    Unified Connection Form. 
    Handles selection of A/B connectors and captures L2/L3 parameters.
    """
    import streamlit as st
    from src.utils.network_utils import get_topology_schema

    raw_type = manager_payload.get("service_context", {}).get("service_type", "IPVPN")
    
    # 1. MCGW Specific Mode Selection
    mcgw_mode = "Physical"
    if "MCGW" in raw_type.upper():
        mcgw_mode = st.radio("MCGW Mode", ["Physical (Port-to-Intf)", "Cloud (Cloud-to-Intf)"], horizontal=True, key="mcgw_mode_sel")

    # 2. Resolve Schema & Labels
    a_table, b_table, label = get_topology_schema(raw_type, mcgw_mode)
    st.info(f"🧬 **Topology:** {label} | **Schema:** `{a_table}` ↔ `{b_table}`")

    # 3. Build Selection Options
    staged_intfs = manager_payload["service_context"]["children"].get("interfaces", [])
    staged_ports = manager_payload["service_context"]["children"].get("ports", [])
    
    # Map for Connector A
    if a_table == "interface":
        a_options = {f"Intf: {i.get('alias')} ({i.get('interface_id')[:8]})": i.get('interface_id') for i in staged_intfs if i.get('interface_id')}
    else:
        a_options = {f"Port: {p.get('port_name')}": p.get('port_id') for p in staged_ports}

    # Map for Connector B
    if b_table == "ports":
        b_options = {f"Port: {p.get('port_name')}": p.get('port_id') for p in staged_ports}
    else:
        b_options = {f"Intf: {i.get('alias')} ({i.get('interface_id')[:8]})": i.get('interface_id') for i in staged_intfs if i.get('interface_id')}

    # 4. Form Container
    with st.container(border=True):
        c1, c2 = st.columns(2)
        sel_a = c1.selectbox(f"Select A ({a_table})", options=list(a_options.keys()) or ["NONE"])
        sel_b = c2.selectbox(f"Select B ({b_table})", options=list(b_options.keys()) or ["NONE"])

        st.divider()
        
        p1, p2 = st.columns(2)
        bw = p1.select_slider("Bandwidth (Mbps)", options=[10, 50, 100, 500, 1000, 10000], value=100)
        vlan = p2.number_input("S-VLAN (0 for untagged)", 0, 4094, value=int(compat_payload.get("vlan_id", 0)))
        conn_name = st.text_input("Connection Alias", value=f"CX-{raw_type}-{st.session_state.get('customer_id', 'GALILEO')[:4]}")

        if st.button("➕ Stage Connection", type="secondary", use_container_width=True):
            if "NONE" not in [sel_a, sel_b]:
                conns = manager_payload["service_context"]["children"].setdefault("connections", [])
                conns.append({
                    "connection_name": conn_name,
                    "connector_a_id": a_options[sel_a],
                    "connector_a_table": a_table,
                    "connector_b_id": b_options[sel_b],
                    "connector_b_table": b_table,
                    "vrf_name": compat_payload.get("service_name", "GLOBAL"),
                    "bandwidth": bw,
                    "vlan_id": vlan
                })
                st.toast("Connection staged successfully.")
                st.rerun() # Refresh parent orchestrator to enable Commit
            else:
                st.error("Please ensure valid A and B components are selected.")                

def _render_l2_fabric_workflow(compat_payload: dict, manager_payload: dict, svc_type: str):
    """
    Handles P2P (EPL) and Multipoint (EVPL/LAN) topology connections.
    """
    import streamlit as st
    import pandas as pd

    # 1. Access Staged Queue
    conn_manifest = manager_payload.get("service_context", {}).setdefault("connections", [])
    q_len = len(conn_manifest)
    
    # 2. Extract Available Ports (Live + Staged logic could be merged here, using Live for safety)
    port_list = compat_payload.get("fabric_ports", [])
    port_options = {f"{p.get('device', 'Unknown')} | {p.get('port_name', 'Unknown')}": str(p.get('port_id')) for p in port_list}
    port_names = list(port_options.keys())

    # --- TOPOLOGY RULES ---
    is_epl = "EPL" in svc_type
    max_conns = 1 if is_epl else 50
    is_locked = (q_len >= max_conns)
    conn_type_val = "Point-to-Point" if is_epl else "Multipoint"

    with st.container(border=True):
        st.subheader(f"🌉 Configure {svc_type} Connection")
        st.caption("Point-to-Point strict cross-connect." if is_epl else "Multipoint Fabric Mesh / Tree.")
        
        if is_epl and len(port_names) < 2:
            st.warning("⚠️ EPL requires exactly 2 active ports to build a connection.")
            return
        elif not is_epl and len(port_names) < 1:
            st.warning("⚠️ At least 1 active port is required.")
            return

        l, r = st.columns(2)
        with l:
            conn_alias = st.text_input("Connection Name", placeholder=f"{svc_type}-LINK-01", key="c_alias_l2", disabled=is_locked)
            
            # Auto-index EPL for convenience
            port_a = st.selectbox("Endpoint A (Source)", options=port_names, index=0, key="c_porta_l2", disabled=is_locked)
            port_z = st.selectbox("Endpoint Z (Destination)", options=port_names, index=1 if is_epl else 0, key="c_portz_l2", disabled=is_locked)

        with r:
            bw_options = ["100M", "500M", "1G", "2G", "5G", "10G", "100G"]
            conn_bw = st.selectbox("Committed Information Rate (CIR)", options=bw_options, index=2, key="c_bw_l2", disabled=is_locked)
            admin_stat = st.radio("Admin Status", ["Up", "Down"], horizontal=True, key="c_admin_l2", disabled=is_locked)
            st.text_input("Topology Type", value=conn_type_val, disabled=True, key="c_topo_l2")

        st.divider()

        if not is_locked:
            if st.button("➕ Stage Connection", type="primary", use_container_width=True):
                if port_a == port_z:
                    st.error("Endpoint A and Z cannot be the same physical port.")
                else:
                    new_conn = {
                        "connection_name": conn_alias or f"{port_a.split(' | ')[-1]} to {port_z.split(' | ')[-1]}",
                        "service_bw": conn_bw,
                        "source_port_id": port_options.get(port_a),
                        "dest_port_id": port_options.get(port_z),
                        "connection_type": conn_type_val,
                        "status": "Staged",
                        "admin_status": admin_stat.lower()
                    }
                    manager_payload["service_context"]["connections"].append(new_conn)
                    st.rerun()
        else:
            if st.button("🗑️ Clear Queue", type="secondary", use_container_width=True):
                manager_payload["service_context"]["connections"] = []
                st.rerun()
                
    _render_manifest_table(conn_manifest, q_len, max_conns)

def render_fabric_connection_provision_form(fs_detail: dict, selected_a: pd.Series, selected_b: pd.Series):
    """
    Final Step 5 Form: Captures Bandwidth and VLAN intent.
    ALIGNED: Matches DB schema ('interface' / 'ports') to satisfy chk_connector_table_values.
    """
    import streamlit as st
    import uuid
    from src.utils.network_utils import handle_stitching_orchestration

    st.markdown("### 📝 Define Connection Parameters")
    
    # 0. Extract Contextual metadata
    service_id = fs_detail.get('service_id')
    # Use service_name for the VRF context as per your database requirement
    vrf_context = fs_detail.get("service_name", "GLOBAL")
    port_tagging = str(selected_b.get('port_tagging', 'untagged')).lower()
    
    # 1. FORM CONTAINER
    with st.container(border=True):
        c1, c2 = st.columns(2)
        
        with c1:
            # --- PARAMETER 1: BANDWIDTH ---
            bw_options = [10, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
            sel_bw = st.select_slider(
                "🚀 Service Bandwidth (Mbps)",
                options=bw_options,
                value=100
            )

        with c2:
            # --- PARAMETER 2: VLAN LOGIC ---
            s_vlan = 0
            # Logic: Only Tagged ports require S-VLAN
            if "tagged" in port_tagging and "untagged" not in port_tagging:
                s_vlan = st.number_input(
                    "🆔 Service VLAN (S-VLAN)",
                    min_value=1,
                    max_value=4094,
                    value=100
                )
                st.caption(f"✨ Port `{selected_b['port_name']}` is **Tagged**.")
            else:
                st.info(f"ℹ️ Port `{selected_b['port_name']}` is **Untagged**.")

        # --- PARAMETER 3: NAMING ---
        default_name = f"CX-{selected_a['interface_name']}-{selected_b['port_name']}"
        conn_name = st.text_input("Connection Name / Circuit ID", value=default_name)

        st.divider()

        # 2. THE PROVISIONING TRIGGER
        if st.button("🚀 Provision Fabric Connection", type="primary", use_container_width=True):
            # Construct the final API Payload matching your PostgreSQL CHECK constraints
            connection_intent = {
                "customer_id": fs_detail.get("customer_id"), 
                "service_id": service_id,
                "connection_id": str(uuid.uuid4()),
                "connection_name": conn_name.strip(),
                "connector_a_id": selected_a.get('interface_id'),
                
                # SCHEMA ALIGNMENT: Must be "interface" (singular) per your \d output
                "connector_a_table": "interface", 
                
                "connector_b_id": selected_b.get('port_id'),
                
                # SCHEMA ALIGNMENT: Must be "ports" (plural) per your \d output
                "connector_b_table": "ports", 
                
                "connection_status": "Active",
                "vrf_name": vrf_context,
                "service_bw": int(sel_bw),
                "s_vlan": int(s_vlan),
                "c_vlan_list": "",
                "health_status": 1 
            }
            
            # TRIGGER ORCHESTRATION: Promotions + Post
            handle_stitching_orchestration(selected_a, selected_b, connection_intent)

def _render_fabric_attachment_logic(payload: dict):
    """
    Unified Pattern Dispatcher.
    Maps service types to their required connectivity patterns.
    """
    import streamlit as st
    
    svc_context = payload.get("service_context", {})
    svc_type = svc_context.get("service_type", "IPVPN")
    
    # 1. Configuration Map: Define the "Rules" for standard services
    TOPOLOGY_RULES = {
        "ELINE EPL":  ("ports", "ports", "L2 Port-to-Port"),
        "ELINE EVPL": ("ports", "ports", "L2 Port-to-Port"),
        "IPVPN":      ("ports", "interfaces", "L3 Port-to-Interface"),
        "IOD":        ("ports", "interfaces", "L3 Port-to-Interface"),
        "ELAN":       ("ports", "interfaces", "L2 Port-to-Interface"),
    }

    # 2. Logic: Handle MCGW specifically to support both use cases
    if svc_type == "MCGW":
        st.info("💡 MCGW supports both Physical and Cloud-native attachments.")
        mcgw_mode = st.radio(
            "Select MCGW Connection Type", 
            ["Physical (Port-to-Interface)", "Cloud (Cloud-to-Interface)"],
            horizontal=True
        )
        
        if "Physical" in mcgw_mode:
            a_table, b_table, label = ("ports", "interfaces", "L3 Port-to-Interface")
        else:
            # Matches your "L3 Port-to-cloud" requirement
            a_table, b_table, label = ("cloud_connections", "interfaces", "L3 Cloud-to-Interface")
    
    else:
        # Resolve standard rules or fallback to generic
        a_table, b_table, label = TOPOLOGY_RULES.get(
            svc_type, ("interfaces", "cloud_connections", "Generic L3")
        )

    # 3. Execution: Call the pattern renderer with the resolved tables
    _execute_pattern_ui(payload, a_table, b_table, label)

def _render_l2_fabric_workflow(compat_payload: dict, manager_payload: dict, svc_type: str):
    """
    Private UI Handler for Layer 2 Carrier Ethernet workflows (EPL/EVPL/ELAN).
    """
    import streamlit as st
    
    pfx = f"l2_conn_{svc_type}"
    
    with st.container(border=True):
        st.markdown(f"##### 🌉 {svc_type} Topology Mapping")
        
        c1, c2 = st.columns(2)
        vlan_id = c1.number_input("S-VLAN ID", 1, 4094, value=int(compat_payload.get("vlan_id", 100)), key=f"{pfx}_vlan")
        bw = c2.number_input("Bandwidth (Mbps)", 1, 100000, value=int(compat_payload.get("bandwidth", 1000)), key=f"{pfx}_bw")
        
        st.info("L2 services establish direct fabric connections between provisioned ports.")

        if st.button("➕ Stage L2 Connection", type="secondary", use_container_width=True, key=f"{pfx}_btn"):
            conns = manager_payload["service_context"]["children"].setdefault("connections", [])
            
            conns.append({
                "type": "L2_EVC",
                "bandwidth": bw,
                "vlan_id": vlan_id,
                "role": "HUB" if "LAN" in svc_type else "P2P"
            })
            
            st.toast(f"{svc_type} Connection Staged.")
            st.rerun()
            
def _render_l3_attachment_workflow(compat_payload: dict, manager_payload: dict, svc_type: str):
    """
    Private UI Handler for IPVPN VRF Attachments.
    Captures logical interface selection and maps it to the topology intent.
    """
    import streamlit as st
    
    pfx = f"l3_conn_{svc_type}"
    
    # Retrieve interfaces provisioned in Step 3
    staged_intfs = manager_payload.get("service_context", {}).get("children", {}).get("interfaces", [])
    
    # Map for the selectbox
    intf_map = {f"{i.get('alias')} ({i.get('interface_id', 'PENDING')[:8]})": i.get('interface_id') 
                for i in staged_intfs if i.get('interface_id')}

    with st.container(border=True):
        st.markdown(f"##### 🛰️ {svc_type} VRF Attachment")
        
        if not intf_map:
            st.warning("⚠️ No committed Interface IDs found. Ensure Step 3 commit succeeded.")
            return

        c1, c2 = st.columns(2)
        selected_label = c1.selectbox("Select Logical Interface", options=list(intf_map.keys()), key=f"{pfx}_intf")
        target_intf_id = intf_map[selected_label]
        
        # Default to the VRF name defined in the service context
        vrf_name = c2.text_input("Target VRF", value=compat_payload.get("vrf_name", ""), key=f"{pfx}_vrf")
        
        role = c1.selectbox("Topology Role", ["SPOKE", "HUB", "PEER"], key=f"{pfx}_role")
        
        if st.button("➕ Add VRF Attachment", type="secondary", use_container_width=True, key=f"{pfx}_btn"):
            if target_intf_id and vrf_name:
                conns = manager_payload["service_context"]["children"].setdefault("connections", [])
                
                conns.append({
                    "interface_id": target_intf_id,
                    "vrf_name": vrf_name,
                    "role": role,
                    "type": "VRF_ATTACH",
                    "bandwidth": compat_payload.get("bandwidth", 0),
                    "vlan_id": compat_payload.get("vlan_id", 0)
                })
                
                st.toast(f"Interface {target_intf_id[:8]} staged for VRF {vrf_name}")
                # THE FIX: Trigger rerun to update the parent 'Commit' button state
                st.rerun()
            else:
                st.error("Both Interface and VRF Name are required.")   

def _render_eline_evc_workflow(manager_payload: dict):
    """
    Step 5 UI Workflow: E-Line P2P Attachment (EVC).
    Stitches Side A (UNI) to Side Z (UNI) using physical port IDs.
    """
    import streamlit as st
    import pandas as pd

    st.subheader("🔗 E-Line P2P Attachment (EVC)")
    st.info("Mapping Side A Physical Port to Side Z Remote Physical Port via EVC.")

    # 1. Pull the staging container from JSON#2
    children = manager_payload.get("service_context", {}).get("children", {})
    
    # 2. Pull the LIVE ports from JSON#1 (Live Manifest)
    # An E-Line requires physical ports to be provisioned and 'Live' first.
    live_ports = st.session_state.live_manifest.get("fabric_ports", [])
    
    # Create a map of Alias -> port_id for the selectboxes
    port_options = {
        f"{p.get('port_name')} ({p.get('location_id', 'Unknown')})": p.get('port_id') 
        for p in live_ports if p.get('port_id')
    }

    if len(port_options) < 2:
        st.warning("⚠️ **Prerequisites Missing:** An E-Line requires TWO provisioned physical ports. Please ensure Step 2 is complete and ports are 'Live'.")
        return

    with st.container(border=True):
        st.markdown("##### 📍 Stitch Ethernet Virtual Circuit")
        c1, c2 = st.columns(2)
        
        with c1:
            a_alias = st.selectbox("A-Side Port (UNI-A)", options=list(port_options.keys()), key="evc_a")
            service_bw = st.select_slider("EVC Bandwidth", options=["10M", "100M", "1000M", "10000M"], value="1000M")
            bw_int = int(service_bw.replace("M", ""))
        
        with c2:
            # Filter A-Side out of Z-Side options to prevent self-looping
            z_options = [k for k in port_options.keys() if k != a_alias]
            z_alias = st.selectbox("Z-Side Port (UNI-Z)", options=z_options, key="evc_z")
            
            # Default name based on the Service Alias in JSON#2
            svc_alias = manager_payload.get("service_context", {}).get("alias", "E-Line")
            conn_name = st.text_input("Circuit ID / Name", value=f"EVC-{svc_alias}")

        if st.button("➕ Queue EVC Stitch", use_container_width=True, type="secondary"):
            if not conn_name.strip():
                st.error("❌ EVC Name cannot be blank.")
            else:
                new_evc = {
                    "service_id": manager_payload.get("service_id"),
                    "connection_name": conn_name.strip(),
                    "connector_a_id": port_options[a_alias],
                    "connector_a_table": "ports",          
                    "connector_b_id": port_options[z_alias],
                    "connector_b_table": "ports",          
                    "connection_status": "Planned",
                    "service_bw": bw_int,
                    "health_status": 4, # 4 = Pending/Unknown
                    "vrf_name": svc_alias # E-Line often uses service alias as the bridge ID
                }
                
                # Append to the intent queue in JSON#2
                children.setdefault("fabric_connections", []).append(new_evc)
                st.toast(f"✅ Queued EVC: {conn_name}")
                st.rerun()

    # 3. Local View: Show what is currently staged in JSON#2
    staged_conns = children.get("fabric_connections", [])
    if staged_conns:
        st.divider()
        st.markdown(f"### 📋 Staged EVCs ({len(staged_conns)})")
        df = pd.DataFrame(staged_conns)[["connection_name", "service_bw", "connection_status"]]
        st.dataframe(df, use_container_width=True, hide_index=True)

def _render_generic_workflow(manager_payload: dict):
    """
    Fallback Workflow: Provides a generic attachment form for 
    unsupported or new service types.
    """
    import streamlit as st
    import pandas as pd

    # Resolve context from JSON#2
    svc_context = manager_payload.get("service_context", {})
    svc_type = svc_context.get("service_type", "GENERIC")
    children = svc_context.get("children", {})
    
    st.subheader(f"🔗 Generic Connection: {svc_type}")
    st.warning(f"Note: No specialized logic defined for {svc_type}. Using manual UUID mapping.")

    # Access Live Manifest (JSON#1) for raw selection
    live = st.session_state.live_manifest
    
    # Create broad maps for "Any-to-Any" stitching
    # This allows a user to manually link any Interface to any Cloud Connection
    intf_map = {i['interface_name']: i['interface_id'] for i in live.get("fabric_interfaces", [])}
    cloud_map = {f"{c['connection_name']}": c['cloud_connection_id'] for c in live.get("cloud_connections", [])}

    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            side_a = st.selectbox("Source (Interface)", options=list(intf_map.keys()), key="gen_a")
            bw = st.number_input("Bandwidth (Mbps)", min_value=10, value=1000, step=100)
            
        with col2:
            side_b = st.selectbox("Destination (Cloud)", options=list(cloud_map.keys()), key="gen_b")
            conn_name = st.text_input("Connection Name", value=f"GEN-{side_a[:5]}")

        if st.button("➕ Queue Generic Stitch", use_container_width=True):
            if not side_a or not side_b:
                st.error("Both Source and Destination are required.")
            else:
                new_stitch = {
                    "service_id": manager_payload.get("service_id"),
                    "connection_name": conn_name.strip(),
                    "connector_a_id": intf_map[side_a],
                    "connector_a_table": "interfaces",
                    "connector_b_id": cloud_map[side_b],
                    "connector_b_table": "cloud_connections",
                    "service_bw": int(bw),
                    "connection_status": "Planned",
                    "health_status": 4
                }
                
                children.setdefault("fabric_connections", []).append(new_stitch)
                st.toast("Generic connection queued.")
                st.rerun()

    # Shared Table View for Staged Items
    staged = children.get("fabric_connections", [])
    if staged:
        st.divider()
        st.dataframe(pd.DataFrame(staged)[["connection_name", "service_bw", "connection_status"]], 
                     use_container_width=True, hide_index=True)
        
    # =====================================================================
    # 🛡️ LEGACY WRAPPERS & BACKWARD COMPATIBILITY
    # Do not remove these until all legacy code references are updated.
    # =====================================================================

def render_fabric_port_form_legacy(data: dict = None, service_type: str = "IPVPN"):
    """
    Legacy wrapper for old port form calls that still pass the 'data' dict.
    Routes to the new state-aware 'render_fabric_port_form'.
    """
    import streamlit as st
    
    # Optional: Add a subtle deprecation warning for developers
    # st.warning("Dev Note: This view is using a legacy function call.")
    
    # Call the new function, ignoring the passed 'data' since we now use session_state
    render_fabric_port_form(service_type=service_type)

def _render_manifest_table(conn_manifest: list, q_len: int, max_conns: int):
    """Helper to render the staged connections table."""
    import streamlit as st
    import pandas as pd
    
    st.subheader(f"📋 Connection Manifest ({q_len}/{max_conns})")
    display_cols = ["connection_name", "service_bw", "connection_type", "status"]
    view_df = pd.DataFrame(conn_manifest) if q_len > 0 else pd.DataFrame(columns=display_cols)
    
    st.data_editor(
        view_df[display_cols] if not view_df.empty else view_df, 
        use_container_width=True, 
        hide_index=True
    )

def render_p2p_stitch_form(fs_detail: dict):
    """
    Final Provisioning Step for EPL and EVPL.
    Queue Edition with Smart Defaults, Mandatory Alias, and Formatted Tables.
    Safely handles dynamic widget updating and strict None-type execution guards.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.service_wizards import rule_logic_EPL, rule_logic_EVPL
    from src.utils.api_customer import get_fabric_service_detail

    # 1. INITIALIZE QUEUE STATE
    if "fc_queue" not in st.session_state:
        st.session_state.fc_queue = []

    # 2. CONTEXT RECOVERY
    if not fs_detail or fs_detail.get("service_id") is None:
        fs_detail = st.session_state.get("active_service_detail", {})

    svc_id = fs_detail.get("service_id")
    svc_alias = fs_detail.get("service_alias") or fs_detail.get("service_name") or "New Service"
    svc_type = str(fs_detail.get("service_type", "EVPL")).upper().replace("EPLAN", "EP-LAN")

    # 3. RULE ENGINE
    if svc_type == "EPL":
        rules = rule_logic_EPL(fs_detail)
        eligible_ports = rules.get("assigned_ports", [])
        mode_label = "EPL: Dedicated Physical Path"
    else:
        rules = rule_logic_EVPL(fs_detail)
        eligible_ports = rules.get("eligible_ports", [])
        mode_label = "EVPL: Virtual Port-to-Port"

    port_map = {
        f"{p['device_name']} | {p['port_name']} ({p.get('port_speed', '10G')}) [{p.get('port_tagging')}]": p 
        for p in eligible_ports
    }

    # 4. GUARDRAIL
    if not port_map:
        st.warning(f"🔎 **No Eligible Ports Found**")
        st.write(f"Customer: **{fs_detail.get('customer_name', 'Unknown')}** | Service: **{svc_alias}**")
        if st.button("🔌 Return to Step 2: Attach Ports", use_container_width=True, type="primary"):
            st.session_state.prov_step = 2
            st.rerun()
        return

    # 5. UI HEADER
    st.markdown(f"### 🚀 Finalize {svc_type} Connection Stitch")
    st.caption(f"Mode: **{mode_label}**")

    # ==========================================
    # 🏗️ THE STITCH UI (Dynamically Linked)
    # ==========================================
    with st.container(border=True):
        c1, c2 = st.columns(2)
        
        port_options = ["-- Select Port --"] + list(port_map.keys())
        
        sel_a_label = c1.selectbox("Connector A (Source)", options=port_options, key="stitch_a")
        
        remaining_options = ["-- Select Port --"] + [opt for opt in port_map.keys() if opt != sel_a_label]
        sel_b_label = c2.selectbox("Connector B (Destination)", options=remaining_options, key="stitch_b")
        
        # ==========================================
        # 🛑 THE FIX: STRICT STATE GUARD
        # ==========================================
        invalid_states = [None, "-- Select Port --", ""]
        
        if sel_a_label in invalid_states or sel_b_label in invalid_states:
            st.info("Please select both source and destination ports to configure bandwidth and VLANs.")
        else:
            p_a, p_b = port_map[sel_a_label], port_map[sel_b_label]
            
            def get_speed(p): 
                s = str(p.get("port_speed", "10G"))
                return 100000 if "100" in s else (400000 if "400" in s else 10000)
            
            max_phys_bw = min(get_speed(p_a), get_speed(p_b))

            st.divider()
            p1, p2, p3 = st.columns([1.5, 1, 1.5])
            
            # Bandwidth Slider
            bw_labels = {10: "10M", 20: "20M", 50: "50M", 100: "100M", 200: "200M", 500: "500M", 1000: "1G", 2000: "2G", 10000: "10G"}
            bw = p1.select_slider(
                "Service Bandwidth", 
                options=[k for k in bw_labels.keys() if k <= max_phys_bw] or [10], 
                value=min(100, max_phys_bw),
                format_func=lambda x: bw_labels.get(x, f"{x}M")
            )

            # Smart Default CE-VLAN
            queued_vlans = [str(q.get("c_vlan_list")) for q in st.session_state.fc_queue if q.get("service_id") == svc_id]
            used_vlans = rules.get("used_ce_vlans", []) + queued_vlans
            
            default_vlan = 200
            while str(default_vlan) in used_vlans and default_vlan < 4094:
                default_vlan += 1

            ce_vlan = p2.number_input("CE-VLAN (Required)", min_value=1, max_value=4094, value=default_vlan)
            conn_alias = p3.text_input("Connection Alias 🛑", value=f"{svc_alias}-V{default_vlan}", help="Mandatory. Maps to connection_name.")
            
            vlan_conflict = str(ce_vlan) in used_vlans
            if vlan_conflict:
                st.error(f"🛑 CE-VLAN {ce_vlan} is already active or in your queue!")

            if st.button("➕ Add Connection to Queue", type="primary", use_container_width=True, disabled=vlan_conflict):
                if not conn_alias.strip():
                    st.error("🛑 Connection Alias is mandatory. Please provide a name.")
                else:
                    payload = {
                        "connection_name": conn_alias.strip(),
                        "service_id": svc_id,
                        "connector_a_id": p_a["port_id"],
                        "connector_a_table": "ports",
                        "connector_b_id": p_b["port_id"],
                        "connector_b_table": "ports",
                        "service_bw": bw,
                        "s_vlan": 0, 
                        "c_vlan_list": str(ce_vlan),
                        "connection_status": "Staged" 
                    }
                    st.session_state.fc_queue.append(payload)
                    st.success(f"Added '{payload['connection_name']}' to Queue!")
                    st.rerun()

    st.divider()

    # ==========================================
    # 📋 THE TABBED DATA VIEWER
    # ==========================================
    all_ports = fs_detail.get("fabric_ports", [])
    port_dict = {p["port_id"]: f"{p.get('device_name')} | {p.get('port_name')}" for p in all_ports}

    tab_queue, tab_active = st.tabs(["📋 Queued Connections", "🌐 Active Connections"])

    with tab_queue:
        if st.session_state.fc_queue:
            display_queue = []
            for q in st.session_state.fc_queue:
                p_a_name = port_dict.get(q["connector_a_id"], "Unknown Port")
                p_b_name = port_dict.get(q["connector_b_id"], "Unknown Port")
                
                display_queue.append({
                    "Alias": q["connection_name"],
                    "Ports (A ↔ B)": f"{p_a_name} ↔ {p_b_name}",
                    "Bandwidth": f"{q['service_bw']} Mbps",
                    "CE-VLAN": q["c_vlan_list"]
                })
                
            st.dataframe(pd.DataFrame(display_queue), use_container_width=True, hide_index=True)
            
            col_submit, col_clear = st.columns([3, 1])
            
            if col_submit.button("🚀 Provision All Queued Connections", type="primary", use_container_width=True):
                success_count = 0
                total_queued = len(st.session_state.fc_queue)
                
                # IMPORTANT: Ensure commit_provisioning_intent is imported globally in your file
                for fc_payload in st.session_state.fc_queue:
                    if commit_provisioning_intent(fc_payload, fs_detail):
                        success_count += 1
                        
                if success_count == total_queued:
                    st.session_state.fc_queue = [] 
                    st.session_state.active_service_detail = get_fabric_service_detail(svc_id)
                    st.session_state.prov_step = 1  
                    st.rerun()
                else:
                    st.warning(f"Provisioned {success_count} out of {total_queued} connections. Check logs.")
                
            if col_clear.button("🗑️ Clear Queue", use_container_width=True):
                st.session_state.fc_queue = []
                st.rerun()
        else:
            st.info("The queue is empty. Use the form above to stage connections.")

    with tab_active:
        active_conns = fs_detail.get("fabric_connections", [])
        if active_conns:
            display_active = []
            for c in active_conns:
                p_a_name = port_dict.get(c.get("connector_a_id"), "Unknown Port")
                p_b_name = port_dict.get(c.get("connector_b_id"), "Unknown Port")
                
                display_active.append({
                    "Alias": c.get("connection_name", "N/A"),
                    "Ports (A ↔ B)": f"{p_a_name} ↔ {p_b_name}",
                    "Bandwidth": f"{c.get('service_bw')} Mbps",
                    "CE-VLAN": c.get("c_vlan_list", "N/A"),
                    "Status": c.get("connection_status", "Active"),
                    "Health": "🟢" if c.get("health_status") == 1 else ("🔴" if c.get("health_status") == 3 else "⚪")
                })
                
            st.dataframe(pd.DataFrame(display_active), use_container_width=True, hide_index=True)
        else:
            st.info("No active connections found for this service.")

def render_l3_stitch_form(port_map: dict, intf_map: dict):
    """Form for IPVPN, MCGW, IOD (Interface to Port)"""
    import streamlit as st
    
    st.info("🌐 Mode: Layer 3 (Logical Interface ↔ Physical Port)")
    if not intf_map:
        st.error("🚨 Missing Interface JSON. Interfaces must be committed in Step 3 for L3 services.")
        return None

    c1, c2 = st.columns(2)
    sel_a_label = c1.selectbox("Connector A: Logical Interface", options=list(intf_map.keys()), key="l3_a")
    sel_b_label = c2.selectbox("Connector B: Physical Port", options=list(port_map.keys()), key="l3_b")

    st.divider()
    p1, p2 = st.columns(2)
    bw = p1.select_slider("Bandwidth (Mbps)", options=[10, 50, 100, 500, 1000, 10000], value=100)
    
    # Dynamically pull the VLAN from the interface JSON the user selected
    default_vlan = int(intf_map[sel_a_label].get("vlan_id", 0))
    vlan = p2.number_input("S-VLAN", value=default_vlan)

    return {
        "connector_a_id": intf_map[sel_a_label].get("interface_id"),
        "connector_b_id": port_map[sel_b_label].get("port_id"),
        "connector_a_table": "interface",
        "connector_b_table": "ports",
        "bandwidth": bw,
        "vlan_id": vlan
    }

def render_multipoint_l2_stitch_form(port_map: dict):
    """Form for E-LAN / Multipoint L2 Stitch (Auto-Created Interface to Multiple Ports)"""
    import streamlit as st

    st.info("🕸️ Mode: Multipoint L2 (Auto-Create Logical Interface ↔ Multiple Physical Ports)")
    if not port_map:
        st.error("🚨 No physical ports available to stitch.")
        return None

    c1, c2 = st.columns(2)
    
    # ==========================================
    # CONNECTOR A: AUTO-CREATE L2 INTERFACE
    # ==========================================
    with c1:
        st.markdown("**Connector A: New L2 Interface**")
        stitch_name = st.text_input("Interface / Domain Name", placeholder="e.g., EVPN-VLAN-100", key="mp_name")
        vlan_id = st.number_input("S-VLAN ID", min_value=1, max_value=4094, value=100, step=1, key="mp_vlan")
        mtu = 9000
        cos = 'BE'

    # ==========================================
    # CONNECTOR B: PHYSICAL PORTS
    # ==========================================
    with c2:
        st.markdown("**Connector B: Physical Ports**")
        selected_port_labels = st.multiselect(
            "Select Participating Ports (Min 2)", 
            options=list(port_map.keys()),
            key="mp_ports"
        )
        
        st.divider()
        bw = st.select_slider("Domain Bandwidth (Mbps)", options=[10, 50, 100, 500, 1000, 10000], value=100, key="mp_bw")

    # Map the selected port labels back to their underlying database IDs
    selected_port_ids = [port_map[label].get("port_id") for label in selected_port_labels]

    # Return the dictionary state instantly (just like the L3 form)
    # Added an 'is_valid' flag so the parent wizard knows if it is safe to show the Commit button
    return {
        "stitch_type": "multipoint_l2",
        "connector_a_table": "interface", 
        "connector_b_table": "ports",
        "connector_b_ids": selected_port_ids, 
        "bandwidth": bw,
        "vlan_id": vlan_id,
        "logical_interface": {
            "auto_create": True,
            "name": stitch_name,
            "vlan_id": vlan_id,
            "mtu": mtu,
            "cos": cos
        },
        "is_valid": bool(stitch_name and len(selected_port_ids) >= 2) 
    }

def commit_provisioning_intent(fc_payload: dict, fs_detail: dict):
    """
    Orchestrates the finalized payload delivery.
    Constructs the exact 'Provisioned' state for ports (Red) and connections (Green) locally.
    Keeps the API layer completely devoid of state-transition logic.
    """
    import streamlit as st
    from src.utils.api_customer import post_port_intent, post_fabric_connection
    from datetime import datetime

    customer_id = fs_detail.get("customer_id")
    
    # 1. DEFINE CONNECTION STATE (Logic is provisioned, so Health is 1 - Green)
    fc_payload.update({
        "connection_status": "Provisioned",
        "health_status": 1, 
        "updated_at": datetime.utcnow().isoformat()
    })

    # 2. DEFINE PORT STATE (Ports are allocated but physical link is down, Health is 3 - Red)
    port_ids = [fc_payload["connector_a_id"], fc_payload["connector_b_id"]]
    ports_in_manifest = {p["port_id"]: p for p in fs_detail.get("fabric_ports", [])}
    
    success = True
    
    with st.spinner("Pushing Fully Built Intent to NDT Fabric..."):
        # A. Commit the Fabric Connection (Stitch)
        if not post_fabric_connection(fc_payload):
            success = False

        # B. Commit the Port Updates
        for p_id in port_ids:
            p_data = ports_in_manifest.get(p_id)
            if p_data:
                # Build the exact mapping the API expects, injecting the explicitly chosen health
                intent_map = {
                    "port_id": p_id,
                    "device_id": p_data.get("device_id"),
                    "port": p_data.get("port_name"),
                    "speed": p_data.get("port_speed"),
                    "alias": p_data.get("port_description"),
                    "optics": p_data.get("port_optic"),
                    "port_tagging": p_data.get("port_tagging"),
                    "admin_status": p_data.get("admin_status"),
                    "port_health_status": 3  # Explicitly forcing RED state for the physical port
                }
                
                try:
                    # Pass the fully built intent to the dumb API
                    post_port_intent(
                        customer_id=customer_id, 
                        port_intent=intent_map, 
                        status_override="Provisioned"
                    )
                except Exception as e:
                    st.error(f"Failed to update port {p_id}: {str(e)}")
                    success = False

    if success:
        st.toast("✅ NDT Synchronized: Service Logic (Green) / Physical Ports (Red)", icon="🌐")
    
    return success

def render_builder_editor_form(customer_id: str, on_close_callback: callable):
    """
    Master UI layout for the BGP Policy Builder.
    Handles the Global Config, the Term List loop, and the Action Bar.
    Contains NO routing state logic (delegated via on_close_callback).
    """
    import streamlit as st
    import uuid
    
    builder = st.session_state.bgp_builder
    direction = builder.get("direction", "Import")
    is_edit_mode = builder.get("policy_id") is not None

    st.markdown(f"#### 📜 Construct {direction} Policy")
    st.caption(f"**Target Context:** `{customer_id}` | Construct hierarchical routing policies.")

    # --- 1. GLOBAL CONFIGURATION UI ---
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        builder["policy_name"] = c1.text_input("Policy Name", value=builder["policy_name"])
        
        new_direction = c2.selectbox(
            "Policy Direction", 
            ["Import", "Export"], 
            index=0 if direction == "Import" else 1,
            disabled=is_edit_mode
        )
        
        if new_direction != direction:
            builder["direction"] = new_direction
            for term in builder["terms"]:
                if new_direction == "Import":
                    term["modifiers"].pop("Set MED", None)
                    term["modifiers"].pop("Prepend AS", None)
                else:
                    term["modifiers"].pop("Set Local Pref", None)
            st.rerun()

    direction = builder["direction"]
    st.divider()

    # --- 2. TERM MANAGEMENT UI ---
    col_title, col_add = st.columns([3, 1])
    col_title.markdown("**Policy Terms (Evaluation Order)**")
    
    if col_add.button("➕ Add New Term", type="secondary", use_container_width=True):
        seq_num = (len(builder["terms"]) + 1) * 10
        builder["terms"].append({
            "term_id": str(uuid.uuid4())[:8],
            "term_name": f"SEQ-{seq_num}",
            "prefixes": [],
            "base_action": "Advertise", 
            "modifiers": {}
        })
        st.rerun()

    if not builder["terms"]:
        st.info("No terms defined. Traffic will hit the implicit default deny. Add a term to begin.")
    else:
        for term_idx, term in enumerate(builder["terms"]):
            render_bgp_term_block(term_idx, direction)

    st.divider()

    # --- 3. ACTION BAR UI (SAVE / CANCEL) ---
    b_cancel, b_save = st.columns(2)
    
    if b_cancel.button("❌ Cancel", use_container_width=True):
        on_close_callback()

    submit_label = "💾 Update Policy" if is_edit_mode else "💾 Provision Policy to Engine"
    
    if b_save.button(submit_label, type="primary", use_container_width=True):
        if not builder["terms"]:
            st.error("Cannot stage an empty policy.")
        else:
            with st.spinner("Pushing to NDT Routing Engine..."):
                try:
                    # Memory queue staging (swap to API calls when ready)
                    if "staged_policies" not in st.session_state:
                        st.session_state.staged_policies = []
                    
                    import copy
                    st.session_state.staged_policies.append(copy.deepcopy(st.session_state.bgp_builder))
                    
                    st.toast(f"✅ Policy '{builder['policy_name']}' Provisioned Successfully", icon="🚀")
                    st.session_state.pop(f"cached_policies_{customer_id}", None) 
                    
                    # Execute the return logic injected by the workflow
                    on_close_callback()
                    
                except Exception as e:
                    st.error(str(e))

def render_bgp_term_block(term_idx: int, direction: str):
    """
    Sub-component UI for editing a specific BGP Term expander.
    Handles 1:N Prefix Match conditions and context-aware Additive Actions.
    """
    import streamlit as st
    
    term = st.session_state.bgp_builder["terms"][term_idx]
    tid = term["term_id"]

    with st.expander(f"⚙️ Term: {term['term_name']} | Matches: {len(term['prefixes'])} | Action: {term['base_action']}", expanded=True):
        
        # --- TERM HEADER & DELETION ---
        h1, h2 = st.columns([4, 1])
        term["term_name"] = h1.text_input("Term Sequence / Name", value=term["term_name"], key=f"t_name_{tid}")
        
        h2.write("") 
        h2.write("")
        if h2.button("🗑️ Remove", key=f"t_del_{tid}", use_container_width=True, type="secondary"):
            st.session_state.bgp_builder["terms"].pop(term_idx)
            st.rerun()

        st.write("---")

        # ==========================================
        # 1. MATCH CONDITIONS (1 to N Prefixes)
        # ==========================================
        st.markdown("**1. Match Conditions (Prefix List)**")
        
        with st.container(border=True):
            p1, p2, p3, p4 = st.columns([3, 2, 2, 1])
            new_ip = p1.text_input("Network (e.g., 10.0.0.0/8)", key=f"p_ip_in_{tid}")
            op = p2.selectbox("Operator", ["Exact", "Or Longer (>)", "Up To (<)"], key=f"p_op_in_{tid}")
            
            is_exact = (op == "Exact")
            mask_val = p3.number_input("Mask Value", min_value=1, max_value=32, value=24, disabled=is_exact, key=f"p_mask_in_{tid}")
            
            p4.write("")
            p4.write("")
            if p4.button("➕ Add", key=f"p_add_btn_{tid}", use_container_width=True):
                if new_ip:
                    term["prefixes"].append({
                        "ip": new_ip, 
                        "operator": op, 
                        "mask_limit": None if is_exact else mask_val
                    })
                    st.rerun()

        if term["prefixes"]:
            for p_idx, p in enumerate(term["prefixes"]):
                col_info, col_del = st.columns([9, 1])
                mask_str = "" if p["operator"] == "Exact" else f" (/ {p['mask_limit']})"
                col_info.code(f"permit {p['ip']} {p['operator'].lower()}{mask_str}")
                
                if col_del.button("❌", key=f"del_p_{tid}_{p_idx}"):
                    term["prefixes"].pop(p_idx)
                    st.rerun()
        else:
            st.caption("💡 *If no prefixes are defined, this term matches ALL routes (0.0.0.0/0 orlonger).*")

        st.write("---")

        # ==========================================
        # 2. ACTIONS & MODIFIERS
        # ==========================================
        st.markdown("**2. Route Actions**")
        
        a1, a2 = st.columns(2)
        term["base_action"] = a1.radio(
            "Base Target Action", 
            ["Advertise", "Reject"], 
            horizontal=True, 
            key=f"a_base_{tid}"
        )

        mod_options = ["Add Community", "Summarize"]
        if direction == "Import":
            mod_options.append("Set Local Pref")
        elif direction == "Export":
            mod_options.append("Prepend AS")
            mod_options.append("Set MED")

        selected_mods = a2.multiselect(
            "Additive Modifiers", 
            options=mod_options, 
            default=list(term["modifiers"].keys()), 
            key=f"a_mods_{tid}"
        )

        synced_mods = {}
        for m in selected_mods:
            synced_mods[m] = term["modifiers"].get(m, "")
        term["modifiers"] = synced_mods

        if term["modifiers"]:
            with st.container(border=True):
                for mod_key in term["modifiers"]:
                    if mod_key == "Add Community":
                        term["modifiers"][mod_key] = st.text_input("Community String", value=term["modifiers"][mod_key], placeholder="e.g., 65000:100", key=f"m_comm_{tid}")
                    elif mod_key == "Set Local Pref":
                        val = int(term["modifiers"][mod_key]) if term["modifiers"][mod_key] else 100
                        term["modifiers"][mod_key] = st.number_input("Local Preference", min_value=0, value=val, key=f"m_lp_{tid}")
                    elif mod_key == "Prepend AS":
                        term["modifiers"][mod_key] = st.text_input("AS Path Prepend", value=term["modifiers"][mod_key], placeholder="e.g., 65000 65000", key=f"m_as_{tid}")
                    elif mod_key == "Set MED":
                        val = int(term["modifiers"][mod_key]) if term["modifiers"][mod_key] else 0
                        term["modifiers"][mod_key] = st.number_input("Multi-Exit Discriminator", min_value=0, value=val, key=f"m_med_{tid}")
                    elif mod_key == "Summarize":
                        st.caption("ℹ️ Summarization flag enabled. (Generates aggregate route)")

def render_private_peering_form(data: dict = None, fs_detail: dict = None):
    """
    Legacy wrapper for the old 2-part cloud form.
    Routes to the new consolidated 'render_cloud_provisioning_form'.
    """
    import streamlit as st
    
    # In the old code, service_id was buried in data or session state.
    # We attempt to reconstruct fs_detail if it wasn't passed, to satisfy the new method.
    if not fs_detail:
        svc_id = (data.get("service_id") if data else None) or st.session_state.get("prov_data", {}).get("service_id")
        fs_detail = {"service_id": svc_id}
        
    render_cloud_provisioning_form(fs_detail)


    # =====================================================================
    # OVERRIDE EXPORTS (If your legacy code uses specific imports)
    # =====================================================================
    # If your old code imports EXACTLY `from src.utils.ui_provisioning_form import render_fabric_port_form`, 
    # and passes `data` to it, rename our *new* function at the top of the file to `_render_fabric_port_form_v2`, 
    # and name the wrapper `render_fabric_port_form`.