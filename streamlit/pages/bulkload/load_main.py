import streamlit as st
import uuid
import pages.bulkload.load_location_data as loc
import pages.bulkload.load_device as dev
import pages.bulkload.load_patch_panel as patch
import pages.bulkload.load_netlink as netlink
import pages.bulkload.load_fabric_conn as FC
import pages.bulkload.load_fabric_service as FS
import pages.bulkload.load_material as material
import pages.bulkload.load_interface as interface
import pages.bulkload.load_lric as lric


def run_location_dashboard():
    # 1. State Management
    if "active_location_id" not in st.session_state:
        st.session_state["active_location_id"] = f"T-{str(uuid.uuid4())[:4].upper()}"
    
    topo_id = st.session_state["active_location_id"]

    # 2. Global Header
    st.title("👥 Bulk load of Data into Table")
    st.caption(f"Session: {topo_id}")

    # 3. Tab Routing
    tabs = st.tabs([
        "👥 Location Data", 
        "🚀 Devices", 
        "🚀 Hardware", 
        "🚀 Netlinks", 
        "🚀 Documents", 
        "🔗 Service Defs", 
        "🔗 Patch Panels", 
        "🔗 Fabric Connections", 
        "🔗 Fabric Services", 
        "🔗 Interface",  
        "🔗 LRIC", 
        "👁️ Materials" 
        
    ])
    
    t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12 = tabs

    with t1:
        # All rendering logic moved here
        loc.render_load_data_view()
        
    with t2:
        dev.render_device_manager()
    with t3:
        st.info("Bulk load of Hardware- Coming Soon")    
    with t4:
        netlink.render_netlink_view()
    with t5:
        st.info("Bulk load of Documents - Coming Soon")
    with t6:
        st.info("Bulk load of Interface - Coming Soon")
    with t7:
        patch.render_patchpanel_tabs()
    with t8:
        FC.render_fabric_connections_view()
    with t9:
        FS.render_fabric_service_view()    
    with t10:    
        interface.render_interface_view()
    with t11:    
        lric.render_lric_view()
    with t12:    
        material.render_material_view()

if __name__ == "__main__":
    run_location_dashboard()