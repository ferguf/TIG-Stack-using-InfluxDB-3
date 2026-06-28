import streamlit as st
import re
import pandas as pd

from src.ui_components import UI
from src.utils.api_network import (
    get_devices_by_short_name,
    get_network_links_detail
)
# Import rendering engines
from src.galileo.plotly_galileo import (
    render_galileo_plotly, 
    render_galileo_template
)
# Import the Registry to automate the UI selection list

from src.galileo.galileo_templates import LayoutRegistry
def apply_intercity_layout(nodes):
    """
    Calculates coordinates for Intercity nodes.
    Uses a larger radius (600+) to accommodate city labels.
    """
    pos_cache = {}
    sites = list(nodes.keys())
    radius = 600 
    
    for i, nid in enumerate(sites):
        import math
        # Distribute nodes evenly in a circle
        angle_deg = (360 / len(sites)) * i - 90
        theta = math.radians(angle_deg)
        
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        pos_cache[str(nid)] = (x, y)
        
    return pos_cache

def render_intercity_explorer(galaxy_nodes=None, galaxy_links=None):
    """
    Main entry point for Intercity visualization.
    If no data is passed, it generates/fetches global backbone data.
    """
    st.subheader("🌐 Intercity Backbone Explorer")

    # 1. Fallback / Mock Data if arguments are missing
    if galaxy_nodes is None:
        # Example Intercity Nodes (Cities)
        galaxy_nodes = {
            "NYC": {"label_header": "NEW YORK", "device_role": "HUB", "colors": [7, 7], "opacity": 1.0},
            "DEN": {"label_header": "DENVER", "device_role": "HUB", "colors": [7, 5], "opacity": 1.0},
            "LON": {"label_header": "LONDON", "device_role": "GATEWAY", "colors": [4, 7], "opacity": 1.0},
            "SIN": {"label_header": "SINGAPORE", "device_role": "GATEWAY", "colors": [7, 7], "opacity": 1.0}
        }
    
    if galaxy_links is None:
        # Example Backbone Links between Cities
        galaxy_links = [
            {"source": "NYC", "target": "DEN", "colors": [7, 1, 7], "width": "l", "style": "solid"},
            {"source": "NYC", "target": "LON", "colors": [7, 1, 4], "width": "l", "style": "solid"},
            {"source": "LON", "target": "SIN", "colors": [4, 1, 7], "width": "l", "style": "solid"}
        ]

    # 2. View Options
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("### ⚙️ View Settings")
        show_links = st.checkbox("Show Intercity Links", value=True)
        layout_type = st.selectbox("Global Layout", ["Circular", "Geographic Projection"])

    # 3. Render
    st.write("### 🔭 Intercity Topology")
    
    # Use the existing plotly renderer (ensure galaxy_orbits is [] if not used)
    # We filter links based on the toggle
    active_links = galaxy_links if show_links else []
    
    from src.galileo.plotly_galileo import render_galileo_plotly
    fig = render_galileo_plotly(galaxy_nodes, [], active_links)
    
    st.plotly_chart(fig, use_container_width=True, key="intercity_viz_canvas")

    # 4. Troubleshooting Inspector
    with st.expander("🛠️ Intercity JSON Debugger"):
        st.json({"nodes": galaxy_nodes, "links": galaxy_links})