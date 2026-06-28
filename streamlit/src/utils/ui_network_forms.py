import streamlit as st
import pandas as pd
import uuid

# =============================================================================
# 1. UTILITIES & VALIDATION
# =============================================================================

def is_valid_uuid(val):
    """Checks if a value is a valid UUID4 string or object."""
    if not val: return False
    try:
        if isinstance(val, uuid.UUID): return True
        uuid.UUID(str(val))
        return True
    except: return False


# =============================================================================
# 2. FILTERING & SEARCH COMPONENTS
# =============================================================================

# In src/utils/ui_network_forms.py

def apply_device_filters(df, key_prefix):
    """Adds filters to the UI with unique keys to avoid ID collisions."""
    st.markdown("#### 🔍 Filter Records")
    cols = st.columns(3)
    
    with cols[0]:
        countries = st.multiselect(
            "Country", 
            options=sorted(df['country'].unique()) if 'country' in df.columns else [],
            key=f"{key_prefix}_country_filter"  # <--- UNIQUE KEY
        )
    
    with cols[1]:
        states = st.multiselect(
            "State", 
            options=sorted(df['state'].unique()) if 'state' in df.columns else [],
            key=f"{key_prefix}_state_filter"    # <--- UNIQUE KEY
        )
        
    with cols[2]:
        cities = st.multiselect(
            "City", 
            options=sorted(df['city'].unique()) if 'city' in df.columns else [],
            key=f"{key_prefix}_city_filter"     # <--- UNIQUE KEY
        )
    
    # ... rest of your filtering logic (df = df[df['country'].isin(countries)] etc.)
    return df
def render_location_search_component(network_label: str, results=None):
    """Site search input and device results table."""
    st.markdown(f"### 🔍 Find {network_label} Devices")
    c1, c2 = st.columns([3, 1])
    with c1: search_term = st.text_input("Enter Site Code", key=f"in_{network_label}")
    with c2: 
        st.write(" ")
        trigger = st.button("Fetch", key=f"btn_{network_label}")
    
    selection = None
    if results:
        from src.ui_components import UI # Lazy Import
        selection = UI.render_selectable_table(pd.DataFrame(results), f"table_{network_label}", "device_id")
    return selection, search_term, trigger


# =============================================================================
# 3. METADATA & DISPLAY COMPONENTS
# =============================================================================

def render_site_metadata_header(site_info: dict, search_term: str):
    """Displays physical facility metrics (CLLI, Lat/Lon, Address)."""
    if not site_info: return
    with st.container(border=True):
        st.markdown(f"##### 📍 Site Information: {search_term.upper()}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CLLI", site_info.get("location_code", "N/A"))
        c2.metric("Facility", site_info.get("facility_type", "N/A"))
        c3.metric("Lat", site_info.get("latitude", "N/A"))
        c4.metric("Lon", site_info.get("longitude", "N/A"))
        
        full_addr = f"{site_info.get('address', '')}, {site_info.get('city', '')}, {site_info.get('state', '')}"
        st.write(f"🏠 **Address:** {full_addr.strip(', ')}")

def render_device_ports_table(device_id: str, device_name: str):
    """Fetches and displays the port inventory for a specific device."""
    from src.api_network import get_ports_by_device # Lazy Import
    from src.ui_components import UI # Lazy Import
    st.subheader(f"🔌 Port Inventory: {device_name}")
    ports = get_ports_by_device(device_id)
    if not ports:
        st.info("No ports found.")
        return
    df = pd.DataFrame(ports)
    return UI.render_selectable_table(df, f"ports_{device_id}", "port_id")


# =============================================================================
# 4. MANAGEMENT FORMS (POST/PUT)
# =============================================================================

