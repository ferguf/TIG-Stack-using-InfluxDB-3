import streamlit as st
import pandas as pd
from src.utils.ui_network_forms import render_site_metadata_header
from src.ui_components import UI

# --- HELPER METHOD: MUST BE DEFINED AT TOP LEVEL ---
from streamlit_extras.stylable_container import stylable_container

def get_lag_provisionable_ports(device_id):
    """
    Fetches Physical ports in 'Staged' or 'Available' state 
    specifically for LAG membership selection.
    """
    from src.api_network import get_ports_by_device
    import pandas as pd
    
    raw = get_ports_by_device(device_id)
    if not raw: return pd.DataFrame()
    df = pd.DataFrame(raw)
    
    # Rule: Must be a physical gig interface in a pre-provisioned state
    mask = (
        (df['port_name'].str.lower().str.startswith('gig')) & 
        (df['port_service_status'].isin(['Staged', 'Available']))
    )
    
    return df[mask].copy()

def get_all_provisionable_ports(device_id):
    """
    Filters for ports ready to transition to 'Ready' status.
    - Physical (gig) must be 'Staged'
    - Logical (ae) must be 'Design'
    """
    from src.api_network import get_ports_by_device
    import pandas as pd
    
    raw = get_ports_by_device(device_id)
    if not raw: return pd.DataFrame()
    df = pd.DataFrame(raw)
    
    mask = (
        ((df['port_name'].str.lower().str.startswith('gig')) & (df['port_service_status'].isin(['Staged', 'Available']))) |
        ((df['port_name'].str.lower().str.startswith('ae')) & (df['port_service_status'] == 'Design'))
    )
    return df[mask].copy()

def render_netlink_tables(df, link_type_label, selected_dev_name):
    """
    Renders categorized link tables and manages deletion/reset with 
    strict state transitions.
    """
    from src.api_network import delete_network_link, update_port
    from src.ui_components import UI
    from streamlit_extras.stylable_container import stylable_container

    # 1. Initialize selection variable to prevent 'not defined' error
    selected_row = None 

    if df.empty:
        st.caption(f"No active {link_type_label} connections found.")
        return

    link_type = link_type_label.lower()
    
    # --- 2. DEFINE TABLE-SPECIFIC COLUMNS & COLORS ---
    if "lag" in link_type:
        h_color = "#E3F2FD"  # Light Blue
        column_mapping = {
            "a_port_name": "🟠 LAG Interface (A)",
            "b_port_name": "🟠 Physical Port (B)",
            "a_port_speed": "Speed",
            "description": "Description"
        }
    elif "Intra" in link_type:
        h_color = "#E8F5E9"  # Light Green
        column_mapping = {
            "a_device_name": "🟢 Device A",
            "a_port_name": "🟢 Port A",
            "b_device_name": "🔵 Device B",
            "b_port_name": "🔵 Port B",
            "a_port_speed": "Speed",
            "cktid": "Patch ID"
        }
    else:  # Inter-PoP
        h_color = "#FFF3E0"  # Light Amber
        column_mapping = {
            "a_device_name": "🟢 Local Device",
            "a_port_name": "🟢 Local Port",
            "b_device_name": "🟠 Remote Device",
            "b_port_name": "🟠 Remote Port",
            "a_port_speed": "Speed",
            "cktid": "Circuit ID"
        }

    # Prepare Display Data
    hidden_ids = ["link_id", "a_port_id", "b_port_id"]
    cols_to_use = [c for c in column_mapping.keys() if c in df.columns]
    df_display = df[cols_to_use + hidden_ids].rename(columns=column_mapping)

    # --- 3. RENDER TABLE ---
    st.write(f"**{link_type_label} Inventory**")
    
    with stylable_container(
        key=f"header_style_{link_type}",
        css_styles=f"""
            div[data-testid="stDataEditor"] th {{
                background-color: {h_color} !important;
                color: black !important;
                font-weight: bold !important;
            }}
        """
    ):
        # The return value is assigned to selected_row here
        selected_row = UI.render_selectable_table(
            df=df_display, 
            key_prefix=f"tab_{link_type}_{selected_dev_name}", 
            id_column_to_hide=hidden_ids
        )

    # --- 4. ACTION AREA (UNBIND LOGIC) ---
    if selected_row:
        with st.container(border=True):
            st.error(f"☢️ **Terminate {link_type_label} Connection?**")
            
            # Dynamic Target Label
            target_a = selected_row.get('🟢 Port A') or selected_row.get('🟠 LAG Interface (A)')
            target_b = selected_row.get('🔵 Port B') or selected_row.get('🟠 Physical Port (B)')
            st.caption(f"Target: {target_a} ↔ {target_b}")

            if UI.button("Confirm Terminate", color="red", key=f"btn_del_{link_type}_{selected_dev_name}"):
                if delete_network_link(selected_row.get('link_id')):
                    
                    # --- UNBIND STATE TRANSITIONS ---
                    if "lag" in link_type:
                        # LAG unBind Logic
                        member_payload = {"port_type": "Physical", "port_service_status": "Available"}
                        ae_payload = {"port_type": "LAG-Bundle", "port_service_status": "Available"}
                    else:
                        # Intra unBind Logic
                        member_payload = {"port_type": "ae0-member", "port_service_status": "Design"}
                        ae_payload = {"port_type": "LAG-Bundle", "port_service_status": "Design"}

                    update_port(selected_row.get('b_port_id'), member_payload)
                    update_port(selected_row.get('a_port_id'), ae_payload)
                    
                    st.toast(f"{link_type_label} unbound successfully.", icon="✅")
                    st.rerun()

                    
