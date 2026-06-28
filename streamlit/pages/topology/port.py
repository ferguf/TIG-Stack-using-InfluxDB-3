import streamlit as st
from src.galileo.plotly_draw import PlotlyDraw
from src.ui_components import UI

class PortTopology:
    def __init__(self):
        self.drawer = PlotlyDraw()

    def show_topology(self, topo_id):
        st.subheader(f"🌐 Galileo Advanced Fabric Dashboard - {topo_id}")

        # --- ORBIT DEFINITIONS ---
        orbits_extended_1 = [
            {"id":"O1","type":"circle","rx":350,"color":"GREEN","style":"NONE","width":"xs"},
            {"id": "O_ELAN", "type": "circle", "size": "XL", "rx": 1}
        ]

        orbits_extended = [
            {"id":"O1","type":"circle","rx":350,"color":"GREEN","style":"NONE","width":"xs"},
            {"id":"O2","type":"circle","rx":200,"color":"blue","style":"solid","width":"xs"},
            {"id": "O_ELAN", "type": "circle", "size": "XL", "rx": 1}
        ]


        # --- DATASET: E-LAN MULTIPOINT FABRIC (Fault Injection Test) ---
        nodes_elan = {
            "E-LAN": {
                "node_type": "sun", 
                "label_header": "E-LAN Service", 
                "colors": [1,6], # Green Hub
                "orbit": "O_ELAN", 
                "size": "sun"
            },
            "EP-01": {"orbit": "O1", "mins": 60, "label_header": "Headquarters", "colors": [1, 1, 1], "size": "xl"},
            "EP-02": {"orbit": "O1", "mins": 8,  "label_header": "Denver", "colors": [1, 1, 1], "size": "m"},
            
            # 🔥 SITE-C is now RED (Critical Alert)
            "EP-03": {"orbit": "O1", "mins": 16, "label_header": "Seattle", "colors": [7, 7, 7], "size": "m"},
            
            "EP-04": {"orbit": "O1", "mins": 24, "label_header": "Portland", "colors": [1, 1, 1], "size": "s"},
            "EP-05": {"orbit": "O1", "mins": 32, "label_header": "LA", "colors": [1, 1, 1], "size": "m"},
            "EP-06": {"orbit": "O1", "mins": 40, "label_header": "NYC", "colors": [5, 6], "size": "m"},
            "EP-07": {"orbit": "O1", "mins": 48, "label_header": "Dallas", "colors": [3, 4], "size": "s"}
        }
        
        # Enhanced Link Generation with Specific Fault Logic
        links_elan = []
        for k in nodes_elan:
            if k == "E-LAN":
                continue
            
            # 🚨 If target is SITE-C, make the middle link segment (Path) RED (ID 7)
            if k == "EP-03":
                l_colors = [1, 7, 7] # [Green Source, Red Path, Red Target]
            else:
                l_colors = [1, 1, 1] # [All Green]
                
            links_elan.append({
                "source": "E-LAN", 
                "target": k, 
                "type": "line", 
                "colors": l_colors
            })
        # --- DATASET 2: HIERARCHICAL CLUSTER (G1 Nodes) ---
        nodes_g1 = {
            "G1-SUN": {"node_type": "sun", "label_header": "CORE-CLUSTER", "colors": [1, 2], "size": "XL"},
            "G1-O1-P1": {"node_type": "planet", "orbit": "O1", "mins": 45, "label_header": "DIST-A", "colors": [1, 2], "size": "m"},
            "G1-O1-P1-M1": {"node_type": "moon", "radius": 100, "mins": 0, "label_header": "ACCESS-A1", "colors": [2, ], "size": "m"},
            "G1-O2-P2": {"node_type": "planet", "orbit": "O1", "mins": 24, "label_header": "DIST-B", "colors": [3, 4], "size": "m"},
            "G1-O2-P1": {"node_type": "planet", "orbit": "O2", "mins": 15, "label_header": "REMOTE-C", "colors": [3, 8], "size": "m"},
            "G1-O2-P1-M1": {"node_type": "moon", "radius": 80, "mins": 15, "label_header": "ACCESS-C1", "colors": [5, 6], "size": "m"}
        }

        links_g1 = [
            {"source": "G1-SUN", "target": "G1-O1-P1", "colors": [1, 3, 3]},
            {"source": "G1-O1-P1", "target": "G1-O1-P1-M1", "colors": [3, 5, 5]},
            {"source": "G1-O2-P2", "target": "G1-O2-P1", "colors": [3, 7, 7]},
            {"source": "G1-O2-P1", "target": "G1-O2-P1-M1", "colors": [7, 5, 5]}
        ]

        # --- RENDERING ---
        st.write("### 💠 E-LAN Fabric Service")
        self.drawer.show_topology(nodes_elan, orbits_extended_1, links_elan, topo_id, key_prefix="elan_xl")

        st.divider()

        st.write("### 💠 Single E-line EPL")
        self.drawer.show_topology(nodes_elan, orbits_extended_1, links_elan, topo_id, key_prefix="eline_1")

        st.divider()

        st.write("### 💠 Single E-line EPL")
        self.drawer.show_topology(nodes_elan, orbits_extended_1, links_elan, topo_id, key_prefix="eline_2")

        st.divider()

        
        st.write("### 🛰️ Core/Access Cluster (XL Hierarchy)")
        self.drawer.show_topology(nodes_g1, orbits_extended, links_g1, topo_id, key_prefix="g1_xl")

if __name__ == "__main__":
    p = PortTopology()
    p.show_topology("COLOR-STRESS-TEST")