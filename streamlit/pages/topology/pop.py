import streamlit as st
from src.galileo.plotly_draw import PlotlyDraw
from src.ui_components import UI

class pop:
    def __init__(self):
        # Initializing the same drawer engine as metro
        self.drawer = PlotlyDraw()

    def show_topology(self, topo_id):
        """
        Executes the Point of Presence (PoP) Topology logic.
        Structure is kept identical to the metro class for dashboard compatibility.
        """
        # --- 1. GEOMETRIC ORBITS ---
        # Tailored for PoP specific layout (Square/Triangle testing)
# --- GEOMETRIC ORBITS ---
# All nodes had radius 200, so we create one orbit for them.
        test_orbits = [
            {
                "id": "O1", 
                "type": "circle", 
                "rx": 200, 
                "ry": 200, 
                "color": "green", 
                "style": "solid", 
                "width": "m"
            }
        ]

        # --- NODES ---
        # Mapping your numeric keys to strings and assigning them to Orbit O1
        test_nodes = {
            "SITE-1": {"node_type": "planet", "orbit": "O1", "angle": 60, "label_header": "site1", "colors": [5, 4]},
            "SITE-2": {"node_type": "planet", "orbit": "O1", "angle": 120, "label_header": "site2", "colors": [5, 4]},
            "SITE-3": {"node_type": "planet", "orbit": "O1", "angle": 180, "label_header": "site3", "colors": [5, 4]},
            "SITE-4": {"node_type": "planet", "orbit": "O1", "angle": 220, "label_header": "site4", "colors": [5, 4]},
            "SITE-5": {"node_type": "planet", "orbit": "O1", "angle": 360, "label_header": "site5", "colors": [5, 4]},
            "SITE-6": {"node_type": "planet", "orbit": "O1", "angle": 280, "label_header": "site6", "colors": [5, 4]},
        }

        # --- LINKS ---
        # Updated source/target to match the new string-based Node IDs
        test_links = [
            {"source": "SITE-1", "target": "SITE-4", "colors": [5, 5]},
            {"source": "SITE-2", "target": "SITE-4", "colors": [5, 5]},
            {"source": "SITE-1", "target": "SITE-3", "colors": [5, 5]},
            {"source": "SITE-2", "target": "SITE-3", "colors": [5, 5]},
            {"source": "SITE-2", "target": "SITE-5", "colors": [5, 5]},
            {"source": "SITE-3", "target": "SITE-4", "colors": [5, 5]},
            {"source": "SITE-3", "target": "SITE-5", "colors": [5, 5]},
            {"source": "SITE-6", "target": "SITE-1", "colors": [5, 5]},
            {"source": "SITE-6", "target": "SITE-2", "colors": [5, 5]},
        ]

        # --- DATA SET 1 (IMAGE 1) ---
        orbits_1 = [
            {"id": "O1", "type": "circle", "rx": 200, "ry": 200, "color": "red", "style": "solid", "width": "m"}
        ]
        nodes_1 = {
            "SITE-1": {"node_type": "planet", "orbit": "O1", "angle": 60, "label_header": "Site 1", "colors": [1, 2]},
            "SITE-2": {"node_type": "planet", "orbit": "O1", "angle": 180, "label_header": "Site 2", "colors": [1, 2]}
        }
        links_1 = [{"source": "SITE-1", "target": "SITE-2", "colors": [2, 3]}]

        # --- DATA SET 2 (IMAGE 2) ---
        orbits_2 = [
            {"id": "O2", "type": "square", "rx": 250, "ry": 250, "color": "blue", "style": "dash", "width": "m"}
        ]
        nodes_2 = {
            "CORE-A": {"node_type": "planet", "orbit": "O2", "angle": 90, "label_header": "HUB-A", "colors": [7, 8]},
            "REMOTE-A": {"node_type": "planet", "orbit": "O2", "angle": 270, "label_header": "REMOTE-A", "colors": [5, 6]}
        }
        links_2 = [{"source": "CORE-A", "target": "REMOTE-A", "colors": [1, 6]}]


