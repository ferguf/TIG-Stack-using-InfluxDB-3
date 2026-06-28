import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Add your specific import for data_ctrl here. 
# It might look like one of these depending on your folder structure:
from pages.network import net_3356_data as data_ctrl
# ==========================================
# --- 1. SUMMARY MODULE ---
# ==========================================

def regional_Summary(state: dict, df_pops: pd.DataFrame):
    """
    Module 1: High-level Global & Regional Aggregation.
    Extracts the true totals directly from the API 'summary' block.
    """
    st.markdown("### 🌐 Global Fabric Executive Summary")
    
    raw_data = state.get("raw", {})
    regions_list = raw_data.get("regions", []) if isinstance(raw_data, dict) else raw_data
    has_new_schema = isinstance(regions_list, list) and any("summary" in r for r in regions_list)
    
    regional_stats = []
    global_volume = df_pops['total_volume_bytes'].sum() if not df_pops.empty else 0
    total_true_pops = 0
    total_true_routers = 0

    if has_new_schema:
        for r_data in regions_list:
            region_name = r_data.get("region", "UNKNOWN")
            summary = r_data.get("summary", {})
            
            true_pop_count = summary.get("pop_count", 0)
            networks = summary.get("networks", [])
            
            role_counts = {}
            net_counts = {}
            true_router_count = 0
            
            for net in networks:
                net_name = net.get("network", net.get("name", "UNKNOWN"))
                roles = net.get("roles", [])
                net_total = 0
                
                for role_obj in roles:
                    role_name = role_obj.get("role", "UNKNOWN")
                    count = role_obj.get("count", 0)
                    role_counts[role_name] = role_counts.get(role_name, 0) + count
                    net_total += count
                    true_router_count += count
                    
                net_counts[net_name] = net_counts.get(net_name, 0) + net_total
            
            total_true_pops += true_pop_count
            total_true_routers += true_router_count

            df_reg = df_pops[df_pops['region'] == region_name] if not df_pops.empty else pd.DataFrame()
            reg_volume = df_reg['total_volume_bytes'].sum() if not df_reg.empty else 0
            reg_pct = (reg_volume / global_volume * 100) if global_volume > 0 else 0.0

            role_str = " | ".join([f"{k}: {v}" for k, v in sorted(role_counts.items())])
            net_str = " | ".join([f"{k}: {v}" for k, v in sorted(net_counts.items())])
            
            regional_stats.append({
                'Region': region_name,
                'PoPs': true_pop_count,
                'Routers': true_router_count,
                'Role Breakdown': role_str if role_str else "N/A",
                'Network Breakdown': net_str if net_str else "N/A",
                'Traffic Volume': data_ctrl.format_bytes(reg_volume),
                'Global Share': reg_pct,
                '_raw_vol': reg_volume 
            })
    else:
        # Legacy Fallback
        total_true_pops = len(df_pops)
        total_true_routers = df_pops['router_count'].sum() if 'router_count' in df_pops.columns else 0
        
        for region in df_pops['region'].unique():
            df_reg = df_pops[df_pops['region'] == region]
            reg_pops = len(df_reg)
            reg_routers = df_reg['router_count'].sum()
            reg_volume = df_reg['total_volume_bytes'].sum()
            reg_pct = (reg_volume / global_volume * 100) if global_volume > 0 else 0.0
            
            role_counts = {}
            net_counts = {}
            
            for _, row in df_reg.iterrows():
                routers = row.get('routers', [])
                pop_nets = row.get('networks', [])
                has_router_level_network = False
                
                if isinstance(routers, list):
                    for r in routers:
                        role = r.get('role', r.get('router_type', 'UNKNOWN'))
                        role_counts[role] = role_counts.get(role, 0) + 1
                        if 'network' in r:
                            has_router_level_network = True
                            net = r['network']
                            net_counts[net] = net_counts.get(net, 0) + 1
                
                if not has_router_level_network and isinstance(pop_nets, list):
                    for net in pop_nets:
                        net_name = net.get('network', net.get('name', 'UNKNOWN'))
                        net_router_count = sum(role_obj.get('count', 0) for role_obj in net.get('roles', []))
                        if net_router_count == 0 and len(pop_nets) == 1:
                            net_router_count = len(routers)
                        net_counts[net_name] = net_counts.get(net_name, 0) + net_router_count

            role_str = " | ".join([f"{k}: {v}" for k, v in sorted(role_counts.items())])
            net_str = " | ".join([f"{k}: {v}" for k, v in sorted(net_counts.items())])
            
            regional_stats.append({
                'Region': region,
                'PoPs': reg_pops,
                'Routers': reg_routers,
                'Role Breakdown': role_str if role_str else "N/A",
                'Network Breakdown': net_str if net_str else "N/A",
                'Traffic Volume': data_ctrl.format_bytes(reg_volume),
                'Global Share': reg_pct,
                '_raw_vol': reg_volume 
            })

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Regions", len(regional_stats))
    m2.metric("Total Online PoPs", total_true_pops)
    m3.metric("Total Routing Nodes", total_true_routers)
    m4.metric("Global Fabric Traffic", data_ctrl.format_bytes(global_volume))
        
    df_summary = pd.DataFrame(regional_stats)
    if not df_summary.empty:
        df_summary = df_summary.sort_values('_raw_vol', ascending=False).drop(columns=['_raw_vol'])
    else:
        df_summary = pd.DataFrame(columns=["Region", "PoPs", "Routers", "Role Breakdown", "Network Breakdown", "Traffic Volume", "Global Share"])

    st.dataframe(
        df_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Region": st.column_config.TextColumn("Region"),
            "PoPs": st.column_config.NumberColumn("PoPs", format="%d 🏢"),
            "Routers": st.column_config.NumberColumn("Routers", format="%d 🖥️"),
            "Role Breakdown": st.column_config.TextColumn("Router Roles"),
            "Network Breakdown": st.column_config.TextColumn("Networks"),
            "Traffic Volume": st.column_config.TextColumn("Traffic Volume"),
            "Global Share": st.column_config.ProgressColumn("Global Traffic Share (%)", format="%.2f%%", min_value=0, max_value=100)
        }
    )
    st.divider()

