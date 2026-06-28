import streamlit as st
import logging
import pandas as pd
import numpy as np

# 1. NDT API Import (100% API Rule)
from src.utils.api_network import get_network_links_detail

# 2. Import rendering engines
from src.galileo.plotly_galileo import render_galileo_beck

logger = logging.getLogger(__name__)

def render_topology_view():
    """
    NDT Regional Backbone View (Formerly Intercity Explorer).
    Aggregates raw device telemetry from the FastAPI layer into regional hubs 
    and intercity backbone links for the Beck layout engine.
    """
    # --- 1. DATA ACQUISITION ---
    with st.spinner("Hydrating NDT Backbone..."):
        raw_links = get_network_links_detail()

    if not raw_links:
        st.error("❌ No topology data available from the API.")
        return

    df_links = pd.DataFrame(raw_links)

    # --- 2. AGGREGATE NODES (Cities/Hubs) ---
    locations_dict = {}
    for _, row in df_links.iterrows():
        for prefix in ['a', 'b']:
            loc = row.get(f'{prefix}_device_location')
            
            # Skip invalid or empty locations
            if not loc or pd.isna(loc):
                continue
                
            # Initialize the Hub if it doesn't exist
            if loc not in locations_dict:
                locations_dict[loc] = {
                    'location_name': loc,
                    'location_x': row.get(f'{prefix}_device_longitude', 0.0),
                    'location_y': row.get(f'{prefix}_device_latitude', 0.0),
                    'devices_list': []
                }
            
            # Append unique devices to the hub's inventory
            dev_id = row.get(f'{prefix}_device_id')
            if not any(d.get('device_id') == dev_id for d in locations_dict[loc]['devices_list']):
                locations_dict[loc]['devices_list'].append({
                    'device_id': dev_id,
                    'device_name': row.get(f'{prefix}_device_name'),
                    'role': row.get(f'{prefix}_device_role')
                })

    beck_nodes = list(locations_dict.values())

    # --- 3. AGGREGATE LINKS (Intercity Backbone) ---
    # Generate a unique list of edges connecting different geographical hubs
    intercity_links = []
    seen_edges = set()
    
    for _, row in df_links.iterrows():
        loc_a = row.get('a_device_location')
        loc_b = row.get('b_device_location')
        
        # Only track Inter-POP (backbone) links
        if loc_a and loc_b and loc_a != loc_b:
            edge_tuple = tuple(sorted([loc_a, loc_b]))
            if edge_tuple not in seen_edges:
                seen_edges.add(edge_tuple)
                intercity_links.append({
                    'source': loc_a,
                    'target': loc_b,
                    'link_type': 'Inter-Pop'
                })

    # Create a clean list of city names for the UI
    city_options = [n['location_name'].upper() for n in beck_nodes]
    city_options.sort()

    # --- ROW 1: CONTROLS & METRICS ---
    st.subheader("🌐 Galileo: Regional Backbone")
    
    col_ctrl, col_m1, col_m2 = st.columns([2, 1, 1])
    
    with col_ctrl:
        selected_city_name = st.selectbox(
            "Select Hub to Inspect:",
            options=["GLOBAL VIEW"] + city_options,
            index=0,
            help="Select a city to drill down into regional performance and inventory."
        )
        
    with col_m1:
        st.metric("Total Hubs", len(beck_nodes))
    with col_m2:
        st.metric("Backbone Edges", len(intercity_links))

    # --- ROW 2: THE MAP ---
    # Pass the aggregated data to the rendering engine
    fig = render_galileo_beck(
        nodes=beck_nodes, 
        links=intercity_links, 
        highlight_node=selected_city_name
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- ROW 3: HUB INTELLIGENCE ---
    st.markdown("---")
    
    if selected_city_name != "GLOBAL VIEW":
        target = selected_city_name.lower().strip()
        node_data = next((n for n in beck_nodes if n['location_name'].lower().strip() == target), None)

        if node_data:
            st.header(f"📊 Hub Intelligence: {selected_city_name}")
            
            perf_col, inv_col = st.columns([2, 1])
            with perf_col:
                device_ids = [d.get('device_id') for d in node_data.get('devices_list', [])]
                st.write("**Performance Context (UUIDs):**")
                st.code(device_ids, language="json")
                
                # Placeholder for real InfluxDB telemetry routing
                st.info(f"Monitoring {len(device_ids)} assets in {selected_city_name}")
                st.line_chart(pd.DataFrame(np.random.randn(20, 2), columns=['IN', 'OUT']))

            with inv_col:
                st.write("**Local Inventory:**")
                df_inv = pd.DataFrame(node_data.get("devices_list", []))
                if not df_inv.empty:
                    st.dataframe(df_inv[['device_name', 'role']], hide_index=True, use_container_width=True)
                else:
                    st.info("No active devices detected in this hub.")
    else:
        st.info("💡 **Global View Active:** Select a city from the dropdown above to view regional telemetry.")