def render_edit_device_form(selected_device, network_label: str):
    """Form to update logical device attributes (Name, Role, Model, Vendor)."""
    from src.api_network import update_device # Lazy Import
    st.divider()
    st.subheader(f"📝 Edit Device: {selected_device['device_name']}")
    
    LIFECYCLE_OPTIONS = ["Active", "Capped Provision", "Capped Growth", "Remove"]
    INV_HEALTH_MAP = {"Planned (4)": 4, "Active (3)": 3}
    
    with st.form(key=f"edit_device_{selected_device['device_id']}"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Device Name", value=selected_device.get("device_name"))
            vendor = st.text_input("Vendor", value=selected_device.get("device_vendor"))
            model = st.text_input("Model", value=selected_device.get("device_model"))
        with col2:
            role = st.text_input("Role", value=selected_device.get("device_role"))
            lifecycle = st.selectbox("Lifecycle", options=LIFECYCLE_OPTIONS, index=0)
            health_label = st.selectbox("Health Status", options=list(INV_HEALTH_MAP.keys()), index=1)
            
        if st.form_submit_button("💾 Save Changes"):
            payload = {"device_name": name, "device_role": role, "device_model": model, "device_vendor": vendor}
            if update_device(selected_device['device_id'], payload):
                st.success("Updated Successfully")
                st.rerun()

def render_edit_location_form(selected_device):
    """Form to manage physical inventory: rack, floor, and aisle data."""
    from src.utils.api_network import get_site_details_by_shortname, get_device_location, save_device_location # Lazy Imports
    
    device_id = selected_device['device_id']
    short_name = str(selected_device.get('location', '')).strip().lower()
    
    # Pre-fetch data to hydrate form
    facility_data = get_site_details_by_shortname(short_name)
    loc_data = get_device_location(device_id)
    exists = loc_data is not None

    with st.form(key=f"loc_form_{device_id}"):
        st.markdown(f"#### 📟 Physical Attributes: {selected_device['device_name']}")
        c1, c2 = st.columns(2)
        
        with c1:
            floor = st.text_input("Floor", value=loc_data.get("floor_number", "") if exists else "")
            aisle = st.text_input("Aisle", value=loc_data.get("aisle_identifier", "") if exists else "")
        
        with c2:
            global_clli = facility_data.get("location_code", "") if facility_data else ""
            clli_8 = st.text_input("CLLI(8)", value=loc_data.get("clli") if exists else global_clli, max_chars=8)
            rack = st.text_input("Rack Identifier", value=loc_data.get("rack_identifier", "") if exists else "")
            
        if st.form_submit_button("💾 Save Physical Location", type="primary"):
            payload = {
                "device_id": device_id,
                "clli": clli_8,
                "floor_number": floor,
                "rack_identifier": rack,
                "aisle_identifier": aisle,
                "location": short_name
            }
            if save_device_location(payload, exists):
                st.success("✅ Physical inventory record saved.")
                st.rerun()

def render_edit_port_form(selected_port):
    """General Port Update Form (Description, Circuit ID, Status)."""
    from src.api_network import update_port # Lazy Import
    
    if not selected_port: return

    port_id = selected_port['port_id']
    st.markdown(f"#### 📝 Edit Port: {selected_port['port_name']}")
    
    with st.form(key=f"edit_port_{port_id}"):
        c1, c2 = st.columns(2)
        
        with c1:
            desc = st.text_input("Port Description", value=selected_port.get("port_description", ""))
            cktid = st.text_input("Circuit ID", value=selected_port.get("port_cktid", ""))
            st.text_input("Port Speed (Read-Only)", value=selected_port.get("port_speed", ""), disabled=True)
            
        with c2:
            STATUS_OPTS = ["Staged", "Active", "Reserved", "Maintenance", "Down"]
            curr_status = selected_port.get("port_service_status", "Staged")
            status_idx = STATUS_OPTS.index(curr_status) if curr_status in STATUS_OPTS else 0
            
            status = st.selectbox("Service Status", options=STATUS_OPTS, index=status_idx)
            optic = st.text_input("Optic Type", value=selected_port.get("port_optic", "NA"))
            tagging = st.selectbox("Tagging", ["Tagged", "Untagged"], index=0 if selected_port.get("port_tagging") == "Tagged" else 1)

        if st.form_submit_button("💾 Save Port Attributes", type="primary"):
            # Construct payload (port_id excluded to prevent Primary Key collision)
            payload = {
                "port_description": desc,
                "port_cktid": cktid,
                "port_service_status": status,
                "port_optic": optic,
                "port_tagging": tagging
            }
            if update_port(port_id, payload):
                st.success(f"✅ Port {selected_port['port_name']} updated.")
                st.rerun()

def render_netlinks_view(selected_dev_name):
    """
    Consolidated dashboard for all network link types.
    Displays Lag, Intra, and Inter connections in organized tabs.
    """
    from src.api_network import get_lag_network_links, delete_network_link, update_port
    from src.ui_components import UI
    import pandas as pd
    import streamlit as st

    st.markdown("### 📊 Active Site Connections")
    
    # Fetch all link data (the LAG view usually contains the comprehensive topology)
    all_links = get_lag_network_links()
    
    if not all_links:
        st.info(f"No active network links found for {selected_dev_name}.")
        return

    # Convert to DataFrame and filter for current device
    df_all = pd.DataFrame(all_links)
    df_site = df_all[df_all['device_name'] == selected_dev_name].copy()

    if df_site.empty:
        st.info(f"No active connections recorded for {selected_dev_name}.")
        return

    # --- CATEGORIZATION LOGIC ---
    # Lag: Usually defined by link_type 'lag'
    df_lag = df_site[df_site['link_type'].str.lower() == 'lag']
    
    # Intra: Links within the same PoP/Site
    df_intra = df_site[df_site['link_type'].str.lower() == 'intra']
    
    # Inter: Links between different sites
    df_inter = df_site[df_site['link_type'].str.lower() == 'inter']

    # --- UI RENDERING (Tabs for Scannability) ---
    tab_lag, tab_intra, tab_inter = st.tabs([
        f"🖇️ LAG ({len(df_lag)})", 
        f"🌐 Intra-PoP ({len(df_intra)})", 
        f"🛣️ Inter-PoP ({len(df_inter)})"
    ])

    column_mapping = {
        "a_port_name": "Endpoint A",
        "b_port_name": "Endpoint B",
        "description": "Description",
        "a_port_speed": "Speed",
        "link_type": "Type"
    }
    # Fields to keep hidden but available for deletion logic
    hidden_ids = ["link_id", "b_port_id", "a_port_id"]

    def render_generic_link_table(df, key):
        if df.empty:
            st.caption("No connections of this type.")
            return None
        
        df_display = df[list(column_mapping.keys()) + hidden_ids].rename(columns=column_mapping)
        return UI.render_selectable_table(
            df=df_display, 
            key_prefix=key, 
            id_column_to_hide=hidden_ids
        )

    with tab_lag:
        sel_lag = render_generic_link_table(df_lag, f"net_lag_{selected_dev_name}")
        if sel_lag:
            render_delete_action(sel_lag, "Physical", "Staged")

    with tab_intra:
        sel_intra = render_generic_link_table(df_intra, f"net_intra_{selected_dev_name}")
        if sel_intra:
            render_delete_action(sel_intra, "Physical", "Staged")

    with tab_inter:
        sel_inter = render_generic_link_table(df_inter, f"net_inter_{selected_dev_name}")
        if sel_inter:
            render_delete_action(sel_inter, "Physical", "Staged")

def render_delete_action(selected_row, reset_type, reset_status):
    """Helper to render the delete UI for any link type."""
    import streamlit as st
    from src.api_network import delete_network_link, update_port

    with st.container(border=True):
        st.warning(f"⚠️ **Action Required:** Remove connection `{selected_row.get('Description')}`?")
        if st.button("🗑️ Terminate Link & Reset Ports", key=f"del_{selected_row['link_id']}"):
            if delete_network_link(selected_row['link_id']):
                # Reset both ends of the link
                reset_payload = {
                    "port_description": "",
                    "port_type": reset_type,
                    "port_service_status": reset_status
                }
                update_port(selected_row['a_port_id'], reset_payload)
                update_port(selected_row['b_port_id'], reset_payload)
                st.toast("Link removed and ports reset.", icon="✅")
                st.rerun()
                
                
def render_fdp_port_editor(selection):
    """
    Specific editor for FDPs using GET /patchPanels/device/{id} 
    and PUT /patchPanels/port/{panel_port_id}.
    """
    from src.utils.api_patch_panel import get_patch_panel, update_panel_port # Lazy Import
    
    panel_id = selection['device_id']
    st.subheader(f"🔌 FDP Port Configuration: {selection['device_name']}")
    
    # 1. Fetch detailed port map specifically for Patch Panels
    panel_details = get_patch_panel(panel_id)
    
    if panel_details and "ports" in panel_details:
        df_ports = pd.DataFrame(panel_details["ports"])
        
        # 2. Use Data Editor for granular port updates
        # We disable ID columns to prevent accidental database corruption
        edited_df = st.data_editor(
            df_ports,
            key=f"fdp_editor_{panel_id}",
            disabled=["panel_port_id", "device_id"],
            hide_index=True,
            use_container_width=True
        )

        if st.button("💾 Save FDP Port Changes", type="primary"):
            success_count = 0
            for _, row in edited_df.iterrows():
                # API Call: PUT /patchPanels/port/{panel_port_id}
                if update_panel_port(row['panel_port_id'], row.to_dict()):
                    success_count += 1
            
            if success_count > 0:
                st.success(f"✅ Updated {success_count} ports.")
                st.rerun()
    else:
        st.info("No port data found for this FDP.")

def render_fdp_admin_controls(selection):
    """Handles the DELETE /patchPanels/device/{id} logic."""
    from src.utils.api_patch_panel import delete_patch_panel # Lazy Import
    
    st.divider()
    with st.expander("🚨 Danger Zone"):
        st.error(f"Deleting `{selection['device_name']}` will remove all associated port records.")
        confirm = st.text_input("Type the device name to confirm", key=f"del_conf_{selection['device_id']}")
        
        if st.button("🗑️ Delete Patch Panel", type="primary", use_container_width=True):
            if confirm == selection['device_name']:
                # API Call: DELETE /patchPanels/device/{device_id}
                if delete_patch_panel(selection['device_id']):
                    st.success("Patch Panel Deleted.")
                    st.rerun()
            else:
                st.warning("Confirmation name does not match.")