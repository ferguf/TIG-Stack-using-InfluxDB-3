import plotly.graph_objects as go
import math
import numpy as np

# Import the registry to enable automatic layout discovery
from src.galileo.galileo_templates import LayoutRegistry

# =============================================================================
# 1. VISUAL DICTIONARIES & MAPPINGS
# =============================================================================

def render_colors(color_ids):
    """Translates health integers into RGBA strings for consistent UI."""
    palette = {
        1: "rgba(34, 197, 94, 1.0)",  2: "rgba(34, 197, 94, 0.4)",   # Green (Healthy)
        3: "rgba(59, 130, 246, 1.0)",  4: "rgba(59, 130, 246, 0.4)",   # Blue (Standard)
        5: "rgba(245, 158, 11, 1.0)",  6: "rgba(245, 158, 11, 0.4)",   # Amber (Warning)
        7: "rgba(239, 68, 68, 1.0)",  8: "rgba(239, 68, 68, 0.4)",    # Red (Critical)
        9: "rgba(100, 100, 100, 0.3)", 10: "rgba(100, 100, 100, 0.1)" # Gray (Dimmed)
    }
    if isinstance(color_ids, list):
        # Handle list of colors (PoP mode)
        return [palette.get(c, palette[3]) for c in color_ids]
        
    if isinstance(color_ids, (int, float)):
        c = int(color_ids)
        base = c if c % 2 != 0 else max(1, c - 1)
        return palette.get(base, palette[3]), palette.get(base + 1, palette[4])
    return palette[3], palette[4]

def get_width(val, default=2.5):
    size_map = {"xs": 0.5, "s": 1.5, "m": 2.5, "l": 4.5, "xl": 7.0}
    if isinstance(val, str): return size_map.get(val.lower(), default)
    try: return float(val) if val is not None else default
    except: return default

def get_normalized_positions(nodes, margin=100):
    """
    Maps location_x/y coordinates to a 0-1000 grid.
    Handles 'nodes' as either a List of dicts or a Dictionary of dicts.
    """
    # Standardize input to a list of attribute dictionaries
    if isinstance(nodes, dict):
        node_list = list(nodes.values())
    else:
        node_list = nodes

    # 1. Extract raw coordinates, safely handling potential strings
    try:
        x_vals = [float(n.get("location_x", 0)) for n in node_list if isinstance(n, dict)]
        y_vals = [float(n.get("location_y", 0)) for n in node_list if isinstance(n, dict)]
    except (ValueError, TypeError, AttributeError):
        return {}
    
    if not x_vals or not y_vals:
        return {}

    # 2. Find Boundaries
    min_x, max_x = min(x_vals), max(x_vals)
    min_y, max_y = min(y_vals), max(y_vals)
    
    range_x = (max_x - min_x) if max_x != min_x else 1
    range_y = (max_y - min_y) if max_y != min_y else 1
    
    # 3. Normalize to 0-1000 Viewport
    pos_cache = {}
    for n in node_list:
        if not isinstance(n, dict):
            continue
            
        raw_x = float(n.get("location_x", 0))
        raw_y = float(n.get("location_y", 0))
        
        # Scale to 0-1000 grid
        norm_x = ((raw_x - min_x) / range_x) * (1000 - 2 * margin) + margin
        norm_y = ((raw_y - min_y) / range_y) * (1000 - 2 * margin) + margin
        
        # Use location_name or label_header as the lookup key
        name = str(n.get("location_name", n.get("label_header", ""))).lower()
        pos_cache[name] = (norm_x, norm_y)
        
    return pos_cache

def get_link_geometry_with_stunt(p1, p2, minute_offset=50, stunt_px=20, style="beck"):
    """
    Generates a 4-point path with an increased 20px lead-out segment:
    1. Start (p1)
    2. Stunt Exit (p1 + 20px at specific clock minute)
    3. Beck Elbow (45/90 degree turn)
    4. End (p2)
    """
    p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
    
    # 0 min = 12 o'clock (-90 degrees)
    angle_rad = math.radians((minute_offset * 6) - 90)
    
    # Calculate the exit point after the px lead-out
    stunt_exit = np.array([
        p1[0] + stunt_px * math.cos(angle_rad),
        p1[1] + stunt_px * math.sin(angle_rad)
    ])

    dx = p2[0] - stunt_exit[0]
    dy = p2[1] - stunt_exit[1]

    if style == "beck":
        # Calculate Beck elbow starting from the end of the 20px stunt
        if abs(dx) > abs(dy):
            elbow = [stunt_exit[0] + np.sign(dx) * abs(dy), p2[1]]
        else:
            elbow = [p2[0], stunt_exit[1] + np.sign(dy) * abs(dx)]
        
        return [p1[0], stunt_exit[0], elbow[0], p2[0]], \
               [p1[1], stunt_exit[1], elbow[1], p2[1]]

    return [p1[0], stunt_exit[0], p2[0]], [p1[1], stunt_exit[1], p2[1]]# =============================================================================
