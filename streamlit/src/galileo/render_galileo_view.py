import streamlit as st
from src.galileo.plotly_galileo import render_geo_map, render_galileo_template, render_galileo_plotly,render_beck_engine,render_standard_engine
from src.galileo.galileo_templates import LayoutRegistry
from src.utils.api_network import get_devices_by_short_name, get_network_links_detail
import re
def build_galaxy_data(devices, links, focus_device_id=None):
    """
    Transforms API data into the Galileo dictionary schema.
    - Fixes NameError by initializing max_port_severity.
    - Fixes Missing PoP elements by using lowercase name keys.
    """
    galaxy_nodes = {}
    # Use lowercase name for the lookup to match link source/target names
    name_lookup = {str(d['device_id']): str(d['device_name']).lower() for d in devices}
    focus_id_str = str(focus_device_id) if focus_device_id else None
    
    # 1. Initialize severity tracking (7 is normal/baseline)
    # This MUST happen before the node loop
    max_port_severity = {str(d['device_id']): 7 for d in devices}
    neighbor_ids = set()

    # 2. Pre-process Links to find neighbors and worst-case port health
    for link in links:
        s_id, t_id = str(link.get('a_device_id')), str(link.get('b_device_id'))
        
        if focus_id_str:
            if s_id == focus_id_str: neighbor_ids.add(t_id)
            elif t_id == focus_id_str: neighbor_ids.add(s_id)

        a_p_health = link.get('a_port_health_status', 7)
        b_p_health = link.get('b_port_health_status', 7)
        
        if s_id in max_port_severity:
            max_port_severity[s_id] = min(max_port_severity[s_id], a_p_health)
        if t_id in max_port_severity:
            max_port_severity[t_id] = min(max_port_severity[t_id], b_p_health)

    # 3. Map Nodes (Dictionary keyed by lowercase name)
    for i, dev in enumerate(devices):
        dev_id = str(dev['device_id'])
        node_key = str(dev.get('device_name', dev_id)).lower()
        
        port_health = max_port_severity.get(dev_id, 7)
        device_health = dev.get('device_health_status', 7)

        # High-density focus logic
        if focus_id_str and dev_id != focus_id_str and dev_id not in neighbor_ids:
            node_colors, opacity = [9, 10], 0.2
        else:
            node_colors, opacity = [port_health, device_health], 1.0

        galaxy_nodes[node_key] = {
            "device_id": dev_id,
            "label_header": dev.get('device_name', dev_id),
            "device_role": str(dev.get('device_role', '')).upper(),
            "location_x": dev.get('location_x', 0),
            "location_y": dev.get('location_y', 0),
            "colors": node_colors,
            "opacity": opacity
        }

    # 4. Map Links (Source/Target using lowercase names)
    galaxy_links = []
    for link in links:
        u_name = name_lookup.get(str(link.get('a_device_id')))
        v_name = name_lookup.get(str(link.get('b_device_id')))
        
        if u_name and v_name:
            galaxy_links.append({
                "source": u_name, 
                "target": v_name,
                "a_device_location": u_name,
                "b_device_location": v_name,
                "colors": [link.get('a_port_health_status', 7), 1, link.get('b_port_health_status', 7)]
            })

    # Standard orbits for POP reference
    galaxy_orbits = [
        {"id": "O1", "rx": 150, "type": "circle", "color": "rgba(255,255,255,0.05)", "style": "dash"},
        {"id": "O2", "rx": 300, "type": "circle", "color": "rgba(255,255,255,0.05)", "style": "dash"},
        {"id": "O3", "rx": 350, "type": "circle", "color": "rgba(255,255,255,0.05)", "style": "dash"}
    ]

    return galaxy_nodes, galaxy_orbits, galaxy_links

def get_pop_netlink_data(site_code: str):
    """
    Fetches raw site data with NO interface filtering.
    Captures 100% of intra-site connectivity for debugging.
    """
    # Fetch devices for the specific site (e.g., 'DEN1')
    all_devices = get_devices_by_short_name(site_code)
    all_links = get_network_links_detail()
    
    # Filter for active devices (Excluding FDP/Passive frames)
    active_devices = [d for d in all_devices if str(d.get('device_role')).upper() != "FDP"]
    
    # Create a set of IDs for O(1) lookup
    device_ids = {str(d['device_id']) for d in active_devices}

    pop_links = []
    for l in all_links:
        s_id = str(l.get('a_device_id'))
        t_id = str(l.get('b_device_id'))
        
        # REMOVED ALL REGEX FILTERS
        # Requirement: Both A and B sides must be in the current site
        # Requirement: Ignore self-loops (A == B)
        if s_id in device_ids and t_id in device_ids and s_id != t_id:
            pop_links.append(l)

    # Transform the raw list into the (nodes, orbits, links) tuple for the engine
    galaxy = build_galaxy_data(active_devices, pop_links)
    return active_devices, pop_links, galaxy
def render_galileo_topology(nodes, links, template_name="Beck Classic", **kwargs):
    """
    Central Engine Router.
    Location: src/galileo/render_galileo_view.py
    """
    from src.galileo.plotly_galileo import render_geo_map, render_beck_engine, render_standard_engine
    
    # 1. Geographic Template -> Uses USA Lat/Long Map
    if template_name == "Geographic":
        return render_geo_map(nodes, links, **kwargs)
    
    # 2. Beck/Classic Templates -> Uses 20px Stunts + Octilinear Elbows
    if "Beck" in template_name or "Classic" in template_name:
        return render_beck_engine(nodes, links, template_name=template_name, **kwargs)
    
    # 3. POP/Internal Templates -> Uses Standard 0-1000 scaled straight lines
    # This is preferred for PoP views to avoid elbow clutter.
    return render_standard_engine(nodes, links, template_name=template_name, **kwargs)
def render_pop_view(nodes, links, template_name=None):
    """Orchestrator for site-specific/internal views."""
    if not template_name:
        template_name = LayoutRegistry.get_default_name("POP")
        
    return render_galileo_template(
        nodes, 
        links, 
        template_name=template_name, 
        mode="POP"
    )

def render_master_view(nodes, links, selected_template, mode="INTERCITY"):
    """
    Entry point for Streamlit rendering.
    """
    mode_str = mode.upper()
    
    # Route based on mode and template
    if mode_str == "POP":
        fig = render_pop_view(nodes, links, template_name=selected_template)
    else:
        fig = render_galileo_topology(nodes, links, template_name=selected_template)
        
    # Unique key for Streamlit to prevent rendering collisions
    safe_tpl = str(selected_template).replace(" ", "_").lower()
    chart_key = f"plotly_{mode_str}_{safe_tpl}"
    
    st.plotly_chart(
        fig, 
        use_container_width=True, 
        config={'displayModeBar': False, 'scrollZoom': True},
        key=chart_key
    )

def render_beck_view(nodes, links):
    """Direct shortcut for the Beck logical backbone visualization."""
    return render_galileo_template(nodes, links, template_name="Beck", mode="INTERCITY")