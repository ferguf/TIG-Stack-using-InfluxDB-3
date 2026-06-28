import plotly.graph_objects as go
import math
import numpy as np

# Import the registry to enable automatic layout discovery
from src.galileo.galileo_templates import LayoutRegistry

# =============================================================================
# 1. VISUAL DICTIONARIES & MAPPINGS
# =============================================================================

def get_width(val, default=2.5):
    size_map = {"xs": 0.5, "s": 1.5, "m": 3, "l": 6, "xl": 12.0}
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

# =============================================================================
# 3. CONSOLIDATED BECK ENGINE (Universal Renderer)
# =============================================================================

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


def render_colors(color_ids):
    """
    Translates API health integers into RGBA tuple strings for consistent UI.
    Schema: 0=Planning, 1=Green, 2=Amber, 3=Red, 4=Unknown(Blue).
    """
    palette = {
        0: ("rgba(108, 117, 125, 1.0)", "rgba(108, 117, 125, 0.3)"), # Gray
        1: ("rgba(34, 197, 94, 1.0)", "rgba(34, 197, 94, 0.3)"),     # Green
        2: ("rgba(245, 158, 11, 1.0)", "rgba(245, 158, 11, 0.4)"),   # Amber
        3: ("rgba(239, 68, 68, 1.0)", "rgba(239, 68, 68, 0.4)"),     # Red
        4: ("rgba(59, 130, 246, 1.0)", "rgba(59, 130, 246, 0.4)")    # Blue
    }
    
    if isinstance(color_ids, list):
        return [palette.get(c, palette[4])[0] for c in color_ids]
        
    if isinstance(color_ids, (int, float)):
        c = int(color_ids)
        return palette.get(c, palette[4])
        
    return palette[4]    

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

# =============================================================================
# 1. VISUAL DICTIONARIES & MAPPINGS
# =============================================================================
def render_colors(color_ids):
    """
    Translates API health integers into RGBA tuple strings (primary, glow) for consistent UI.
    Maps to the explicit schema: 0=Planning, 1=Green, 2=Amber, 3=Red, 4=Unknown(Blue).
    """
    palette = {
        0: ("rgba(108, 117, 125, 1.0)", "rgba(108, 117, 125, 0.3)"), # Gray (Provisioning/Planning)
        1: ("rgba(34, 197, 94, 1.0)", "rgba(34, 197, 94, 0.3)"),     # Green (Healthy)
        2: ("rgba(245, 158, 11, 1.0)", "rgba(245, 158, 11, 0.4)"),   # Amber (Warning/Degraded)
        3: ("rgba(239, 68, 68, 1.0)", "rgba(239, 68, 68, 0.4)"),     # Red (Critical/Down)
        4: ("rgba(59, 130, 246, 1.0)", "rgba(59, 130, 246, 0.4)")    # Blue (Unknown)
    }
    
    # If passed a list of colors (PoP mode compatibility), return a list of primary hexes
    if isinstance(color_ids, list):
        return [palette.get(c, palette[4])[0] for c in color_ids]
        
    # Standard return: Tuple of (Primary Color, Glow Color)
    if isinstance(color_ids, (int, float)):
        c = int(color_ids)
        return palette.get(c, palette[4])
        
    # Fail-safe default to Unknown
    return palette[4]

def get_width(val, default=2.5):
    size_map = {"xs": 0.5, "s": 1.5, "m": 3, "l": 6, "xl": 12.0}
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