# 2. GEOMETRIC MATH ENGINE
# =============================================================================

def get_link_geometry(p1, p2, style="beck"):
    """
    Calculates the 3-point path for octilinear or straight links.
    - beck: Forces 45/90 degree elbows.
    - line: Direct vector.
    """
    p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]

    if style == "beck" or style == "classic":
        # BECK LOGIC: 45-degree intercept
        if abs(dx) > abs(dy):
            elbow = [p1[0] + np.sign(dx) * abs(dy), p2[1]]
        else:
            elbow = [p2[0], p1[1] + np.sign(dy) * abs(dx)]
        return [p1[0], elbow[0], p2[0]], [p1[1], elbow[1], p2[1]]

    return [p1[0], p2[0]], [p1[1], p2[1]]

def render_3_color_segment_link(fig, p1, p2, colors, is_active=True):
    """
    Finalized Link Drawer: 
    - Forced High-Visibility for PoP Views.
    - Uses interpolation to chop the line into 3 parts.
    """
    import plotly.graph_objects as go
    from src.galileo.plotly_galileo import render_colors

    # Linear interpolation function
    def interp(t):
        return (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1]))

    # If coordinates are identical (collapsed), abort drawing to save resources
    if p1[0] == p2[0] and p1[1] == p2[1]:
        return

    # Segment points
    pts = [p1, interp(0.33), interp(0.66), p2]
    
    # 3-Color mapping
    segment_colors = []
    for c in colors:
        col, _ = render_colors(c) # Returns rgba string
        segment_colors.append(col)

    for i in range(3):
        start, end = pts[i], pts[i+1]
        
        fig.add_trace(go.Scatter(
            x=[start[0], end[0], None],
            y=[start[1], end[1], None],
            mode='lines',
            line=dict(
                width=4 if is_active else 1.5, # Slightly thicker for visibility
                color=segment_colors[i]
            ),
            opacity=1.0 if is_active else 0.15,
            hoverinfo='none',
            showlegend=False
        ))

def render_3_color_link(fig, p1, p2, colors, is_active=True):
    """
    Renders a single logical link as 3 segments: 
    [A-Port Health] --- [Link Status] --- [Z-Port Health]
    """
    # 1. Define the 3 segment points (0%, 33%, 66%, 100%)
    # x = x1 + t(x2 - x1)
    def get_pt(t):
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))

    pts = [p1, get_pt(0.33), get_pt(0.66), p2]
    
    # 2. Map health integers to Hex colors
    # 1=Green, 2=Yellow, 3=Orange, 4=Red, 7=Blue/Default
    health_map = {1: "#00FF00", 2: "#FFFF00", 3: "#FFA500", 4: "#FF0000", 7: "#00D1FF"}
    
    # link_colors = [a_status, path_status, z_status]
    # Default to Blue if data is missing
    c_list = [health_map.get(c, "#00D1FF") for c in colors]

    for i in range(3):
        start, end = pts[i], pts[i+1]
        opacity = 0.8 if is_active else 0.15
        
        fig.add_trace(go.Scatter(
            x=[start[0], end[0], None],
            y=[start[1], end[1], None],
            mode='lines',
            line=dict(width=3 if is_active else 1, color=c_list[i]),
            opacity=opacity,
            hoverinfo='none',
            showlegend=False
        ))
# =============================================================================
# 3. CONSOLIDATED BECK ENGINE (Universal Renderer)
# =============================================================================

