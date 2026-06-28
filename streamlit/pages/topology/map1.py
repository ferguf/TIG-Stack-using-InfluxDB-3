import streamlit as st
from src.galileo.svg_galileo import render_galileo

def show_gateway(topology_id):
    st.subheader(f"🌐 Gateway Settings for {topology_id}")
    if "gateway_label" not in st.session_state:
        st.session_state["gateway_label"] = f"GW-{topology_id}"
    st.text_input("Gateway Label", key="gateway_label")

def show_topology(topology_id):
    st.subheader("🚀 Metro Network Map")
    
    # 1. Initialize the variable to None to avoid UnboundLocalENodeor
    svg_str = None 
    
    label = st.session_state.get("gateway_label", "topology_id")

    # 2. Prepare Data
    nodes = {
        0: {"radius": 0, "colors":[5,3],   "angle": 0, "label_header": "The Sun"},
        1: {"radius": 160, "colors":[4,8], "angle": 45, "label_header": "Earth"},
        2: {"radius": 190, "colors":[6,3], "angle": 50, "label_header": "Moon", "size": "XS"},
        3: {"radius": 160, "colors":[3,6], "angle": 180, "label_header": "Mars"},
        4: {"radius": 280, "colors":[7,2], "angle": 315, "label_header": "Saturn"},
    }
    links = [
            {"source": 0, "colors": [1,2], "target": 1},
            {"source": 0, "colors": [3,4], "target": 3},
            {"source": 0, "colors": [5,6], "target": 4},
            {"source": 1, "colors": [7,8], "target": 2 , "size": "XS", "type": "dash"},
            {"source": 4, "colors": [7,8], "target": 2 , "size": "XS", "type": "dash"},
            ]

    # 3. Try to generate the SVG
    try:
        svg_str = render_galileo(nodes, [], links)
    except Exception as e:
        st.error(f"Engine failed to run: {e}")

    # 4. Render only if svg_str was successfully assigned
    if svg_str:
        # Check length for debugging
        st.write(f"SVG Length: {len(svg_str)}")
        
        # 2025-compliant: Replaces use_container_width=True
        st.image(svg_str, width='stretch')
    else:
        st.warning("No SVG was generated. Check terminal for import eNodeors.")
        
      
def show_pop(topology_id):
    st.subheader("🚀 Route Vision")
    
    # 1. Initialize the variable to None to avoid UnboundLocalENodeor
    svg_str = None 
    
    label = st.session_state.get("gateway_label", "topology_id")

    # 2. Prepare Data
    nodes = {
        1: {"radius": 200, "angle": 60, "colors": [5, 4], "size_outer": 15, "size_inner": 10, "label_header": "site1"},
        2: {"radius": 200, "angle": 120, "colors": [5, 4], "size_outer": 15, "size_inner": 10, "label_header": "site2"},
        3: {"radius": 200, "angle": 180, "colors": [5, 4], "size_outer": 15, "size_inner": 10, "label_header": "site3"},
        4: {"radius": 200, "angle": 220, "colors": [5, 4], "size_outer": 15, "size_inner": 10, "label_header": "site4"},
        5: {"radius": 200, "angle": 360, "colors": [5, 4], "size_outer": 15, "size_inner": 10, "label_header": "site5"},
        6: {"radius": 200, "angle": 280, "colors": [5, 4], "size_outer": 15, "size_inner": 10, "label_header": "site6"},
    }
    links = [
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 4},
            {"source": 2, "colors": [5, 5], "size": "m", "type": "solid", "target": 4},
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 3},
            {"source": 2, "colors": [5, 5], "size": "m", "type": "solid", "target": 3},
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 4},
            {"source": 2, "colors": [5, 5], "size": "m", "type": "solid", "target": 5},
            {"source": 3, "colors": [5, 5], "size": "m", "type": "solid", "target": 4},
            {"source": 3, "colors": [5, 5], "size": "m", "type": "solid", "target": 5},            
            {"source": 6, "colors": [5, 5], "size": "m", "type": "solid", "target": 1},  
            {"source": 6, "colors": [5, 5], "size": "m", "type": "solid", "target": 2},  
    ]
    arcs = [
            {"source": 1, "target": 1, "visible": False, "colors": [5, 6], "size": "XS", "type": "dash"}, # Visual guide
        ]
    
    # 3. Try to generate the SVG
    try:
        svg_str = render_galileo(nodes, arcs, links)
    except Exception as e:
        st.error(f"Engine failed to run: {e}")

    # 4. Render only if svg_str was successfully assigned
    if svg_str:
        # Check length for debugging
        st.write(f"SVG Length: {len(svg_str)}")
        
        # 2025-compliant: Replaces use_container_width=True
        st.image(svg_str, width='stretch')
    else:
        st.warning("No SVG was generated. Check terminal for import eNodeors.")
    st.subheader("🚀 Metro Network Map")
    
    # 1. Initialize the variable to None to avoid UnboundLocalENodeor
    svg_str = None 
    
    label = st.session_state.get("gateway_label", "topology_id")

    # 2. Prepare Data

    nodes = {
        1: {"radius": 0, "angle": 0, "colors": [5, 6], "size_outer": 15, "size_inner": 20, "label_header": "IPVPN"},
        2: {"radius": 200, "angle": 0, "colors": [5, 6], "size_outer": 15, "size_inner": 10, "label_header": "site2"},
        3: {"radius": 200, "angle": 60, "colors": [5, 6], "size_outer": 15, "size_inner": 10, "label_header": "site3"},
        4: {"radius": 200, "angle": 120, "colors": [5, 6], "size_outer": 15, "size_inner": 10, "label_header": "site4"},
        5: {"radius": 200, "angle": 180, "colors": [5, 6], "size_outer": 15, "size_inner": 10, "label_header": "site5"},
        6: {"radius": 200, "angle": 280, "colors": [7, 6], "size_outer": 15, "size_inner": 10, "label_header": "site6"},
        7: {"radius": 200, "angle": 260, "colors": [7, 6], "size_outer": 15, "size_inner": 10, "label_header": "site6"},
    }
    links = [
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 2},
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 3},
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 4},
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 5},
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 6},
            {"source": 1, "colors": [5, 5], "size": "m", "type": "solid", "target": 7},
    ]
    arcs = [
            {"source": 1, "target": 1, "visible": False, "colors": [5, 6], "size": "XS", "type": "dash"}, # Visual guide
        ]
  
    # 3. Try to generate the SVG
    try:
        svg_str = render_galileo(nodes, arcs , links)
    except Exception as e:
        st.error(f"Engine failed to run: {e}")

    # 4. Render only if svg_str was successfully assigned
    if svg_str:
        # Check length for debugging
        st.write(f"SVG Length: {len(svg_str)}")
        
        # 2025-compliant: Replaces use_container_width=True
        st.image(svg_str, width='stretch')
    else:
        st.warning("No SVG was generated. Check terminal for import eNodeors.")
 
      