# ==========================================
# --- 2. TABLE MODULE ---
# ==========================================
def regional_table(df_pops: pd.DataFrame, scope: str = "Global"):
    """
    Module 2: Master PoP Ledger and dynamic Hardware Inventory drill-down.
    Updated: Title dynamically reflects the active filter scope.
    """
    import streamlit as st
    import pandas as pd
    
    st.markdown(f"### 📍 Active PoP Ledger: `{scope}`")
    st.caption("Complete site inventory. Select a row to inspect local chassis hardware.")
    
    df_display = df_pops[['region', 'pop_id', 'city', 'router_count', 'formatted_volume', 'total_volume_bytes']].copy()
    
    safe_max_traffic = max(1, int(df_display['total_volume_bytes'].max())) if not df_display.empty else 1
    safe_max_routers = max(1, int(df_display['router_count'].max())) if not df_display.empty else 1

    selection_event = st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row",
        column_config={
            "region": "Region",
            "pop_id": st.column_config.TextColumn("PoP ID"),
            "city": "City",
            "router_count": st.column_config.ProgressColumn("Chassis", format="%d 🖥️", min_value=0, max_value=safe_max_routers),
            "formatted_volume": "Total Volume",
            "total_volume_bytes": st.column_config.ProgressColumn("Capacity Utilization", format=" ", min_value=0, max_value=safe_max_traffic)
        }
    )

    if selection_event.selection.rows:
        selected_idx = selection_event.selection.rows[0]
        selected_pop = df_pops.iloc[selected_idx]
        
        with st.container(border=True):
            st.markdown(f"### 🛰️ Hardware Inventory: `{selected_pop['pop_id'].upper()}`")
            
            routers = selected_pop.get('routers', [])
            if routers:
                df_routers = pd.DataFrame(routers)
                
                if 'role' not in df_routers.columns:
                    df_routers['role'] = df_routers.get('router_type', 'UNKNOWN')
                
                if 'network' not in df_routers.columns:
                    pop_nets = selected_pop.get('networks', [])
                    net_str = ", ".join([n.get('network', n.get('name', 'UNKNOWN')) for n in pop_nets]) if pop_nets else "UNKNOWN"
                    df_routers['network'] = net_str

                if 'sum_Gbytes' in df_routers.columns:
                    df_routers['sum_Gbytes'] = pd.to_numeric(df_routers['sum_Gbytes'], errors='coerce').fillna(0)
                    df_routers['calc_bytes'] = df_routers['sum_Gbytes'] * (1024**3)
                elif 'sum_bytes' in df_routers.columns:
                    df_routers['sum_bytes'] = pd.to_numeric(df_routers['sum_bytes'], errors='coerce').fillna(0)
                    df_routers['calc_bytes'] = df_routers['sum_bytes']
                else:
                    df_routers['calc_bytes'] = 0.0
                
                df_routers['Volume'] = df_routers['calc_bytes'].apply(data_ctrl.format_bytes)
                safe_router_max = max(1, int(df_routers['calc_bytes'].max()))

                display_cols = ['router', 'role', 'network', 'calc_bytes', 'Volume']
                df_routers = df_routers[[c for c in display_cols if c in df_routers.columns]]

                st.dataframe(
                    df_routers, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "router": st.column_config.TextColumn("Router Hostname"),
                        "role": st.column_config.TextColumn("Logical Role"),
                        "network": st.column_config.TextColumn("Network ID"),
                        "calc_bytes": st.column_config.BarChartColumn("Traffic Distribution", y_min=0, y_max=safe_router_max),
                        "Volume": st.column_config.TextColumn("Volume")
                    }
                )
            else:
                st.info("No routing hardware telemetry available for this specific PoP.")
    else:
        st.info("💡 **Awaiting site selection.** Click a PoP in the ledger above.")

