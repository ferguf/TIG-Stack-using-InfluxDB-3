import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pages.network import net_3356_data as data_ctrl
from pages.network import traffic_3356_plotly_pop as plotter
import pages.network.traffic_3356_plotly_pop as nmap

# ==========================================
# --- 1. TOP 20 PERFORMANCE MODULE ---
# ==========================================

def render_router_view():
    """
    NDT Presentation Layer: Main controller for Router & Node Analytics.
    Orchestrates the Leaderboard and delegates the Inspection Tabs.
    """
    st.title("📟 Router & Node Analytics")

    # --- SCOPE SAFETY ---
    with st.spinner("Fetching Chassis Leaderboard..."):
        router_state = data_ctrl.router_traffic_leaderboard(limit=20)

    # Create the primary workspace tabs
    tab_leaderboard, tab_map, tab_details = st.tabs([
        "🏆 Top 20 Performance", 
        "🗺️ Top 20 MAP", 
        "🔍 Router - Router Flow Analysis"
    ])

    # --- TAB 1: TOP 20 PERFORMANCE ---
    with tab_leaderboard:
        render_top_20_performance(router_state)

    # --- TAB 2: TOP 20 MAP ---
    with tab_map:
        # Calls the map module (assumes nmap is imported)
        nmap.render_top_20_map(router_state)
        
    # --- TAB 3: ROUTER DETAILS DELEGATION ---
    with tab_details:
        # Calls the individual inspection module we built earlier
        render_individual_node_inspection(router_state)