def render_standard_engine(nodes, links, template_name="Circular", highlight_node=None, **kwargs):
    import streamlit as st
    import plotly.graph_objects as go
    from src.galileo.galileo_templates import LayoutRegistry
    
    layout_meta = LayoutRegistry.templates.get(template_name, {})
    layout_func = layout_meta.get("func")
    mode = layout_meta.get("mode", "POP")
    raw_pos = layout_func(nodes) if layout_func else {}

    # 1. Coordinate Mapping
    pos = {str(k).lower(): v for k, v in raw_pos.items()} if mode == "POP" else get_normalized_positions(raw_pos)

    # --- DEBUG SECTION ---
    with st.expander("🛠️ Link Handshake Debugger", expanded=False):
        st.write(f"**Template Mode:** {mode}")
        st.write(f"**Nodes in Layout (Keys):** {list(pos.keys())[:10]}... (Total: {len(pos)})")
        
        mismatched = []
        for l in links[:20]: # Check first 20 links
            u, v = str(l.get('source', '')).lower(), str(l.get('target', '')).lower()
            if u not in pos or v not in pos:
                mismatched.append({"source_key": u, "u_found": u in pos, "target_key": v, "v_found": v in pos})
        
        if mismatched:
            st.error(f"❌ Found {len(mismatched)} broken links in sample. Check key alignment!")
            st.table(mismatched)
        else:
            st.success("✅ All sampled links successfully matched to node coordinates.")
    # --- END DEBUG ---

    fig = go.Figure()
    target_node = str(highlight_node).lower() if highlight_node else None

    for link in links:
        u, v = str(link.get('source', '')).lower(), str(link.get('target', '')).lower()
        if u in pos and v in pos:
            is_active = not target_node or (u == target_node or v == target_node)
            l_colors = link.get('colors', [7, 7, 7])
            render_3_color_segment_link(fig, pos[u], pos[v], l_colors, is_active)

    render_nodes_standard(fig, nodes, pos, highlight_node=target_node)
    _apply_global_layout(fig, f"Galileo View: {template_name}")
    
    fig.update_layout(xaxis=dict(autorange=True), yaxis=dict(autorange=True, scaleanchor="x"))
    return fig

def render_beck_engine(nodes, links, template_name="Beck Classic", mode="INTERCITY", highlight_node=None, **kwargs):
    """
    Consolidated Engine:
    - Fixes Auto-scaling by passing node values to normalization.
    - Implements 20px lead-out with 5-minute clock increments.
    """
    from src.galileo.galileo_templates import LayoutRegistry
    
    # FIX: Ensure we pass the actual data objects, not just the string keys
    node_data = list(nodes.values()) if isinstance(nodes, dict) else nodes
    
    # 1. Normalize positions to force 0-1000 edge-to-edge scaling
    pos = get_normalized_positions(node_data, margin=100)
    
    if not pos:
        return go.Figure().update_layout(title="Coordinate Normalization Failed")

    fig = go.Figure()
    node_slot_registry = {}
    target_city = str(highlight_node).lower() if highlight_node and highlight_node != "global view" else None

    # 2. Process Filtered aeX Links
    for link in links:
        u = str(link.get('source', link.get('a_device_location', ''))).lower()
        v = str(link.get('target', link.get('b_device_location', ''))).lower()

        if u in pos and v in pos:
            p1, p2 = pos[u], pos[v]
            
            # 5-minute increment departure angles
            current_slot = node_slot_registry.get(u, 0)
            node_slot_registry[u] = current_slot + 5
            departure_min = current_slot % 60
            
            # 4-point Geometry with 20px lead-out
            lx, ly = get_link_geometry_with_stunt(
                p1, p2, 
                minute_offset=departure_min, 
                stunt_px=20, 
                style="beck" if "Classic" in template_name else "line"
            )

            is_active = not target_city or (u == target_city or v == target_city)
            
            fig.add_trace(go.Scatter(
                x=lx, y=ly, mode='lines',
                line=dict(width=3, color=f"rgba(0, 209, 255, {0.8 if is_active else 0.1})"),
                hoverinfo='none', showlegend=False
            ))

    # 3. Render Nodes using standardized pos
    render_nodes(fig, nodes, pos, highlight_node=target_city)
    
    fig.update_layout(
        template="plotly_dark",
        xaxis=dict(range=[0, 1000], visible=False, fixedrange=False),
        yaxis=dict(range=[0, 1000], visible=False, fixedrange=False),
        margin=dict(l=10, r=10, t=10, b=10),
        height=700
    )
    return fig

# =============================================================================
# 4. GEOGRAPHIC RENDERER
# =============================================================================

