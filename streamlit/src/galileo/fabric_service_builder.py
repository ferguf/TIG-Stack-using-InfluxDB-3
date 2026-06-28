import streamlit as st
import pandas as pd

import streamlit as st
import pandas as pd


class FabricServiceBuilder:
    """
    Template builder for generating specific Galileo network topologies 
    and summaries based on service types (EPL, EVPL, ELAN, etc.).
    """
    def __init__(self):
        # Initialize the drawer once when the builder is called
        try:
            from src.galileo.plotly_draw import PlotlyDraw 
            self.drawer = PlotlyDraw()
        except Exception as e:
            st.error(f"PlotlyDraw visual engine failed to initialize: {e}")
            self.drawer = None

    def get_node_clock_positions(self, node_count: int) -> list:
        """
        Calculates evenly spaced radial positions on a 60-minute clock face.
        Used by the Galileo drawing engine to place orbiting nodes without overlap.
        """
        if node_count <= 0:
            return []
        
        # If there is only one node, place it top-dead-center
        if node_count == 1:
            return [0]
            
        # Calculate even spacing for multiple nodes
        spacing = 60.0 / node_count
        
        # Return a list of rounded minute positions (0-59)
        return [int(round(i * spacing)) % 60 for i in range(node_count)]

    def render_fabric_summary(self, data):
        """
        Renders a detailed summary breakdown of the current fabric.
        Translates raw telemetry integers to human-readable statuses.
        """
        st.subheader("📊 Fabric Summary Report")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Orbits", len(data.get("orbits", [])))
        c2.metric("Total Nodes", len(data.get("nodes", {})))
        c3.metric("Fabric Connections", len(data.get("links", [])))
        
        st.divider()
        
        links = data.get("links", [])
        if links:
            st.markdown("#### Active Fabric Interfaces")
            
            # Telemetry mapping for the data table
            status_map = {0: "Provisioning", 1: "Green", 2: "Amber", 3: "Red", 4: "Unknown"}
            
            summary_data = []
            for link in links:
                colors = link.get("colors", [4, 4, 4])
                # Ensure array has 3 elements
                while len(colors) < 3: colors.append(4)
                    
                h_str = f"{status_map.get(colors[0], 'Unknown')} / {status_map.get(colors[1], 'Unknown')} / {status_map.get(colors[2], 'Unknown')}"
                
                summary_data.append({
                    "Local Node": link.get("source"),
                    "Local Port": link.get("port_a", "eth0"),
                    "Direction": "⟷",
                    "Remote Port": link.get("port_z", "eth0"),
                    "Remote Node": link.get("target"),
                    "Health (A/Fiber/Z)": h_str
                })
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
        else:
            st.info("No fabric connections have been configured yet.")

    def render_physical_layer_topology(self, all_ports: list, fs_ports: list, fs_links: list, vrf_name: str, topo_id: str = "phys_view", key_prefix: str = "gal_phys"):
        """
        Tier 1: Physical Port Topology.
        Implements strict 0-4 Telemetry colors for Ports, Hubs, and Cross-Connects.
        """
        import streamlit as st
        from src.galileo.galileo_templates import get_base64_image

        # 1. UI TOGGLE (Bound to the specific topology instance to prevent state loss)
        view_mode = st.radio(
            "🎛️ Port Visibility Filter:",
            options=["Active Service Ports", "All Customer Inventory"],
            horizontal=True,
            key=f"toggle_{topo_id}"
        )
        
        if view_mode == "All Customer Inventory":
            st.caption("💡 *Unassociated inventory ports are dimmed and orbit the hub without a connection line.*")

        # 2. STRICT DEDUPLICATION
        unique_all_ports = list({p.get('port_id'): p for p in all_ports if p.get('port_id')}.values())
        unique_fs_ports = list({p.get('port_id'): p for p in fs_ports if p.get('port_id')}.values())

        display_ports = unique_fs_ports if view_mode == "Active Service Ports" else unique_all_ports

        # 3. INITIALIZE TOPOLOGY (Hub is always added)
        galileo_nodes = {}
        galileo_links = []
        
        galileo_orbits = [
            {"id": "O1_PORTS", "type": "circle", "rx": 200, "ry": 200, "style": "dashed"},
            {"id": "O2_CPE", "type": "circle", "rx": 400, "ry": 400, "style": "solid"}
        ]

        mcgw_hub_name = vrf_name or "Hub"
        galileo_nodes[mcgw_hub_name] = {
            "label_header": mcgw_hub_name,
            "orbit": "none", "x": 0, "y": 0,
            "size": "xxl", "colors": [1, 1], # Green Hub
            "node_type": "sun", "icon_type": "MCGW",
            "icon": get_base64_image("templates/png/MCGW.png"),
            "hovertext": f"<b>MCGW Hub: {mcgw_hub_name}</b>"
        }

        # 4. MAP CONNECTIONS TO PORTS
        port_to_cx = {}
        for cx in (fs_links or []):
            if cx.get('connector_a_id'): port_to_cx[cx.get('connector_a_id')] = cx
            if cx.get('connector_b_id'): port_to_cx[cx.get('connector_b_id')] = cx

        # 5. BUILD NODES (If ports exist)
        if not display_ports:
            st.info(f"No physical ports found in '{view_mode}'.")
        else:
            if len(display_ports) == 2:
                port_positions = [45, 15] 
            else:
                port_positions = self.get_node_clock_positions(len(display_ports))
                
            active_ids = {p.get("port_id") for p in unique_fs_ports}

            for idx, port in enumerate(display_ports):
                p_mins = port_positions[idx]
                port_id = port.get('port_id')
                
                p_name = port.get('port_name', 'Unknown')
                p_speed = port.get('port_speed', 'N/A')
                oper = str(port.get("oper_status", "down")).lower()
                device_name = port.get("device_name", f"PE-Router-{idx}")
                
                is_active_stitch = port_id in active_ids
                
                # --- TELEMETRY ENGINE IMPLEMENTATION ---
                if is_active_stitch:
                    port_health = [1, 1] if oper == "up" else [3, 3] # Red if Down
                    cpe_color = [4, 4] # Unknown demarc
                    link_hub_color = [1, 1, 1] if oper == "up" else [3, 3, 3]
                    link_cpe_color = [1, 1, 1] if oper == "up" else [3, 3, 3]
                else:
                    port_health = [0, 0] # Provisioning/Inventory (Gray)
                    cpe_color = [0, 0] 
                    link_hub_color = [0, 0, 0]
                    link_cpe_color = [0, 0, 0]
                
                port_key = f"{key_prefix}_{port_id}"
                
                cx_info = port_to_cx.get(port_id, {})
                vlan_text = f"<br>S-VLAN: {cx_info.get('s_vlan', 'N/A')}" if is_active_stitch else ""
                
                galileo_nodes[port_key] = {
                    "label_header": p_name,
                    "label_sub": device_name, 
                    "orbit": "O1_PORTS", 
                    "mins": p_mins, 
                    "size": "m", 
                    "colors": port_health, 
                    "node_type": "planet",
                    "icon_type": "FabricPort",
                    "icon": get_base64_image("templates/png/FabricPort.png"),
                    "hovertext": f"<b>Port: {p_name}</b><br>Device: {device_name}<br>Speed: {p_speed}<br>Oper: {oper.upper()}<br>Status: {'Active in Service' if is_active_stitch else 'Available Inventory'}{vlan_text}"
                }
                
                if is_active_stitch:
                    galileo_links.append({"source": port_key, "target": mcgw_hub_name, "colors": link_hub_color, "type": "line"})

                cpe_key = f"{key_prefix}_CPE_{port_id}"
                galileo_nodes[cpe_key] = {
                    "label_header": f"CPE-{idx+1}",
                    "orbit": "O2_CPE", 
                    "mins": p_mins, 
                    "size": "s",
                    "colors": cpe_color, 
                    "node_type": "satellite",
                    "icon_type": "CPE",
                    "icon": get_base64_image("templates/png/CPE.png"),
                    "hovertext": f"Customer Edge connected to {device_name} / {p_name}"
                }
                
                galileo_links.append({"source": cpe_key, "target": port_key, "colors": link_cpe_color, "type": "line"})

        # 6. ALWAYS RENDER THE DRAWER
        if hasattr(self, 'drawer') and self.drawer:
            self.drawer.show_topology(galileo_nodes, galileo_orbits, galileo_links, topo_id=topo_id, key_prefix=key_prefix)

    def render_l2_evc_topology(self, fs_detail: dict = None, topo_id: str = "l2_view", key_prefix: str = "gal_l2"):
        """
        Renders the Layer 2 Virtual Connection Topology.
        Applies strict 0-4 telemetry to Virtual Switch Interfaces (VSI) and EVCs.
        """
        from src.galileo.galileo_templates import get_base64_image
        import streamlit as st

        if fs_detail is None: fs_detail = {}
        service_name = fs_detail.get("service_alias") or fs_detail.get("service_name", "L2 Service")
        svc_type = str(fs_detail.get("service_type", "EPL")).upper().replace("EPLAN", "EP-LAN").replace("EVP-LLAN", "EVP-LAN")
        
        raw_ports = fs_detail.get("fabric_ports", [])
        conns = fs_detail.get("fabric_connections", [])

        if not conns:
            st.info("No active virtual circuits (EVCs) stitched for this service yet.")
            return

        unique_raw_ports = list({str(p.get('port_id')).strip(): p for p in raw_ports if p.get('port_id')}.values())

        port_to_cx = {}
        for cx in conns:
            a_id = str(cx.get('connector_a_id', '')).strip()
            b_id = str(cx.get('connector_b_id', '')).strip()
            if a_id and a_id != 'None': port_to_cx[a_id] = cx
            if b_id and b_id != 'None': port_to_cx[b_id] = cx

        evc_ports = [p for p in unique_raw_ports if str(p.get('port_id')).strip() in port_to_cx]
        node_count = len(evc_ports)

        if not evc_ports:
            st.info("Cannot resolve EVC endpoints to the physical inventory. Awaiting stitching.")
            return

        galileo_nodes = {}
        galileo_links = []
        galileo_orbits = [
            {"id": "O1_PORTS", "type": "circle", "rx": 250, "ry": 250, "style": "dashed"},
            {"id": "O2_CPE", "type": "circle", "rx": 400, "ry": 400, "style": "solid"}
        ]

        is_multipoint = svc_type in ["EP-LAN", "EVP-LAN"]

        if is_multipoint:
            positions = self.get_node_clock_positions(node_count)
            hub_key = f"{key_prefix}_VSI_HUB"
            galileo_nodes[hub_key] = {
                "label_header": service_name,
                "label_sub": f"L2 Domain ({svc_type})",
                "orbit": "none", "x": 0, "y": 0,
                "size": "xl", "colors": [1, 1], # Green Hub
                "node_type": "sun", "icon_type": "MCGW", 
                "icon": get_base64_image("templates/png/MCGW.png"),
                "hovertext": f"<b>{service_name}</b><br>Multipoint Virtual Switch Interface"
            }
        else:
            positions = [45, 15] if node_count == 2 else self.get_node_clock_positions(node_count)

        port_key_map = {}

        for idx, port in enumerate(evc_ports): 
            port_id = str(port.get("port_id")).strip()
            port_name = port.get("port_name", f"Port-{idx}")
            device_name = port.get("device_name", "Unknown Device")
            status = str(port.get("port_service_status", "staged")).lower()
            
            p_key = f"{key_prefix}_PORT_{idx}"
            port_key_map[port_id] = p_key
            p_mins = positions[idx]

            galileo_nodes[p_key] = {
                "label_header": device_name,
                "label_sub": port_name,
                "orbit": "O1_PORTS",
                "mins": p_mins, "size": "m",
                "colors": [1, 1] if status == "active" else [0, 0], # Green or Provisioning
                "node_type": "planet", "icon_type": "port",
                "icon": get_base64_image("templates/png/FabricPort.png"), 
                "hovertext": f"<b>{device_name}</b><br>Port: {port_name}<br>Status: {status.upper()}"
            }

            cpe_key = f"{key_prefix}_CPE_{idx}"
            galileo_nodes[cpe_key] = {
                "label_header": f"CPE Node {idx+1}",
                "orbit": "O2_CPE",
                "mins": p_mins, "size": "s",
                "colors": [4, 4], # Unknown demarcation
                "node_type": "satellite", "icon_type": "CPE",
                "icon": get_base64_image("templates/png/CPE.png"),
                "hovertext": f"<b>Customer Premise Equipment</b><br>Demarcation for {device_name}"
            }

            galileo_links.append({"source": cpe_key, "target": p_key, "colors": [1, 1, 1] if status == "active" else [0, 0, 0], "type": "line"})

            if is_multipoint:
                galileo_links.append({
                    "source": p_key, "target": hub_key, 
                    "colors": [1, 1, 1] if status == "active" else [0, 0, 0], 
                    "type": "solid",
                    "hovertext": "Logical Attachment"
                })

        if not is_multipoint:
            for cx in conns:
                a_id = str(cx.get("connector_a_id", "")).strip()
                b_id = str(cx.get("connector_b_id", "")).strip()
                
                if a_id in port_key_map and b_id in port_key_map:
                    cx_status = str(cx.get("connection_status", "staged")).lower()
                    bw = f"{cx.get('service_bw', 'Unknown')} Mbps"
                    cx_name = cx.get("connection_name", "EVC")
                    vlan = cx.get("c_vlan_list", "Untagged")
                    
                    galileo_links.append({
                        "source": port_key_map[a_id],
                        "target": port_key_map[b_id],
                        "colors": [1, 1, 1] if cx_status == "active" else [0, 0, 0],
                        "type": "solid",
                        "hovertext": f"<b>EVC: {cx_name}</b><br>BW: {bw}<br>VLAN: {vlan}<br>State: {cx_status.upper()}",
                        "text": bw
                    })

        if getattr(self, 'drawer', None):
            self.drawer.show_topology(galileo_nodes, galileo_orbits, galileo_links, topo_id=topo_id, key_prefix=key_prefix)

    def render_logical_layer_topology(self, fs_detail: dict = None, interfaces: list = None, vrf_name: str = None, topo_id: str = "log_view", key_prefix: str = "gal_log"):
        """
        Renders the Tier 2 Logical Layer (L3VPN / VRF).
        """
        from src.galileo.galileo_templates import get_base64_image
        import streamlit as st
        
        if fs_detail is None: fs_detail = {}
        if interfaces is None: interfaces = fs_detail.get("fabric_interfaces", [])
        if not vrf_name: vrf_name = fs_detail.get("service_alias") or fs_detail.get("service_name") or "Core VRF"

        if not interfaces: 
            st.info("No logical interface data available for this routing instance.")
            return

        galileo_nodes = {}
        galileo_links = []
        galileo_orbits = [{"id": "O1_INTF", "type": "circle", "rx": 300, "ry": 300, "style": "dotted"}]

        vrf_key = f"{key_prefix}_VRF_{vrf_name.replace(' ', '_')}"

        galileo_nodes[vrf_key] = {
            "label_header": vrf_name, 
            "label_sub": f"RT: {fs_detail.get('route_target', 'Unknown')}",
            "orbit": "none", 
            "x": 0, "y": 0, 
            "size": "xxl",
            "colors": [1, 1], 
            "node_type": "sun", 
            "icon_type": "MCGW",
            "icon": get_base64_image("templates/png/MCGW.png"),
            "hovertext": f"<b>{vrf_name}</b><br>Virtual Routing & Forwarding Instance"
        }

        positions = self.get_node_clock_positions(len(interfaces))
        
        for idx, intf in enumerate(interfaces):
            i_name = intf.get('interface_name', 'Unnamed-L3')
            status = str(intf.get('status', 'staged')).lower() 
            ip_addr = intf.get('ip_address', 'No IP Assigned')
            vlan = intf.get('vlan_id', 'Untagged')
            
            intf_key = f"{key_prefix}_INTF_{idx}"
            
            galileo_nodes[intf_key] = {
                "label_header": i_name, 
                "label_sub": ip_addr,
                "orbit": "O1_INTF", 
                "mins": positions[idx], 
                "size": "s",
                "colors": [1, 1] if status == 'active' else [0, 0],
                "node_type": "planet", 
                "icon_type": "Interface",
                "icon": get_base64_image("templates/png/Interface.png"),
                "hovertext": f"<b>{i_name}</b><br>IP: {ip_addr}<br>VLAN: {vlan}<br>Status: {status.upper()}"
            }
            
            galileo_links.append({
                "source": intf_key, 
                "target": vrf_key,
                "colors": [1, 1, 1] if status == 'active' else [0, 0, 0], 
                "type": "dotted",
                "hovertext": "Logical Attachment"
            })

        if getattr(self, 'drawer', None):
            self.drawer.show_topology(galileo_nodes, galileo_orbits, galileo_links, topo_id, key_prefix)

    def render_routing_layer_topology(self, fs_detail: dict = None, interfaces: list = None, vrf_name: str = None, topo_id: str = "rtg_view", key_prefix: str = "gal_rtg"):
        """
        Tier 3: Protocol Topology.
        BGP Down states trigger Critical Red alerts.
        """
        import streamlit as st
        from src.galileo.galileo_templates import get_base64_image

        if fs_detail is None: fs_detail = {}
        if interfaces is None: interfaces = fs_detail.get("fabric_interfaces", [])
        if not vrf_name: vrf_name = fs_detail.get("service_alias") or fs_detail.get("service_name") or "Core VRF"

        if not interfaces:
            st.info("No routing metadata found.")
            return

        galileo_nodes = {}
        galileo_links = []
        
        galileo_orbits = [
            {"id": "O1_BGP", "type": "circle", "rx": 320, "ry": 320, "style": "solid"},
            {"id": "O2_STATIC", "type": "circle", "rx": 520, "ry": 520, "style": "dotted"}
        ]

        all_bgp = []
        all_static = []
        for intf in interfaces:
            i_name = intf.get('interface_name', 'Unknown')
            for bgp in intf.get('bgp_neighbors', []):
                all_bgp.append({"data": bgp, "intf": i_name})
            for static in intf.get('static_routes', []):
                all_static.append({"data": static, "intf": i_name})

        total_routing_nodes = len(all_bgp) + len(all_static)
        if total_routing_nodes == 0:
            st.info("No routing protocols (BGP or Static) configured for this service.")
            return
            
        positions = self.get_node_clock_positions(total_routing_nodes)
        vrf_key = f"{key_prefix}_VRF_{vrf_name.replace(' ', '_')}"

        galileo_nodes[vrf_key] = {
            "label_header": vrf_name, "orbit": "none", "x": 0, "y": 0,
            "size": "xxl", "colors": [1, 1], "node_type": "sun", 
            "icon_type": "MCGW", "icon": get_base64_image("templates/png/MCGW.png"),
            "text": "Control Plane",
            "hovertext": f"<b>{vrf_name}</b><br>Global Routing Instance"
        }

        for idx, item in enumerate(all_bgp):
            bgp = item["data"]
            intf_name = item["intf"]
            p_mins = positions[idx]
            
            neighbor_ip = bgp.get('neighbor_ip', '0.0.0.0')
            remote_asn = bgp.get('remote_asn') or bgp.get('remote_as', 'N/A')
            state = str(bgp.get('session_state') or bgp.get('state', "down")).lower()
            
            bgp_key = f"{key_prefix}_BGP_{idx}_{neighbor_ip}"
            is_up = state in ["established", "up"]
            
            # Critical Red alerts for downed BGP
            galileo_nodes[bgp_key] = {
                "label_header": f"AS{remote_asn} | {neighbor_ip} | {state.upper()}",
                "orbit": "O1_BGP", "mins": p_mins, "size": "m",
                "colors": [1, 1] if is_up else [3, 3],
                "node_type": "planet", "icon_type": "bgp",
                "icon": get_base64_image("templates/png/bgp.png") or get_base64_image("templates/png/Router.png"),
                "hovertext": f"<b>BGP Peer</b><br>IP: {neighbor_ip}<br>AS: {remote_asn}<br>State: {state.upper()}<br>Via: {intf_name}"
            }
            galileo_links.append({"source": bgp_key, "target": vrf_key, "colors": [1, 1, 1] if is_up else [3, 3, 3], "type": "line"})

        bgp_offset = len(all_bgp)
        for idx, item in enumerate(all_static):
            route = item["data"]
            intf_name = item["intf"]
            global_idx = bgp_offset + idx
            p_mins = positions[global_idx]
            
            prefix_ip = route.get('ip_prefix') or route.get('prefix', '0.0.0.0')
            mask = route.get('prefix_mask', '')
            full_prefix = f"{prefix_ip}/{mask}" if mask else prefix_ip
            next_hop = route.get('next_hop', 'Drop')
            
            static_key = f"{key_prefix}_STATIC_{idx}_{prefix_ip}"
            
            galileo_nodes[static_key] = {
                "label_header": full_prefix,
                "label_sub": f"NH: {next_hop}",
                "orbit": "O2_STATIC", "mins": p_mins, "size": "s",
                "colors": [1, 1], "node_type": "satellite",
                "icon_type": "Static", 
                "icon": get_base64_image("templates/png/Static.png") or get_base64_image("templates/png/Interface.png"),
                "hovertext": f"<b>Static Route</b><br>Dest: {full_prefix}<br>Next-Hop: {next_hop}<br>Via: {intf_name}"
            }
            galileo_links.append({"source": static_key, "target": vrf_key, "colors": [1, 1, 1], "type": "dotted"})

        if getattr(self, 'drawer', None):
            self.drawer.show_topology(galileo_nodes, galileo_orbits, galileo_links, topo_id=topo_id, key_prefix=key_prefix)
            
    def render_cloud_layer_topology(self, cloud_partners: list, vrf_name: str, topo_id: str = "cloud_view", key_prefix: str = "gal_cloud"):
            """
            Renders the Tier 4 Cloud Layer.
            """
            from src.galileo.galileo_templates import get_base64_image
            import streamlit as st
            
            if not cloud_partners: 
                st.info("No active Cloud Interconnects (VXCs) found for this service.")
                return

            flat_vxcs = []
            for cp in cloud_partners:
                p_name = cp.get('partner_name', 'Cloud')
                conns = cp.get('connections', [])
                
                if not conns and 'region' in cp:
                    flat_vxcs.append({
                        "partner_name": p_name,
                        "region": cp.get('region', 'Unknown'),
                        "conn_name": cp.get('connection_name', f"{p_name}-VXC"),
                        "bw": cp.get('service_bw', 'N/A'),
                        "status": cp.get('service_status', 'Active')
                    })
                else:
                    for c in conns:
                        flat_vxcs.append({
                            "partner_name": p_name,
                            "region": c.get('region', 'Unknown'),
                            "conn_name": c.get('connection_name', f"{p_name}-VXC"),
                            "bw": c.get('service_bw', 'N/A'),
                            "status": c.get('service_status', 'Active')
                        })

            if not flat_vxcs:
                st.info("No active Cloud Interconnects (VXCs) found for this service.")
                return

            galileo_nodes = {}
            galileo_links = []
            galileo_orbits = [{"id": "O3_CLOUD", "type": "circle", "rx": 400, "ry": 400, "style": "dashed"}]

            galileo_nodes[vrf_name] = {
                "label_header": vrf_name, 
                "orbit": "none", "x": 0, "y": 0, "size": "xxl",
                "colors": [1, 1], "node_type": "sun", "icon_type": "MCGW",
                "icon": get_base64_image("templates/png/MCGW.png"),
                "hovertext": f"<b>MCGW Hub: {vrf_name}</b>",
                "text": "MCGW Hub"
            }

            positions = self.get_node_clock_positions(len(flat_vxcs))
            
            for idx, vxc in enumerate(flat_vxcs):
                partner_name = vxc['partner_name']
                region = vxc['region']
                conn_name = vxc['conn_name']
                bw = vxc['bw']
                status = str(vxc['status']).lower()
                
                cp_key = f"{key_prefix}_CLOUD_{idx}_{partner_name}_{region}"
                
                l_color = [1, 1, 1] if status == "active" else [0, 0, 0]
                
                galileo_nodes[cp_key] = {
                    "label_header": partner_name, 
                    "label_sub": conn_name, 
                    "orbit": "O3_CLOUD", 
                    "mins": positions[idx], 
                    "size": "l",
                    "colors": [1, 1] if status == "active" else [0, 0], 
                    "node_type": "planet", 
                    "icon_type": partner_name, 
                    "icon": get_base64_image(f"templates/png/{partner_name}.png"),
                    "hovertext": f"<b>{partner_name} VXC</b><br>Region: {region}<br>Conn: {conn_name}<br>BW: {bw} Mbps<br>Status: {status.upper()}"
                }
                
                galileo_links.append({
                    "source": vrf_name, 
                    "target": cp_key, 
                    "colors": l_color, 
                    "type": "line",
                    "hovertext": f"{bw} Mbps",
                    "text": f"{bw} Mbps"
                })

            if getattr(self, 'drawer', None):
                self.drawer.show_topology(galileo_nodes, galileo_orbits, galileo_links, topo_id=topo_id, key_prefix=key_prefix)
                
    def calculate_node_minute(self, node_index: int, total_nodes: int) -> int:
        """
        Determines the clock position (0-59) based on total node count.
        """
        if total_nodes <= 0: return 0
        if total_nodes == 1: return 15
        if total_nodes == 2: return 15 if node_index == 0 else 45
            
        spacing = 60 // total_nodes
        return (node_index * spacing) % 60