def get_filtered_port_data(device_id, view_mode):
    from src.api_network import get_ports_by_device
    import pandas as pd
    
    raw_ports = get_ports_by_device(device_id)
    if not raw_ports: return pd.DataFrame()
    df = pd.DataFrame(raw_ports)
    
    # Standardize data
    df['port_type'] = df['port_type'].fillna('')
    df['port_name'] = df['port_name'].fillna('')
    df['port_service_status'] = df['port_service_status'].fillna('')
    
    mask = pd.Series([False] * len(df))

    if view_mode == "AE":
        # Rule: Display ANY port starting with 'ae' that is not 'Physical'
        # Removed status restrictions so 'Active' AEs still show in the list
        mask = (
            (df['port_name'].str.lower().str.startswith('ae')) & 
            (df['port_type'] != 'Physical')
        )
        
    elif view_mode == "LAG Member":
        # Rule: Show ports that are already members (aeX-member)
        mask = df['port_type'].str.contains("-member", case=False)
        
    elif view_mode == "Physical":
        # Rule: Show physical hardware (gig) available for new links
        mask = (
            ((df['port_type'] == 'Physical') | (df['port_name'].str.lower().str.startswith('gig'))) &
            (df['port_service_status'].isin(['Available','Staged']))
        )
        
    return df[mask].copy()