# 1. Define Orbits based on your unique Radii
        Metro_orbits = [
            {"id": "ORB_200", "rx": 200, "type": "circle", "style": "none", "width": 1, "color": "rgba(255,255,255,0.1)"},
            {"id": "ORB_250", "rx": 250, "type": "circle", "style": "none", "width": 1, "color": "rgba(255,255,255,0.1)"},
            {"id": "ORB_270", "rx": 270, "type": "circle", "style": "dash", "width": 1, "color": "rgba(255,255,255,0.1)"},
        ]

        # 2. Map Nodes to Orbits and Angles
        Metro_nodes = {
            "1": {"orbit": "ORB_270", "angle": 80,  "colors": [5, 6], "node_type": "planet", "label_header": "GW1.DEN1"},
            "2": {"orbit": "ORB_270", "angle": 100, "colors": [5, 6], "node_type": "planet", "label_header": "GW2.DEN1"},
            "3": {"orbit": "ORB_200", "angle": 0,   "colors": [5, 6], "node_type": "planet", "label_header": "Node3.DEN1"},
            "4": {"orbit": "ORB_200", "angle": 270, "colors": [5, 6], "node_type": "planet", "label_header": "Node4.DEN1"},
            "5": {"orbit": "ORB_200", "angle": 180, "colors": [5, 6], "node_type": "planet", "label_header": "Node5.DEN1"},
            "6": {"orbit": "ORB_250", "angle": 350, "colors": [1, 3], "node_type": "planet", "label_header": "Node6.DEN1"},
            "7": {"orbit": "ORB_250", "angle": 300, "colors": [1, 3], "node_type": "planet", "label_header": "Node7.DEN1"},
            "8": {"orbit": "ORB_250", "angle": 250, "colors": [5, 6], "node_type": "planet", "label_header": "Node8.PHX1"},
            "9": {"orbit": "ORB_250", "angle": 200, "colors": [5, 6], "node_type": "planet", "label_header": "Node9.CHI1"},
            "10": {"orbit": "ORB_250", "angle": 150, "colors": [5, 6], "node_type": "planet", "label_header": "Node10.DAL1"},
        }

        # 3. Merged Links and Arcs with Segmented Colors
        Metro_links = [
            # Straight Links (from your links list)
            {"source": "1", "target": "2", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "1", "target": "3", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "3", "target": "4", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "4", "target": "5", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "5", "target": "2", "colors": [5, 6], "type": "line", "width": 3},
            
            # Arced Links (from your arcs list)
            {"source": "6", "target": "1", "colors": [5, 6], "type": "arc", "bend": -0.2, "width": 3},
            {"source": "7", "target": "6", "colors": [1, 2], "type": "arc", "bend": -0.2, "width": 3}, # Segmented Red/Red-Glow
            {"source": "8", "target": "7", "colors": [5, 6], "type": "arc", "bend": -0.2, "width": 3},
            {"source": "9", "target": "8", "colors": [5, 6], "type": "arc", "bend": -0.2, "width": 3},
            {"source": "10", "target": "9", "colors": [5, 6], "type": "arc", "bend": -0.2, "width": 3},
            {"source": "2", "target": "10", "colors": [6, 6], "type": "arc", "bend": -0.2, "width": 3},
            ]

        # 1. Define Orbits using the MPLS pattern
        MPLS_orbits = [
            {"id": "80_orbit", "rx": 80, "type": "circle", "style": "solid", "width": 3},
            {"id": "200_orbit", "rx": 250, "type": "circle", "style": "dot", "width": 2},
            {"id": "350_orbit", "rx": 450, "type": "circle", "style": "dash", "width": 1},
            {"id": "0_square", "rx": 300, "type": "square", "color": "blue", "style": "solid", "width": 1},
            ]

        # 2. Map Nodes (IDs converted to strings for the engine)
        MPLS_nodes = {
            "1": {
                "orbit": "200_orbit", "angle": 320, "colors": [1, 2], 
                "device_role": "VAR", "label_header": "VAR1.DEN1"
            },
            "2": {
                "orbit": "200_orbit", "angle": 270, "colors": [1, 6], 
                "device_role": "VAR", "label_header": "VAR2.DEN1"
            },
            "3": {
                "orbit": "200_orbit", "angle": 220, "colors": [1, 6], 
                "device_role": "VAR", "label_header": "VAR3.DEN1"
            },
            "4": {
                "orbit": "80_orbit",  "angle": 60,  "colors": [1, 6], 
                "device_role": "SDR", "label_header": "SDR1.DEN1"
            },
            "5": {
                "orbit": "80_orbit",  "angle": 120, "colors": [1, 3], 
                "device_role": "SDR", "label_header": "SDR2.DEN1"
            },
            "6": {
                "orbit": "200_orbit", "angle": 80,  "colors": [1, 2], 
                "device_role": "RR",  "label_header": "RR1.DEN1"
            },
            "7": {
                "orbit": "200_orbit", "angle": 100, "colors": [1, 2], 
                "device_role": "RR",  "label_header": "RR2.DEN1"
            },
            "8": {
                "orbit": "350_orbit", "angle": 20,  "colors": [1, 3], 
                "device_role": "SDR", "label_header": "SDR1.PHX1"
            },
            "9": {
                "orbit": "350_orbit", "angle": 0,   "colors": [1, 1], 
                "device_role": "SDR", "label_header": "SDR2.CHI1"
            },
            "10": {
                "orbit": "350_orbit", "angle": 180, "colors": [1, 1], 
                "device_role": "SDR", "label_header": "SDR1.DAL1"
            },
        }

        # 3. Merged Links and Segmented Arcs
        MPLS_links = [
            # Straight Links (2-color segmented if colors provided)
            {"source": "1", "target": "4", "colors": [1, 5], "type": "line", "width": 3},
            {"source": "1", "target": "5", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "2", "target": "5", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "2", "target": "4", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "3", "target": "5", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "3", "target": "4", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "6", "target": "4", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "6", "target": "5", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "7", "target": "4", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "7", "target": "5", "colors": [5, 6], "type": "line", "width": 3},
            {"source": "8", "target": "4", "colors": [5, 6], "type": "line", "width": 5}, # XL width
            {"source": "9", "target": "5", "colors": [5, 6], "type": "line", "width": 5},
            {"source": "10", "target": "5", "colors": [5, 6], "type": "line", "width": 5},
            {"source": "4", "target": "5", "colors": [5, 6], "type": "line", "width": 5},

            # Arced Links / Visual Guides
            {"source": "1", "target": "6", "colors": [5, 6], "type": "arc", "bend": 0.4, "style": "dash", "width": 1},
            {"source": "7", "target": "1", "colors": [7, 7], "type": "arc", "bend": -0.4, "style": "dash", "width": 1},
            {"source": "2", "target": "6", "colors": [8, 8], "type": "arc", "bend": 0.3, "style": "dash", "width": 1},
            {"source": "7", "target": "2", "colors": [8, 8], "type": "arc", "bend": -0.3, "style": "dash", "width": 1},
            {"source": "3", "target": "6", "colors": [8, 8], "type": "arc", "bend": 0.2, "style": "dash", "width": 1},
            {"source": "7", "target": "3", "colors": [8, 8], "type": "arc", "bend": -0.2, "style": "dash", "width": 1},
        ]

        # --- RENDER IMAGE 1 ---
        st.write("### 🌐 3549 Pop layout using ICONs")
        self.drawer.show_topology(
            MPLS_nodes, 
            MPLS_orbits, 
            MPLS_links, 
            topo_id, 
            key_prefix="MPLS_2"
        )
        UI.display_topology_debug(Metro_nodes, Metro_orbits, Metro_links, key_prefix="MPLS_2")
        st.divider() # Visual separation between images

        # --- RENDER IMAGE 1 ---
        st.write("### 🌐 Metro Rings using arch or links")
        self.drawer.show_topology(
            Metro_nodes, 
            Metro_orbits, 
            Metro_links, 
            topo_id, 
            key_prefix="Metro_2"
        )
        UI.display_topology_debug(Metro_nodes, Metro_orbits, Metro_links, key_prefix="Metro_2")
        st.divider() # Visual separation between images

        # --- RENDER IMAGE 1 ---
        st.write("### 🌐 Eline EPL or EVPL that is having problems")
        self.drawer.show_topology(
            nodes_1, 
            orbits_1, 
            links_1, 
            topo_id, 
            key_prefix="img1_ring"
        )
        UI.display_topology_debug(test_nodes, test_orbits, test_links, key_prefix="image_ring")
        st.divider() # Visual separation between images

        # --- RENDER IMAGE 2 ---
        st.write("### 🟦 Eline EPL")
        self.drawer.show_topology(
            nodes_2, 
            orbits_2, 
            links_2, 
            topo_id, 
            key_prefix="img2_access"
        )
        UI.display_topology_debug(test_nodes, test_orbits, test_links, key_prefix="img_access")
        st.divider() # Visual separation between images
        
        # --- 4. EXECUTE DRAW ---
        # Calls the drawer with identical signature to metro.py
        st.write("### 🟦 E-line EVPL with Multi EVCs")
        self.drawer.show_topology(test_nodes, test_orbits, test_links, topo_id, key_prefix="Metro_1")
        UI.display_topology_debug(test_nodes, test_orbits, test_links, key_prefix="Metro_1")