def render_twin_topology(fs_detail: dict, key_prefix: str = "twin"):
    """
    Standardized entry point for rendering the multi-tier Digital Twin.
    """
    import streamlit as st
    import uuid
    from src.galileo.fabric_service_builder import FabricServiceBuilder
    
    builder = FabricServiceBuilder()
    
    topo_id = str(fs_detail.get("service_id", "default"))
    vrf_name = fs_detail.get("service_name", "GALILEO-CORE")
    svc_type = str(fs_detail.get("service_type", "")).upper().replace("EPLAN", "EP-LAN").replace("EVP-LLAN", "EVP-LAN")

    is_l2_evc = svc_type in ["EPL", "EVPL", "EP-LAN", "EVP-LAN"]
    is_l3_vpn = svc_type in ["IPVPN", "L3VPN", "INTERNET", "MCGW"]

    raw_ports = fs_detail.get('fabric_ports') or []
    interfaces = fs_detail.get('fabric_interfaces') or []
    cloud_partners = fs_detail.get('cloud_interconnects') or []
    connections = fs_detail.get('fabric_connections') or []

    salt_key = f"topo_salt_{topo_id}"
    if salt_key not in st.session_state:
        st.session_state[salt_key] = uuid.uuid4().hex[:6]
    safe_prefix = f"{key_prefix}_{st.session_state[salt_key]}"

    active_port_ids = set()
    for cx in connections:
        if cx.get('connector_a_id'): active_port_ids.add(str(cx.get('connector_a_id')).strip())
        if cx.get('connector_b_id'): active_port_ids.add(str(cx.get('connector_b_id')).strip())

    filtered_ports = {}
    for p in raw_ports:
        pid = str(p.get('port_id', '')).strip()
        if not pid: continue
        if pid in active_port_ids or p.get('association_type') == 'service':
            filtered_ports[pid] = p

    ports = list(filtered_ports.values())
    
    has_routing = any(
        (i.get('bgp_neighbors') or i.get('static_routes')) 
        for i in interfaces if isinstance(i, dict)
    )

    tab_configs = []
    
    if raw_ports:
        tab_configs.append({"title": "🔌 Physical", "type": "phys"})
        
    if is_l2_evc:
        tab_configs.append({"title": "🌐 EVC Flow", "type": "log_l2"})
    elif is_l3_vpn:
        tab_configs.append({"title": "🌐 VRF Topology", "type": "log_l3"})
        
    if has_routing:
        tab_configs.append({"title": "🛰️ Protocol", "type": "rtg"})
    if cloud_partners:
        tab_configs.append({"title": "☁️ Cloud", "type": "cloud"})

    if not tab_configs:
        st.info("No topology data has been provisioned for this service yet.")
        return

    st_tabs = st.tabs([t["title"] for t in tab_configs])

    for idx, config in enumerate(tab_configs):
        with st_tabs[idx]:
            if config["type"] == "phys":
                builder.render_physical_layer_topology(
                    all_ports=raw_ports, 
                    fs_ports=ports, 
                    fs_links=connections,
                    vrf_name=vrf_name, 
                    topo_id=f"p_{topo_id}", 
                    key_prefix=f"{safe_prefix}_phys"
                )
            elif config["type"] == "log_l2":
                builder.render_l2_evc_topology( 
                    fs_detail=fs_detail, 
                    topo_id=f"l2_{topo_id}", 
                    key_prefix=f"{safe_prefix}_l2"
                )
            elif config["type"] == "log_l3":
                builder.render_logical_layer_topology(
                    fs_detail=fs_detail,
                    interfaces=interfaces, 
                    vrf_name=vrf_name, 
                    topo_id=f"l3_{topo_id}", 
                    key_prefix=f"{safe_prefix}_l3"
                )
            elif config["type"] == "rtg":
                builder.render_routing_layer_topology(
                    fs_detail=fs_detail,
                    interfaces=interfaces, 
                    vrf_name=vrf_name, 
                    topo_id=f"r_{topo_id}", 
                    key_prefix=f"{safe_prefix}_rtg"
                )
            elif config["type"] == "cloud":
                builder.render_cloud_layer_topology(
                    cloud_partners=cloud_partners, 
                    vrf_name=vrf_name, 
                    topo_id=f"c_{topo_id}", 
                    key_prefix=f"{safe_prefix}_cloud"
                )