def show_ring(topology_id):
    st.subheader("🚀 Route Vision")
    
    # 1. Initialize the variable to None to avoid UnboundLocalENodeor
    svg_str = None 
    
    label = st.session_state.get("gateway_label", "topology_id")

    # 2. Prepare Data
    nodes = {
        1: {"radius": 270, "angle": 80, "colors": [5, 6], "size_outer": 15, "size_inner": 10, "label_header": "GW1.DEN1"},
        2: {"radius": 270, "angle": 100, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "GW2.DEN1"},
        3: {"radius": 200, "angle": 0, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node3.DEN1"},
        4: {"radius": 200, "angle": 270, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node4.DEN1"},
        5: {"radius": 200, "angle": 180, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node5.DEN1"},
        6: {"radius": 250, "angle": 350, "colors": [1, 3], "size_outer": 15, "size_inner": 10,"label_header": "Node6.DEN1"},
        7: {"radius": 250, "angle": 300, "colors": [1, 3], "size_outer": 15, "size_inner": 10,"label_header": "Node7.DEN1"},
        8: {"radius": 250, "angle": 250, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node8.PHX1"},
        9: {"radius": 250, "angle": 200, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node9.CHI1"},
        10: {"radius": 250, "angle":150, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node10.DAL1"},

    }
    links = [
            {"source": 1, "colors": [5, 6], "size": "L", "type": "solid", "target": 2},
            {"source": 1, "colors": [5, 6], "size": "L", "type": "solid", "target": 3}, 
            {"source": 3, "colors": [5, 6], "size": "L", "type": "solid", "target": 4},
            {"source": 4, "colors": [5, 6], "size": "L", "type": "solid", "target": 5},
            {"source": 5, "colors": [5, 6], "size": "L", "type": "solid", "target": 2},
            # {"source": 6, "colors": [5, 6], "size": "L", "type": "solid", "target": 1},
            # {"source": 7, "colors": [5, 6], "size": "L", "type": "solid", "target": 6},
            # {"source": 8, "colors": [5, 6], "size": "L", "type": "solid", "target": 7},
            # {"source": 9, "colors": [5, 6], "size": "L", "type": "solid", "target": 8},
            # {"source": 9, "colors": [5, 6], "size": "L", "type": "solid", "target": 8},
            # {"source": 10, "colors": [5, 6], "size": "L", "type": "solid", "target": 9},
            # {"source": 2, "colors": [5, 6], "size": "L", "type": "solid", "target": 10},
             ]
    arcs = [
            # {"source": 1, "colors": [1, 5], "size": "L", "type": "solid", "target": 2},
            # {"source": 1, "colors": [5, 6], "size": "L", "type": "solid", "target": 3}, 
            # {"source": 3, "colors": [5, 6], "size": "L", "type": "solid", "target": 4},
            # {"source": 4, "colors": [5, 6], "size": "L", "type": "solid", "target": 5},
            # {"source": 5, "colors": [5, 6], "size": "L", "type": "solid", "target": 2},
            {"source": 6, "colors": [5, 6], "size": "L", "type": "solid", "target": 1},
            {"source": 7, "colors": [1, 2], "size": "L", "type": "solid", "target": 6},
            {"source": 8, "colors": [5, 6], "size": "L", "type": "solid", "target": 7},
            {"source": 9, "colors": [5, 6], "size": "L", "type": "solid", "target": 8},
            {"source": 9, "colors": [5, 6], "size": "L", "type": "solid", "target": 8},
            {"source": 10, "colors": [5, 6], "size": "L", "type": "solid", "target": 9},
            {"source": 2, "colors": [6, 6], "size": "L", "type": "solid", "target": 10},
             ]
    
    # 3. Try to generate the SVG
    try:
        svg_str = render_galileo(nodes, arcs, links)
    except Exception as e:
        st.error(f"Engine failed to run: {e}")

    # 4. Render only if svg_str was successfully assigned
    if svg_str:
        # Check length for debugging
        st.write(f"SVG Length: {len(svg_str)}")
        
        # 2025-compliant: Replaces use_container_width=True
        st.image(svg_str, width='stretch')
    else:
        st.warning("No SVG was generated. Check terminal for import eNodeors.") 
 
def show_route_vision(topology_id):
    st.subheader("🚀 Route Vision")
    
    # 1. Initialize the variable to None to avoid UnboundLocalENodeor
    svg_str = None 
    
    label = st.session_state.get("gateway_label", "topology_id")

    # 2. Prepare Data
    nodes = {
        1: {"radius": 200, "angle": 320, "colors": [1, 2], "size_outer": 15, "size_inner": 10, "label_header": "site1"},
        2: {"radius": 200, "angle": 270, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "VAR2.DEN1"},
        3: {"radius": 200, "angle": 200, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "VAR3.DEN1"},
        4: {"radius": 80, "angle": 60, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node1.DEN1"},
        5: {"radius": 80, "angle": 120, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node2.DEN1"},
        6: {"radius": 200, "angle": 80, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node1.DEN1"},
        7: {"radius": 200, "angle": 100, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node2.DEN1"},
        8: {"radius": 350, "angle": 30, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node1.PHX1"},
        9: {"radius": 350, "angle": 10, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node2.CHI1"},
        10: {"radius": 350, "angle": 160, "colors": [5, 6], "size_outer": 15, "size_inner": 10,"label_header": "Node1.DAL1"},

    }
    links = [
            {"source": 1, "colors": [1, 5], "size": "L", "type": "solid", "target": 4},
            {"source": 1, "colors": [5, 6], "size": "L", "type": "solid", "target": 5}, 
            {"source": 2, "colors": [5, 6], "size": "L", "type": "solid", "target": 5},
            {"source": 2, "colors": [5, 6], "size": "L", "type": "solid", "target": 4},
            {"source": 3, "colors": [5, 6], "size": "L", "type": "solid", "target": 5},
            {"source": 3, "colors": [5, 6], "size": "L", "type": "solid", "target": 4},
            {"source": 6, "colors": [5, 6], "size": "L", "type": "solid", "target": 4},
            {"source": 6, "colors": [5, 6], "size": "L", "type": "solid", "target": 5},
            {"source": 7, "colors": [5, 6], "size": "L", "type": "solid", "target": 4},
            {"source": 7, "colors": [5, 6], "size": "L", "type": "solid", "target": 5},
            {"source": 8, "colors": [5, 6], "size": "XL", "type": "solid", "target": 4},
            {"source": 9, "colors": [5, 6], "size": "XL", "type": "solid", "target": 5},
            {"source": 10, "colors": [5, 6], "size": "XL", "type": "solid", "target": 5},
            {"source": 4, "colors": [5, 6], "size": "XL", "type": "solid", "target": 5},
             ]
    arcs = [
            {"source": 1, "target": 6, "visible": True, "radius": 600, "colors": [5, 6], "size": "XS", "type": "dash"}, # Visual guide
            {"source": 7, "target": 1, "radius": 600, "colors": [7, 7], "size": "XS", "type": "dash"},
            {"source": 2, "target": 6, "colors": [8, 8], "size": "XS", "type": "dash"},
            {"source": 7, "target": 2, "colors": [8, 8], "size": "XS", "type": "dash"},
            {"source": 3, "target": 6, "colors": [8, 8], "size": "XS", "type": "dash"},
            {"source": 7, "target": 3, "colors": [8, 8], "size": "XS", "type": "dash"},
        ]
    
    # 3. Try to generate the SVG
    try:
        svg_str = render_galileo(nodes, arcs, links)
    except Exception as e:
        st.error(f"Engine failed to run: {e}")

    # 4. Render only if svg_str was successfully assigned
    if svg_str:
        # Check length for debugging
        st.write(f"SVG Length: {len(svg_str)}")
        
        # 2025-compliant: Replaces use_container_width=True
        st.image(svg_str, width='stretch')
    else:
        st.warning("No SVG was generated. Check terminal for import eNodeors.")