import streamlit as st
import pandas as pd

# --- INTERNAL MODULE IMPORTS ---
from src.utils.api_network import get_devices, fetch_master_dashboard
from pages.network import topology_map  

# IMPORT THE UNIFIED ENGINES
from pages.network import network_inventory
from pages.network import network_dashboard

# ==========================================
# 🚀 MAIN ORCHESTRATOR: AS209
# ==========================================

def render_device_dashboard():
    # Maintain global UI consistency
    if "page_config_set" not in st.session_state:
        st.set_page_config(page_title="209 Command Center", layout="wide")
        st.session_state["page_config_set"] = True
    
    # 1. HEADER & GLOBAL CONTROLS
    st.title("🎛️ 209 Network Command Center")
    col_refresh, _ = st.columns([1, 6])
    with col_refresh:
        if st.button("🔄 Force Refresh Data", use_container_width=True):
            st.rerun()
            
    st.divider()

    # 2. TRUE LAZY-LOADING ROUTER
    active_view = st.radio(
        "Select View",
        ["🗄️ 209 Inventory", "📊 209 Dashboard", "🕸️ 209 Topology"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.write("<br>", unsafe_allow_html=True)

    # 3. CONDITIONAL EXECUTION & DATA FETCHING
    if active_view == "🗄️ 209 Inventory":
        with st.spinner("Fetching Inventory Telemetry..."):
            # Call the unified engine with the AS209 context
            network_inventory.render_inventory_dashboard(initial_network="AS209")

    elif active_view == "📊 209 Dashboard":
        with st.spinner("Fetching 209 Network Telemetry..."):
            dashboard_data = fetch_master_dashboard("AS209")
            if not dashboard_data:
                st.warning("⚠️ No telemetry data available for AS209.")
            else:
                # Call the unified engine with the AS209 context
                network_dashboard.render_network_dashboard(dashboard_data, target_asn="AS209")

    elif "Topology" in active_view:
        topology_map.render_topology_view(network="AS209")

if __name__ == "__main__":
    render_device_dashboard()