def render_geo_map(nodes, links, highlight_node=None):
    """
    Renders the Geographic USA Backbone.
    Uses native Lat/Long keys to prevent 'Layout Missing Data' errors.
    """
    import plotly.graph_objects as go
    fig = go.Figure()

    # 1. BASEMAP SETUP
    fig.add_trace(go.Scattergeo(lat=[None], lon=[None], showlegend=False))

    # 2. COORDINATE MAPPING (Case-Insensitive)
    coord_map = {}
    for n in nodes:
        try:
            # Explicit float casting for Scattergeo reliability
            lat = float(n.get("location_lat") or n.get("lat"))
            lon = float(n.get("location_long") or n.get("lon"))
            name = str(n.get("location_name", "")).lower()
            coord_map[name] = (lat, lon)
        except (TypeError, ValueError):
            continue

    # 3. RENDER LINKS (Fiber Spans)
    target_city = str(highlight_node).lower() if highlight_node and highlight_node != "GLOBAL VIEW" else None

    for link in links:
        # Check all possible key sources for the link endpoints
        u = str(link.get("a_device_location", link.get("source", ""))).lower()
        v = str(link.get("b_device_location", link.get("target", ""))).lower()
        
        if u in coord_map and v in coord_map:
            # Highlighting Logic: Dim links not connected to the selected hub
            is_active = not target_city or (u == target_city or v == target_city)
            opacity = 0.6 if is_active else 0.1
            
            fig.add_trace(go.Scattergeo(
                lat=[coord_map[u][0], coord_map[v][0], None],
                lon=[coord_map[u][1], coord_map[v][1], None],
                mode='lines',
                line=dict(width=1.5 if is_active else 1, color=f"rgba(59, 130, 246, {opacity})"),
                hoverinfo='skip'
            ))

    # 4. RENDER NODES (City Hubs)
    for node in nodes:
        try:
            lat = float(node.get("location_lat") or node.get("lat"))
            lon = float(node.get("location_long") or node.get("lon"))
            name = str(node.get("location_name", "Unknown"))
            
            is_target = target_city and name.lower() == target_city
            health = node.get("location_health_max", 3)
            primary_color, _ = render_colors(health)

            # Highlighting Logic for markers
            opacity = 1.0 if (not target_city or is_target) else 0.4

            fig.add_trace(go.Scattergeo(
                lat=[lat],
                lon=[lon],
                mode='markers+text' if is_target else 'markers',
                text=[f"<b>{name.upper()}</b>"] if is_target else [],
                textposition="top center",
                name=name,
                marker=dict(
                    size=18 if is_target else 12,
                    color=primary_color,
                    opacity=opacity,
                    line=dict(width=2, color="#FFFFFF" if is_target else "rgba(255,255,255,0.4)")
                ),
                hovertext=f"Hub: {name.upper()}<br>Status: {health}"
            ))
        except (TypeError, ValueError):
            continue

    # 5. USA PROJECTION CONFIG
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=0, r=0, t=0, b=0),
        height=450,
        geo=dict(
            scope='usa',
            projection_type='albers usa',
            showland=True,
            landcolor="#111",
            subunitcolor="#333",
            showlakes=True,
            lakecolor="#000"
        )
    )
    return fig
# =============================================================================
# 5. SPECIALIZED RENDERERS (PoP / Clock)
# =============================================================================

def render_galileo_plotly(galaxy_nodes, galaxy_orbits, galaxy_links):
    """Circular PoP Reference View."""
    fig = go.Figure()
    pos_cache = {}
    orbit_map = {str(o["id"]): o for o in galaxy_orbits}
    
    for nid, node in galaxy_nodes.items():
        theta = math.radians(node.get("angle", 0) - 90)
        orb = orbit_map.get(str(node.get("orbit", "O1")), {"rx": 150})
        rx = float(orb.get("rx", 150))
        pos_cache[str(nid)] = (rx * math.cos(theta), rx * math.sin(theta))
        
    render_links_generic(fig, galaxy_links, pos_cache)
    render_nodes(fig, galaxy_nodes, pos_cache)
    _apply_global_layout(fig, "PoP Reference View")
    return fig

