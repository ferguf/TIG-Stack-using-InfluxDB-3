import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
import base64

# --- INTERNAL MODULE IMPORTS ---
from src.galileo.plotly_galileo import render_geo_map, render_3_color_segment_link, render_nodes_standard
from src.galileo.galileo_templates import LAYOUT_REGISTRY

# --- GALILEO SDK TAXONOMY ---
from src.galileo.galileo_taxonomy import extract_role, ICON_MAP

# ==========================================
# 1. GALILEO DATA ADAPTERS & NDT HELPERS
# ==========================================

def calculate_map_extent(nodes: list) -> dict:
    if not nodes:
        return {"n": 0, "s": 0, "e": 0, "w": 0, "center_lat": 0, "center_lon": 0}
        
    lats = [n.get('lat', 0.0) for n in nodes]
    lons = [n.get('lon', 0.0) for n in nodes]
    
    n, s = max(lats), min(lats)
    e, w = max(lons), min(lons)
    
    return {
        "n": n, "s": s, "e": e, "w": w,
        "center_lat": (n + s) / 2,
        "center_lon": (e + w) / 2,
        "lat_delta": (n - s) + 2, 
        "lon_delta": (e - w) + 2
    }

def get_health_color(status: int) -> str:
    health_map = {
        5: '#28a745', 4: '#00d1ff', 3: '#ffc107', 
        2: '#fd7e14', 1: '#dc3545', 0: '#6c757d'
    }
    try:
        return health_map.get(int(status), '#6c757d')
    except (ValueError, TypeError):
        return '#6c757d'

def extract_pop_from_hostname(hostname: str) -> str:
    h = str(hostname).strip().upper()
    if '.' in h:
        parts = h.split('.')
        if len(parts) > 1: return re.sub(r'\d+$', '', parts[1])
    if '-' in h:
        return re.sub(r'\d+$', '', h.split('-')[0])
    return h

def parse_device_role(row: pd.Series, side_prefix: str) -> str:
    role_val = row.get(f"{side_prefix}_device_role")
    if pd.isna(role_val) or str(role_val).strip() == "":
        hostname = str(row.get(f"{side_prefix}_device_name", "")).upper()
        # Fallback to the centralized taxonomy parser if the DB lacks a role
        return extract_role(hostname)
    return str(role_val).upper()

def parse_speed_to_gbps(raw_speed) -> float:
    if pd.isna(raw_speed) or str(raw_speed).strip() == "":
        return 0.0
        
    speed_str = str(raw_speed).strip().upper()
    try:
        num_part = ''.join(c for c in speed_str if c.isdigit() or c == '.')
        if not num_part: return 0.0
        val = float(num_part)
        
        if 'T' in speed_str: return val * 1000.0
        elif 'G' in speed_str: return val
        elif 'M' in speed_str: return val / 1000.0
        else: return val / 1_000_000.0
    except Exception:
        return 0.0

def format_capacity_label(cap_gbps: float) -> str:
    if cap_gbps >= 1000:
        return f"{cap_gbps / 1000:.1f} Tbps"
    return f"{cap_gbps:.0f} Gbps"

def get_worst_status(status_list: list) -> int:
    if not status_list:
        return 4 
    severity_weights = {3: 50, 2: 40, 1: 30, 0: 20, 4: 10}
    return max(status_list, key=lambda k: severity_weights.get(k, 10))

