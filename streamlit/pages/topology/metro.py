import streamlit as st
from src.galileo.plotly_draw import PlotlyDraw
from src.ui_components import UI

class metro:
    def __init__(self):
        self.drawer = PlotlyDraw()

    def show_topology(self, topo_id):
            # Named geometric orbits
            test_orbits = [
                {"id": "O1", "type": "circle", "rx": 200, "color": "red", "style": "solid", "width": "xs"},
                {"id": "O2", "type": "square", "rx": 250, "color": "blue", "style": "solid", "width": "x"},
                {"id": "O3", "type": "triangle", "rx": 300, "color": "green", "style": "dash", "width": "m"},
                {"id": "O4", "type": "circle", "rx": 350, "color": "white", "style": "dotdash", "width": "l"},
                {"id": "O5", "type": "hexagon", "rx": 450, "color": "white", "style": "dash", "width": "xl"},
                {"id": "O_ELLIPSE","type": "ellipse", "rx": 700, "ry": 300, "color": "green", "style": "solid", "width": "m"}
            ]
            
            test_nodes = {
                # --- FIRST SET (Existing + Adjusted) ---
                "G1-SUN": {
                    "node_type": "sun", "label_header": "CORE-CLUSTER", "colors": [1, 2]
                },
                "G1-O1-P1": {
                    "node_type": "planet", "orbit": "O1", "mins": 45, # West (9 o'clock)
                    "label_header": "DIST-A", "colors": [3, 4]
                },
                "G1-O1-P1-M1": {
                    "node_type": "moon", "radius": 100, "mins": 0, # North of P1 (12 o'clock)
                    "label_header": "ACCESS-A1", "colors": [5, 6]
                },

                # --- SECOND SET (New Branch) ---
                # Planet on the South side of the inner ring
                "G1-O2-P2": {
                    "node_type": "planet", "orbit": "O1", "mins": 55, # SOUTH (6 o'clock)
                    "label_header": "DIST-B", "colors": [3, 4]
                },
                # Planet on the East side of the outer hexagon
                "G1-O2-P1": {
                    "node_type": "planet", "orbit": "O2", "mins": 15, # EAST (3 o'clock)
                    "label_header": "REMOTE-C", "colors": [7, 8]
                },
                # Moon orbiting the new Remote-C planet
                "G1-O2-P1-M1": {
                    "node_type": "moon", "radius": 80, "mins": 15, # East of its planet
                    "label_header": "ACCESS-C1", "colors": [5, 6]
                }
            }
            
            test_links = [
                # Links for First Set
                {"source": "G1-SUN", "target": "G1-O1-P1", "colors": [1, 3]},
                {"source": "G1-O1-P1", "target": "G1-O1-P1-M1", "colors": [3, 5]},
                
                # Links for Second Set
                {"source": "G1-SUN", "target": "G1-O1-P2", "colors": [1, 3]},
                {"source": "G1-O2-P2", "target": "G1-O2-P1", "colors": [3, 7]},
                {"source": "G1-O2-P1", "target": "G1-O2-P1-M1", "colors": [7, 5]}
            ]

            self.drawer.show_topology(test_nodes, test_orbits, test_links, topo_id, key_prefix="metro")
            UI.display_topology_debug(test_nodes, test_orbits, test_links, key_prefix="metro")