def bind_unbind_port_logic(action_type, context, data):
    """
    Orchestrator for Port Sequencing:
    Bind: Staged -> Design -> Ready
    Unbind: Ready -> Design -> Available
    """
    from src.api_network import update_port, post_network_link, delete_network_link
    import streamlit as st

    # --- ROUTINE 1: LAG (Internal Binding) ---
    # Transitions: Staged -> Design | Physical -> LAG-Member
    if context == "LAG":
        if action_type == "bind":
            ae, phys = data['target_ae'], data['selected_phys']
            ae_name = str(ae.get('Port', ae.get('port_name', ''))).lower()
            
            payload = {
                "endpoint_a": str(ae['port_id']), "endpoint_a_type": "lag",
                "endpoint_b": str(phys['port_id']), "endpoint_b_type": "physical",
                "link_type": "lag", "description": f"LAG:{ae_name}"
            }
            if post_network_link(payload):
                # Parent Bundle becomes 'LAG' (Design)
                update_port(ae['port_id'], {"port_type": "LAG", "port_service_status": "Design"})
                # Physical Port becomes 'LAG-member' (Design)
                update_port(phys['port_id'], {
                    "port_type": "LAG-member",
                    "port_description": f"{ae_name}-member",
                    "port_service_status": "Design"
                })
                return True

        elif action_type == "unbind":
            row = data['row']
            if delete_network_link(row['link_id']):
                # Side A (AE): Reverts to LAG-Bundle (Available)
                update_port(row['a_port_id'], {
                    "port_type": "LAG-Bundle", 
                    "port_service_status": "Available",
                    "port_description": ""
                })
                # Side B (Phys): Reverts to Physical (Available)
                update_port(row['b_port_id'], {
                    "port_type": "Physical", 
                    "port_service_status": "Available",
                    "port_description": ""
                })
                return True

    # --- ROUTINE 2: INTRA (Device-to-Device) ---
    # Transitions: Design -> Ready | LAG -> Intra-Pop
    elif context == "Intra":
        if action_type == "bind":
            a, z, ckt = data['port_a'], data['port_z'], data['ckt']
            a_name = str(a.get('Port', a.get('port_name', ''))).lower()
            z_name = str(z.get('Port', z.get('port_name', ''))).lower()

            # Like-to-Like Validation
            if a_name.startswith('ae') != z_name.startswith('ae'):
                st.error("🚫 Type Mismatch: Must be ae<->ae or gig<->gig")
                return False

            payload = {
                "endpoint_a": str(a['port_id']), "endpoint_a_type": "lag" if a_name.startswith('ae') else "physical",
                "endpoint_b": str(z['port_id']), "endpoint_b_type": "lag" if z_name.startswith('ae') else "physical",
                "link_type": "intra-Pop", "description": f"Intra: {a_name} <-> {z_name}"
            }
            if post_network_link(payload):
                # Both sides move to 'Ready' status and 'Intra-Pop' type (if ae)
                update_port(a['port_id'], {
                    "port_type": "Intra-Pop" if a_name.startswith('ae') else "Physical", 
                    "port_service_status": "Ready"
                })
                update_port(z['port_id'], {
                    "port_type": "Intra-Pop" if z_name.startswith('ae') else "Physical", 
                    "port_service_status": "Ready", 
                    "port_cktid": ckt
                })
                return True

        elif action_type == "unbind":
            row = data['row']
            l_name = str(row.get('Local Port', row.get('🟢 Port A', ''))).lower()
            r_name = str(row.get('Remote Port', row.get('🔵 Port B', ''))).lower()

            if delete_network_link(row['link_id']):
                # Reverts to 'Design' status and 'LAG' type (if ae)
                update_port(row['a_port_id'], {
                    "port_type": "LAG" if l_name.startswith('ae') else "Physical", 
                    "port_service_status": "Design"
                })
                update_port(row['b_port_id'], {
                    "port_type": "LAG" if r_name.startswith('ae') else "Physical", 
                    "port_service_status": "Design"
                })
                return True
# --- ROUTINE 3: INTER (Site-to-Site) ---
    # Transitions: Design/Staged -> Ready | Local -> Remote
    elif context == "Inter":
        if action_type == "bind":
            a, z, ckt = data['port_a'], data['port_z'], data['ckt']
            
            # Helper to check if it's an AE bundle
            a_is_ae = str(a.get('Port', a.get('port_name', ''))).lower().startswith('ae')
            z_is_ae = str(z.get('Port', z.get('port_name', ''))).lower().startswith('ae')

            # 1. ENFORCE LIKE-TO-LIKE RULE
            if a_is_ae != z_is_ae:
                st.error("🚫 Connection Error: Inter-PoP must be Like-to-Like (AE-to-AE or Gig-to-Gig).")
                return False

            # 2. CREATE THE NETWORK LINK
            payload = {
                "endpoint_a": str(a['port_id']),
                "endpoint_a_type": "lag" if a_is_ae else "physical",
                "endpoint_b": str(z['port_id']),
                "endpoint_b_type": "lag" if z_is_ae else "physical",
                "link_type": "inter-Pop",
                "description": f"Inter-PoP: {a.get('Port')} <-> {z.get('Port')}",
                "port_cktid": ckt  # Save the Global Circuit ID
            }

            if post_network_link(payload):
                # 3. UPDATE PORT STATUS TO 'READY'
                # Transition: Design -> Ready (AE) or Staged -> Ready (Physical)
                update_port(a['port_id'], {
                    "port_type": "Inter-Pop" if a_is_ae else "Physical", 
                    "port_service_status": "Ready"
                })
                update_port(z['port_id'], {
                    "port_type": "Inter-Pop" if z_is_ae else "Physical", 
                    "port_service_status": "Ready", 
                    "port_cktid": ckt
                })
                return True

        elif action_type == "unbind":
            row = data['row']
            # Revert to 'Design' state so it can be re-provisioned
            if delete_network_link(row['link_id']):
                update_port(row['a_port_id'], {"port_service_status": "Design"})
                update_port(row['b_port_id'], {"port_service_status": "Design"})
                return True    
    return False
     
