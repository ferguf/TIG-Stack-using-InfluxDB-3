import streamlit as st
import pandas as pd
import numpy as np
import logging

# --- NDT CORE IMPORTS ---
from src.utils.api_network import get_network_links_detail
from src.galileo.galileo_templates import LAYOUT_REGISTRY
from src.galileo.plotly_galileo import render_geo_map, render_galileo_template

logger = logging.getLogger(__name__)

def render_map_explorer():
    """
    1:4:4 Geographic & Logical Backbone Dashboard.
    Uses LayoutRegistry for mode-aware template discovery.
    Adheres to the 100% API Rule by aggregating raw link telemetry.
    UPDATED: Global View now renders an interactive ledger of all Inter-Pop backbone links.
    """
    with st.spinner("Hydrating NDT Backbone..."):
        raw_links = get_network_links_detail()

    if not raw_links:
        st.warning("❌ No network data available from the API.")
        return

    df_links = pd.DataFrame(raw_links)

    # --- 1. AGGREGATE NODES (Coordinate Hunting) ---
    locations_dict = {}
    for _, row in df_links.iterrows():
        for prefix in ['a', 'b']:
            loc = row.get(f'{prefix}_device_location')
            
            if not loc or pd.isna(loc):
                continue
                
            if loc not in locations_dict:
                locations_dict[loc] = {
                    'location_name': loc,
                    'location_x': None,
                    'location_y': None,
                    'location_lat': None,  
                    'location_long': None, 
                    'devices_list': [],
                    'hub_health': 5
                }
            
            raw_lon = row.get(f'{prefix}_device_longitude')
            raw_lat = row.get(f'{prefix}_device_latitude')
            
            if pd.notna(raw_lon) and pd.notna(raw_lat):
                try:
                    lon, lat = float(raw_lon), float(raw_lat)
                    if locations_dict[loc]['location_lat'] is None:
                        locations_dict[loc]['location_x'] = lon
                        locations_dict[loc]['location_y'] = lat
                        locations_dict[loc]['location_long'] = lon
                        locations_dict[loc]['location_lat'] = lat
                except ValueError:
                    pass 

            dev_id = row.get(f'{prefix}_device_id')
            dev_health = int(row.get(f'{prefix}_device_health_status', 5))
            
            if not any(d.get('device_id') == dev_id for d in locations_dict[loc]['devices_list']):
                locations_dict[loc]['devices_list'].append({
                    'device_id': dev_id,
                    'device_name': row.get(f'{prefix}_device_name'),
                    'role': row.get(f'{prefix}_device_role'),
                    'health': dev_health
                })
                locations_dict[loc]['hub_health'] = min(locations_dict[loc]['hub_health'], dev_health)

    nodes = list(locations_dict.values())

    # --- 2. AGGREGATE LINKS (Unique Inter-Pop Spans) ---
    intercity_edges = {}
    for _, row in df_links.iterrows():
        loc_a = row.get('a_device_location')
        loc_b = row.get('b_device_location')
        
        if loc_a and loc_b and loc_a != loc_b:
            edge_tuple = tuple(sorted([loc_a, loc_b]))
            
            h_a = int(row.get('a_port_health_status', 5))
            h_b = int(row.get('b_port_health_status', 5))
            current_link_health = min(h_a, h_b)
            
            if edge_tuple not in intercity_edges:
                intercity_edges[edge_tuple] = {
                    'source': loc_a,
                    'target': loc_b,
                    'link_type': 'Inter-Pop',
                    'bundle_health': current_link_health
                }
            else:
                existing_health = intercity_edges[edge_tuple]['bundle_health']
                intercity_edges[edge_tuple]['bundle_health'] = min(existing_health, current_link_health)

    links_list = list(intercity_edges.values())

    if not nodes:
        st.warning("No location data found in the current topology.")
        return

    # --- 3. CONTAINERS (1:4:4) ---
    row1 = st.container() 
    row2 = st.container() 
    row3 = st.container() 

    with row1:
        st.subheader("🌐 Galileo: Regional Backbone")
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        
        with c1:
            intercity_templates = {name: meta for name, meta in LAYOUT_REGISTRY.items() if meta.get('mode') == 'INTERCITY'}
            tpl_options = list(intercity_templates.keys())
            default_idx = tpl_options.index("Geographic") if "Geographic" in tpl_options else 0
            
            selected_template = st.radio(
                "🗺️ Map View",
                options=tpl_options if tpl_options else ["Geographic"],
                index=default_idx if tpl_options else 0,
                horizontal=True
            )
            
        with c2:
            city_list = sorted([n['location_name'].upper() for n in nodes])
            selected_city = st.selectbox("📍 Hub Inspector", options=["GLOBAL VIEW"] + city_list)
        
        c3.metric("Regional Hubs", len(nodes))
        c4.metric("Backbone Spans", len(links_list))

    with row2:
        if selected_template == "Geographic":
            fig = render_geo_map(nodes, links_list, highlight_node=selected_city)
        else:
            fig = render_galileo_template(
                nodes, 
                links_list, 
                template_name=selected_template, 
                mode="INTERCITY"
            )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with row3:
        st.markdown("---")
        
        # Determine the subset of links to display based on Global vs Hub selection
        if selected_city == "GLOBAL VIEW":
            st.header("📊 Global Inter-Pop Topology")
            df_inter_pop = df_links[df_links['a_device_location'] != df_links['b_device_location']].copy()
            st.caption("Showing all backbone spans across the global fabric.")
            source_hdr, dest_hdr = "Source", "Destination"
        else:
            target = selected_city.upper()
            st.header(f"📊 Inter-Pop Topology: {target}")
            df_inter_pop = df_links[
                ((df_links['a_device_location'].str.upper() == target) & (df_links['b_device_location'].str.upper() != target)) |
                ((df_links['b_device_location'].str.upper() == target) & (df_links['a_device_location'].str.upper() != target))
            ].copy()
            source_hdr, dest_hdr = "Local", "Remote"

        if not df_inter_pop.empty:
            ledger_data = []
            for _, link in df_inter_pop.iterrows():
                # For Hub view, normalize Local/Remote sides
                if selected_city != "GLOBAL VIEW":
                    is_a_local = str(link['a_device_location']).upper() == target
                    loc_pfx, rem_pfx = ('a', 'b') if is_a_local else ('b', 'a')
                else:
                    # In Global view, use original A/B as Source/Destination
                    loc_pfx, rem_pfx = 'a', 'b'
                
                ledger_data.append({
                    "Link ID": link['link_id'],
                    f"{source_hdr} Hub": link.get(f'{loc_pfx}_device_location'),
                    f"{source_hdr} Device": link.get(f'{loc_pfx}_device_name'),
                    f"{source_hdr} Port": link.get(f'{loc_pfx}_port_name'),
                    "Direction": "⟷",
                    f"{dest_hdr} Hub": link.get(f'{rem_pfx}_device_location'),
                    f"{dest_hdr} Device": link.get(f'{rem_pfx}_device_name'),
                    f"{dest_hdr} Port": link.get(f'{rem_pfx}_port_name'),
                    "Health": link.get(f'{rem_pfx}_port_health_status')
                })
            
            # Use Destination Hub for sorting order
            df_ledger = pd.DataFrame(ledger_data).sort_values(by=f"{dest_hdr} Hub").reset_index(drop=True)
            
            st.caption("Select a row below to inspect real-time port telemetry.")
            
            selection_event = st.dataframe(
                df_ledger, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Link ID": None,
                    "Health": st.column_config.ProgressColumn("Health", min_value=0, max_value=5, format="%d")
                }
            )

            # --- TELEMETRY DRILL-DOWN ---
            selected_rows = selection_event.selection.rows
            if selected_rows:
                selected_idx = selected_rows[0]
                selected_link_data = df_ledger.iloc[selected_idx]
                
                # Dynamic labels for the chart title
                l_port = selected_link_data[f'{source_hdr} Port']
                r_port = selected_link_data[f'{dest_hdr} Port']
                
                st.markdown("---")
                st.subheader(f"📈 Telemetry: {l_port} ⟷ {r_port}")
                st.markdown(f"**UUID Tracking:** `{selected_link_data['Link ID']}`")
                
                # Mock Telemetry (Replace with InfluxDB logic)
                chart_data = pd.DataFrame(
                    np.random.randn(20, 2) * 200 + 1000, 
                    columns=['Ingress (Gbps)', 'Egress (Gbps)']
                )
                st.line_chart(chart_data, color=["#00d1ff", "#636EFA"])
        else:
            st.info(f"No active Inter-Pop backbone connections detected.")