def adapt_api_to_galileo(df_links: pd.DataFrame, mode: str = "backbone"):
    import pandas as pd
    
    if df_links is None or (isinstance(df_links, pd.DataFrame) and df_links.empty):
        return [], []

    nodes_dict = {}
    galileo_links = []
    mode = str(mode).strip().lower()

    # ==========================================
    # MACRO/BACKBONE MODE (PoP Aggregation)
    # ==========================================
    if mode == "backbone":
        link_agg = {}
        
        for _, row in df_links.iterrows():
            name_a = str(row.get("a_device_name", "")).upper()
            loc_a = extract_pop_from_hostname(name_a)
            a_dev_status = 4 if pd.isna(row.get("a_device_health_status")) else int(row.get("a_device_health_status"))
            a_port_status = 4 if pd.isna(row.get("a_port_health_status")) else int(row.get("a_port_health_status"))

            name_b = str(row.get("b_device_name", "")).upper()
            loc_b = extract_pop_from_hostname(name_b)
            b_dev_status = 4 if pd.isna(row.get("b_device_health_status")) else int(row.get("b_device_health_status"))
            b_port_status = 4 if pd.isna(row.get("b_port_health_status")) else int(row.get("b_port_health_status"))

            link_status = 4 if pd.isna(row.get("link_health_status")) else int(row.get("link_health_status"))

            if loc_a:
                if loc_a not in nodes_dict:
                    lat_a = row.get("a_device_latitude", 0.0)
                    lon_a = row.get("a_device_longitude", 0.0)
                    nodes_dict[loc_a] = {
                        "location_name": loc_a,
                        "lat": 0.0 if pd.isna(lat_a) else float(lat_a),
                        "lon": 0.0 if pd.isna(lon_a) else float(lon_a),
                        "_dev_healths": [],
                        "_port_link_healths": []
                    }
                nodes_dict[loc_a]["_dev_healths"].append(a_dev_status)
                nodes_dict[loc_a]["_port_link_healths"].extend([a_port_status, link_status])

            if loc_b:
                if loc_b not in nodes_dict:
                    lat_b = row.get("b_device_latitude", 0.0)
                    lon_b = row.get("b_device_longitude", 0.0)
                    nodes_dict[loc_b] = {
                        "location_name": loc_b,
                        "lat": 0.0 if pd.isna(lat_b) else float(lat_b),
                        "lon": 0.0 if pd.isna(lon_b) else float(lon_b),
                        "_dev_healths": [],
                        "_port_link_healths": []
                    }
                nodes_dict[loc_b]["_dev_healths"].append(b_dev_status)
                nodes_dict[loc_b]["_port_link_healths"].extend([b_port_status, link_status])

            if loc_a and loc_b and loc_a != loc_b:
                port_a = str(row.get("a_port_name", "Unknown"))
                port_b = str(row.get("b_port_name", "Unknown"))
                cap = parse_speed_to_gbps(row.get("a_port_speed", row.get("speed", 0)))
                hover_label = f"{name_a}::{port_a} ↔ {name_b}::{port_b} | {format_capacity_label(cap)}"

                pair_key = tuple(sorted([loc_a, loc_b]))
                
                if pair_key not in link_agg:
                    link_agg[pair_key] = {
                        "source": pair_key[0], 
                        "target": pair_key[1], 
                        "capacity_gbps": 0.0,
                        "_source_ports": [],
                        "_target_ports": [],
                        "_links": [],
                        "hover_texts": []
                    }

                if loc_a == pair_key[0]:
                    link_agg[pair_key]["_source_ports"].append(a_port_status)
                    link_agg[pair_key]["_target_ports"].append(b_port_status)
                else:
                    link_agg[pair_key]["_source_ports"].append(b_port_status)
                    link_agg[pair_key]["_target_ports"].append(a_port_status)
                    
                link_agg[pair_key]["_links"].append(link_status)
                link_agg[pair_key]["capacity_gbps"] += cap
                link_agg[pair_key]["hover_texts"].append(hover_label)

        for loc, data in nodes_dict.items():
            data["colors"] = [get_worst_status(data["_dev_healths"]), get_worst_status(data["_port_link_healths"])]
            del data["_dev_healths"]
            del data["_port_link_healths"]

        for pair_key, data in link_agg.items():
            galileo_links.append({
                "source": data["source"],
                "target": data["target"],
                "capacity_gbps": data["capacity_gbps"],
                "colors": [get_worst_status(data["_source_ports"]), get_worst_status(data["_links"]), get_worst_status(data["_target_ports"])],
                "hover_text": "<br>".join(data["hover_texts"])
            })

        return list(nodes_dict.values()), galileo_links

    # ==========================================
    # MICRO/ORBITAL MODE (Device Granularity)
    # ==========================================
    link_agg = {}
    
    for _, row in df_links.iterrows():
        name_a = str(row.get("a_device_name", "")).upper()
        id_a = name_a.lower()
        role_a = str(row.get("a_device_role", "UNKNOWN")).upper()
        a_dev_status = 4 if pd.isna(row.get("a_device_health_status")) else int(row.get("a_device_health_status"))
        a_port_status = 4 if pd.isna(row.get("a_port_health_status")) else int(row.get("a_port_health_status"))

        if id_a:
            if id_a not in nodes_dict:
                nodes_dict[id_a] = {
                    "id": id_a, 
                    "label_header": name_a, 
                    "device_role": role_a,
                    "_dev_healths": [], 
                    "_port_healths": []
                }
            nodes_dict[id_a]["_dev_healths"].append(a_dev_status)
            nodes_dict[id_a]["_port_healths"].append(a_port_status)

        name_b = str(row.get("b_device_name", "")).upper()
        id_b = name_b.lower()
        role_b = str(row.get("b_device_role", "UNKNOWN")).upper()
        b_dev_status = 4 if pd.isna(row.get("b_device_health_status")) else int(row.get("b_device_health_status"))
        b_port_status = 4 if pd.isna(row.get("b_port_health_status")) else int(row.get("b_port_health_status"))

        if id_b:
            if id_b not in nodes_dict:
                nodes_dict[id_b] = {
                    "id": id_b, 
                    "label_header": name_b, 
                    "device_role": role_b,
                    "_dev_healths": [], 
                    "_port_healths": []
                }
            nodes_dict[id_b]["_dev_healths"].append(b_dev_status)
            nodes_dict[id_b]["_port_healths"].append(b_port_status)

        link_status = 4 if pd.isna(row.get("link_health_status")) else int(row.get("link_health_status"))
        cap = parse_speed_to_gbps(row.get("a_port_speed", row.get("speed", 0)))
        port_a = str(row.get("a_port_name", "Unknown"))
        port_b = str(row.get("b_port_name", "Unknown"))
        hover_label = f"{name_a}::{port_a} ↔ {name_b}::{port_b} | {format_capacity_label(cap)}"

        if id_a and id_b and id_a != id_b:
            pair_key = tuple(sorted([id_a, id_b]))
            
            if pair_key not in link_agg:
                link_agg[pair_key] = {
                    "source": pair_key[0], 
                    "target": pair_key[1], 
                    "capacity_gbps": 0.0, 
                    "_source_ports": [], 
                    "_target_ports": [], 
                    "_links": [], 
                    "hover_texts": []
                }

            if id_a == pair_key[0]:
                link_agg[pair_key]["_source_ports"].append(a_port_status)
                link_agg[pair_key]["_target_ports"].append(b_port_status)
            else:
                link_agg[pair_key]["_source_ports"].append(b_port_status)
                link_agg[pair_key]["_target_ports"].append(a_port_status)
                
            link_agg[pair_key]["_links"].append(link_status)
            link_agg[pair_key]["capacity_gbps"] += cap
            link_agg[pair_key]["hover_texts"].append(hover_label)

    for nid, data in nodes_dict.items():
        data["colors"] = [get_worst_status(data["_dev_healths"]), get_worst_status(data["_port_healths"])]
        del data["_dev_healths"]
        del data["_port_healths"]

    for pair_key, data in link_agg.items():
        galileo_links.append({
            "source": data["source"], 
            "target": data["target"], 
            "capacity_gbps": data["capacity_gbps"],
            "colors": [get_worst_status(data["_source_ports"]), get_worst_status(data["_links"]), get_worst_status(data["_target_ports"])],
            "hover_text": "<br>".join(data["hover_texts"])
        })

    return list(nodes_dict.values()), galileo_links

