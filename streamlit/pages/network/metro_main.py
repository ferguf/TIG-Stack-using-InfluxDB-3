import streamlit as st
import uuid
# Ensure this import matches the file created in Step 2
import pages.network.metro_data as metro

def run_metro_dashboard():
    # 1. State Management
    if "active_net_id" not in st.session_state:
        st.session_state["active_net_id"] = f"NET-{str(uuid.uuid4())[:4].upper()}"
    
    topo_id = st.session_state["active_net_id"]

    # 2. Global Header
    st.title("🌐 metro Network Management")
    st.caption(f"Session: {topo_id}")

    # 3. Tab Routing
    t1, t2, t3, t4 = st.tabs([
        "📥 Load Data", 
        "🚀 Health", 
        "🔗 Design", 
        "📦 Inventory" 
    ])
    
    with t1:
        # This calls the method in the file below
        metro.render_load_data_view()
        
    with t2:
        st.info("Network Health Monitoring - Coming Soon")
        
    with t3:
        st.info("Design & Path Topology - Coming Soon")
        
    with t4:
        st.info("Hardware Inventory View - Coming Soon")

if __name__ == "__main__":
    run_metro_dashboard()