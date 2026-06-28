import streamlit as st
import pandas as pd

# --- INTERNAL MODULE IMPORTS ---
from src.utils.api_network import get_devices, fetch_master_dashboard
from pages.network import dashboard_3549  
from pages.network import topology_map  
from pages.network import net_3549_inventory as Net3549Inventory  
from pages.network import network_inventory

# ==========================================
# 🚀 MAIN ORCHESTRATOR
# ==========================================

def render_device_dashboard():
    # Only call set_page_config if this is the main entry point
    if "page_config_set" not in st.session_state:
        st.set_page_config(page_title="3549 Command Center", layout="wide")
        st.session_state["page_config_set"] = True
    
    # 1. HEADER & GLOBAL CONTROLS
    st.title("🎛️ 3549 Network Command Center")
    col_refresh, _ = st.columns([1, 6])
    with col_refresh:
        if st.button("🔄 Force Refresh Data", use_container_width=True):
            st.rerun()
            
    st.divider()

    # 2. TRUE LAZY-LOADING ROUTER (Replaces st.tabs)
    # Using a horizontal radio button creates explicit execution blocks.
    active_view = st.radio(
        "Select View",
        ["🗄️ 3549 Inventory", "📊 3549 Dashboard", "🕸️ 3549 Topology"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.write("<br>", unsafe_allow_html=True)

    # 3. CONDITIONAL EXECUTION & DATA FETCHING
    if active_view == "🗄️ 3549 Inventory":
        # Data is only fetched when the Inventory view is active
        with st.spinner("Fetching Inventory Telemetry..."):
            raw_data = get_devices()
            if not raw_data:
                st.error("⚠️ No device data returned from the API. Please ensure the backend is running.")
            else:
                df = pd.DataFrame(raw_data)
                if 'updated_at' in df.columns:
                    df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce').dt.strftime('%b %d, %Y %I:%M %p')
                
                # Assuming this function handles its own data or relies on global state
                network_inventory.render_inventory_dashboard(initial_network="AS3549")

    elif active_view == "📊 3549 Dashboard":
        # God Mode data is only fetched when the Dashboard view is active
        with st.spinner("Fetching 3549 Network Telemetry..."):
            dashboard_data = fetch_master_dashboard("AS3549")
            if not dashboard_data:
                st.warning("⚠️ No telemetry data available from the API.")
            else:
                dashboard_3549.render_3549_dashboard(dashboard_data)

    elif "Topology" in active_view:
        topology_map.render_topology_view(network="AS3549")

if __name__ == "__main__":
    render_device_dashboard()