# ==========================================
# 2. PURE GEO-MAPPING COMPONENT (BACKBONE)
# ==========================================

def render_global_backbone_map(nodes: list, links: list, title: str = "Inter-Pop Backbone Topology"):
    c1, c2 = st.columns([5, 1])
    c1.markdown(f"#### 🌍 {title}")
    c1.caption("Displays geographical connectivity powered by the Galileo mapping engine.")
    
    if not nodes or not links:
        st.info("🗺️ No backbone topology data available to map.")
        return

    with st.spinner("Rendering Galileo Geo-Map..."):
        try:
            fig = render_geo_map(nodes=nodes, links=links)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to render Galileo Geo-Map: {e}")

# ==========================================
# 3. PURE ORBITAL COMPONENT (REGIONAL POP)
# ==========================================

def get_link_width(capacity_gbps) -> float:
    import pandas as pd
    try:
        if pd.isna(capacity_gbps): return 1.0
        cap = float(capacity_gbps)
        if cap <= 10.0: return 1.0
        elif cap <= 100.0: return 2.5
        else: return 4.5
    except Exception:
        return 1.0

def render_orbital_pop_map(nodes_payload: dict, links_payload: list, selected_template: str, title: str = "Orbital PoP Architecture"):
    st.markdown(f"#### 🏢 {title}")

    if not nodes_payload:
        st.info("🗺️ No localized node data available to map.")
        return

    # ==========================================
    # 🌍 UNIVERSAL GEO-FILTER PIPELINE
    # ==========================================
    pop_counts = {}
    for attrs in nodes_payload.values():
        p = extract_pop_from_hostname(attrs.get("label_header", ""))
        if p: pop_counts[p] = pop_counts.get(p, 0) + 1
    current_pop_base = max(pop_counts, key=pop_counts.get) if pop_counts else "UNKNOWN"

    remote_pops = set()
    for attrs in nodes_payload.values():
        p = extract_pop_from_hostname(attrs.get("label_header", ""))
        if p and p != current_pop_base:
            remote_pops.add(p)
    remote_pops = sorted(list(remote_pops))

    if remote_pops:
        with st.expander("🌍 Universal Viewport Filter: Connected Facilities", expanded=False):
            selected_remote_pops = st.multiselect(
                "Show/Hide Remote Cities:",
                options=remote_pops,
                default=remote_pops,
                help="Dynamically removes remote PoPs from the viewport before the layout engine runs."
            )

        if len(selected_remote_pops) < len(remote_pops):
            filtered_nodes = {}
            for nid, attrs in nodes_payload.items():
                p = extract_pop_from_hostname(attrs.get("label_header", ""))
                if p == current_pop_base or p in selected_remote_pops:
                    filtered_nodes[nid] = attrs

            valid_node_keys = {str(k).lower() for k in filtered_nodes.keys()}
            filtered_links = []
            for link in links_payload:
                if str(link.get("source", "")).lower() in valid_node_keys and \
                   str(link.get("target", "")).lower() in valid_node_keys:
                    filtered_links.append(link)

            nodes_payload = filtered_nodes
            links_payload = filtered_links

    with st.spinner(f"Mapping architecture via {selected_template}..."):
        try:
            layout_meta = LAYOUT_REGISTRY.get(selected_template)
            if not layout_meta:
                st.error(f"Galileo Engine Error: Template '{selected_template}' not found in registry.")
                return

            pos_cache = layout_meta["func"](nodes_payload)
            pos_cache.pop("_debug", None)

            fig_pop = go.Figure()

            # ==========================================
            # RENDER LINKS
            # ==========================================
            for link in links_payload:
                source_key = str(link.get("source", "")).lower()
                target_key = str(link.get("target", "")).lower()

                if source_key in pos_cache and target_key in pos_cache:
                    p1 = pos_cache[source_key]
                    p2 = pos_cache[target_key]
                    
                    link_colors = link.get("colors", [4, 4, 4])
                    hover_text = link.get("hover_text", "")

                    render_3_color_segment_link(
                        fig_pop, p1, p2,
                        colors=link_colors,
                        is_active=True,
                        link_text=hover_text
                    )

            # ==========================================
            # RENDER NODES & BYPASS BROWSER CACHE
            # ==========================================
            def get_fresh_base64_uri(file_path: str):
                if not os.path.exists(file_path): return None
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded_string}"
            
            for orig_name, attrs in nodes_payload.items():
                role = attrs.get("device_role", "OTHER")
                
                if "icon" not in attrs:
                    # Dynamically fetch the icon path from the global taxonomy
                    img_path = ICON_MAP.get(role, "templates/png/OTHER.png")
                    b64_uri = get_fresh_base64_uri(img_path)
                    
                    if b64_uri:
                        attrs["icon"] = b64_uri
                    else:
                        st.sidebar.warning(f"Icon file missing on disk: {img_path} for role [{role}]")
                
                if "size" not in attrs:
                    attrs["size"] = "m"

            render_nodes_standard(fig_pop, nodes_payload, pos_cache)

            # Background Layout Enhancements
            if "Backbone Layout" in selected_template:
                for r in [180, 280, 380, 500, 550, 600]:
                    fig_pop.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line=dict(color="rgba(255, 255, 255, 0.08)", dash="dot"))
                for r in [530, 580, 630]:
                    fig_pop.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line=dict(color="rgba(255, 255, 255, 0.03)", dash="dot"))
            elif "Edge Layout" in selected_template:
                for r in [180, 280, 380, 480, 580, 680, 780]:
                    fig_pop.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line=dict(color="rgba(255, 255, 255, 0.08)", dash="dot"))
                for r in [610, 710, 810]: 
                    fig_pop.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line=dict(color="rgba(255, 255, 255, 0.03)", dash="dot"))
            elif "Universe" in selected_template or "Circular" in selected_template:
                for r in [150, 300, 450]:
                    fig_pop.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line=dict(color="rgba(255, 255, 255, 0.08)", dash="dot"))

            fig_pop.update_layout(
                template="plotly_dark",
                height=850,
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(fig_pop, use_container_width=True)

        except Exception as e:
            st.error(f"Render Engine Exception: {e}")