# --- MAIN VIEW ---

def render_links_management_view():
    """
    Top-level view for Link Management.
    Workflow: Context Search -> System Inspection -> Configuration.
    """
    import streamlit as st
    from src.api_network import (
        get_devices_by_short_name, 
        get_site_details_by_shortname, 
        get_lag_network_links
    )
    from src.utils.ui_debug import render_system_debugger
    
    st.subheader("🔗 Network Link Configuration")

    # --- 1. SEARCH SITE CONTEXT ---
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        home_site = c1.text_input("📍 Primary Site Code", placeholder="e.g., den1", key="link_home_site_input")
        if c2.button("Get Site Devices", type="primary", use_container_width=True):
            with st.spinner("Fetching..."):
                st.session_state["link_active_site_info"] = get_site_details_by_shortname(home_site)
                st.session_state["link_active_devices"] = get_devices_by_short_name(home_site)
                st.session_state["link_active_site_code"] = home_site

    # --- 2. MAIN WORKSPACE ---
    active_devices = st.session_state.get("link_active_devices", [])
    home_site_code = st.session_state.get("link_active_site_code")
    
    if active_devices:
        device_names = [d['device_name'] for d in active_devices]
        
        # Header Control Panel
        head_col1, head_col2 = st.columns([1, 1], gap="large")
        with head_col1:
            link_category = st.radio(
                "**Select Link Category:**",
                options=["LAG", "Intra-PoP", "Inter-PoP"],
                horizontal=True,
                key="link_category_radio"
            )
        with head_col2:
            selected_dev_name = st.selectbox(
                "**Select Active Device:**", 
                options=device_names, 
                key="global_device_selector"
            )

        # --- 3. SYSTEM STATE INSPECTOR (DEBUGGER) ---
        current_lags = get_lag_network_links()
        sel_dev_obj = next((d for d in active_devices if d['device_name'] == selected_dev_name), {})
        
        debug_tiers = {
            "📟 Port State": st.session_state.get(f"lag_active_ports_{sel_dev_obj.get('device_id')}"),
            "🔗 Netlink State": current_lags,
            "🎯 Context": {
                "device": selected_dev_name,
                "site": home_site_code,
                "category": link_category
            }
        }
        render_system_debugger(debug_tiers, scope=f"Netlink_{selected_dev_name}")

        st.divider()

        # --- 4. DYNAMIC CONTENT RENDERING ---
        # Routing to specific view methods
        if link_category == "LAG":
            render_lag_view(selected_dev_name, device_names)
            
        elif link_category == "Intra-PoP":
            intra_pop_link_form(home_site_code, device_names, selected_dev_name)
            
        elif link_category == "Inter-PoP":
            # Note: Method defined below to handle remote site selection
            inter_pop_link_form(home_site_code, device_names, selected_dev_name)
        
        else:
            # Fallback for debugging
            st.info(f"Route not found for category: {link_category}")

            
