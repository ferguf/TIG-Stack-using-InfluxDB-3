import streamlit as st

# Import Tier logic
import pages.customer.dashboard as dashboard
import pages.customer.service as cust_tier
import pages.customer.fabric_service as fs_tier
import pages.customer.fabric_connection as fc_tier
import pages.customer.port as port_tier
from pages.customer import route_vision as RV
import pages.customer.fabric_provision as prov  # New Provisioning module
import src.utils.service_wizards as wizards

# Import Core Utilities
from src.state_managers import FabricStateManager
from src.utils.ui_debug import render_system_debugger
from src.ui_messages import MessageCenter


def run_customer_dashboard():
    """
    Main entry point for the Customer Operations Dashboard.
    Orchestrates Global State, System Debugging with a visibility toggle.
    """
    import streamlit as st
    
    # --- 1. CORE UTILITY IMPORTS ---
    import pages.customer.dashboard as dashboard
    import pages.customer.service as cust_tier
    import pages.customer.fabric_service as fs_tier
    import pages.customer.fabric_connection as fc_tier
    import pages.customer.port as port_tier
    from pages.customer import route_vision as RV
    import pages.customer.fabric_provision as prov
    import src.utils.service_wizards as wizards
    from src.state_managers import FabricStateManager
    from src.ui_messages import MessageCenter
    from src.utils.ui_debug import render_global_system_debugger

    # --- 2. INITIALIZATION & AUTO-SYNC ---
    manager = FabricStateManager()
    manager.initialize()
    MessageCenter.display_messages()

    active_fs = st.session_state.get("active_fs")
    if active_fs and manager.get_active_id("fs") != active_fs:
        fs_detail = st.session_state.get("active_service_detail", {})
        manager.set_active("fs", active_fs, fs_detail)

    # --- 3. THE DEBUG GATE (Radio Toggle) ---
    # Positioned at the top to control the Global System Inspector
    _, c_toggle = st.columns([3, 1])
    with c_toggle:
        debug_view = st.radio(
            "System Debug",
            ["Hide", "Show"],
            index=0, # Default to Hide for a clean production view
            horizontal=True,
            key="ndt_global_debug_toggle",
            label_visibility="collapsed"
        )

    # Only render the consolidated debugger if "Show" is selected
    if debug_view == "Show":
        render_global_system_debugger(manager=manager, scope="DashboardRoot")
    else:
        st.caption("🛠️ Debugger Offline | Toggle 'Show' to inspect Fabric Tiers")

    # --- 4. UNIVERSAL INTERCEPTION POINT ---
    show_launcher = st.session_state.get("show_launcher", True)

    if not show_launcher:
        st.title("⚡ Active Provisioning Workflow")
        active_customer_id = manager.get_active_id("cust") or st.session_state.get("active_cust")
        
        if not active_customer_id:
            st.error("⚠️ Lost customer context.")
            if st.button("⬅️ Return to Dashboard"):
                st.session_state.show_launcher = True
                st.rerun()
        else:
            wizards.render_sub_wizard_logic(active_customer_id)
        return  

    # --- 5. STANDARD OPERATIONS DASHBOARD (TABS) ---
    st.title("🌐 Network Fabric Operations")

    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "👥 Customers", "🔌 Fabric Services", "🛠️ Provision Wizard", 
        "👁️ Dashboard", "🔌 Provision Wizard (Old)", "🛠️ Provisioning (Old)", "👁️ Vision"
    ])

    with t1: cust_tier.show_customers()
    with t2:
        if manager.get_active_id("cust"):
            fs_tier.show_fabric_service(manager.get_active_id("cust"))
    with t3: wizards.show_wizard()
    with t4: dashboard.show_dashboard()
    with t5: prov.show_provisioning_view()
    with t6: fc_tier.show_fabric_connection()
    with t7:
        if manager.get_active_id("fs"):
            RV.show_route_vision(manager.get_active_id("fs"))

if __name__ == "__main__":
    run_customer_dashboard()