def render_3_color_segment_link(fig, p1, p2, colors, is_active=True, link_text=""):
    """
    Renders a single logical link as 3 segments: [A-Port Health] --- [Link Status] --- [Z-Port Health].
    Uses the centralized `render_colors` schema (0=Planning, 1=Green, 2=Amber, 3=Red, 4=Unknown).
    """
    if p1[0] == p2[0] and p1[1] == p2[1]: 
        return

    def interp(t):
        return (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1]))

    # 1. Standardize the input colors (Fallback to 4=Unknown if missing)
    if not isinstance(colors, list):
        colors = [4, 4, 4]
    
    while len(colors) < 3:
        colors.append(colors[-1] if colors else 4)
    colors = colors[:3]

    # 2. Map IDs to RGBA using the central schema
    # render_colors(c) returns a tuple (Primary, Glow), we only need [0] for the line
    segment_colors = [render_colors(c)[0] for c in colors]

    # 3. Draw the 3 segments (0-33%, 33-66%, 66-100%)
    pts = [p1, interp(0.33), interp(0.66), p2]
    
    for i in range(3):
        start, end = pts[i], pts[i+1]
        fig.add_trace(go.Scatter(
            x=[start[0], end[0], None],
            y=[start[1], end[1], None],
            mode='lines',
            line=dict(
                width=3 if is_active else 1.5, 
                color=segment_colors[i]
            ),
            opacity=0.9 if is_active else 0.15,
            # --- TOOLTIP ENGINE ---
            text=[link_text] if link_text else [],
            hoverinfo='text' if link_text else 'none',
            showlegend=False
        ))

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
    Implements 3-Color Link Segments and 2-Color Device Halo schemas.
    """
    import plotly.graph_objects as go
    fig = go.Figure()

    # 1. BASEMAP SETUP
    fig.add_trace(go.Scattergeo(lat=[None], lon=[None], showlegend=False))

    # 2. COORDINATE MAPPING (Case-Insensitive)
    coord_map = {}
    for n in nodes:
        try:
            lat = float(n.get("location_lat") or n.get("lat"))
            lon = float(n.get("location_long") or n.get("lon"))
            name = str(n.get("location_name", "")).lower()
            coord_map[name] = (lat, lon)
        except (TypeError, ValueError):
            continue

    # 3. RENDER LINKS (Fiber Spans - 3 Color Schema)
    target_city = str(highlight_node).lower() if highlight_node and highlight_node != "GLOBAL VIEW" else None

    # Helper function to interpolate lat/lon for the 3 visual segments
    def interp(t, p1, p2):
        return p1 + t * (p2 - p1)

    for link in links:
        u = str(link.get("a_device_location", link.get("source", ""))).lower()
        v = str(link.get("b_device_location", link.get("target", ""))).lower()
        
        if u in coord_map and v in coord_map:
            is_active = not target_city or (u == target_city or v == target_city)
            opacity = 0.8 if is_active else 0.1
            line_width = 2.5 if is_active else 1.0

            # Extract 3-color array, default to Standard Blue
            link_colors = link.get("colors", [3, 3, 3])
            c1, _ = render_colors(link_colors[0])
            c2, _ = render_colors(link_colors[1])
            c3, _ = render_colors(link_colors[2])
            
            lat1, lon1 = coord_map[u]
            lat2, lon2 = coord_map[v]
            
            lats = [lat1, interp(0.33, lat1, lat2), interp(0.66, lat1, lat2), lat2]
            lons = [lon1, interp(0.33, lon1, lon2), interp(0.66, lon1, lon2), lon2]
            segment_hex = [c1, c2, c3]
            
            # --- Draw the 3 Visible Segments ---
            for i in range(3):
                fig.add_trace(go.Scattergeo(
                    lat=[lats[i], lats[i+1], None],
                    lon=[lons[i], lons[i+1], None],
                    mode='lines',
                    line=dict(width=line_width, color=segment_hex[i]),
                    opacity=opacity,
                    hoverinfo='skip'
                ))

            # --- Draw the Invisible Midpoint Hover Target ---
            hover_text = link.get("hover_text", link.get("hovertext", ""))
            if hover_text:
                fig.add_trace(go.Scattergeo(
                    lat=[lats[1] + 0.5 * (lats[2] - lats[1])], 
                    lon=[lons[1] + 0.5 * (lons[2] - lons[1])],
                    mode='markers',
                    marker=dict(size=14, color='rgba(0,0,0,0)'), # Invisible hit-box
                    hoverinfo='text',
                    text=[hover_text],
                    showlegend=False
                ))

    # 4. RENDER NODES (City Hubs - 2 Color Schema)
    for node in nodes:
        try:
            lat = float(node.get("location_lat") or node.get("lat"))
            lon = float(node.get("location_long") or node.get("lon"))
            name = str(node.get("location_name", "Unknown"))
            
            is_target = target_city and name.lower() == target_city
            opacity = 1.0 if (not target_city or is_target) else 0.4
            base_size = 18 if is_target else 12

            # Extract 2-color array: [Device Health, Interface Health]
            node_colors = node.get("colors", [3, 4])
            primary_color, _ = render_colors(node_colors[0])
            _, glow_color = render_colors(node_colors[1])

            # Layer A: Dark Background Cutout (Prevents line stabbing)
            fig.add_trace(go.Scattergeo(
                lat=[lat], lon=[lon], mode='markers',
                marker=dict(size=base_size + 10, color="#111", opacity=opacity),
                hoverinfo='skip', showlegend=False
            ))

            # Layer B: Outer Glow / Interface Health Indicator
            fig.add_trace(go.Scattergeo(
                lat=[lat], lon=[lon], mode='markers',
                marker=dict(
                    size=base_size + 6, 
                    color="rgba(0,0,0,0)", 
                    line=dict(width=3, color=glow_color)
                ),
                opacity=opacity, hoverinfo='skip', showlegend=False
            ))

            # Layer C: Inner Core / Device Health Indicator
            fig.add_trace(go.Scattergeo(
                lat=[lat], lon=[lon],
                mode='markers+text' if is_target else 'markers',
                text=[f"<b>{name.upper()}</b>"] if is_target else [],
                textposition="top center",
                name=name,
                marker=dict(
                    size=base_size,
                    color=primary_color,
                    opacity=opacity,
                    line=dict(width=2, color="#FFFFFF" if is_target else "rgba(255,255,255,0.4)")
                ),
                hovertext=f"Hub: {name.upper()}<br>Device Code: {node_colors[0]} | Port Code: {node_colors[1]}"
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

def get_node_size(size_val, default=22):
    """Maps string aliases to pixel diameters."""
    size_map = {
        "sun": 45, "xl": 40, "l": 30, 
        "m": 22, "s": 15, "xs": 10
    }
    if isinstance(size_val, str):
        return size_map.get(size_val.lower(), default)
    return size_val if size_val else default

def render_galileo_plotly(nodes, orbits, links):
    """
    Comprehensive update to the Galileo orbital renderer.
    Fixes the clock-face math to ensure:
    - 0 mins = North (+Y)
    - 15 mins = East (+X)
    - 30 mins = South (-Y)
    - 45 mins = West (-X)
    """
    import plotly.graph_objects as go
    import math

    fig = go.Figure()
    pos_cache = {}
    orb_map = {str(o["id"]): o for o in orbits}

    # 1. Background Orbits (Visual structure only)
    render_orbits(fig, orbits)

    # 2. Position Nodes with Corrected Clock-Face Math
    for nid, attrs in nodes.items():
        node_type = str(attrs.get("node_type", "")).lower()
        
        if node_type == "sun":
            # The Sun remains the unique center point
            x, y = 0.0, 0.0
        else:
            oid = str(attrs.get("orbit"))
            radius = float(orb_map.get(oid, {}).get("rx", 200))
            
            # Clock-Face logic: Convert minutes to degrees (1 min = 6 degrees)
            # Default to 0 if 'mins' or 'angle' is missing
            mins = float(attrs.get("mins", attrs.get("angle", 0) / 6))
            
            # CORRECTED MATH: 
            # 1. 90 degrees starts us at North (+Y)
            # 2. Subtracting (mins * 6) ensures clockwise rotation
            theta_deg = 90 - (mins * 6)
            theta_rad = math.radians(theta_deg)
            
            x = radius * math.cos(theta_rad)
            y = radius * math.sin(theta_rad)
        
        pos_cache[str(nid).lower()] = (x, y)

    # 3. Render 3-Color Segment Links
    # Logic from
    for link in links:
        u, v = str(link.get("source")).lower(), str(link.get("target")).lower()
        if u in pos_cache and v in pos_cache:
            # Renders A-Port, Path, and Z-Port health in one line
            render_3_color_segment_link(
                fig, 
                pos_cache[u], 
                pos_cache[v], 
                link.get("colors", [3, 3, 3])
            )

    # 4. Render Nodes using the Standardized Size Engine
    # Logic from

# =============================================================================
# 6. BACKWARDS COMPATIBILITY ALIASES
# =============================================================================

# Redirects old Intercity/Backbone calls to the consolidated engine
render_galileo_beck = render_beck_engine

# Redirects old Template/PoP calls to the consolidated engine
render_galileo_template = render_beck_engine

# =============================================================================
# 1. CORE RENDER ENGINE
# =============================================================================

def render_standard_engine(nodes, links, orbits=None, template_name="Galileo Universe", highlight_node=None, **kwargs):
    """
    Standardizes the rendering pipeline.
    Ensures dynamic viewport scaling based on the largest orbital radius.
    """
    import plotly.graph_objects as go
    from src.galileo.galileo_templates import LayoutRegistry

    # 1. Coordinate Handshake
    layout_meta = LayoutRegistry.templates.get(template_name, LayoutRegistry.templates.get("Galileo Universe", {}))
    layout_func = layout_meta.get("func")
    
    if layout_func:
        raw_pos = layout_func(nodes, orbits_list=orbits) if orbits else layout_func(nodes)
    else:
        raw_pos = {}

    pos = {str(k).lower(): v for k, v in raw_pos.items() if k != "_debug"}
    fig = go.Figure()

    # 2. LAYER 1: Background Orbits
    if orbits:
        render_orbits(fig, orbits)

    # 3. LAYER 2: Links
    target_node = str(highlight_node).lower() if highlight_node else None
# Inside render_standard_engine (Layer 2: Links)
    for link in links:
        u, v = str(link.get('source', '')).lower(), str(link.get('target', '')).lower()
        if u in pos and v in pos:
            is_active = not target_node or (u == target_node or v == target_node)
            l_colors = link.get('colors', [3, 3, 3])
            
            # Extract the tooltip text from the link dictionary
            l_text = link.get('hovertext', link.get('text', 'Fabric Connection'))
            
            # Pass everything including the link_text argument
            render_3_color_segment_link(
                fig, pos[u], pos[v], l_colors, 
                is_active=is_active, 
                link_text=l_text # <--- Ensure this is passed
            )


    # 4. LAYER 3: Nodes
    render_nodes_standard(fig, nodes, pos, highlight_node=target_node)
    
    # 5. DYNAMIC VIEWPORT SCALING
    # Find the largest orbit to set the boundaries, default to 500
    max_radius = 500
    if orbits:
        max_radius = max([float(o.get("rx", 0)) for o in orbits] + [float(o.get("ry", 0)) for o in orbits])
    
    dynamic_limit = max_radius + 100 # Add 100px padding
    
    _apply_global_layout(fig, f"Galileo: {template_name}", limit=dynamic_limit)
    
    return fig

# =============================================================================
# 2. GEOMETRY & VISUALS
# =============================================================================

def render_orbits(fig, orbits):
    """Draws sharp geometric background rings. Supports 'none' for invisible guides."""
    import math
    import plotly.graph_objects as go

    VALID_DASH = ['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot']
    width_map = {"xs": 1.2, "s": 2.0, "m": 3.5, "l": 6.0, "xl": 10.0}
    
    for orb in orbits:
        otype = str(orb.get("type", "circle")).lower()
        style = str(orb.get("style", "solid")).lower()
        
        # 🚀 THE FIX: Intercept 'none' and skip drawing the visible trace.
        # The orbit still exists in the dictionary for node snapping!
        if style == "none" or style == "hidden":
            continue

        rx = float(orb.get("rx", 250))
        ry = float(orb.get("ry", rx))
        
        # Style Normalization
        if style == "dotdash": style = "dashdot" 
        if style not in VALID_DASH: style = "solid" 
        
        x_pts, y_pts = [], []
        if otype in ["circle", "ellipse"]:
            theta = [math.radians(i * (360/64)) for i in range(65)]
            x_pts = [rx * math.cos(t) for t in theta]
            y_pts = [ry * math.sin(t) for t in theta]
        elif otype in ["square", "rectangle"]:
            x_pts = [-rx, rx, rx, -rx, -rx]
            y_pts = [ry, ry, -ry, -ry, ry]
        elif otype == "triangle":
            x_pts = [0, rx, -rx, 0]
            y_pts = [ry, -ry, -ry, ry]

        if x_pts:
            fig.add_trace(go.Scatter(
                x=x_pts, y=y_pts, mode='lines',
                line=dict(
                    color=orb.get("color", "rgba(255,255,255,0.2)"),
                    width=width_map.get(str(orb.get("width", "xs")).lower(), 1.2),
                    dash=style
                ),
                hoverinfo='skip', showlegend=False
            ))

def _apply_global_layout(fig, title_text, limit=600):
    """
    Applies the master styling and locks the aspect ratio.
    Accepts a dynamic limit to prevent geometric clipping.
    """
    fig.update_layout(
        template="plotly_dark", 
        plot_bgcolor="#111", 
        paper_bgcolor="#111",
        xaxis=dict(
            range=[-limit, limit], 
            showgrid=False, 
            zeroline=False, 
            showticklabels=False
        ),
        yaxis=dict(
            range=[-limit, limit], 
            showgrid=False, 
            zeroline=False, 
            showticklabels=False, 
            scaleanchor="x", # Forces 1:1 aspect ratio
            scaleratio=1
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(text=title_text, font=dict(size=16, color="white")),
        hovermode='closest', 
        showlegend=False
    )
# =============================================================================
# 3. NODE RENDERER (Color/Size Fix)
# =============================================================================
def render_nodes_standard(fig, nodes, pos_cache, highlight_node=None):
    """
    Renders nodes with increased icon size and tightly matched halos.
    Includes an adjustable scale multiplier for the PNG icon size.
    """
    import plotly.graph_objects as go

    # 1. SCALE MAPPING: Doubled base sizes for 100% increase (m=44, l=70, etc.)
    size_map = {"sun": 110, "xl": 90, "l": 70, "m": 44, "s": 24, "xs": 16}
    
    nodes_proc = nodes if isinstance(nodes, dict) else {n.get("label_header", "??"): n for n in nodes}

    for nid, attrs in nodes_proc.items():
        nid_l = str(nid).lower()
        if nid_l not in pos_cache: continue
            
        x, y = pos_cache[nid_l]
        
        # 2. HIGHLIGHT & DIMENSIONS
        is_target = highlight_node and nid_l == str(highlight_node).lower()
        px = size_map.get(str(attrs.get("size", "m")).lower(), 44)
        
        # Plate size (the colored background plate)
        health_px = px * 1.5 if is_target else px
        
        # Halo size: Tightly matched to the plate size
        halo_px = health_px + 8 
        halo_width = 6
        
        # 3. COLOR ENGINE
        c_ids = attrs.get("colors", [3, 4])
        inner_col, _ = render_colors(c_ids[0])
        _, outer_glow = render_colors(c_ids[1] if len(c_ids) > 1 else c_ids[0] + 1)

        # 4. LAYER 1: HALO (Tightly matched)
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers',
            marker=dict(size=halo_px, color="rgba(0,0,0,0)", line=dict(width=halo_width, color=outer_glow)),
            hoverinfo='skip', showlegend=False
        ))

        # 5. LAYER 2: ICON PLATE
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers+text',
            text=[f"<br><br><br><b>{str(attrs.get('label_header', nid)).upper()}</b>"] if (is_target or not highlight_node) else [],
            textposition="bottom center",
            marker=dict(size=health_px, color=inner_col, line=dict(width=2, color="white")),
            hovertext=attrs.get("hovertext", f"Node: {nid}"),
            hoverinfo='text',
            showlegend=False
        ))

        # 6. LAYER 3: ICON OVERLAY
        img_url = attrs.get("icon")
        if img_url:
            # 🎛️ ADJUST PNG SIZE HERE:
            # 0.5 = 50% of the circle (Smaller)
            # 0.8 = 80% of the circle (Current Baseline)
            # 1.0 = 100% of the circle (Touches the edge)
            # 1.2 = 120% of the circle (Spills over into the halo ring)
            img_scale = health_px * 1.6
            
            fig.add_layout_image(dict(
                source=img_url, xref="x", yref="y", x=x, y=y,
                sizex=img_scale, sizey=img_scale,
                xanchor="center", yanchor="middle", sizing="contain", layer="above"
            ))