def render_lag_view(selected_dev_name, device_names):
    """
    Handles internal device LAG membership with Unified View.
    No radio buttons; displays all provisionable ports at once.
    """
    import streamlit as st
    import pandas as pd
    from src.api_network import get_network_links_detail_by_device
    from src.ui_components import UI

    active_devices = st.session_state.get("link_active_devices", [])
    sel_dev_obj = next((d for d in active_devices if d['device_name'] == selected_dev_name), None)
    if not sel_dev_obj: 
        return

    dev_id = sel_dev_obj['device_id']

    # --- 1. EXISTING INVENTORY ---
    detailed_links = get_network_links_detail_by_device(dev_id)
    if detailed_links:
        df_all = pd.DataFrame(detailed_links)
        df_lag = df_all[df_all['link_type'].str.lower() == 'lag']
        if not df_lag.empty:
            st.markdown("#### 🖇️ Existing LAG Inventory")
            render_netlink_tables(df_lag, "LAG", selected_dev_name)

    st.divider()

    # --- 2. UNIFIED PROVISIONING FORM ---
    st.markdown("#### 🛠️ Internal LAG Membership")
    
    c_ae, c_phys = st.columns([1, 2], gap="large")
    
    with c_ae:
        st.markdown("##### 🎯 Target AE (Bundle)")
        # Show all AE interfaces regardless of state (so you can add members to active LAGs)
        ae_df = get_filtered_port_data(dev_id, "AE") 
        if not ae_df.empty:
            ae_opts = ae_df.sort_values('port_name').to_dict('records')
            target_ae = st.selectbox(
                "Select Bundle", 
                options=ae_opts, 
                format_func=lambda x: str(x['port_name']).lower().strip(),
                key=f"ae_sel_{dev_id}"
            )
        else:
            st.info("No AE interfaces available.")
            target_ae = None

    with c_phys:
        st.markdown("##### 🔌 Available Physical Ports")
        # Unified fetch: Show everything that could be a member (Staged/Design Physicals)
        df_filt = get_lag_provisionable_ports(dev_id)
        selected_phys = None
        if not df_filt.empty:
            port_map = {
                "port_name": "Port", 
                "port_speed": "Speed", 
                "port_description": "Description",
                "port_service_status": "Status",
                "port_type": "Type"
            }
            df_disp = df_filt[list(port_map.keys()) + ["port_id"]].rename(columns=port_map)
            selected_phys = UI.render_selectable_table(df_disp, f"lag_tab_{dev_id}", "port_id")
        else:
            st.caption("No physical ports available to be bound.")

    # --- 3. BINDING LOGIC ---
    if target_ae and selected_phys:
        if UI.button("🔗 Finalize LAG Binding", color="blue", key=f"lag_btn_{dev_id}"):
            success = bind_unbind_port_logic(
                action_type="bind", 
                context="LAG", 
                data={'target_ae': target_ae, 'selected_phys': selected_phys}
            )
            if success:
                st.toast(f"✅ Bound {selected_phys.get('Port')} to {target_ae['port_name'].lower()}")
                st.rerun()               

