import streamlit as st
import pandas as pd
from src.galileo.plotly_draw import PlotlyDraw
from src.galileo.galileo_templates import get_base64_image

class DynamicTopology:
    def __init__(self):
        self.drawer = PlotlyDraw()

    def show_builder(self, topo_id="galileo_builder"):
        """Main entry point: Vertical Stack Layout with Automatic Scaling"""
        if "dyn_data" not in st.session_state:
            st.session_state["dyn_data"] = {"nodes": {}, "orbits": [], "links": []}
        
        data = st.session_state["dyn_data"]

        # Container A: The Fabric Architect (Top)
        with st.container(border=True):
            st.header("🛠️ Topology Designer")
            st.info("Orbits can be generated in bulk, Nodes are placed  on an Orbit , Nodes are placed into orbit ,  Links connect Nodes together.")
            t1, t2, t3 = st.tabs(["🪐 Orbits", "🛰️ Nodes", "🔗 Links"])
            
            with t1: self.render_orbit_manager()
            with t2: self.render_node_manager()
            with t3: self.render_link_manager()

        st.write("") 

        # Container B: The Galileo Viewport (Bottom)
        with st.container(border=True, height=750):
            st.header("👁️ Topology Viewer")
            if data["nodes"] or data["orbits"]:
                # The render key helps Streamlit identify if the chart needs a full redraw
                render_key = f"dyn_v_{len(data['orbits'])}_{len(data['nodes'])}_{len(data['links'])}"
                
                # Handshake: Just pass the data. 
                # The drawer's 'scaleanchor' and 'autorange' handle the +100px feel.
                self.drawer.show_topology(
                    data["nodes"], 
                    data["orbits"], 
                    data["links"], 
                    topo_id, 
                    key_prefix=render_key
                )
            else:
                st.info("Start by using the Mass Injection tools or tables above.")
    # =========================================================
    # 1. ORBIT MANAGER
    # =========================================================

    def render_orbit_manager(self):
        data = st.session_state["dyn_data"]
        
        # 1. Power Tools Section
        with st.expander("🚀 Mass Orbit Injection", expanded=False):
            c1, c2, c3 = st.columns(3)
            q_type = c1.selectbox("Shape", ["circle", "square", "triangle", "hexagon"], key="q_orb_type")
            q_count = c2.number_input("How many?", min_value=1, max_value=10, value=1)
            
            # FIXED: Using explicit keywords to avoid positional argument conflict
            q_step = c3.number_input(
                label="Radius Step (px)", 
                min_value=50, 
                max_value=600, 
                value=100, 
                step=50
            )
            
            if st.button("✨ Generate Orbits", use_container_width=True):
                for i in range(q_count):
                    new_r = (len(data['orbits']) + 1) * q_step
                    # Ensure we don't exceed our 600px hard boundary
                    final_r = min(new_r, 600)
                    
                    data["orbits"].append({
                        "id": f"O{len(data['orbits'])+1}", 
                        "type": q_type, "rx": final_r, "ry": final_r,
                        "color": "#3BC55E", "style": "dot", "width": "xs"
                    })
                st.rerun()

        st.divider()

        # 2. Global Actions Row (CRUD)
        st.subheader("Orbit Inventory")
        ga1, ga2 = st.columns([3, 1])
        
        orb_state = st.session_state.get("orb_editor", {})
        sel_orbs = orb_state.get("selection", {}).get("rows", [])
        
        with ga1:
            if sel_orbs:
                if st.button(f"🗑️ Delete {len(sel_orbs)} Selected Orbit(s)", type="primary", use_container_width=True):
                    data["orbits"] = [v for i, v in enumerate(data["orbits"]) if i not in sel_orbs]
                    st.rerun()
            else:
                st.info("Select rows in the table to enable deletion.")

        with ga2:
            if st.button("🧨 Clear All", help="Wipe all orbits", use_container_width=True):
                data["orbits"] = []
                st.rerun()

        # 3. Editable Table (CRUD)
        df_orbits = pd.DataFrame(data["orbits"]) if data["orbits"] else pd.DataFrame(
            columns=["id", "type", "rx", "ry", "color", "style", "width"]
        )
        
        edited_orbits = st.data_editor(
            df_orbits, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="orb_editor",
            column_config={
                "type": st.column_config.SelectboxColumn("Geometry", options=["circle", "ellipse", "square", "rectangle", "triangle", "hexagon"]),
                # Table constraints also set to 600
                "rx": st.column_config.NumberColumn("Radius X", min_value=50, max_value=600, step=10),
                "ry": st.column_config.NumberColumn("Radius Y", min_value=50, max_value=600, step=10),
                "style": st.column_config.SelectboxColumn("Style", options=["solid", "dot", "dash", "dashdot","none"]),
            }
        )
        
        if st.button("💾 Save Orbit Changes", use_container_width=True):
            data["orbits"] = edited_orbits.to_dict('records')
            st.rerun()

    # =========================================================
    # 2. NODE MANAGER
    # =========================================================

    def render_node_manager(self):
        import streamlit as st
        import pandas as pd
        
        data = st.session_state["dyn_data"]
        icon_choices = ["None", "VAR", "SDR"]
        
        # 1. Mass Injection Power Tool
        with st.expander("🚀 Mass Node Injection", expanded=False):
            # Row 1: Base settings
            c1, c2, c3 = st.columns([2, 2, 1])
            base_name = c1.text_input("Node Base Name", value="PE-", key="node_base_input")
            orb_ids = [o["id"] for o in data["orbits"]]
            target_orb = c2.selectbox("Target Orbit", orb_ids if orb_ids else ["None"], key="node_target_orb")
            n_count = c3.number_input(label="Count", min_value=1, max_value=32, value=4, key="node_count_input")
            
            # Row 2: Health, Halo, and Icon Pickers
            h1, h2, h3 = st.columns([2, 2, 2])
            inj_health = h1.number_input("Health (Inner) [1=Opt, 10=Crit]", min_value=1, max_value=10, value=1, key="inj_health")
            inj_halo = h2.number_input("Halo (Outer) [1=Std, 10=Alert]", min_value=1, max_value=10, value=1, key="inj_halo")
            inj_icon = h3.selectbox("Assign Icon", options=icon_choices, key="inj_icon")
            
            if st.button("✨ Auto-Generate & Balance", use_container_width=True):
                if target_orb != "None":
                    spacing = 60 / n_count
                    for i in range(n_count):
                        nid = f"{base_name}{i+1}"
                        
                        # Translate the icon selection to a Base64 string
                        b64_icon = None
                        if inj_icon != "None":
                            # Make sure your filenames match these strings (e.g., VAR.png, SDR.png)
                            img_path = f"templates/png/{inj_icon}.png"
                            b64_icon = get_base64_image(img_path)

                        data["nodes"][nid] = {
                            "label_header": nid, 
                            "orbit": target_orb, 
                            "mins": round(i * spacing, 1),
                            "size": "m", 
                            "colors": [inj_health, inj_halo, 1], 
                            "node_type": "planet",
                            "icon_type": inj_icon,  # Keep human-readable type for the UI table
                            "icon": b64_icon        # Keep the Base64 payload for Plotly
                        }
                    st.rerun()

        st.divider()

        # 2. Global Node Actions Row
        st.subheader("Node Inventory")
        ga1, ga2 = st.columns([3, 1])
        
        node_state = st.session_state.get("node_editor", {})
        sel_nodes = node_state.get("selection", {}).get("rows", [])
        
        with ga1:
            if sel_nodes:
                if st.button(f"🗑️ Delete {len(sel_nodes)} Selected Node(s)", type="primary", use_container_width=True):
                    current_ids = list(data["nodes"].keys())
                    for idx in sel_nodes:
                        if idx < len(current_ids):
                            nid = current_ids[idx]
                            if nid in data["nodes"]: del data["nodes"][nid]
                    st.rerun()
            else:
                st.info("Edit values below or select rows to delete.")

        with ga2:
            if st.button("🧨 Clear All Nodes", use_container_width=True):
                data["nodes"] = {}
                st.rerun()

        # 3. Editable Node Table 
        node_rows_data = []
        for k, v in data["nodes"].items():
            colors = v.get("colors", [3, 4, 1])
            node_rows_data.append({
                "ID": k, 
                "Orbit": v.get("orbit", "O1"), 
                "Mins": v.get("mins", 0),
                "Health [1]": colors[0], 
                "Halo [2]": colors[1], 
                "Size": v.get("size", "m"),
                "Icon": v.get("icon_type", "None") # Expose the selector type to the table
            })
        
        df_nodes = pd.DataFrame(node_rows_data) if node_rows_data else pd.DataFrame(columns=["ID", "Orbit", "Mins", "Health [1]", "Halo [2]", "Size", "Icon"])
        
        edited_nodes = st.data_editor(
            df_nodes, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="node_editor",
            column_config={
                "Orbit": st.column_config.SelectboxColumn("Orbit", options=orb_ids),
                "Size": st.column_config.SelectboxColumn("Size", options=["xs", "s", "m", "l", "xl", "sun"]),
                "Mins": st.column_config.NumberColumn("Mins", min_value=0, max_value=60, step=0.1),
                "Health [1]": st.column_config.NumberColumn("Health (Inner)", min_value=1, max_value=10, help="1=Optimal, 10=Critical"),
                "Halo [2]": st.column_config.NumberColumn("Halo (Outer)", min_value=1, max_value=10, help="1=Standard, 10=Alert"),
                "Icon": st.column_config.SelectboxColumn("Icon Overlay", options=icon_choices)
            }
        )

        if st.button("💾 Save Node Changes", use_container_width=True):
            new_nodes = {}
            for _, row in edited_nodes.iterrows():
                nid = row["ID"]
                icon_type = row.get("Icon", "None")
                
                # Check if we need to encode a new base64 string based on table edits
                b64_icon = None
                if icon_type != "None":
                    img_path = f"templates/png/{icon_type}.png"
                    b64_icon = get_base64_image(img_path)

                new_nodes[nid] = {
                    "label_header": nid, 
                    "orbit": row["Orbit"], 
                    "mins": row["Mins"],
                    "size": row["Size"], 
                    "colors": [row["Health [1]"], row["Halo [2]"], 1], 
                    "node_type": "sun" if row["Size"] == "sun" else "planet",
                    "icon_type": icon_type,
                    "icon": b64_icon
                }
            data["nodes"] = new_nodes
            st.rerun()

    # =========================================================
    # 3. LINK MANAGER
    # =========================================================

    def render_link_manager(self):
        data = st.session_state["dyn_data"]
        
        # 1. Global Link Actions Row
        st.subheader("Link Inventory")
        ga1, ga2 = st.columns([3, 1])
        
        link_state = st.session_state.get("link_editor", {})
        sel_links = link_state.get("selection", {}).get("rows", [])
        
        with ga1:
            if sel_links:
                if st.button(f"🗑️ Delete {len(sel_links)} Selected Link(s)", type="primary", use_container_width=True):
                    # Filter out the selected indices from the list
                    data["links"] = [v for i, v in enumerate(data["links"]) if i not in sel_links]
                    st.rerun()
            else:
                st.info("Select rows to enable deletion or edit status [1, 2, 3] below.")

        with ga2:
            if st.button("🧨 Clear All Links", use_container_width=True, help="Wipe all cross-connects"):
                data["links"] = []
                st.rerun()

        # 2. Prepare Data for Table
        link_rows = []
        for l in data["links"]:
            colors = l.get("colors", [3, 3, 3])
            link_rows.append({
                "Source (A)": l.get("source"),
                "Target (Z)": l.get("target"),
                "Status A [1]": colors[0],
                "Perf/Fiber [2]": colors[1],
                "Status Z [3]": colors[2]
            })

        df_links = pd.DataFrame(link_rows) if link_rows else pd.DataFrame(
            columns=["Source (A)", "Target (Z)", "Status A [1]", "Perf/Fiber [2]", "Status Z [3]"]
        )

        # 3. Editable Link Table
        node_ids = list(data["nodes"].keys())
        edited_links = st.data_editor(
            df_links,
            num_rows="dynamic",
            use_container_width=True,
            key="link_editor",
            column_config={
                "Source (A)": st.column_config.SelectboxColumn("Source A", options=node_ids, required=True),
                "Target (Z)": st.column_config.SelectboxColumn("Target Z", options=node_ids, required=True),
                "Status A [1]": st.column_config.NumberColumn("Status A", min_value=1, max_value=10, help="Source  Health"),
                "Perf/Fiber [2]": st.column_config.NumberColumn("SLA", min_value=1, max_value=10, help=" Service Performance"),
                "Status Z [3]": st.column_config.NumberColumn("Status Z", min_value=1, max_value=10, help="Target  Health"),
            }
        )

        # 4. Save and Pack [1, 2, 3] Scheme
        if st.button("💾 Save Link Changes", use_container_width=True):
            new_links = []
            for _, row in edited_links.iterrows():
                # Prevent self-linking and ensure valid selection
                if row["Source (A)"] and row["Target (Z)"] and row["Source (A)"] != row["Target (Z)"]:
                    new_links.append({
                        "source": row["Source (A)"],
                        "target": row["Target (Z)"],
                        # Packing the 3-color scheme for the Galileo engine
                        "colors": [row["Status A [1]"], row["Perf/Fiber [2]"], row["Status Z [3]"]],
                        "type": "line"
                    })
            data["links"] = new_links
            st.rerun()