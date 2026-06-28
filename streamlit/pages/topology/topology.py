import streamlit as st
import streamlit.components.v1 as components
import drawsvg as draw
import math

# --- CORE GALILEO ENGINE (Your original code) ---
W, H = 900, 800
NODE_COLORS = {
    1: "#ef4444", 2: "#f59e0b", 3: "#22c55e", 4: "#3b82f6",
    5: "#ef444480", 6: "#f59e0b80", 7: "#22c55e80", 8: "#3b82f680",
}
SIZE_MAP = {"XS": 1, "S": 2, "M": 4, "L": 6, "XL": 8}
TYPE_MAP = {"solid": None, "dash": "5,5", "double-dash": "2,2"}

def get_pos(radius, angle_deg):
    theta = math.radians(angle_deg - 90)
    return radius * math.cos(theta), radius * math.sin(theta)

def render_node(d, node_id, attrs):
    if not attrs.get("visible", True): return
    nx, ny = (0, 0) if attrs["radius"] == 0 else get_pos(attrs["radius"], attrs["angle"])
    colors = attrs.get("colors", [7, 3])
    outer_color, inner_color = NODE_COLORS.get(colors[0], "#64748b"), NODE_COLORS.get(colors[1], "#0f172a")
    d.append(draw.Circle(nx, ny, attrs.get("size_outer", 15), fill=outer_color))
    d.append(draw.Circle(nx, ny, attrs.get("size_inner", 10), fill=inner_color, stroke="black"))
    d.append(draw.Text(attrs.get("label_header", ""), 12, nx, ny + attrs.get("size_outer", 15) + 10, fill="white", text_anchor="middle"))

def render_arc(d, n1, n2, attrs):
    x1, y1 = get_pos(n1["radius"], n1["angle"])
    x2, y2 = get_pos(n2["radius"], n2["angle"])
    p = draw.Path(stroke=NODE_COLORS.get(attrs.get("colors", [8,4])[0]), stroke_width=SIZE_MAP.get(attrs.get("size", "S")), fill="none", stroke_dasharray=TYPE_MAP.get(attrs.get("type", "solid")))
    p.M(x1, y1).A(n1["radius"], n1["radius"], 0, 0, 1, x2, y2)
    d.append(p)

def render_galileo(galaxy_nodes, galaxy_arcs, galaxy_links):
    d = draw.Drawing(W, H, origin="center")
    d.append(draw.Rectangle(-W/2, -H/2, W, H, fill="#1a1a1a")) # Dark background
    for arc in galaxy_arcs: render_arc(d, galaxy_nodes[arc["source"]], galaxy_nodes[arc["target"]], arc)
    for node_id, attrs in galaxy_nodes.items(): render_node(d, node_id, attrs)
    return d.as_svg()

# --- STREAMLIT APP ---
st.set_page_config(page_title="Galileo Solar System", layout="wide")

st.title("🌌 Galileo Topology: Solar System")
st.write("A 3-planet orbital model rendered using the Galileo engine.")

# Define the Solar System Data
nodes = {
    0: {"radius": 0, "angle": 0, "colors": [6, 2], "size_outer": 40, "size_inner": 30, "label_header": "SUN"},
    1: {"radius": 120, "angle": 45, "colors": [5, 1], "size_outer": 15, "size_inner": 8, "label_header": "Inner Planet"},
    2: {"radius": 220, "angle": 180, "colors": [7, 3], "size_outer": 20, "size_inner": 12, "label_header": "Middle Planet"},
    3: {"radius": 320, "angle": 300, "colors": [8, 4], "size_outer": 25, "size_inner": 15, "label_header": "Outer Planet"},
}

# Add orbital paths (Arcs that loop back to themselves or show the path)
arcs = [
    {"source": 1, "target": 1, "colors": [5, 5], "size": "XS", "type": "dash"}, # Visual guide
    {"source": 2, "target": 2, "colors": [7, 7], "size": "XS", "type": "dash"},
    {"source": 3, "target": 3, "colors": [8, 8], "size": "XS", "type": "dash"},
]

# Generate SVG
svg_code = render_galileo(nodes, arcs, [])

# Display in Streamlit
components.html(svg_code, height=800)

st.info("The visualization is generated as a native SVG string and embedded via an iframe.")