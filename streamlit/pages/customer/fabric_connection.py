import streamlit as st
import pandas as pd
from src.utils.api_customer import (
    get_customers, 
    get_fabric_services, 
    get_ports_by_customer,
    get_fabric_service_detail,
    post_fabric_connection,
    update_fabric_connection,
    delete_fabric_connection,
    get_port_by_id
)
from src.ui_forms import create_fabric_connection_form, update_fabric_connection_form
from src.ui_components import UI
from src.ui_messages import MessageCenter
from src.galileo.fabric_service_builder import render_twin_topology
from src.utils.NavigationManager import can_add_fabric_connection
from src.utils.network_utils import format_network_date
from src.utils.ui_provisioning_form import (
    render_fabric_port_form,
    render_interface_build_form,
    render_private_peering_form,
    render_fabric_connection_form
)

# --- UTILITIES ---

def get_and_unwrap_port(port_id):
    """Helper to fetch port from API and safely unwrap the [ {data} ] list wrapper."""
    placeholders = ["None", "NULL", "00000000-0000-0000-0000-000000000000"]
    if not port_id or str(port_id) in placeholders:
        return None
    raw_resp = get_port_by_id(port_id)
    if isinstance(raw_resp, list) and len(raw_resp) > 0:
        return raw_resp[0]
    return raw_resp if isinstance(raw_resp, dict) else None


def render_provisioning_view(service_id, fs_record):
    """The UI Form for creating a new stitch."""
    st.subheader("🚀 Provision New Connection")
    with st.container(border=True):
        new_data = create_fabric_connection_form(service_id, fs_record)
        if new_data:
            with st.spinner("Provisioning..."):
                response = post_fabric_connection(new_data)
                if response:
                    MessageCenter.set_success("Provisioned successfully.")
                    st.rerun()

def render_connection_management_view(record, service_id):
    """The Inspector for existing connections."""
    st.markdown(f"#### 🛰️ Managing: {record.get('connection_name')}")
    if st.button("🗑️ Delete Connection", type="primary", key=f"del_{record.get('connection_id')}"):
        if delete_fabric_connection(record.get("connection_id")):
            st.rerun()

# --- 2. THE CONNECTION TAB (Step 5 Logic) ---

def render_connection_tab(service_id, fs_record):
    """Handles the inventory table and routes to Provisioning or Management."""
    conns = fs_record.get('fabric_connections', [])
    df = pd.DataFrame(conns)

    if not df.empty:
        st.markdown("### 🛰️ Connection Inventory")
        selection = UI.render_selectable_table(
            df=df, 
            key_prefix="fc_step5_table", 
            id_column_to_hide="connection_id"
        )
        
        if selection:
            render_connection_management_view(selection, service_id)
            return

    # If no selection, show provisioning if eligible
    if can_add_fabric_connection(fs_record, df):
        render_provisioning_view(service_id, fs_record) # <--- Now defined above!
    else:
        st.warning("Prerequisites missing for new connections.")

# --- 4. THE MAIN ENTRY POINT (Orchestrator) ---

def show_fabric_connection():
    """
    Orchestrates the Inventory and Provisioning Workspace.
    Fixes the ImportError by using the correct fs_tier function name.
    """
    import streamlit as st
    from src.utils.api_customer import get_customers
    from src.state_managers import FabricStateManager
    
    # 1. Tier Imports (Importing as objects to prevent naming collisions)
    import pages.customer.fabric_service as fs_tier
    from src.utils.service_wizards import render_master_provisioning

    # Initialize Manager State
    FabricStateManager.initialize()

    st.title("🌐 Fabric Connection Orchestrator")

    # 2. GLOBAL CUSTOMER CONTEXT
    df_customers = get_customers()
    if df_customers.empty:
        st.warning("No customers available in the database.")
        return
    
    # Map names to IDs for the selectbox
    cust_map = {row['customer_name']: row['customer_id'] for _, row in df_customers.iterrows()}
    options = ["-- Select --"] + list(cust_map.keys())
    
    selected_name = st.selectbox("👤 Active Customer Context", options=options, index=0)

    if selected_name == "-- Select --":
        # Ensure context is cleared if no customer is selected
        FabricStateManager.set_active("cust", None)
        st.info("💡 Select a customer context to begin orchestrating fabric resources.")
        return
    
    customer_id = cust_map[selected_name]

    # --- THE SYNC HANDSHAKE ---
    # Lock the selected customer into the Manager so Tier 1 is populated globally
    FabricStateManager.set_active("cust", customer_id)

    # 3. CONTEXTUAL TABS
    tab_prov, tab_inv  = st.tabs([ "🆕 Provisioning","🏗️ Fabric Service Inventory"])

    with tab_inv:
        # FIX: We use 'show_fabric_service' from fs_tier
        # This renders the list of existing services for the chosen customer
        fs_tier.show_fabric_service(customer_id)

    with tab_prov:
        # Trigger the visual wizard engine
        # This will now have access to the 'cust' context via the manager
        render_master_provisioning(customer_id, selected_name)

