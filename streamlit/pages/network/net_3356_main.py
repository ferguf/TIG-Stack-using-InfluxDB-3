import streamlit as st
import uuid
import requests
import logging
import pages.network.net_3356_global as Net3356
from pages.network import topology_map
import pages.network.net_3356_inventory as Net3356Inventory

def run_3356_dashboard():
    # 1. State Management
    if "active_net_id" not in st.session_state:
        st.session_state["active_net_id"] = f"NET-{str(uuid.uuid4())[:4].upper()}"
    
    topo_id = st.session_state["active_net_id"]

    # 2. Global Header
    st.title("🌐 3356 Network Management")
    st.caption(f"Session: {topo_id}")

    # 3. Tab Routing
    t4, t2, t3, t1 = st.tabs([
        "📦 Inventory" ,
        "📥 Router to Router", 
        "🚀 Health", 
        "🔗 Topology"

    ])
    with t4:
        # Call the new inventory dashboard method
        Net3356Inventory.render_inventory_dashboard()
    
    with t2:
        Net3356.render_traffic_dashboard()
        
    with t3:
        st.info("Network Health Monitoring - Coming Soon")
        
    with t1:
        # Topology executes purely when requested. 
        # We explicitly pass the AS3356 network parameter to the universal renderer.
        topology_map.render_topology_view(network="AS3356")
        

if __name__ == "__main__":
    run_3356_dashboard()