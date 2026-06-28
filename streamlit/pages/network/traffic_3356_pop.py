import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging

# --- IMPORT DATA CONTROLLER ---
from pages.network import net_3356_data as data_ctrl
from pages.network import traffic_3356_plotly_pop as plotter

logger = logging.getLogger(__name__)

def apply_dashboard_theme(fig, height=550):
    """Standardizes Plotly charts to the NDT Dark Mode theme."""
    fig.update_layout(
        template="plotly_dark", height=height,
        margin=dict(t=40, b=20, l=20, r=20),
        font=dict(size=12, color="#E0E0E0"),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False), yaxis=dict(visible=False)
    )
    return fig

def render_pop_view():
    """
    NDT Presentation Layer: Renders the Point of Presence (PoP) drill-down view.
    Features: Automated telemetry fetch and default site selection (DEN1).
    """
    st.title("📍 PoP Inspection & Flow Analysis")
    st.markdown("Select a specific Point of Presence to visualize bi-directional egress and ingress telemetry.")

    # --- 0. STATE INITIALIZATION ---
    if "last_selected_pop" not in st.session_state:
        st.session_state.last_selected_pop = None

    # --- 1. DATA ACQUISITION ---
    with st.spinner("Synchronizing Global PoP Database..."):
        state = data_ctrl.regional_detail_summary()

    if "error" in state:
        st.error(f"⚠️ {state['error']}")
        return

    df_pops = state["df_pops"]

    if df_pops.empty:
        st.warning("No PoP data found in the API payload.")
        return

    st.divider()

    # --- 2. CASCADING UI CONTROLS ---
    st.markdown("### 🎛️ Site Selector")

    with st.container(border=True):
        # --- 1. REGION SELECTION (With NAMER Default) ---
        available_regions = sorted(df_pops['region'].unique().tolist())
        
        # Define your target default region label
        target_region = "NAMER" 
        reg_default_idx = 0
        if target_region in available_regions:
            reg_default_idx = available_regions.index(target_region)
        
        selected_region = st.radio(
            "🌍 **1. Select Operating Region**", 
            options=available_regions, 
            index=reg_default_idx, # Forces "NAMER" on boot
            horizontal=True
        )
        
        # --- 2. POP SELECTION (With DEN1 Default) ---
        df_filtered_region = df_pops[df_pops['region'] == selected_region]
        available_pops = sorted(df_filtered_region['pop_id'].unique().tolist())
        
        pop_default_idx = 0
        target_pop = "den1"
        
        # Case-insensitive check for the PoP target
        if target_pop.lower() in [p.lower() for p in available_pops]:
            # Find the actual casing used in the list
            pop_default_idx = [p.lower() for p in available_pops].index(target_pop.lower())

        selected_pop_id = st.selectbox(
            "🏢 **2. Select or Search PoP Site**", 
            options=available_pops,
            index=pop_default_idx, # Forces "DEN1" within NAMER
            help="Type to search for a specific PoP identifier."
        )

        # Sync state to trigger the automated fetch
        if selected_pop_id != st.session_state.last_selected_pop:
            st.session_state.last_selected_pop = selected_pop_id
        
    # --- 3. SITE OVERVIEW & AUTOMATED TELEMETRY ---
    if selected_pop_id:
        st.divider()
        pop_data = df_filtered_region[df_filtered_region['pop_id'] == selected_pop_id].iloc[0]
        
        st.markdown(f"### 📊 Site Overview: `{pop_data['pop_id'].upper()}`")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Location", f"{pop_data.get('city', 'Unknown')}, {pop_data.get('country', '')}")
        m2.metric("Primary Provider", pop_data.get('provider', 'Unknown'))
        m3.metric("Routers", pop_data.get('router_count', 0))
        m4.metric("Status", "🟢 Active")
        
        st.divider()

        # --- 4. AUTOMATED FETCH (No Button Required) ---
        st.markdown(f"### 🌊 Bi-Directional Flow Analysis")
        
        with st.spinner(f"Querying Backbone Fabric for {selected_pop_id.upper()}..."):
            # Automated API call to the pop2pop telemetry endpoint
            flow_state = data_ctrl.pop_to_pop_telemetry(selected_pop_id.lower(), limit=25)
        
        if "error" in flow_state:
            st.error(flow_state["error"])
        else:
            df_flows = flow_state["df_flows"]
            
            if not df_flows.empty:
                # Define presentation tabs
                tab_graphy, tab_intercity, tab_local, tab_ledger = st.tabs([
                    "🕸️ Graphy View", 
                    "➡️ Pop Intercity Traffic",
                    "➡️ Pop Local Traffic", 
                    "📋 Router2Router Ledger"
                ])
                
                center_node = selected_pop_id.upper()
                
                # --- TAB: GRAPHY VIEW ---
                with tab_graphy:
                    st.markdown("### 🔍 Tri-View Flow Analysis")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("**🕸️ Hub & Spoke Topology**")
                        st.plotly_chart(
                            plotter.create_radial_topology(df_flows, center_node, height=500), 
                            use_container_width=True
                        )

                    with col2:
                        st.markdown("**📊 Egress vs Ingress (Split-Axis)**")
                        st.plotly_chart(
                            plotter.create_split_axis_bar(df_flows, center_node, height=500), 
                            use_container_width=True
                        )

                    with col3:
                        st.markdown("**🍩 Directional Traffic Share**")
                        st.plotly_chart(
                            plotter.create_dual_donuts_vertical(df_flows, center_node, height=750),
                            use_container_width=True
                        )

                # --- TAB: INTERCITY TRAFFIC (Sankey) ---
                with tab_intercity:
                    st.plotly_chart(
                        plotter.create_sankey_chart(df_flows, center_node, height=600), 
                        use_container_width=True
                    )

                # --- TAB: LOCAL TRAFFIC (Chassis Inventory) ---
                with tab_local:
                    render_chassis_inventory_tab(selected_pop_id)
                
                # --- TAB: DATA LEDGER ---
                with tab_ledger:
                    df_ledger, ledger_config = plotter.get_flow_ledger_config(df_flows)
                    st.dataframe(
                        df_ledger,
                        use_container_width=True,
                        hide_index=True,
                        column_config=ledger_config
                    )
            else:
                st.warning(f"No active flows detected for {selected_pop_id.upper()} in current telemetry window.")

