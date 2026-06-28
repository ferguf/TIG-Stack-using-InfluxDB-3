import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
# Import your actual API hooks
from src.utils.api_customer import get_customers, get_fabric_services, get_fabric_service_detail
from src.utils.ui_route_vision import render_route_vision
from src.galileo.fabric_service_builder import render_twin_topology

def show_dashboard():
    """
    Renders the Day 2 Operations view.
    Features interactive row selection to trigger deep-dive Digital Twin views.
    Includes a nested Inventory tab for Ports, Interfaces, and Connections.
    """
    import streamlit as st
    import pandas as pd
    from src.utils.api_customer import get_customers, get_fabric_services, get_fabric_service_detail

    st.header("📊 Day 2 Operations Dashboard")
    st.caption("Monitor the health, status, and inventory of provisioned Fabric Services.")
    st.divider()

    # ==========================================
    # 1. FETCH & SELECT CUSTOMER
    # ==========================================
    db_customers_df = get_customers()
    
    if db_customers_df.empty:
        st.warning("⚠️ No customers found in the database. Please verify API connectivity.")
        return

    # Map customer names to their IDs directly from the DataFrame
    cust_options = {row['customer_name']: row['customer_id'] for _, row in db_customers_df.iterrows()}
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_cust_name = st.selectbox(
            "Select Customer Account", 
            options=list(cust_options.keys()),
            key="day2_cust_select"
        )
    
    customer_id = cust_options[selected_cust_name]

    # ==========================================
    # 2. FETCH LIVE SERVICE INVENTORY
    # ==========================================
    with st.spinner(f"Fetching live telemetry for {selected_cust_name}..."):
        # Fetch actual services for the selected customer
        live_services = get_fabric_services(customer_id)
        
    df_services = pd.DataFrame(live_services)

    if df_services.empty:
        st.info(f"No active Fabric Services found for {selected_cust_name}.")
        return

    # ==========================================
    # 3. HIGH-LEVEL HEALTH METRICS
    # ==========================================
    st.markdown("### 📈 Fleet Summary")
    
    status_col = df_services.get('status', df_services.get('oper_status', pd.Series(['unknown'] * len(df_services))))
    
    total_svcs = len(df_services)
    active_svcs = len(df_services[status_col.astype(str).str.lower().isin(['active', 'up'])])
    staged_svcs = len(df_services[status_col.astype(str).str.lower().isin(['staged', 'provisioning'])])
    issue_svcs = total_svcs - (active_svcs + staged_svcs) 
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Services", total_svcs)
    m2.metric("Active & Healthy", active_svcs, delta="Operational", delta_color="normal")
    m3.metric("Staged / Pending", staged_svcs, delta="Building", delta_color="off")
    m4.metric("Attention Required", issue_svcs, delta="Alerts", delta_color="inverse" if issue_svcs > 0 else "off")

    st.divider()

    # ==========================================
    # 4. INTERACTIVE SERVICE INVENTORY TABLE
    # ==========================================
    
    st.markdown("### 🗄️ Service Inventory")
    st.caption("👈 **Click on any row** to view the live Digital Twin and service manifest.")
    
    def map_status_icon(val):
        v = str(val).lower()
        if v in ["active", "up"]: return "✅ Active"
        elif v in ["staged", "provisioning"]: return "⏳ Staged"
        elif v in ["degraded", "warning"]: return "⚠️ Degraded"
        elif v in ["down", "failed"]: return "❌ Down"
        return f"❓ {val}"

    # Safely apply the mapping
    status_col = df_services.get('status', df_services.get('oper_status', pd.Series(['unknown'] * len(df_services))))
    df_services["health_display"] = status_col.apply(map_status_icon)

    display_cols = ["service_name", "service_type", "health_display", "service_id"]
    existing_cols = [c for c in display_cols if c in df_services.columns]

    # 🟢 OPTIMIZATION: Create a dedicated "view" dataframe so the index is locked
    df_view = df_services[existing_cols].copy()

    # Render the interactive table
    event = st.dataframe(
        df_view,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",   
        on_select="rerun",             
        key="day2_inventory_table",    
        column_config={
            "service_name": st.column_config.TextColumn("Service Name", width="medium"),
            "service_type": st.column_config.TextColumn("Architecture", width="small"),
            "health_display": st.column_config.TextColumn("Health Status", width="small"),
            "service_id": st.column_config.TextColumn("Galileo ID", width="medium")
        }
    )

    # ==========================================
    # 5. DEEP DIVE (Triggers on Row Click)
    # ==========================================
    if event and event.selection.rows:
        # 🟢 OPTIMIZATION: Safely pull the ID directly from our locked view dataframe
        selected_idx = event.selection.rows[0]
        selected_svc_id = df_view.iloc[selected_idx]['service_id']
        selected_svc_name = df_view.iloc[selected_idx]['service_name']
        
        st.divider()
        st.markdown(f"### 🔍 Service Deep Dive: `{selected_svc_name}`")
        
        with st.spinner("Fetching service telemetry and routing state..."):
            svc_detail = get_fabric_service_detail(selected_svc_id)
            
        if svc_detail:
            # 🚀 Create the 4 Core Operational Tabs
            t_topo, t_perf, t_route, t_inv = st.tabs([
                "🗺️ Topology", 
                "📈 Performance", 
                "🛰️ Route Vision",
                "🗄️ Inventory"
            ])
            
            # --- TAB 1: TOPOLOGY ---
            with t_topo:
                from src.utils.service_wizards import render_fabric_service_overview
                render_fabric_service_overview(fs_detail=svc_detail, is_read_only=True)

                # --- TAB 2: PERFORMANCE PLUMBING ---
            with t_perf:
                from src.utils.ui_telemetry import render_telemetry_tab 
                render_telemetry_tab(t_perf, svc_detail)

            # --- TAB 3: ROUTE VISION ---
            with t_route:
                from src.utils.ui_route_vision import render_route_vision
                render_route_vision(selected_svc_id, svc_detail)
                
            # --- TAB 4: INVENTORY ---
            with t_inv:
                st.markdown("#### 📦 Component Details")
                st.caption("Review the raw underlying data objects attached to this service.")
                
                # 🟢 Sub-Tabs for Component Types
                sub_port, sub_intf, sub_conn = st.tabs(["🔌 Ports", "🌐 Interfaces", "🔗 Fabric Connections"])
                
                with sub_port:
                    ports = svc_detail.get("fabric_ports", [])
                    if ports:
                        st.dataframe(pd.DataFrame(ports), use_container_width=True, hide_index=True)
                    else:
                        st.info("No physical ports are assigned to this service.")
                        
                with sub_intf:
                    interfaces = svc_detail.get("fabric_interfaces", [])
                    if interfaces:
                        st.dataframe(pd.DataFrame(interfaces), use_container_width=True, hide_index=True)
                    else:
                        st.info("No logical interfaces are assigned to this service.")
                        
                with sub_conn:
                    connections = svc_detail.get("fabric_connections", [])
                    if connections:
                        st.dataframe(pd.DataFrame(connections), use_container_width=True, hide_index=True)
                    else:
                        st.info("No fabric connections have been stitched for this service yet.")
                    
        else:
            st.error("❌ Failed to retrieve the service details.")