def render_nodes(fig, nodes, pos_cache, highlight_node=None):
    """
    Renders nodes with a dual-ring health visual and background halo cutouts.
    
    ANNOTATION:
    - Handles 'nodes' as either a Dictionary (PoP) or a List (Intercity).
    - highlight_node: If provided, enlarges the target node and dims others.
    """
    # 1. STANDARDIZE INPUT
    # If data is a list (Intercity), convert to dict for consistent looping
    if isinstance(nodes, list):
        # Use location_name as the key to match the pos_cache keys
        nodes_to_process = {str(n.get("location_name", "")).lower(): n for n in nodes}
    else:
        # Standardize existing dict keys to lowercase
        nodes_to_process = {str(k).lower(): v for k, v in nodes.items()}

    # 2. RENDER LOOP
    for nid, attrs in nodes_to_process.items():
        nid_s = str(nid).lower()
        if nid_s not in pos_cache: 
            continue
            
        x, y = pos_cache[nid_s]
        
        # 3. HIGHLIGHT LOGIC
        # Determine if this specific node is the focused hub
        is_target = highlight_node and nid_s == str(highlight_node).lower()
        
        # Scale nodes: Highlighted = 35px, Standard = 22px, Dimmed = 18px
        if highlight_node:
            base_size = 35 if is_target else 18
            opacity = 1.0 if is_target else 0.4
        else:
            base_size = 22
            opacity = 1.0

        # 4. EXTRACT HEALTH COLORS
        # Logic for PoP (colors list) vs Intercity (location_health_max)
        if "colors" in attrs:
            # PoP Schema: [Port Health, Device Health]
            inner_id = attrs.get("colors", [7])[0]
            outer_id = attrs.get("colors", [7, 8])[1] if len(attrs.get("colors", [])) > 1 else inner_id + 1
        else:
            # Intercity Schema: Primary health status code
            inner_id = attrs.get("location_health_max", 3)
            outer_id = inner_id + 1
        
        primary_color, _ = render_colors(inner_id)
        _, glow_color = render_colors(outer_id)

        # 5. DRAW BACKGROUND HALO (The 'Cutout')
        # This prevents link lines from 'stabbing' the node center
        fig.add_trace(go.Scatter(
            x=[x], y=[y], 
            mode='markers', 
            marker=dict(
                size=base_size + 10, 
                color="#0e1117", # Matches your dark theme background
                opacity=opacity
            ), 
            hoverinfo='none', 
            showlegend=False
        ))

        # 6. DRAW OUTER GLOW (Interface/Secondary Health)
        fig.add_trace(go.Scatter(
            x=[x], y=[y], 
            mode='markers', 
            marker=dict(
                size=base_size + 8, 
                color="rgba(0,0,0,0)", 
                line=dict(width=4, color=glow_color)
            ), 
            opacity=opacity,
            hoverinfo='none', 
            showlegend=False
        ))
        
        # 7. DRAW INNER CORE (Device/Primary Health)
        label = attrs.get('label_header', attrs.get('location_name', nid_s))
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y], 
            mode='markers+text', 
            text=[f"<b>{label.upper()}</b>"] if (is_target or not highlight_node) else [], 
            textposition="bottom center", 
            marker=dict(
                size=base_size, 
                color=primary_color, 
                line=dict(width=2, color="white" if is_target else "rgba(255,255,255,0.7)")
            ), 
            opacity=opacity,
            hovertext=f"Node: {label}<br>Status ID: {inner_id}",
            showlegend=False
        ))

def render_nodes_with_icons(fig, nodes, pos_cache, highlight_node=None):
    """
    Enhanced node renderer that integrates PNG icons from 'template/png/'.
    Maintains the 3-layer visual stack: 
    1. Background Halo (Cutout)
    2. Outer Glow (Health)
    3. Custom PNG Icon (Role-based)
    """
    import plotly.graph_objects as go
    import os

    # Standardize input to a dict keyed by lowercase name
    if isinstance(nodes, dict):
        nodes_to_process = {str(k).lower(): v for k, v in nodes.items()}
    else:
        nodes_to_process = {str(n.get("location_name", n.get("label_header", ""))).lower(): n for n in nodes}

    for nid, attrs in nodes_to_process.items():
        if nid not in pos_cache: 
            continue
            
        x, y = pos_cache[nid]
        is_target = highlight_node and nid == str(highlight_node).lower()
        
        # Scaling logic
        base_size = 40 if is_target else (22 if highlight_node else 28)
        opacity = 1.0 if (not highlight_node or is_target) else 0.3

        # Extract [Inner (Device), Outer (Interface)] health colors
        colors = attrs.get("colors", [7, 7])
        inner_id, outer_id = colors[0], colors[1] if len(colors) > 1 else colors[0]
        primary_color, _ = render_colors(inner_id)
        _, glow_color = render_colors(outer_id)

        # 1. HALO CUTOUT (Prevents link lines from crossing into the icon)
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers',
            marker=dict(size=base_size + 12, color="#111"),
            opacity=opacity, hoverinfo='none', showlegend=False
        ))

        # 2. OUTER GLOW RING (Represents Interface/Aggregate Health)
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers',
            marker=dict(
                size=base_size + 10, 
                color="rgba(0,0,0,0)", 
                line=dict(width=3, color=glow_color)
            ),
            opacity=opacity, hoverinfo='none', showlegend=False
        ))
        
        # 3. PNG ICON INJECTION
        # Determine filename based on role (e.g., 'SDR' -> 'template/png/sdr.png')
        role = str(attrs.get("device_role", "generic")).lower()
        icon_path = f"template/png/{role}.png"
        
        # We use add_layout_image for the sharpest rendering of local assets
        fig.add_layout_image(
            dict(
                source=icon_path,
                xref="x", yref="y",
                x=x, y=y,
                sizex=base_size, sizey=base_size,
                xanchor="center", yanchor="middle",
                opacity=opacity,
                layer="above"
            )
        )

        # 4. LABEL (Device Name)
        label = attrs.get('label_header', attrs.get('location_name', nid))
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='text',
            text=[f"<b>{label.upper()}</b>"] if (is_target or not highlight_node) else [],
            textposition="bottom center",
            textfont=dict(color="white" if is_target else "rgba(255,255,255,0.7)"),
            opacity=opacity, showlegend=False,
            hovertext=f"Role: {role.upper()}<br>Status: {inner_id}"
        ))
        