def intra_pop_link_form(home_site, home_devices, selected_dev_a):
    """
    Refactored Intra-PoP workflow using centralized logic.
    Delegates state-machine and API calls to bind_unbind_port_logic.
    """
    import streamlit as st
    import pandas as pd
    from src.api_network import get_network_links_detail_by_device
    from src.ui_components import UI

    active_devs = st.session_state.get("link_active_devices", [])
    obj_a = next((d for d in active_devs if d['device_name'] == selected_dev_a), None)
    if not obj_a:
        st.warning("Please select a device to continue.")
        return

    dev_id_a = obj_a['device_id']

    # --- 1. INVENTORY MANAGEMENT (Tabs) ---
    st.markdown(f"#### 📋 {selected_dev_a} Connection Inventory")
    detailed_links = get_network_links_detail_by_device(dev_id_a)
    
    if detailed_links:
        df_all = pd.DataFrame(detailed_links)
        # Filter based on naming convention for synced tab counts
        df_lag_inv = df_all[df_all['a_port_name'].str.lower().str.startswith('ae')]
        df_intra_inv = df_all[df_all['link_type'].str.lower() == 'intra-pop']

        t_lag, t_intra = st.tabs([f"🖇️ LAG ({len(df_lag_inv)})", f"🌐 intra-PoP ({len(df_intra_inv)})"])
        with t_lag: 
            render_netlink_tables(df_lag_inv, "LAG", selected_dev_a)
        with t_intra: 
            render_netlink_tables(df_intra_inv, "Intra", selected_dev_a)
    else:
        st.info("No active connections found.")

    st.divider()

    # --- 2. PROVISIONING ZONE (Selection) ---
    st.markdown("#### 🛠️ New Connection Provisioning")
    view_mode = st.radio("**🔍 View Filter:**", ["Physical", "LAG Member", "AE"], horizontal=True, key=f"intra_v_{dev_id_a}")
    
    # Columns requested: Port, Speed, Description, Status, Type
    port_map = {
        "port_name": "Port", 
        "port_speed": "Speed", 
        "port_description": "Description", 
        "port_service_status": "Status", 
        "port_type": "Type"
    }
    display_cols = list(port_map.keys()) + ["port_id"]

    col_a, col_z = st.columns(2, gap="large")

    with col_a:
        with st.container(border=True):
            st.markdown(f"##### 🅰️ Side A: {selected_dev_a}")
            df_a = get_filtered_port_data(dev_id_a, view_mode)
            selected_port_a = None
            if not df_a.empty:
                df_a['port_description'] = df_a['port_description'].fillna('---')
                df_a_disp = df_a[display_cols].rename(columns=port_map)
                selected_port_a = UI.render_selectable_table(df_a_disp, f"i_a_{dev_id_a}", "port_id")
            else:
                st.caption("No ports available for this filter.")

    with col_z:
        with st.container(border=True):
            dev_z_name = st.selectbox("Select Device Z", options=home_devices, key="z_dev_sel")
            obj_z = next((d for d in active_devs if d['device_name'] == dev_z_name), None)
            selected_port_z = None
            if obj_z:
                df_z = get_filtered_port_data(obj_z['device_id'], view_mode)
                if not df_z.empty:
                    df_z['port_description'] = df_z['port_description'].fillna('---')
                    df_z_disp = df_z[display_cols].rename(columns=port_map)
                    selected_port_z = UI.render_selectable_table(df_z_disp, f"i_z_{obj_z['device_id']}", "port_id")
                else:
                    st.caption("No ports available.")

    # --- 3. BINDING LOGIC (Using Centralized Routine) ---
    if selected_port_a and selected_port_z:
        if selected_port_a['port_id'] == selected_port_z['port_id']:
            st.error("🚫 Cannot bind a port to itself.")
            return

        ckt = st.text_input("Circuit / Patch ID", placeholder="P-XXXX")
        
        if st.button("🚀 Commit Connection", type="primary", use_container_width=True):
            # Package all required metadata for the orchestrator
            bind_data = {
                'port_a': selected_port_a,
                'port_z': selected_port_z,
                'ckt': ckt
            }
            
            # Execute the centralized Intra bind routine
            success = bind_unbind_port_logic(
                action_type="bind", 
                context="Intra", 
                data=bind_data
            )
            
            if success:
                st.toast(f"✅ Intra-PoP link committed at {home_site}", icon="🚀")
                st.rerun()