def render_top_20_performance(router_state: dict):
    """
    NDT Presentation Layer: Renders the Top 20 Backbone Egress Leaders charts and ledger.
    """
    st.markdown("### Backbone Egress Leaders")
    
    if "df_routers" in router_state and not router_state["df_routers"].empty:
        # 1. Grab top 20 and sort ascending so the largest renders at the top of the Plotly chart
        df = router_state["df_routers"].head(20).copy()
        df = df.sort_values('router_egress_total_bytes', ascending=True)
        
        # 2. Extract the exact list of routers to force Plotly to sync the Y-axes
        ordered_routers = df['router'].tolist()

        col1, col2 = st.columns([2, 1])

        with col1:
            # --- Main Volume Chart ---
            fig_vol = px.bar(
                df, 
                x='router_egress_total_bytes', 
                y='router',
                orientation='h',
                title="Total Egress Volume by Chassis",
                color='router_egress_total_bytes',
                color_continuous_scale='Viridis',
                template="plotly_dark"
            )
            # 3. Apply the strict array sort order directly to the Y-axis
            fig_vol.update_yaxes(categoryorder='array', categoryarray=ordered_routers)
            fig_vol.update_layout(height=600)
            st.plotly_chart(fig_vol, use_container_width=True)

        with col2:
            # --- Composition Breakdown ---
            st.markdown("**Traffic Type %**")
            
            # SAFEGUARD: Compute missing percentages on the fly if the API dropped them
            required_cols = ['pct_local_of_router_egress', 'pct_intra_of_router_egress', 'pct_inter_of_router_egress']
            for col in required_cols:
                if col not in df.columns:
                    safe_total = df['router_egress_total_bytes'].replace(0, 1) # Prevent div/0
                    base_col = col.replace("pct_", "").replace("_of_router_egress", "_egress_bytes")
                    if base_col in df.columns:
                        df[col] = (df[base_col] / safe_total) * 100
                    else:
                        df[col] = 0.0 # Ultimate fallback

            # 4. Melt the FULL 20-router dataframe to match the left chart
            df_comp = df.melt(
                id_vars=['router'], 
                value_vars=required_cols,
                var_name='Type', 
                value_name='%'
            )
            
            df_comp['Type'] = df_comp['Type'].str.extract(r'pct_(.*)_of', expand=False)
            
            fig_comp = px.bar(
                df_comp, 
                x='%', 
                y='router', 
                color='Type',
                orientation='h', 
                barmode='stack',
                color_discrete_map={'local': '#00d1ff', 'intra': '#ffc107', 'inter': '#dc3545'},
                template="plotly_dark"
            )
            
            # 5. Apply the EXACT SAME strict array sort order to the right chart.
            # Re-enable showticklabels to display the router names on this graph as well.
            fig_comp.update_yaxes(
                categoryorder='array', 
                categoryarray=ordered_routers, 
                showticklabels=True, 
                title=""
            )
            fig_comp.update_layout(
                height=600,
                xaxis=dict(title=""),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        # Data Table Footer
        with st.expander("📋 View Leaderboard Ledger"):
            st.dataframe(df.sort_values('router_egress_total_bytes', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.error("Telemetry Unavailable: Check NDT API Connection.")

# ==========================================
# --- MAIN ORCHESTRATOR ---
# ==========================================

def TOP_20_routers(state: dict):
    """
    Handles the selection of a chassis from the Top 20 Performance List.
    """
    selected_node = None
    df_top = state.get("df_routers", pd.DataFrame())
    
    if df_top.empty:
        df_top = st.session_state.get("topo_df_routers", pd.DataFrame())
        
    if not df_top.empty and 'router' in df_top.columns:
        top_list = df_top['router'].tolist()
        selected_node = st.selectbox(
            f"Select from Top {len(top_list)} Nodes", 
            options=top_list,
            key="top_20_dropdown_active"
        )
    else:
        st.warning("⚠️ Leaderboard data unavailable. Please refresh the Regional Overview.")
        
    return selected_node

# ==========================================
# --- 2. TOPOLOGY DISCOVERY (MAP) MODULE ---
# ==========================================
def TOP_20_MAP(raw_regions: list):
    """
    Handles manual entry and regional topology drill-down (Region -> Type -> PoP -> Router).
    """
    selected_node = None
    manual_val = st.text_input("Direct Chassis Entry", placeholder="e.g., ear1.den1", key="manual_entry_field")
    st.divider()
    st.markdown("##### 🛠️ Topology Discovery")
    
    if raw_regions:
        # Region -> Type -> PoP -> Router
        reg_names = sorted([r.get('region') for r in raw_regions if r.get('region')])
        sel_region = st.radio("Region", options=reg_names, horizontal=True, key="disc_reg")

        region_payload = next((r for r in raw_regions if r.get('region') == sel_region), {})
        all_pops = [p for prov in region_payload.get('providers', []) for p in prov.get('pops', [])]
        
        found_types = sorted(list(set(r.get('router_type', '').upper() for p in all_pops for r in p.get('routers', []))))
        sel_type = st.radio("Type", options=found_types if found_types else ["UNKNOWN"], horizontal=True, key="disc_type")

        valid_pops = [p for p in all_pops if any(r.get('router_type', '').upper() == sel_type for r in p.get('routers', []))]
        pop_ids = sorted([p['pop'].upper() for p in valid_pops if 'pop' in p])
        
        if pop_ids:
            sel_pop_id = st.selectbox("PoP Location", options=pop_ids, key="disc_pop")
            target_pop = next((p for p in valid_pops if p.get('pop', '').upper() == sel_pop_id), {})
            router_list = sorted([r['router'] for r in target_pop.get('routers', []) if r.get('router_type', '').upper() == sel_type])
            discovery_node = st.selectbox("Target Chassis", options=router_list, key="disc_router_final")
            selected_node = manual_val.strip().lower() if manual_val.strip() else discovery_node

    return selected_node

# ==========================================
# --- 3. EXPLICIT DETAIL MODULE ---
# ==========================================

def Router_Router_details(selected_node: str, formatted_date: str):
    """
    Fetches and renders the individual node inspection data (Metrics, Sankey, Tables).
    Uses the globally selected date passed down from the orchestrator.
    """
    st.divider()
    
    with st.spinner(f"NDT: Querying Detail for {selected_node.upper()} on {formatted_date}..."):
        detail_res = data_ctrl.router_detail_summary(selected_node, report_date=formatted_date)
        
    if detail_res.get("success"):
        raw_payload = detail_res["raw"]
        
        # Handle list vs dict return from API
        if isinstance(raw_payload, list) and len(raw_payload) > 0:
            root_obj = raw_payload[0]
        else:
            root_obj = raw_payload
        
        # Extract the summary dictionary
        summary = root_obj.get("summary", {})

        # METRICS HEADER 
        m1, m2, m3, m4 = st.columns(4)
        
        # Safe string handling
        city = summary.get('city') or 'Unknown'
        state = summary.get('state') or ''
        loc_str = f"{city}, {state}".strip(", ").upper()
        m1.metric("Location", loc_str)
        
        pop = summary.get('pop') or 'Unknown'
        m2.metric("PoP ID", str(pop).upper())
        
        # Safe numeric formatting for Global Share
        g_share = summary.get('pct_router_egress_of_global')
        display_g_share = f"{g_share:.4f}%" if g_share is not None else "N/A"
        m3.metric("Global Share", display_g_share)
        
        # Safe numeric formatting & logic for Backbone Role
        inter_pct = summary.get('pct_inter_of_router_egress')
        if inter_pct is not None:
            role = "Core (Backbone)" if inter_pct > 50 else "Edge (Access)"
            help_text = f"Inter-AS: {inter_pct:.2f}%"
        else:
            role = "Unknown"
            help_text = "Inter-AS data unavailable"
            
        m4.metric("Backbone Role", role, help=help_text)
        
        st.divider()

        # FLOW VISUALIZATION (Sankey & Tables)
        egress = root_obj.get("egress_flows", [])
        ingress = root_obj.get("ingress_flows", [])
        
        if egress or ingress:
            st.markdown(f"### 🔀 Traffic Adjacency: `{summary.get('router', selected_node).upper()}`")
            combined = []
            
            # Extract flows and immediately tag null/empty peers as "UNKNOWN"
            for f in egress:
                peer = f.get('peer_router')
                peer_val = str(peer) if peer else "UNKNOWN"
                combined.append({'src_pop': selected_node, 'dst_pop': peer_val, 'total_bytes': f.get('flow_bytes', 0)})
                
            for f in ingress:
                peer = f.get('peer_router')
                peer_val = str(peer) if peer else "UNKNOWN"
                combined.append({'src_pop': peer_val, 'dst_pop': selected_node, 'total_bytes': f.get('flow_bytes', 0)})
            
            df_s = pd.DataFrame(combined)
            
            # ==========================================
            # --- ULTIMATE PLOTTER BULLETPROOFING ---
            # ==========================================
            # 1. Fill any straggling exact 'None' or NaN values
            df_s['src_pop'] = df_s['src_pop'].fillna("UNKNOWN")
            df_s['dst_pop'] = df_s['dst_pop'].fillna("UNKNOWN")
            
            # 2. Force the entire column to be string types (prevents .upper() crashes)
            df_s['src_pop'] = df_s['src_pop'].astype(str)
            df_s['dst_pop'] = df_s['dst_pop'].astype(str)
            
            # Now the plotter is safe to run
            st.plotly_chart(plotter.create_sankey_chart(df_s, selected_node, height=500), use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 📤 Top Egress")
                st.dataframe(pd.DataFrame(egress), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("#### 📥 Top Ingress")
                st.dataframe(pd.DataFrame(ingress), use_container_width=True, hide_index=True)
        else:
            st.info(f"Metadata for {selected_node} loaded. No flow adjacency available for {formatted_date}.")

        with st.expander("🛠️ API JSON Inspector"):
            st.json(root_obj)
    else:
        st.error(f"❌ Failed to resolve detail for: {selected_node} on {formatted_date}")

def render_individual_node_inspection(state: dict):
    """
    NDT Tab View: Individual Chassis Inspection.
    Ties together selection models and detail hydration with Date reactivity.
    """
    st.markdown("### 🔍 Individual Node Inspection")

    # --- 1. GLOBAL DATE CONTROL ---
    default_date = pd.to_datetime(st.session_state.get("selected_date", "2026-04-25"))
    selected_date = st.date_input(
        "📅 Topology Date", 
        value=default_date, 
        key="global_topo_date"
    )
    formatted_date = selected_date.strftime("%Y-%m-%d")

    # --- 2. TOPOLOGY & LEADERBOARD HYDRATION (DATE-REACTIVE) ---
    # Re-hydrate if the map doesn't exist OR if the date has changed
    if "topo_map" not in st.session_state or st.session_state.get("topo_map_date") != formatted_date:
        with st.spinner(f"NDT: Hydrating Global Topology Map for {formatted_date}..."):
            topo_res = data_ctrl.regional_detail_summary(report_date=formatted_date)
            
            st.session_state["topo_map"] = topo_res.get("raw", {}).get("regions", [])
            st.session_state["topo_df_routers"] = topo_res.get("df_routers", pd.DataFrame())
            st.session_state["topo_map_date"] = formatted_date # Save the timestamp
    
    raw_regions = st.session_state["topo_map"]

    # --- 3. SELECTION UI TOGGLE ---
    selection_mode = st.radio(
        "Navigation Mode",
        options=["Top 20 Performance List", "Discovery & Manual Entry"],
        horizontal=True,
        key="chassis_selection_mode"
    )

    selected_node = None

    # Determine selected node based on user's chosen mode
    if selection_mode == "Top 20 Performance List":
        selected_node = TOP_20_routers(state)
    else:
        # Renamed to match the definition below
        selected_node = render_discovery_controls(raw_regions)

    # --- 4. RENDER DETAILS IF NODE SELECTED ---
    if selected_node:
        # Ensure your Router_Router_details function is passing the formatted_date
        Router_Router_details(selected_node, formatted_date)
    
def render_discovery_controls(raw_regions: list, manual_val: str = ""):
    """
    NDT Discovery Component: Interactive UI to drill down from Region -> Role -> PoP -> Chassis.
    Features 'ALL' bypasses at both the Role and PoP levels to ensure 100% visibility.
    """
    selected_node = None
    
    # Optional: Allow user to type the name directly, skipping dropdowns
    manual_val = st.text_input("Direct Chassis Entry (Optional)", placeholder="e.g., ear1.den1", key="manual_entry_field")
    st.divider()
    
    if raw_regions:
        # ==========================================
        # --- 1. SCHEMA TRANSLATION HELPERS ---
        # ==========================================
        def get_reg_name(r_obj):
            return r_obj.get('region', r_obj.get('name', 'UNKNOWN'))
        
        def get_role(r_obj):
            return r_obj.get('role', r_obj.get('router_type', 'UNKNOWN')).upper()
        
        def get_router_name(r_obj):
            return r_obj.get('router', r_obj.get('name', 'UNKNOWN'))
        
        def get_pop_name(p_obj):
            return p_obj.get('pop', p_obj.get('short_name', p_obj.get('name', 'UNKNOWN'))).upper()

        # ==========================================
        # --- 2. REGION & ROLE DISCOVERY ---
        # ==========================================
        reg_names = sorted(list(set([get_reg_name(r) for r in raw_regions if get_reg_name(r) != 'UNKNOWN'])))
        sel_region = st.radio("Region", options=reg_names, horizontal=True, key="disc_reg")

        region_payload = next((r for r in raw_regions if get_reg_name(r) == sel_region), {})
        all_pops = [p for prov in region_payload.get('providers', []) for p in prov.get('pops', [])]
        
        found_types = sorted(list(set(get_role(r) for p in all_pops for r in p.get('routers', []) if get_role(r) != 'UNKNOWN')))
        type_options = ["ALL"] + found_types if found_types else ["ALL", "UNKNOWN"]
        sel_type = st.radio("Hardware Role", options=type_options, horizontal=True, key="disc_type")

        # ==========================================
        # --- 3. POP DISCOVERY (With ALL bypass) ---
        # ==========================================
        if sel_type == "ALL":
            valid_pops = all_pops
        else:
            valid_pops = [p for p in all_pops if any(get_role(r) == sel_type for r in p.get('routers', []))]
            
        pop_ids = sorted(list(set([get_pop_name(p) for p in valid_pops if get_pop_name(p) != 'UNKNOWN'])))
        
        # Inject "ALL" into the PoP selection
        pop_options = ["ALL"] + pop_ids if pop_ids else ["ALL"]
        sel_pop_id = st.selectbox("PoP Location", options=pop_options, key="disc_pop")
        
        # ==========================================
        # --- 4. CHASSIS DISCOVERY (Unfiltered Aggregation) ---
        # ==========================================
        router_list = []
        
        # If ALL PoPs are selected, we iterate through all valid PoPs.
        # Otherwise, we just grab the single selected PoP.
        if sel_pop_id == "ALL":
            target_pops = valid_pops
        else:
            target_pops = [p for p in valid_pops if get_pop_name(p) == sel_pop_id]
            
        for target_pop in target_pops:
            if sel_type == "ALL":
                r_list = [get_router_name(r) for r in target_pop.get('routers', []) if get_router_name(r) != 'UNKNOWN']
            else:
                r_list = [get_router_name(r) for r in target_pop.get('routers', []) if get_role(r) == sel_type and get_router_name(r) != 'UNKNOWN']
            
            router_list.extend(r_list)
            
        # Deduplicate and sort the final massive list
        router_list = sorted(list(set(router_list)))
        
        if router_list:
            discovery_node = st.selectbox(f"Target Chassis ({len(router_list)} found)", options=router_list, key="disc_router_final")
            selected_node = manual_val.strip().lower() if manual_val.strip() else discovery_node
        else:
            st.warning("No routing nodes found matching the current filters.")
            selected_node = None

    return selected_node