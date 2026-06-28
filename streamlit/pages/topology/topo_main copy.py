import streamlit as st
# 1. Standard Imports (Top Level)
from src.ui_messages import MessageCenter
import pages.topology.service as service
import pages.topology.topology as topology
import streamlit.pages.topology.pop as pop
import pages.topology.metro as metro

# This must be the first streamlit command in your script
st.set_page_config(page_title="Network Map", layout="wide")

def run_topology_dashboard():
    # 1. State

    
    # 2. Data Load


    # 3. Header
    name = st.session_state.get("active_customer_name")
    st.title(f"👥 Selected: {name}" if name else "👥 Topology Dashboard")

    # 4. Tabs
    t1, t2, t3, t4 = st.tabs(["👥 Gateway", "🚀 Metro ", "🔗 AWS Last Mile Interconect ", "👁️ Route Vision"])

    with t1:
        service.show_gateway()

    with t2:
        active_id = st.session_state.get("active_customer_id")
        if active_id:
            topology.show_topology(active_id)
        else:
            st.warning("⚠️ Please select a Customer in the first tab.")

if __name__ == "__main__":
    run_topology_dashboard()