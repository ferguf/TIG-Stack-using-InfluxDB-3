from pages.network import traffic_3356_plotly_pop as plotter  # Ensure your plotter is imported
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import logging

# --- IMPORT DATA CONTROLLER ---
from pages.network import net_3356_data as data_ctrl

logger = logging.getLogger(__name__)

def apply_dashboard_theme(fig, height=400):
    fig.update_layout(
        template="plotly_dark", height=height,
        margin=dict(t=40, b=20, l=20, r=20),
        font=dict(size=12, color="#E0E0E0"),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def render_global_view():
    """
    NDT Presentation Layer: Renders the macro-level global dashboard.
    Includes aggregate KPIs, defensive donut charts, and a regional ledger.
    """
    st.title("🌍 Global Fabric Overview")
    st.markdown("Macro-level inspection of egress volumes and routing efficiencies across the entire global network.")

    with st.spinner("Aggregating Global Telemetry..."):
        state = data_ctrl.global_traffic_summary()

    if "error" in state:
        st.error(f"⚠️ {state['error']}")
        return

    global_metrics = state["global_metrics"]
    df_regions = state["df_regions"]
    
    # --- MACRO KPIs ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tracked Regions", len(df_regions))
    m2.metric("Total PoPs", f"{global_metrics.get('pop_count', 0):,}")
    m3.metric("Active Routers", f"{global_metrics.get('router_count_total', 0):,}")
    m4.metric("Aggregate Fabric Volume", data_ctrl.format_bytes(global_metrics.get('global_egress_traffic', 0)))
    
    st.divider()

    # --- 📊 VISUALIZATION: GLOBAL & REGIONAL DONUTS ---
    st.markdown("### 📊 Egress Traffic Distribution")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### Global Trraffic Breakdown")
        
        # 1. Aggregate global raw bytes
        g_local = df_regions['local_traffic'].sum() if 'local_traffic' in df_regions.columns else 0
        g_intra = df_regions['intra_traffic'].sum() if 'intra_traffic' in df_regions.columns else 0
        g_inter = df_regions['inter_traffic'].sum() if 'inter_traffic' in df_regions.columns else 0

        # --- DEFENSIVE SCHEMA INJECTION ---
        # Provides the exact keys the Plotly 'create_single_donut' function expects
        df_global_flows = pd.DataFrame([
            {'src_pop': 'GLOBAL FABRIC', 'dst_pop': 'LOCAL (Edge)', 'target': 'LOCAL (Edge)', 'value': g_local, 'egress_bytes': g_local, 'total_bytes': g_local},
            {'src_pop': 'GLOBAL FABRIC', 'dst_pop': 'INTRA (Fabric)', 'target': 'INTRA (Fabric)', 'value': g_intra, 'egress_bytes': g_intra, 'total_bytes': g_intra},
            {'src_pop': 'GLOBAL FABRIC', 'dst_pop': 'INTER (Backbone)', 'target': 'INTER (Backbone)', 'value': g_inter, 'egress_bytes': g_inter, 'total_bytes': g_inter}
        ])

        # Plot global donut
        fig_global = plotter.create_single_donut(
            df_flows=df_global_flows, 
            center_node="GLOBAL FABRIC", 
            direction='egress', 
            height=400
        )
        st.plotly_chart(fig_global, use_container_width=True)

    with chart_col2:
        st.markdown("#### Regional Drill-Down")
        
        # 2. Allow the user to select a specific region
        regions_list = df_regions['region'].unique()
        selected_region = st.selectbox("Select Region", regions_list, label_visibility="collapsed")
        
        # Extract row data for the selected region
        reg_data = df_regions[df_regions['region'] == selected_region].iloc[0]

        # --- DEFENSIVE SCHEMA INJECTION ---
        df_regional_flows = pd.DataFrame([
            {'src_pop': selected_region, 'dst_pop': 'LOCAL (Edge)', 'target': 'LOCAL (Edge)', 'value': reg_data.get('local_traffic', 0), 'egress_bytes': reg_data.get('local_traffic', 0), 'total_bytes': reg_data.get('local_traffic', 0)},
            {'src_pop': selected_region, 'dst_pop': 'INTRA (Fabric)', 'target': 'INTRA (Fabric)', 'value': reg_data.get('intra_traffic', 0), 'egress_bytes': reg_data.get('intra_traffic', 0), 'total_bytes': reg_data.get('intra_traffic', 0)},
            {'src_pop': selected_region, 'dst_pop': 'INTER (Backbone)', 'target': 'INTER (Backbone)', 'value': reg_data.get('inter_traffic', 0), 'egress_bytes': reg_data.get('inter_traffic', 0), 'total_bytes': reg_data.get('inter_traffic', 0)}
        ])

        # Plot regional donut
        fig_regional = plotter.create_single_donut(
            df_flows=df_regional_flows, 
            center_node=selected_region, 
            direction='egress', 
            height=400
        )
        st.plotly_chart(fig_regional, use_container_width=True)

    st.divider()

    # --- REGIONAL TABLE VIEW ---
    st.markdown("### 📋 Regional Inventory Ledger")
    
    # Create a display copy to avoid mutating the core state dataframe
    df_display = df_regions.copy()
    
    # Clean up lists for UI display
    if 'providers' in df_display:
        df_display['providers'] = df_display['providers'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        
    # Apply human-readable byte formatting
    for col in ['local_traffic', 'intra_traffic', 'inter_traffic', 'total_egress_traffic']:
        if col in df_display: 
            df_display[col] = df_display[col].apply(data_ctrl.format_bytes)
            
    # Convert decimal routing ratios to standard percentages
    for col in ['pct_local', 'pct_intra', 'pct_inter']:
        if col in df_display: 
            df_display[col] = (df_display[col] * 100)

    # Render the interactive dataframe
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "region": "Region", 
            "providers": "Providers", 
            "pop_count": st.column_config.NumberColumn("PoPs"),
            "router_count_total": st.column_config.NumberColumn("Total Routers"),
            "local_traffic": "Local Vol", 
            "intra_traffic": "Intra-PoP Vol", 
            "inter_traffic": "Inter-PoP Vol", 
            "total_egress_traffic": "Total Egress Vol",
            "pct_local": st.column_config.NumberColumn("Local %", format="%.2f%%"),
            "pct_intra": st.column_config.NumberColumn("Intra %", format="%.2f%%"),
            "pct_inter": st.column_config.NumberColumn("Inter %", format="%.2f%%"),
            # Hide granular router counts from the macro view
            "router_count_agw": None, 
            "router_count_ear": None, 
            "router_count_edge": None, 
            "router_count_other": None
        }
    )
if __name__ == "__main__":
    render_global_view()