def render_chassis_inventory_tab(selected_pop_id):
    """
    NDT Infrastructure View: Renders PoP summary metrics followed by a two-tab workspace.
    Tab 1: Physical Asset Ledger
    Tab 2: Internal Egress Flow Mapping
    """
    st.markdown(f"### 🏗️ Site Infrastructure: {selected_pop_id.upper()}")
    
    # 1. Fetch Unified Summary Data
    site_summary = data_ctrl.get_pop_site_summary(selected_pop_id)
    
    if not site_summary["success"]:
        st.error(f"❌ Site Inventory Unavailable: {site_summary.get('error')}")
        return

    raw_data = site_summary["raw"]
    summary = raw_data.get("summary", {})
    raw_routers = raw_data.get("routers", [])

    if not summary:
        st.warning("⚠️ Aggregate summary block missing from API response.")
        return

    # 2. Site-Level Metric Row (Global Context - stays outside tabs)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Router Count", len(raw_routers))
    m2.metric("Inter Bytes", data_ctrl.format_bytes(summary.get("inter_bytes", 0)))
    m3.metric("Intra Bytes", data_ctrl.format_bytes(summary.get("intra_bytes", 0)))
    m4.metric("Total Bytes", data_ctrl.format_bytes(summary.get("total_bytes", 0)))
    m5.metric("% of Global", f"{summary.get('pct_of_global', 0):.3f}%")

    st.divider()

    # 3. Define Workspace Tabs
    tab_flows, tab_inventory = st.tabs(["🧬 Pop traffic","📟 Detailed Node Inventory" ])

    # --- TAB 1: DETAILED NODE INVENTORY ---
    with tab_flows:
        if raw_routers:
            st.markdown("#### Chassis-to-Category Flow Mapping")
            
            # Transform Router list into Sankey format
            sankey_data = []
            for r in raw_routers:
                r_id = r.get('router', 'Unknown')
                
                # Check each egress category
                if r.get('inter_egress_bytes', 0) > 0:
                    sankey_data.append({'src': r_id, 'dst': 'INTER (Backbone)', 'val': r['inter_egress_bytes'], 'clr': '#dc3545'})
                if r.get('intra_egress_bytes', 0) > 0:
                    sankey_data.append({'src': r_id, 'dst': 'INTRA (Fabric)', 'val': r['intra_egress_bytes'], 'clr': '#ffc107'})
                if r.get('local_egress_bytes', 0) > 0:
                    sankey_data.append({'src': r_id, 'dst': 'LOCAL (Edge)', 'val': r['local_egress_bytes'], 'clr': '#00d1ff'})

            if sankey_data:
                df_sankey = pd.DataFrame(sankey_data)
                
                # --- NDT Plotter Integration ---
                # Call the external plotting function with the black text/margin fixes
                fig = plotter.create_internal_sankey(
                    df_sankey, 
                    title=f"Internal Egress vectors: {selected_pop_id.upper()}", 
                    height=600
                )
                
                # Render the chart
                st.plotly_chart(fig, use_container_width=True)
                
                # Optional: Let the user see the raw data vectors driving the chart
                with st.expander("🔍 View traffic Detailsr"):
                    st.dataframe(df_sankey, use_container_width=True, hide_index=True)
            else:
                st.info("Zero egress flows detected.")
        else:
            st.info("No router telemetry available for flow mapping.")

    with tab_inventory:
        if raw_routers:
            df_chassis = pd.DataFrame(raw_routers)
            df_disp = df_chassis.copy()
            
            # Map API keys to human-readable UI columns
            byte_map = {
                'router_egress_total_bytes': 'Total Out',
                'inter_egress_bytes': 'Inter Out',
                'intra_egress_bytes': 'Intra Out',
                'local_egress_bytes': 'Local Out'
            }
            
            for raw_col, disp_col in byte_map.items():
                if raw_col in df_disp.columns:
                    df_disp[disp_col] = df_disp[raw_col].apply(data_ctrl.format_bytes)
                else:
                    df_disp[disp_col] = "0 B"

            # Normalize Backbone Load (pct to 0.0-1.0 float)
            if 'pct_inter' in df_disp.columns:
                df_disp['load_val'] = df_disp['pct_inter'] / 100
            elif 'pct_inter_of_router_egress' in df_disp.columns:
                df_disp['load_val'] = df_disp['pct_inter_of_router_egress'] / 100
            else:
                df_disp['load_val'] = 0.0

            # Filter for final display
            desired_cols = ['router', 'router_type', 'location_code', 'Total Out', 'Inter Out', 'Intra Out', 'Local Out', 'load_val']
            available_cols = [col for col in desired_cols if col in df_disp.columns]

            st.dataframe(
                df_disp[available_cols],
                column_config={
                    "router": "Router ID",
                    "router_type": "Role",
                    "location_code": "CLLI Code",
                    "load_val": st.column_config.ProgressColumn(
                        "Backbone Intensity",
                        help="Ratio of INTER-backbone traffic to total site egress",
                        format="%.2f",
                        min_value=0,
                        max_value=1
                    )
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No individual router telemetry found for this PoP.")

    # --- TAB 2: INTERNAL FLOW DYNAMICS (Router -> Category) ---

if __name__ == "__main__":
    render_pop_view()