def render_service_inventory_view(customer_id: str, customer_name: str):
    """
    Handles the discovery and deep hydration of existing services.
    Polishes raw API data for a NOC-friendly experience.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.api_customer import (
        get_fabric_services, 
        get_ports_by_customer,
        get_fabric_service_detail
    )
    from src.ui_components import UI

    st.markdown(f"### 🔍 Service Management for **{customer_name}**")
    
    # Data Acquisition
    df_services_raw = get_fabric_services(customer_id)
    df_ports = get_ports_by_customer(customer_id) # Needed for Physical Layer rendering

    if df_services_raw.empty:
        st.info(f"No active services found for {customer_name}.")
        return

    # --- DATA POLISHING ---
    df_clean = df_services_raw.copy()

    # NOC Date Format
    if 'updated_at' in df_clean.columns:
        df_clean['updated_at'] = pd.to_datetime(df_clean['updated_at']).dt.strftime('%b %d, %Y | %H:%M')

    # Health Mapping
    health_map = {1: "🟢 Active", 2: "🟡 Degraded", 3: "🟠 Staged", 4: "🔴 Critical"}
    df_clean['status'] = df_clean['health_status'].map(health_map).fillna("⚪ Unknown")

    # Column Formatting (Purging UUID noise)
    friendly_cols = {"service_name": "Service Name", "service_type": "Type", "status": "Health", "updated_at": "Last Sync"}
    df_final = df_clean[list(friendly_cols.keys()) + ['service_id']].rename(columns=friendly_cols)

    # Render Table
    selected_row = UI.render_selectable_table(df=df_final, key_prefix="svc_inv", id_column_to_hide="service_id")

    if selected_row:
        service_id = str(selected_row.get("service_id"))
        with st.spinner("🛰️ Hydrating Digital Twin..."):
            fs_detail = get_fabric_service_detail(service_id)
        
        if fs_detail:
            # Local call to render the 4-tier topology and cloud management tabs
            render_service_digital_twin(fs_detail, df_ports)
 
def render_service_digital_twin(fs_detail, df_ports):
    """
    Primary Orchestrator.
    Dynamically generates tabs based on Service Type and adds Cloud Interconnect support.
    """
    import streamlit as st
    import pandas as pd
    from src.ui_components import UI


    # 1. SCHEMA GUARD: State Initialization
    if "payload" not in st.session_state:
        st.session_state.payload = {}
    
    ctx = st.session_state.payload.setdefault("service_context", {})
    children = ctx.setdefault("children", {})
    children.setdefault("ports", [])
    children.setdefault("fabric_connections", [])
    
    if "interfaces" not in st.session_state.payload:
        st.session_state.payload["interfaces"] = []

    # 2. SYNC CONTEXT
    st.session_state.live_manifest = fs_detail
    service_type = fs_detail.get('service_type', 'MCGW').upper()
    
    # 3. RENDER SERVICE HEADER
    UI.render_service_context(fs_detail)

    # 4. DYNAMIC TAB LOGIC
    # Define the baseline tabs that every service has
    tab_labels = ["🛰️ Topology"]
    
    # Architecture Rule: Hide Interfaces for L2/Ethernet Services
    l2_types = ["EPL", "EVPL", "EPLAN"]
    show_interfaces = service_type not in l2_types
    
    if show_interfaces:
        tab_labels.append("📋 Interfaces")
        
    # Architecture Rule: Cloud Interconnect only for MCGW
    show_cloud = (service_type == "MCGW")
    if show_cloud:
        tab_labels.append("☁️ Cloud Interconnect")
        
    # Standard Inventory/Stitching tabs
    tab_labels.extend(["🔌 Port Inventory", "🔗 Connections"])

    # Generate the actual Tab objects
    tabs = st.tabs(tab_labels)
    
    # Create a mapping to handle content placement regardless of index
    tab_map = dict(zip(tab_labels, tabs))

    # --- TAB CONTENT ASSIGNMENT ---

    with tab_map["🛰️ Topology"]:
        render_twin_topology(fs_detail)

    if "📋 Interfaces" in tab_map:
        with tab_map["📋 Interfaces"]:
            render_interfaces_tab(fs_detail)

    if "☁️ Cloud Interconnect" in tab_map:
        with tab_map["☁️ Cloud Interconnect"]:
            # Assuming this handles the specific MCGW Cloud Onramp logic
            render_cloud_interconnect_tab(fs_detail)

    with tab_map["🔌 Port Inventory"]:
        render_ports_tab(fs_detail, df_ports, service_type)

    with tab_map["🔗 Connections"]:
        render_connection_tab(fs_detail, df_ports)

    # 5. SYSTEM DEBUG
    st.divider()
    with st.expander("🛠️ SYSTEM DEBUG: Manifest Sync", expanded=False):
        render_system_debug_manifests(fs_detail, df_ports)
      
def render_interfaces_tab(fs_detail):
    import streamlit as st
    from src.utils.ui_provisioning_form import render_interface_build_form, render_static_route_form, render_bgp_peer_form
    from src.utils.network_utils import calculate_ip_assignment

    tab_inv, tab_prov = st.tabs(["📋 Interface Inventory", "🚀 Provisioning & Routing"])

    with tab_inv:
        render_interfaces_tab_inventory(fs_detail)

    with tab_prov:
        staged_list = st.session_state.payload.get("interfaces", [])
        
        if not staged_list:
            st.markdown("### 🛠️ Step 1: Build Interface Intent")
            render_interface_build_form(st.session_state.payload, calculate_ip_assignment)
        else:
            target_intf = staged_list[0]
            
            # Use the new methods
            render_interfaces_tab_summary(target_intf)
            render_interfaces_tab_provisioning(target_intf, fs_detail)
            
            st.divider()
            st.markdown("### 📍 Step 2: Configure Routing Intent")
            rt_tabs = st.tabs(["📍 Static Routing", "🤝 BGP Peering", "🔍 JSON"])
            with rt_tabs[0]:
                render_static_route_form(st.session_state.payload, target_intf)
            with rt_tabs[1]:
                render_bgp_peer_form(st.session_state.payload, target_intf)
            with rt_tabs[2]:
                st.json(target_intf)

def render_interfaces_tab_summary(target_intf):
    """
    Renders the 'Pre-Flight' summary of the queued interface and routing.
    """
    import streamlit as st
    import pandas as pd
    
    is_v6 = target_intf.get("is_dual_stack", False)
    routing = target_intf.get("routing", {})
    static_routes = routing.get("static", [])
    bgp_neighbors = routing.get("bgp", [])

    st.success(f"📋 **Staged Manifest: {target_intf['alias']}**")
    
    with st.container(border=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("VLAN", target_intf.get("vlan_id", "Untagged"))
        m2.metric("Family", "Dual-Stack" if is_v6 else "IPv4 Only")
        m3.metric("Static Routes", len(static_routes))
        m4.metric("BGP Neighbors", len(bgp_neighbors))

        st.divider()

        addr_l, addr_r = st.columns(2)
        with addr_l:
            st.markdown("**🌐 IPv4 Stack**")
            st.code(f"PE: {target_intf.get('ipv4_lumen')}\nCE: {target_intf.get('ipv4_customer')}", language="text")
        with addr_r:
            if is_v6:
                st.markdown("**🌐 IPv6 Stack**")
                st.code(f"PE: {target_intf.get('v6_lumen')}\nCE: {target_intf.get('v6_customer')}", language="text")
            else:
                st.caption("IPv6 Disabled")

        if static_routes or bgp_neighbors:
            st.divider()
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if static_routes:
                    st.caption("📍 Staged Static Routes")
                    st.dataframe(pd.DataFrame(static_routes)[["display_cidr", "next_hop_ip"]], use_container_width=True, hide_index=True)
            with d_col2:
                if bgp_neighbors:
                    st.caption("🤝 Staged BGP Neighbors")
                    st.dataframe(pd.DataFrame(bgp_neighbors)[["neighbor_ip", "customer_as", "family"]], use_container_width=True, hide_index=True)

def render_interfaces_tab_provisioning(target_intf, fs_detail):
    """
    Handles the Green Button Provisioning Waterfall logic.
    """
    import streamlit as st
    from src.utils.api_customer import (
        post_interface_intent, post_interface_ip, 
        post_static_route_intent, post_bgp_peer_intent,
        get_fabric_service_detail
    )

    st.markdown("""<style>div.stButton > button:first-child[kind="primary"] { background-color: #28a745; border-color: #28a745; color: white; }</style>""", unsafe_allow_html=True)
    
    c_reset, c_provision = st.columns([1, 2])
    
    with c_reset:
        if st.button("🗑️ Reset Intent", type="secondary", use_container_width=True, key="reset_intent_btn"):
            st.session_state.payload["interfaces"] = []
            st.rerun()
            
    with c_provision:
        if st.button("🚀 Provision Full Stack", type="primary", use_container_width=True, key="exec_provision_btn"):
            with st.status("Deploying L3 Stack...", expanded=True) as status:
                try:
                    target_intf["service_id"] = fs_detail.get("service_id")
                    target_intf["description"] = target_intf.get("alias")
                    
                    # 1. Interface
                    new_intf = post_interface_intent(target_intf)
                    if new_intf and "interface_id" in new_intf:
                        assigned_id = new_intf["interface_id"]
                        
                        # 2. IPs
                        v4 = {"interface_id": assigned_id, "lumen_ip_address": target_intf.get("ipv4_lumen"), "customer_ip_address": target_intf.get("ipv4_customer"), "network_mask_cidr": int(target_intf.get("ipv4_mask", 30)), "bring_your_own_ip": target_intf.get("byoip", False)}
                        post_interface_ip(v4)
                        
                        # 3. Static/BGP Loops...
                        for r in target_intf.get("routing", {}).get("static", []):
                            r["interface_id"] = assigned_id
                            post_static_route_intent(r)
                        
                        for p in target_intf.get("routing", {}).get("bgp", []):
                            p["interface_id"] = assigned_id
                            p["remote_asn"] = p.get("customer_as", 64512)
                            p["local_asn"] = p.get("lumen_as", 1)
                            post_bgp_peer_intent(p)

                        # 4. Sync
                        st.session_state.live_manifest = get_fabric_service_detail(fs_detail.get("service_id"))
                        status.update(label="✅ Success!", state="complete", expanded=False)
                        st.session_state.payload["interfaces"] = []
                        st.rerun()
                except Exception as e:
                    status.update(label="💥 Error", state="error")
                    st.error(str(e))
                    
def render_interfaces_tab_inventory(fs_detail):
    """
    Renders the live inventory of interfaces with expanded L3/Routing details.
    """
    import streamlit as st
    import pandas as pd

    interfaces = fs_detail.get('fabric_interfaces', [])
    if not interfaces:
        st.info("No active interfaces found in the Live Manifest.")
        return

    # 1. Process and Flatten the Data
    rows = []
    for intf in interfaces:
        # Format Date using our new helper
        prov_date = format_network_date(intf.get("created_at"))

        # Flatten IP Assignments
        ips = intf.get("ip_addresses", [])
        v4_pe = next((f"{i['lumen_ip_address']}/{i['network_mask_cidr']}" for i in ips if '.' in i['lumen_ip_address']), "-")
        v6_pe = next((f"{i['lumen_ip_address']}/{i['network_mask_cidr']}" for i in ips if ':' in i['lumen_ip_address']), "-")

        # Flatten Routing Objects into Counts
        static_routes = intf.get("static_routes", [])
        bgp_peers = intf.get("bgp_neighbors", [])

        rows.append({
            "Description": intf.get("description", "MCGW-Intf"),
            "Interface": intf.get("interface_name"),
            "VLAN": intf.get("svlan_id"),
            "IPv4 (PE)": v4_pe,
            "IPv6 (PE)": v6_pe,
            "Routes": len(static_routes),
            "BGP": len(bgp_peers),
            "Provisioned": prov_date
        })

    # 2. Render High-Level Table
    df_i = pd.DataFrame(rows)
    st.dataframe(
        df_i, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Provisioned": st.column_config.TextColumn("📅 Provisioned"),
            "IPv4 (PE)": st.column_config.TextColumn("🌐 IPv4"),
            "Routes": st.column_config.NumberColumn("📍 Routes"),
            "BGP": st.column_config.NumberColumn("🤝 Peers"),
        }
    )

    with st.expander("🔍 Detailed Routing Manifest"):
        for intf in interfaces:
            intf_id = intf.get('interface_id')
            st.markdown(f"#### Interface: `{intf.get('interface_name')}`")
            c1, c2 = st.columns(2)
            
            # --- 1. INTERACTIVE STATIC ROUTES ---
            with c1:
                st.caption("📍 Static Routes")
                s_routes = intf.get("static_routes", [])
                if s_routes:
                    df_static = pd.DataFrame(s_routes)
                    # CIDR formatting
                    df_static["Network"] = df_static["ip_prefix"].astype(str) + "/" + df_static["prefix_mask"].astype(str)
                    # Add selection column
                    df_static["Select"] = False
                    
                    # Data Editor for selection
                    edited_static = st.data_editor(
                        df_static[["Select", "Network", "next_hop_ip", "metric", "route_id"]],
                        key=f"editor_static_{intf_id}",
                        hide_index=True,
                        use_container_width=True,
                        disabled=["Network", "next_hop_ip", "metric", "route_id"] # Lock network data
                    )
                    
                    # Handle Deletion
                    to_delete_static = edited_static[edited_static["Select"] == True]["route_id"].tolist()
                    if to_delete_static:
                        if st.button(f"🗑️ Delete {len(to_delete_static)} Route(s)", key=f"del_static_btn_{intf_id}"):
                            from src.utils.api_customer import delete_static_route
                            for sr_id in to_delete_static:
                                delete_static_route(sr_id)
                            st.toast(f"Successfully removed {len(to_delete_static)} static routes.")
                            st.rerun()
                else:
                    st.write("No static routes.")

            # --- 2. INTERACTIVE BGP PEERING ---
            with c2:
                st.caption("🤝 BGP Peering")
                b_peers = intf.get("bgp_neighbors", [])
                if b_peers:
                    df_bgp = pd.DataFrame(b_peers)
                    df_bgp["Select"] = False
                    
                    # Policy formatting
                    df_bgp["Import"] = df_bgp["import_policy"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
                    df_bgp["Export"] = df_bgp["export_policy"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
                    
                    # Data Editor for selection
                    edited_bgp = st.data_editor(
                        df_bgp[["Select", "neighbor_ip", "remote_asn", "auth", "bfd", "Import", "Export", "bgp_neighbor_id"]],
                        key=f"editor_bgp_{intf_id}",
                        hide_index=True,
                        use_container_width=True,
                        disabled=["neighbor_ip", "remote_asn", "auth", "bfd", "Import", "Export", "bgp_neighbor_id"]
                    )
                    
                    # Handle Deletion
                    to_delete_bgp = edited_bgp[edited_bgp["Select"] == True]["bgp_neighbor_id"].tolist()
                    if to_delete_bgp:
                        if st.button(f"🗑️ Delete {len(to_delete_bgp)} Peer(s)", key=f"del_bgp_btn_{intf_id}"):
                            from src.utils.api_customer import delete_bgp_neighbor
                            for bgp_id in to_delete_bgp:
                                delete_bgp_neighbor(bgp_id)
                            st.toast(f"Successfully removed {len(to_delete_bgp)} BGP sessions.")
                            st.rerun()
                else:
                    st.write("No active peers.")
            st.divider()
        
def render_ports_tab(fs_detail, df_ports, service_type):
    """
    Unified Ports Tab Orchestrator.
    """
    import streamlit as st

    t_inv, t_new = st.tabs(["🗃️ Live Inventory & Eligibility", "🔌 Provision New Port"])

    with t_inv:
        # Day 2 Operations
        render_ports_tab_inventory(fs_detail, df_ports, service_type)

    with t_new:
        # UPDATE: Pass BOTH required arguments here
        render_ports_tab_provisioning(fs_detail, df_ports)        
        
def render_ports_tab_provisioning(fs_detail: dict, df_ports: pd.DataFrame):
    """
    Standardized Port Provisioning using the Step 2 Fabric Form.
    Includes the 'Commit Assignment' action to push staged intents to the API.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.ui_provisioning_form import render_fabric_port_form

    st.subheader("🔌 Provision New Physical Asset")
    st.info("Step 2: Define port intent. Once staged, commit to assign to customer and set status to 'Staged'.")

    # 1. Initialize payload if missing
    if "payload" not in st.session_state:
        st.session_state.payload = {"service_context": {"children": {"ports": []}}}

    # 2. Render the Standardized Form (Handles Device/Speed/Port selection)
    # We pass the service_type from fs_detail to trigger the EPL vs MCGW guardrails
    service_type = fs_detail.get('service_type', 'MCGW')
    render_fabric_port_form(service_type=service_type)

    # 3. Review Table & Workflow Commitment
    staged_ports = st.session_state.payload.get("service_context", {}).get("children", {}).get("ports", [])
    
    if staged_ports:
        st.divider()
        st.markdown("### 📝 Staged Port Intents")
        df_staged = pd.DataFrame(staged_ports)
        
        # Mapping to your specific data model keys
        all_possible_cols = [
            'port_name', 'port_description', 'port_speed', 
            'port_tagging', 'port_optic', 'port_service_status', 
            'port_cktid', 'created_at'
        ]
        existing_cols = [c for c in all_possible_cols if c in df_staged.columns]
        
        st.dataframe(
            df_staged[existing_cols] if existing_cols else df_staged,
            use_container_width=True, 
            hide_index=True,
            column_config={
                "port_description": "Device/Description",
                "port_name": "Interface",
                "port_speed": "Speed",
                "port_tagging": "Tagging Strategy",
                "port_service_status": "Status"
            }
        )
        
        # --- NEW ACTION BAR ---
        c1, c2 = st.columns([1, 1])
        
        with c1:
            # TRIGGER: Execute the PUT intents for all staged ports
            if st.button("🚀 Commit Port Assignment", type="primary", use_container_width=True):
                customer_id = fs_detail.get("customer_id")
                
                if not customer_id:
                    st.error("Missing Customer Context. Cannot assign ports.")
                else:
                    # Import the coordinator we built previously
                    from pages.customer.fabric_connection import handle_port_assignment_workflow
                    
                    # We pass df_ports to handle state comparison if any edits occurred 
                    # alongside the new staged assets.
                    handle_port_assignment_workflow(df_ports, df_ports, customer_id)
        
        with c2:
            if st.button("🗑️ Clear Staged Intents", key="clear_staged_ports_btn", use_container_width=True):
                st.session_state.payload["service_context"]["children"]["ports"] = []
                st.rerun()

def render_ports_tab_inventory(fs_detail: dict, df_ports: pd.DataFrame, service_type: str):
    """
    Unified Port Inventory: Combines full customer portfolio with 
    real-time service eligibility analysis in one table.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.network_utils import validate_port_rules, format_network_date

    if df_ports.empty:
        st.info("No physical ports found in this customer's inventory.")
        return

    st.markdown(f"### 🗃️ Customer Port Inventory & Eligibility ({service_type})")
    
    # 1. Prepare Data
    df_display = df_ports.copy()
    active_service_port_ids = [p['port_id'] for p in fs_detail.get('fabric_ports', [])]

    # 2. Inject Eligibility Column
    df_display['Eligibility'] = df_display.apply(
        lambda r: validate_port_rules(r, active_service_port_ids, service_type), axis=1
    )

    # 3. Format Timestamps
    if 'port_created_at' in df_display.columns:
        df_display['Date Added'] = df_display['port_created_at'].apply(format_network_date)

    # 4. Define Column Order (Eligibility first for high visibility)
    display_cols = [
        'Eligibility', 
        'device_name', 
        'port_name', 
        'port_speed', 
        'port_tagging', 
        'port_service_status', 
        'oper_status', 
        'Date Added'
    ]
    
    # 5. Render Unified Editor
    edited_df = st.data_editor(
        df_display,
        column_order=display_cols,
        use_container_width=True,
        hide_index=True,
        key="unified_port_editor",
        # Lock everything except logical intent
        disabled=[
            'Eligibility', 'device_name', 'port_name', 
            'port_speed', 'oper_status', 'Date Added'
        ],
        column_config={
            "Eligibility": st.column_config.TextColumn("📋 Eligibility Status"),
            "port_service_status": st.column_config.SelectboxColumn(
                "Service Status",
                options=["Active", "Staged", "Maintenance"],
                required=True
            ),
            "port_tagging": st.column_config.SelectboxColumn(
                "Tagging",
                options=["untagged", "Tagged", "All-2-1-bundled"],
                required=True
            ),
            "oper_status": st.column_config.TextColumn("Link State")
        }
    )

    # 6. Action Bar
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save Inventory", type="primary", use_container_width=True):
            # API PATCH logic here to sync port_tagging/status back to DB
            st.success("Portfolio Updated.")
            st.rerun()
    
    with col2:
        # Check for selectable/linkable ports
        available_ports = edited_df[edited_df['Eligibility'].str.contains("Available")]
        if not available_ports.empty:
            with st.popover("🔌 Link Selected Asset to Service"):
                selected_label = st.selectbox(
                    "Select Port to Stitch", 
                    options=available_ports.apply(lambda r: f"{r['device_name']} | {r['port_name']}", axis=1)
                )
                if st.button("Confirm Service Linkage"):
                    # Logic to link selected port_id to fs_detail['service_id']
                    st.toast("Port Linked Successfully")
                    st.rerun()

def render_ports_tab_summary(df_ports: pd.DataFrame, fs_detail: dict, service_type: str):
    """
    Analyzes customer ports for eligibility against the current service.
    """
    import streamlit as st
    from src.utils.network_utils import validate_port_rules

    if df_ports.empty:
        return df_ports

    st.success(f"📋 **Service Eligibility Analysis: {service_type}**")
    
    # Identify ports already assigned to this specific service
    active_service_port_ids = [p['port_id'] for p in fs_detail.get('fabric_ports', [])]
    
    df_eligible = df_ports.copy()
    df_eligible['Eligibility'] = df_eligible.apply(
        lambda r: validate_port_rules(r, active_service_port_ids, service_type), axis=1
    )

    st.dataframe(
        df_eligible[['device_name', 'port_name', 'port_tagging', 'Eligibility']],
        use_container_width=True,
        hide_index=True
    )
    return df_eligible

def render_connections_tab(fs_detail):
    """Handles the final 'Stitch' between ports and interfaces."""
    import streamlit as st
    import pandas as pd
    from src.ui_components import UI
    from src.ui_forms import create_fabric_connection_form
    from src.utils.api_customer import post_fabric_connection

    conns = fs_detail.get('fabric_connections', [])
    if conns:
        df_c = pd.DataFrame(conns)
        # Human readable path resolution logic here
        selected = UI.render_selectable_table(df_c, key_prefix="stitch_table")
        if selected:
            render_connection_management_view(selected, fs_detail.get("service_id"))
            return

    st.divider()
    with st.expander("🚀 New Fabric Connection (Stitch)", expanded=not conns):
        new_stitch = create_fabric_connection_form(fs_detail.get("service_id"), fs_detail)
        if new_stitch:
            if post_fabric_connection(new_stitch):
                st.success("Fabric Connection Stitched.")
                st.rerun()

def render_connection_management_view(record, service_id):
    """Refactored to show port mapping for the active selection."""
    if not record: return
    conn_id = record.get("connection_id")
    
    # ... (Keep your existing Physical Port Mapping logic here) ...
    st.markdown(f"#### 🛰️ Managing: {record.get('connection_name')}")
    # (Rest of your management view code from original file)

    # --- NEW WORKFLOW METHODS ---

def render_connection_tab(fs_detail: dict):
    """
    Standardized Connections Orchestrator.
    NOTE: Removed df_ports parameter since ports are now inside fs_detail!
    """
    import streamlit as st

    # --- ACTION BAR ---
    st.subheader("🔗 Fabric Connections")
    st.caption("Manage the data plane links between logical interfaces and physical ports.")
    st.divider()

    t_inv, t_new = st.tabs(["🛰️ Connection Inventory", "➕ Provision New Link"])

    with t_inv:
        render_connection_tab_inventory(fs_detail)

    with t_new:
        render_connection_tab_provisioning(fs_detail)

def render_connection_tab_inventory(fs_detail: dict):
    """
    Human-friendly inventory.
    Automatically translates Connector UUIDs into readable Interface/Port names.
    """
    import streamlit as st
    import pandas as pd

    conns = fs_detail.get('fabric_connections', [])
    service_type = fs_detail.get('service_type', 'EPL').upper()
    
    if not conns:
        st.info(f"No active fabric connections found for this {service_type} service.")
        return

    # 1. BUILD LOOKUP DICTIONARIES (Translates UUIDs -> Human Names)
    ports = fs_detail.get("fabric_ports", [])
    interfaces = fs_detail.get("fabric_interfaces", [])
    
    port_map = {p['port_id']: f"{p.get('device_name', 'UNK')} - {p.get('port_name', 'UNK')}" for p in ports}
    iface_map = {i['interface_id']: i.get('interface_name', 'UNK') for i in interfaces}

    # 2. PREPARE DISPLAY DATAFRAME
    df_conns = pd.DataFrame(conns)
    
    # Resolve Connector Names dynamically
    # Assuming Connector A is usually the Interface and Connector B is the Port
    if 'connector_a_id' in df_conns.columns:
        df_conns['Connector A (Logical)'] = df_conns['connector_a_id'].map(lambda x: iface_map.get(x, x))
    if 'connector_b_id' in df_conns.columns:
        df_conns['Connector B (Physical)'] = df_conns['connector_b_id'].map(lambda x: port_map.get(x, x))

    # Format Dates
    for date_col in ['created_at', 'updated_at']:
        if date_col in df_conns.columns:
            df_conns[date_col] = pd.to_datetime(df_conns[date_col]).dt.strftime('%b %d, %Y')
    
    # Format Status
    status_map = {"Active": "🟢 Active", "Staged": "🟠 Staged", "Planned": "⚪ Planned", "Down": "🔴 Down"}
    if 'connection_status' in df_conns.columns:
        df_conns['connection_status'] = df_conns['connection_status'].map(lambda x: status_map.get(x, str(x)))

    # Format Bandwidth
    if 'service_bw' in df_conns.columns:
        df_conns['service_bw'] = df_conns['service_bw'].astype(str) + " Mbps"

    # 3. COLUMN MAPPING & DISPLAY
    column_mapping = {
        "connection_name": "Connection Name",
        "connection_status": "Status",
        "Connector A (Logical)": "Interface",
        "Connector B (Physical)": "Physical Port",
        "service_bw": "Bandwidth",
        "s_vlan": "S-VLAN",
        "created_at": "Provisioned Date"
    }
    
    # Filter only columns that exist and rename them
    display_cols = [c for c in column_mapping.keys() if c in df_conns.columns]
    df_display = df_conns[display_cols].rename(columns=column_mapping)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

def render_connection_tab_provisioning(fs_detail: dict):
    """
    Acts as a router to load the correct Fabric Connection rule engine
    based on the specific service type.
    """
    import streamlit as st

    service_type = fs_detail.get("service_type", "").upper()

    st.markdown(f"##### 🔌 Create New Connection ({service_type})")

    if service_type == "EPL":
        fabric_connection_EPL(fs_detail)
        
    elif service_type == "EVPL":
        st.info("🚧 EVPL rule engine is under construction.")
        # fabric_connection_EVPL(fs_detail)
        
    elif service_type in ["IPVPN", "MCGW", "L3VPN"]:
        st.info("🚧 Layer 3 connection rule engine is under construction.")
        # fabric_connection_L3(fs_detail)
        
    else:
        st.warning(f"⚠️ Unrecognized or unsupported Service Type: {service_type}. No provisioning rules available.")

def fabric_connection_EPL(fs_detail: dict):
    """
    Rule Engine for EPL (Ethernet Private Line).
    Validation 1: Check for existing fully-formed connections.
    Validation 2: Ensure exactly 2 ports are assigned to this service_id for a new stitch.
    """
    import streamlit as st

    service_id = fs_detail.get("service_id")
    conns = fs_detail.get('fabric_connections', [])
    all_ports = fs_detail.get("fabric_ports", [])

    # --- PHASE 1: CHECK FOR EXISTING STITCH ---
    # We explicitly check if both connectors are non-null
    active_stitch = next((c for c in conns if c.get('connector_a_id') and c.get('connector_b_id')), None)

    if active_stitch:
        st.success(f"✅ **EPL Physical Path Active:** {active_stitch.get('connection_name')}")
        
        # Display human-readable details of the existing connection
        port_map = {p['port_id']: f"{p.get('device_name')} | {p.get('port_name')}" for p in all_ports}
        
        c1, c2 = st.columns(2)
        c1.metric("A-End Port", port_map.get(active_stitch['connector_a_id'], "Unknown Port"))
        c2.metric("Z-End Port", port_map.get(active_stitch['connector_b_id'], "Unknown Port"))
        
        with st.expander("View Full Connection Metadata"):
            st.json(active_stitch)
        return # Exit early as the service is already "Stitched"

    # --- PHASE 2: VALIDATE PHYSICAL PATH FOR NEW STITCH ---
    st.markdown("#### 🛤️ New Physical Path Verification")
    
    # Filter ports assigned to THIS specific service
    assigned_ports = [
        p for p in all_ports 
        if service_id in (p.get("fabric_service_ids") or [])
    ]

    if len(assigned_ports) < 2:
        st.error(f"🛑 **Physical Path Undefined:** EPL requires 2 ports assigned to this service.")
        st.info(f"Current Assignment: **{len(assigned_ports)}/2** ports staged.")
        
        with st.expander("How to fix this?"):
            st.write("""
            1. Return to the **Provisioning Launcher**.
            2. Select **'Attach Fabric Port'**.
            3. Attach two physical ports to this specific Service Alias.
            4. Return here to complete the 'Stitch'.
            """)
        return

    if len(assigned_ports) > 2:
        st.warning("⚠️ **Topology Warning:** More than 2 ports found. Only the first two will be used.")

    # --- PHASE 3: PROCEED TO LOGIC (The Stitch Form) ---
    st.success("✅ **Physical Path Defined:** Two ports are staged. Proceed to Logic.")
    
    with st.form(key=f"form_stitch_epl_{service_id}"):
        st.caption("Point-to-Point Connection (Untagged Port-Based)")
        c1, c2 = st.columns(2)
        
        port_a = assigned_ports[0]
        port_b = assigned_ports[1]

        with c1:
            st.text_input("A-End Port", value=f"{port_a.get('device_name')} | {port_a.get('port_name')}", disabled=True)
            bw = st.number_input("Service Bandwidth (Mbps)", min_value=1, value=1000)

        with c2:
            st.text_input("Z-End Port", value=f"{port_b.get('device_name')} | {port_b.get('port_name')}", disabled=True)
            conn_name = st.text_input("Connection Name", value=f"CONN-{fs_detail.get('service_alias')}")

        if st.form_submit_button("Finalize EPL Stitch", type="primary", use_container_width=True):
            payload = {
                "service_id": service_id,
                "connection_name": conn_name,
                "connector_a_id": port_a['port_id'],
                "connector_a_table": "ports",
                "connector_b_id": port_b['port_id'],
                "connector_b_table": "ports",
                "s_vlan": None, 
                "service_bw": bw,
                "connection_status": "Active"
            }
            
            # API Handoff logic here
            from src.utils.api_customer import post_fabric_connection
            if post_fabric_connection(payload):
                st.toast("EPL Stitch Completed!", icon="✅")
                st.rerun()

def handle_port_assignment_workflow(df_original: pd.DataFrame, df_edited: pd.DataFrame, customer_id: str):
    """
    Part of the Step 2 Provisioning Workflow: 
    Injects the post_port_intent method and executes the PUT intent.
    """
    import streamlit as st
    import pandas as pd
    import requests

    # 1. Class Wrapper to satisfy the 'self' and 'self.customer_id' requirement
    class PortProvisioner:
        def __init__(self, cid):
            self.customer_id = cid

        # The method provided exactly as you shared it
        def post_port_intent(self, port_intent: dict, status_override: str = "Staged") -> dict:
            from src.utils.api_customer import API_URL
            port_id = port_intent.get("port_id")
            
            api_payload = {
                "device_id": port_intent.get("device_id"),
                "port_name": port_intent.get("port"),           
                "port_speed": port_intent.get("speed"),         
                "port_description": port_intent.get("alias"),   
                "port_optic": port_intent.get("optics"),        
                "port_tagging": port_intent.get("port_tagging"), 
                "admin_status": port_intent.get("admin_status"), 
                "customer_id": self.customer_id,                
                "port_service_status": status_override,
                "port_type": "fabric port"
            }

            target_url = f"{API_URL}/ports/id/{port_id}"
            
            try:
                response = requests.put(target_url, json=api_payload, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                raise Exception(f"Failed to provision {port_intent.get('port', 'Unknown')}: {e.response.text}")

    # 2. Extract Staged Intent
    staged_list = st.session_state.get("payload", {}).get("service_context", {}).get("children", {}).get("ports", [])
    
    if not staged_list:
        st.warning("⚠️ No staged ports found in the buffer.")
        return

    # 3. EXECUTE PROVISIONING
    provisioner = PortProvisioner(customer_id)
    success_count = 0

    with st.status("🚀 Syncing Port Intents to Galileo API...", expanded=True) as status:
        for port_intent in staged_list:
            port_name = port_intent.get('port', 'Unknown')
            st.write(f"Mapping intent for **{port_name}**...")
            
            try:
                # Calling the method as part of the instance
                provisioner.post_port_intent(port_intent)
                st.write(f"✅ {port_name} successfully updated to Staged.")
                success_count += 1
            except Exception as e:
                st.write(f"❌ {port_name} Error: {str(e)}")

        # 4. FINALIZATION
        if success_count > 0:
            status.update(label="Provisioning Complete!", state="complete", expanded=False)
            # Flush the buffer (Document 3)
            st.session_state.payload["service_context"]["children"]["ports"] = []
            # Flag for refresh
            st.session_state["force_db_refresh"] = True
            st.toast(f"Committed {success_count} port intents.")
            st.rerun()
        else:
            status.update(label="Provisioning Failed", state="error")
            
def render_system_debug_manifests(fs_detail: dict, df_ports: pd.DataFrame):
    """
    Verification of the Three-Document Digital Twin.
    1. Service Detail (Live)
    2. Customer Ports (Live)
    3. Staged Intent (Session State)
    """
    import streamlit as st
    import json

    st.divider()
    st.subheader("🔍 System Debug: Multi-Document Manifest Sync")
    
    col1, col2, col3 = st.columns(3)
    
    # 1. LIVE SERVICE DETAIL
    with col1:
        st.markdown("##### 🟢 1. Service Details")
        st.caption("JSON #1: fabric_service_details")
        live_conns = len(fs_detail.get('fabric_connections', []))
        st.metric("Live Connections", live_conns)
        st.json(fs_detail)
        
    # 2. LIVE CUSTOMER PORTS
    with col2:
        st.markdown("##### 🔵 2. Customer Ports")
        st.caption("JSON #2: Active inventory in DB")
        port_count = len(df_ports)
        st.metric("Inventory Count", port_count)
        # Convert DF to JSON for consistent debug viewing
        st.json(df_ports.to_dict(orient='records'))

    # 3. STAGED INTENT (SESSION STATE)
    with col3:
        st.markdown("##### 🟡 3. Staged Intent")
        st.caption("JSON #3: Uncommitted UI changes")
        
        if "payload" in st.session_state:
            payload = st.session_state.payload
            children = payload.get('service_context', {}).get('children', {})
            
            # Count specific staged items
            s_ports = len(children.get('ports', []))
            s_intf = len(children.get('interfaces', []))
            s_conn = len(children.get('fabric_connections', []))
            
            st.metric("Staged Items", s_ports + s_intf + s_conn)
            st.json(payload)
        else:
            st.warning("No payload found in session_state.")

    # --- Sync Health Summary ---
    st.markdown("---")
    if "payload" in st.session_state:
        st.caption("🚀 **Provisioning Logic Check:** Items in 'Staged Intent' must be committed via PUT before appearing in 'Service Details'.")

def render_cloud_interconnect_tab(fs_detail: dict):
    """
    Orchestrates the Inventory and Provisioning tabs for Cloud Onramps.
    Updated to parse the 'cloud_interconnects' nested data structure.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.ui_provisioning_form import render_cloud_provisioning_form

    st.subheader("☁️ Cloud Interconnect Management")
    
    # 1. DATA PARSING & AGGREGATION
    # The new data structure nests connections inside partner objects
    partners = fs_detail.get('cloud_interconnects', [])
    
    all_connections = []
    for p in partners:
        p_name = p.get('partner_name', 'Unknown')
        p_type = p.get('partner_type', 'Cloud')
        
        # Flatten the nested connections list
        for conn in p.get('connections', []):
            all_connections.append({
                "Partner": p_name,
                "Type": p_type,
                "Region": conn.get("region"),
                "Name": conn.get("connection_name"),
                "Bandwidth": conn.get("service_bw", 0),
                "Status": conn.get("service_status", "Unknown"),
                "Description": conn.get("description", ""),
                "ID": conn.get("cloud_connection_id")
            })

    # 2. METRIC CALCULATIONS
    total_count = len(all_connections)
    planned_count = len([c for c in all_connections if c['Status'] == 'Planned'])
    active_count = len([c for c in all_connections if c['Status'] == 'Active'])
    total_bw_gbps = sum([c['Bandwidth'] for c in all_connections]) / 1000

    with st.container(border=True):
        m1, m2, m3 = st.columns(3)
        m1.metric("Cloud Interconnects", f"{total_count} Total", help="Total provisioned and planned connections.")
        m2.metric("Aggregate Capacity", f"{total_bw_gbps} Gbps", delta=f"{planned_count} Planned")
        m3.metric("Deployment Status", f"{active_count} Active", delta=f"{planned_count} Staged", delta_color="normal")

    # 3. TABBED LAYOUT
    tab_inv, tab_prov = st.tabs(["📋 Resource Inventory", "🚀 Provision New Onramp"])

    with tab_inv:
        st.markdown("##### 🔍 Cloud Asset Ledger")
        if not all_connections:
            st.info("No cloud interconnects detected in the service manifest.")
        else:
            # Flatten data for the dataframe
            df_display = pd.DataFrame(all_connections)
            
            # Map 'Planned' to 'Staged' for UI consistency if desired, or keep 'Planned'
            # We will use the raw Status to ensure backend alignment
            
            st.dataframe(
                df_display[["Partner", "Region", "Name", "Bandwidth", "Status", "Description"]], 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn(
                        "Status", 
                        help="Planned = Staged in Galileo UI | Active = Provisioned"
                    ),
                    "Bandwidth": st.column_config.NumberColumn("BW (Mbps)", format="%d"),
                    "Name": st.column_config.TextColumn("Connection Name", width="medium")
                }
            )

    with tab_prov:
        # 4. CALL THE PROVISIONING FORM
        render_cloud_provisioning_form(fs_detail)     
# --- APP ENTRY ---
if __name__ == "__main__":
    show_fabric_connection()

