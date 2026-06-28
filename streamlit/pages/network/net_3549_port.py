import streamlit as st
import pandas as pd
import os
from src.ui_components import UI
from src.api_network import (
    get_site_details_by_shortname,
    post_device,
    get_devices_by_location, 
    post_device_ports, 
    API_URL
)
from src.utils.ui_network_forms import render_device_ports_table, render_location_search_component
from src.utils.file_utils import (
    find_and_read_role_file,
    normalize_dataframe_columns,
    sanitize_for_api,
    clean_device_payload
)

# Configuration
ROLES_DIR = "/streamlit/templates/roles"

# ---------------------------------------------------------
# 1. INGESTION ENGINE (Device + Port Lifecycle)
# ---------------------------------------------------------

def ingest_single_device_chain(row: pd.Series):
    """
    Automated Provisioning Sequence:
    1. Create Device -> 2. Find Role Template -> 3. Post Ports
    """
    # Step 1: Create Device
    device_payload = clean_device_payload(row.to_dict())
    resp_device = post_device(device_payload)
    
    if not resp_device or "device_id" not in resp_device:
        return False, f"Device API failed for {row.get('device_name')}"

    dev_id = resp_device["device_id"]

    # Step 2: Role File Processing
    df_ports, role_file = find_and_read_role_file(row.get("device_model"))
    
    if df_ports is None:
        return False, f"Missing Role Template: {role_file}"

    try:
        # Step 3: Bulk Post Ports
        df_ports["device_id"] = dev_id
        ports_payload = sanitize_for_api(df_ports).to_dict(orient="records")
        
        if post_device_ports(dev_id, ports_payload):
            return True, f"Success: {row.get('device_name')} + {len(df_ports)} ports."
        return False, f"Port API rejected {row.get('device_name')}"

    except Exception as e:
        return False, f"Processing Error: {str(e)}"

# ---------------------------------------------------------
# 2. UI VIEW (Main Entry Point)
# ---------------------------------------------------------

def render_load_data_view():
    """
    Unified Device & Port Management View.
    Flow: Search Site -> Review Site Info -> Manage Device Ports.
    """
    st.header("🚀 Device & Port Management")
    
    # 1. Retrieve cached data from session state
    results = st.session_state.get("cached_3549_search")
    site_info = st.session_state.get("cached_site_info")
    
    # 2. Render Search Input Component
    # selection: the row picked from the inventory table
    # trigger: boolean if 'Fetch' was clicked
    selection, search_term, trigger = render_location_search_component("3549", results=results)
    
    # 3. Handle Search Logic
    if trigger and search_term:
        with st.spinner(f"Searching for site {search_term.upper()}..."):
            api_results = get_devices_by_location(search_term)
            api_site_info = get_site_details_by_shortname(search_term)
            
            if api_results:
                st.session_state["cached_3549_search"] = api_results
                st.session_state["cached_site_info"] = api_site_info
                st.rerun()
            else:
                st.error(f"No active devices found for {search_term.upper()}")
                st.session_state["cached_3549_search"] = None
                st.session_state["cached_site_info"] = None

    # 4. Site Information Section
    if site_info:
        st.divider()
        with st.container(border=True):
            st.markdown(f"#### 📍 Site Context: {search_term.upper()}")
            
            # Row 1: High-level Site Identifiers
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("CLLI", site_info.get("location_code", "N/A"))
            c2.metric("Facility", site_info.get("facility_type", "N/A"))
            c3.metric("Latitude", site_info.get("latitude", "N/A"))
            c4.metric("Longitude", site_info.get("longitude", "N/A"))

            # Row 2: Physical Address
            st.markdown("---")
            addr = site_info.get("address", "No address on file")
            city = site_info.get("city", "")
            state = site_info.get("state", "")
            zip_code = site_info.get("zip_code", "")
            
            full_address = f"{addr}, {city}, {state} {zip_code}".strip(", ")
            st.info(f"🏠 **Physical Address:** {full_address}")

    # 5. Interface Management Section
    # Triggers when a row is clicked in the selection table rendered by search_component
    if selection is not None:
        st.divider()
        st.subheader(f"🔌 Interface Management: {selection['device_name']}")
        
        # Renders the port-level table, editing forms, and state controls
        render_device_ports_table(
            device_id=selection['device_id'],
            device_name=selection['device_name']
        )
    
    # 6. Reset Option (Floating at bottom for convenience)
    if results or site_info:
        st.sidebar.divider()
        if st.sidebar.button("🧹 Clear Selection", use_container_width=True):
            st.session_state["cached_3549_search"] = None
            st.session_state["cached_site_info"] = None
            st.rerun()