def inter_pop_link_form(home_site_code, device_names, selected_dev_a):
    """
    Complete Inter-PoP Logic with View Filter Radio Buttons.
    """
    import streamlit as st
    import pandas as pd
    from src.api_network import (
        get_network_links_detail_by_device, 
        get_devices_by_short_name
    )
    from src.ui_components import UI

    # --- 1. INITIALIZE LOCAL CONTEXT ---
    active_devs = st.session_state.get("link_active_devices", [])
    obj_a = next((d for d in active_devs if d['device_name'] == selected_dev_a), None)
    if not obj_a:
        st.error("Local device context lost. Please re-run site search.")
        return
    dev_id_a = obj_a['device_id']

    # --- 2. INVENTORY MANAGEMENT (Tabs) ---
    st.markdown(f"#### 📋 {selected_dev_a} Connection Inventory")
    detailed_links = get_network_links_detail_by_device(dev_id_a)
    
    if detailed_links:
        df_all = pd.DataFrame(detailed_links)
        df_lag_inv = df_all[df_all['link_type'].str.lower() == 'lag']
        df_intra_inv = df_all[df_all['link_type'].str.lower() == 'intra-pop']
        df_inter_inv = df_all[df_all['link_type'].str.lower() == 'inter-pop']

        t_lag, t_intra, t_inter = st.tabs([
            f"🖇️ LAG ({len(df_lag_inv)})", 
            f"🌐 Intra-PoP ({len(df_intra_inv)})", 
            f"🌎 Inter-PoP ({len(df_inter_inv)})"
        ])
        
        with t_lag: render_netlink_tables(df_lag_inv, "LAG", selected_dev_a)
        with t_intra: render_netlink_tables(df_intra_inv, "Intra", selected_dev_a)
        with t_inter: render_netlink_tables(df_inter_inv, "Inter", selected_dev_a)

    st.divider()

    # --- 3. NEW PROVISIONING (Discovery & Filtered Selection) ---
    st.markdown("#### 🛠️ New Inter-PoP Provisioning")
    
    # ADDED: Filter Radio Buttons to toggle port selection pool
    view_mode = st.radio(
        "**🔍 View Filter:**", 
        ["Physical", "LAG Member", "AE"], 
        horizontal=True, 
        key=f"inter_v_{dev_id_a}"
    )

    port_map = {
        "port_name": "Port", 
        "port_speed": "Speed", 
        "port_description": "Description", 
        "port_service_status": "Status", 
        "port_type": "Type"
    }
    display_cols = list(port_map.keys()) + ["port_id"]

    col_a, col_z = st.columns(2, gap="large")

    # --- SIDE A: LOCAL ---
    with col_a:
        with st.container(border=True):
            st.markdown(f"##### 🅰️ Side A: {home_site_code.upper()}")
            # Using the radio filter logic
            df_a = get_filtered_port_data(dev_id_a, view_mode)
            selected_port_a = None
            if not df_a.empty:
                df_a_disp = df_a[display_cols].rename(columns=port_map)
                selected_port_a = UI.render_selectable_table(df_a_disp, f"inter_a_{dev_id_a}", "port_id")
            else:
                st.caption(f"No ports available for filter: {view_mode}")

    # --- SIDE Z: REMOTE DISCOVERY ---
    with col_z:
        with st.container(border=True):
            st.markdown("##### 💤 Side Z: Remote Discovery")
            remote_site = st.text_input("📍 Search Remote Site Code", placeholder="e.g. ord1", key="inter_rem_site")
            selected_port_z = None
            
            if remote_site:
                remote_devs = get_devices_by_short_name(remote_site)
                if remote_devs:
                    z_dev_name = st.selectbox("Select Remote Router", options=[d['device_name'] for d in remote_devs])
                    obj_z = next((d for d in remote_devs if d['device_name'] == z_dev_name), None)
                    
                    if obj_z:
                        # Applying the SAME radio filter to the remote side
                        df_z = get_filtered_port_data(obj_z['device_id'], view_mode)
                        if not df_z.empty:
                            df_z_disp = df_z[display_cols].rename(columns=port_map)
                            selected_port_z = UI.render_selectable_table(df_z_disp, f"inter_z_{obj_z['device_id']}", "port_id")
                        else:
                            st.caption(f"No ports available for filter: {view_mode}")
                else:
                    st.warning(f"No devices found at site: {remote_site}")

    # --- 4. COMMIT ---
    if selected_port_a and selected_port_z:
        st.divider()
        ckt_id = st.text_input("📋 Global Circuit ID", placeholder="CKT-XXXXX")
        
        if st.button("🚀 Commit Inter-PoP Link", type="primary", use_container_width=True):
            # Enforce Like-to-Like is handled inside bind_unbind_port_logic
            success = bind_unbind_port_logic(
                action_type="bind", 
                context="Inter", 
                data={'port_a': selected_port_a, 'port_z': selected_port_z, 'ckt': ckt_id}
            )
            if success:
                st.toast(f"✅ Inter-PoP link {ckt_id} established!", icon="🚀")
                st.rerun()
            
def render_netlink_view():
    """
    Unified entry point for the 3549 Dashboard.
    Combines Bulk Ingestion and Active Inventory Management.
    """
    st.title("🌐 Netlink Connection Manager")
    
    # 1. Top Level: Bulk Load / CSV Ingestion
    # This allows you to add/delete/update links via CSV
    with st.expander("📥 Bulk Netlink Ingestion", expanded=False):
        # We need to import these here to avoid circular imports if necessary
        from pages.bulkload.load_netlink import render_netlink_view as render_bulk_view
        render_bulk_view()
    
    st.divider()
    
    # 2. Main Level: Active Inventory & Manual Provisioning
    # This calls your existing function that handles the UI tabs and tables
    render_links_management_view()