def region_graphs(df_pops: pd.DataFrame) -> str:
    """
    NDT Presentation Component: Macro Traffic Analytics using Plotly.
    Interactive Regional Drill-Down to analyze site-level throughput.
    Updated: Returns the selected scope to act as a universal filter.
    """
    import streamlit as st
    import plotly.graph_objects as go

    st.divider()
    st.markdown("### 📊 Traffic Analytics & Site Rankings")
    
    try:
        if df_pops.empty:
            st.warning("⚠️ Cannot render graphs: df_pops is completely empty.")
            return "Global"
        elif df_pops['total_volume_bytes'].sum() == 0:
            st.info("📊 Not enough traffic data to generate analytics graphs.")
            return "Global"

        # --- INTERACTIVE SCOPE SELECTOR ---
        # Get unique regions, sort them, and prepend "Global"
        available_regions = sorted(df_pops['region'].dropna().unique().tolist())
        scope_options = ["Global"] + available_regions
        
        selected_scope = st.radio(
            "🌍 **Select Analytics Scope:**", 
            options=scope_options, 
            horizontal=True
        )

        # Apply the filter based on the selection
        if selected_scope == "Global":
            df_plot = df_pops.copy()
            bar_title = "🏆 Top 10 PoPs (Global)"
        else:
            df_plot = df_pops[df_pops['region'] == selected_scope].copy()
            bar_title = f"🏆 Top 10 PoPs ({selected_scope})"

        c1, c2 = st.columns(2)
        
        # --- Chart 1: Dynamic Top 10 Bar Chart ---
        with c1:
            with st.container(border=True):
                st.markdown(f"#### {bar_title}")
                
                # Sort, grab top 10, then reverse for bottom-up rendering in Plotly
                df_top_pops = df_plot.sort_values('total_volume_bytes', ascending=False).head(10)
                df_top_pops = df_top_pops.sort_values('total_volume_bytes', ascending=True)
                
                fig_bar = go.Figure(go.Bar(
                    x=df_top_pops['total_volume_bytes'],
                    y=df_top_pops['pop_id'].str.upper(),
                    orientation='h',
                    marker_color='rgba(0, 209, 255, 0.85)', # NDT Cyan
                    text=df_top_pops['formatted_volume'],
                    textposition='inside',
                    insidetextanchor='middle',
                    hovertemplate="<b>%{y}</b><br>Volume: %{text}<extra></extra>"
                ))
                
                fig_bar.update_layout(
                    height=400,
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # --- Chart 2: Dynamic Distribution Pie Chart ---
        with c2:
            with st.container(border=True):
                if selected_scope == "Global":
                    st.markdown("#### 🌍 Global Regional Distribution")
                    df_pie = df_plot.groupby('region')['total_volume_bytes'].sum().reset_index()
                    pie_labels = df_pie['region']
                    pie_values = df_pie['total_volume_bytes']
                else:
                    st.markdown(f"#### 🏢 {selected_scope} Internal Site Share")
                    # Show the share of the top sites within the selected region
                    df_pie = df_plot.sort_values('total_volume_bytes', ascending=False)
                    
                    # If a region has tons of PoPs (like NA), group the tail into "Other"
                    if len(df_pie) > 10:
                        top9 = df_pie.iloc[:9].copy()
                        other_vol = df_pie.iloc[9:]['total_volume_bytes'].sum()
                        other_df = pd.DataFrame([{'pop_id': 'OTHER SITES', 'total_volume_bytes': other_vol}])
                        df_pie = pd.concat([top9, other_df])
                        
                    pie_labels = df_pie['pop_id'].str.upper()
                    pie_values = df_pie['total_volume_bytes']
                
                # Extended NDT color palette
                pie_colors = ['#29B6F6', '#66BB6A', '#FFA726', '#FFEE58', '#EF5350', '#AB47BC', '#EC407A', '#8D6E63', '#78909C', '#BDBDBD']
                
                fig_pie = go.Figure(go.Pie(
                    labels=pie_labels,
                    values=pie_values,
                    hole=0.5,
                    marker=dict(colors=pie_colors, line=dict(color='#0e1117', width=2)),
                    textinfo='label+percent',
                    hovertemplate="<b>%{label}</b><br>Share: %{percent}<extra></extra>"
                ))
                
                fig_pie.update_layout(
                    height=400,
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
        return selected_scope

    except Exception as e:
        st.error(f"🛑 Graph Rendering Error: {e}")
        return "Global"

def render_regional_view():
    """
    Main Entry Point: Fetches data, enhances it, and renders the 3 child modules.
    Updated: Bridges the interactive graph selection into the table filter.
    """
    import streamlit as st
    import pandas as pd
    
    st.title("🗺️ Regional Topology & PoP Details")
    st.markdown("Inspect Point of Presence (PoP) density and aggregate traffic volumes across the complete global fabric.")

    # --- API CONTROLS ---
    with st.container(border=True):
        selected_date = st.date_input("📅 Report Date", value=pd.to_datetime("2026-04-23"))

    # --- DATA ACQUISITION ---
    with st.spinner("NDT: Hydrating Complete Regional Topology..."):
        state = data_ctrl.regional_detail_summary(report_date=selected_date.strftime("%Y-%m-%d"))

    if "error" in state:
        st.error(f"⚠️ {state['error']}")
        return

    df_pops = state.get("df_pops", pd.DataFrame())
    if df_pops.empty:
        st.warning("No PoP data found for the selected date.")
        return

    # --- DATA ENHANCEMENT ---
    def get_hybrid_pop_volume(row):
        traffic_obj = row.get('traffic', {})
        if isinstance(traffic_obj, dict) and 'sum_Gbytes' in traffic_obj:
            return float(traffic_obj.get('sum_Gbytes', 0)) * (1024**3)
        
        routers = row.get('routers', [])
        total_bytes = 0.0
        if isinstance(routers, list):
            for r in routers:
                if 'sum_Gbytes' in r:
                    total_bytes += float(r.get('sum_Gbytes', 0)) * (1024**3)
                elif 'sum_bytes' in r:
                    total_bytes += float(r.get('sum_bytes', 0))
        return total_bytes

    df_pops['total_volume_bytes'] = df_pops.apply(get_hybrid_pop_volume, axis=1)
    df_pops['formatted_volume'] = df_pops['total_volume_bytes'].apply(data_ctrl.format_bytes)
    df_pops['router_count'] = df_pops['routers'].apply(lambda x: len(x) if isinstance(x, list) else 0)

    # --- RENDER MODULES ---
    regional_Summary(state, df_pops)
    
    # Capture the radio button selection from the graph module
    active_scope = region_graphs(df_pops)
    
    # Filter the dataframe before handing it to the table
    if active_scope and active_scope != "Global":
        df_pops_filtered = df_pops[df_pops['region'] == active_scope].copy()
    else:
        df_pops_filtered = df_pops.copy()
        
    regional_table(df_pops_filtered, scope=active_scope)