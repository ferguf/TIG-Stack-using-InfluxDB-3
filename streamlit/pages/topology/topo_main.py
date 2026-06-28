import streamlit as st
import uuid
from pages.topology import map1
from pages.topology.metro import metro  # Ensure file is metro.py, class is metro
from pages.topology.pop import pop      # Ensure file is pop.py, class is pop
from pages.topology.builder import DynamicTopology
from pages.topology.port import PortTopology      # Ensure file is pop.py, class is pop

def run_topology_dashboard():
    # 1. State Management
    if "active_topology_id" not in st.session_state:
        st.session_state["active_topology_id"] = f"T-{str(uuid.uuid4())[:4].upper()}"
    
    topo_id = st.session_state["active_topology_id"]

    # 2. Global Header
    st.title("👥 Topology Dashboard")
    st.caption(f"Session: {topo_id}")

    # 3. Tab Routing
    tabs = st.tabs([
        "👥 Gateway", 
        "🚀 Metro", 
        "🔗 Pop", 
        "👁️ route Visio", 
        "👁️ topology builder", 
        "📊 Plotly Metro",
        "📊 Plotly Pop",
        "📊 Plotly Port"
        ])
    
    t1, t2, t3, t4, t5, t6, t7,t8 = tabs

    with t1:
        map1.show_ring(topo_id)
    with t2:
        map1.show_ring(topo_id)
    with t3:
        map1.show_pop(topo_id)
    with t4:
        map1.show_route_vision(topo_id)
    with t5:
        topo = DynamicTopology()
        topo.show_builder(topo_id)      
    with t6:
        # Tab 6: Plotly Metro
        metro_view = metro()
        metro_view.show_topology(topo_id)
    with t7:
        # Tab 7: Plotly Pop

        pop_view = pop()
        pop_view.show_topology(topo_id)
    with t8:
        # Tab 7: Plotly Pop

        port_view = PortTopology()
        port_view.show_topology(topo_id)


if __name__ == "__main__":
    run_topology_dashboard()