def render_links_generic(fig, galaxy_links, pos_cache):
    """Generic link drawer for PoP views."""
    for link in galaxy_links:
        p1 = pos_cache.get(str(link.get("source")))
        p2 = pos_cache.get(str(link.get("target")))
        if not p1 or not p2: continue
        
        # Extract health for PoP link colors
        health = link.get("colors", [3, 1, 3])[1] # Use middle index
        col, _ = render_colors(health)
        
        fig.add_trace(go.Scatter(
            x=[p1[0], p2[0], None], y=[p1[1], p2[1], None],
            mode='lines', line=dict(color=col, width=get_width(link.get("width", "m"))),
            showlegend=False
        ))

def render_nodes_standard(fig, nodes, pos_cache, highlight_node=None):
    """
    Implements 100% functionality of the original node renderer:
    Background Halo -> Outer Glow (Interface) -> Inner Core (Device)
    """
    import plotly.graph_objects as go

    # Standardize input to a dict keyed by lowercase name
    if isinstance(nodes, dict):
        nodes_to_process = {str(k).lower(): v for k, v in nodes.items()}
    else:
        nodes_to_process = {str(n.get("location_name", n.get("label_header", ""))).lower(): n for n in nodes}

    for nid, attrs in nodes_to_process.items():
        if nid not in pos_cache: continue
        x, y = pos_cache[nid]
        
        is_target = highlight_node and nid == str(highlight_node).lower()
        base_size = 35 if is_target else (18 if highlight_node else 22)
        opacity = 1.0 if (not highlight_node or is_target) else 0.4

        # Extract [Inner (Device), Outer (Interface)] health colors
        colors = attrs.get("colors", [7, 7])
        inner_id, outer_id = colors[0], colors[1] if len(colors) > 1 else colors[0]
        primary_color, _ = render_colors(inner_id)
        _, glow_color = render_colors(outer_id)

        # 1. Halo Cutout (Black circle to hide overlapping link lines)
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers',
            marker=dict(size=base_size + 10, color="#111"),
            opacity=opacity, hoverinfo='none', showlegend=False
        ))

        # 2. Outer Glow Ring
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers',
            marker=dict(size=base_size + 8, color="rgba(0,0,0,0)", 
                        line=dict(width=4, color=glow_color)),
            opacity=opacity, hoverinfo='none', showlegend=False
        ))
        
        # 3. Device Core Marker + Label
        label = attrs.get('label_header', attrs.get('location_name', nid))
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers+text',
            text=[f"<b>{label.upper()}</b>"] if (is_target or not highlight_node) else [],
            textposition="bottom center",
            marker=dict(size=base_size, color=primary_color, 
                        line=dict(width=2, color="white" if is_target else "rgba(255,255,255,0.7)")),
            opacity=opacity, showlegend=False
        ))
    
def _apply_global_layout(fig, title_text):
    fig.update_layout(
        template="plotly_dark", plot_bgcolor="#111", paper_bgcolor="#111",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x"),
        margin=dict(l=20, r=20, t=60, b=20),
        title=dict(text=title_text, font=dict(size=18))
    )
# =============================================================================
# 6. BACKWARDS COMPATIBILITY ALIASES
# =============================================================================

# Redirects old Intercity/Backbone calls to the consolidated engine
render_galileo_beck = render_beck_engine

# Redirects old Template/PoP calls to the consolidated engine
render_galileo_template = render_beck_engine