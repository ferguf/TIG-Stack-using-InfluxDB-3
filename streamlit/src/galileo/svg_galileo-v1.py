import drawsvg as draw
import math

# Internal configuration
W, H = 600, 600
NODE_COLORS = {
    1: "#ef4444",   # Red
    2: "#ef444480", # Red Opaque
    3: "#f59e0b",   # Amber
    4: "#f59e0b80", # Amber Opaque
    5: "#22c55e",   # Green
    6: "#22c55e80", # Green Opaque
    7: "#3b82f6",   # Blue
    8: "#3b82f680", # Blue Opaque
    9: "#a855f7",   # Purple
    10: "#a855f780" # Purple Opaque
}
SIZE_MAP = {"XS": 1, "S": 2, "M": 4, "L": 6, "XL": 8}
TYPE_MAP = {"solid": None, "Solid": None, "dash": "5,5", "double-dash": "2,2"}

def get_pos(radius, angle_deg):
    """Converts polar coordinates to Cartesian x, y."""
    theta = math.radians(angle_deg - 90)
    return radius * math.cos(theta), radius * math.sin(theta)

def create_split_gradient(d, color_a, color_b, grad_id, x1, y1, x2, y2):
    """Creates a linear gradient with a hard 50% split."""
    # Using gradientUnits='userSpaceOnUse' ensures the 50% stop 
    # is the physical center between the two nodes.
    grad = draw.LinearGradient(x1, y1, x2, y2, id=grad_id, gradientUnits='userSpaceOnUse')
    grad.add_stop(0.5, color_a, 1)
    grad.add_stop(0.5, color_b, 1)
    d.append(grad)
    return f"url(#{grad_id})"

def render_node(d, node_id, attrs):
    if not attrs.get("visible", True): return
    
    # Handle central Sun vs orbiting nodes
    nx, ny = (0, 0) if attrs.get("radius", 0) == 0 else get_pos(attrs["radius"], attrs["angle"])
    
    # Defensive color fetching
    colors = attrs.get("colors", [7, 3])
    c1 = colors[0] if len(colors) > 0 else 7
    c2 = colors[1] if len(colors) > 1 else 3
    
    outer_color = NODE_COLORS.get(c1, "#64748b")
    inner_color = NODE_COLORS.get(c2, "#0f172a")
    
    r_outer = attrs.get("size_outer", 15)
    r_inner = attrs.get("size_inner", 10)
    
    d.append(draw.Circle(nx, ny, r_outer, fill=outer_color))
    d.append(draw.Circle(nx, ny, r_inner, fill=inner_color, stroke="black", stroke_width=1))
    
    # Label
    label = attrs.get("label_header", "")
    if label:
        d.append(draw.Text(label, 12, nx, ny + r_outer + 12, fill="white", text_anchor="middle", font_family="sans-serif"))

def render_arc(d, galaxy_nodes, arc, index):
    """Renders curved connections with split colors."""
    if not arc.get("visible", True): return
    
    try:
        n1, n2 = galaxy_nodes[arc["source"]], galaxy_nodes[arc["target"]]
        x1, y1 = get_pos(n1["radius"], n1["angle"])
        x2, y2 = get_pos(n2["radius"], n2["angle"])
        
        colors = arc.get("colors", [8, 4])
        color_a = NODE_COLORS.get(colors[0], "#64748b")
        color_b = NODE_COLORS.get(colors[1], "#0f172a")
        
        grad_id = f"arc_grad_{index}"
        grad_url = create_split_gradient(d, color_a, color_b, grad_id, x1, y1, x2, y2)
        
        p = draw.Path(
            stroke=grad_url, 
            stroke_width=SIZE_MAP.get(arc.get("size", "S"), 2), 
            fill="none", 
            stroke_dasharray=TYPE_MAP.get(arc.get("type", "solid"))
        )
        # Standard arc logic
        p.M(x1, y1).A(n1["radius"], n1["radius"], 0, 0, 1, x2, y2)
        d.append(p)
    except KeyError as e:
        print(f"Skipping arc: missing node reference {e}")

def render_link(d, galaxy_nodes, link, index):
    """Renders straight connections with split colors."""
    if not link.get("visible", True): return
    
    try:
        n1, n2 = galaxy_nodes[link["source"]], galaxy_nodes[link["target"]]
        x1, y1 = (0, 0) if n1.get("radius", 0) == 0 else get_pos(n1["radius"], n1["angle"])
        x2, y2 = (0, 0) if n2.get("radius", 0) == 0 else get_pos(n2["radius"], n2["angle"])
        
        colors = link.get("colors", [8, 4])
        color_a = NODE_COLORS.get(colors[0], "#64748b")
        color_b = NODE_COLORS.get(colors[1], "#0f172a")
        
        grad_id = f"link_grad_{index}"
        grad_url = create_split_gradient(d, color_a, color_b, grad_id, x1, y1, x2, y2)

        d.append(draw.Line(
            x1, y1, x2, y2, 
            stroke=grad_url, 
            stroke_width=SIZE_MAP.get(link.get("size", "S"), 2), 
            stroke_dasharray=TYPE_MAP.get(link.get("type", "solid"))
        ))
    except KeyError as e:
        print(f"Skipping link: missing node reference {e}")

def render_galileo(galaxy_nodes, galaxy_arcs, galaxy_links):
    """Main entry point: Renders background, then connections, then nodes."""
    d = draw.Drawing(W, H, origin="center")
    
    # Background
    d.append(draw.Rectangle(-W/2, -H/2, W, H, fill="#1a1a1a")) 
    
    # 1. Arcs (Curves)
    for i, arc in enumerate(galaxy_arcs): 
        render_arc(d, galaxy_nodes, arc, i)
        
    # 2. Links (Straight Lines)
    for i, link in enumerate(galaxy_links):
        render_link(d, galaxy_nodes, link, i)
        
    # 3. Nodes (Always last so they appear on top)
    for node_id, attrs in galaxy_nodes.items(): 
        render_node(d, node_id, attrs)
        
    return d.as_svg()