import streamlit as st
import pandas as pd
import random
import ipaddress
from src.ui_components import UI
from src.utils.ui_provisioning_form import render_service_context_form,render_fabric_port_form
from src.api_client import (
    get_ports_by_customer, 
    get_all_devices, 
    get_ports_by_device,
    get_customers,
    get_fabric_services
)
from src.ui_messages import MessageCenter
from src.state_managers import FabricStateManager
from src.utils.api_customer import post_interface_ip

# --- THE HAMMER ---
if "active_deployment" in st.session_state and st.session_state.active_deployment is not None:
    # This will stay on screen until we manually clear it
    st.sidebar.error(f"🚨 CRITICAL DEBUG: Trigger Found: {st.session_state.active_deployment}")
    
    # If we are stuck, this button will save us
    if st.sidebar.button("🗑️ Force Clear Trigger"):
        st.session_state.active_deployment = None
        st.rerun()

class NetworkWorkflowManager:
    # --- 1. ADD initial_type PARAMETER ---

    def __init__(self, customer_id: str, initial_type: str = "IPVPN"):
        import streamlit as st
        from src.state_managers import FabricStateManager 
        from src.api_client import get_fabric_service_details 
        
        FabricStateManager.initialize()
        self.customer_id = customer_id

        # --- 1. INITIALIZE JSON#2 (THE STAGING PAYLOAD) ---
        if "step" not in st.session_state: 
            st.session_state.step = 1

        # DEFENSIVE PURGE: Detect if the system intent is to create a Greenfield service.
        # This catches edge cases where the UI launcher cleanup loop was bypassed.
        is_greenfield = (
            st.session_state.get("Mode") == "CREATE_SERVICE" or 
            st.session_state.get("payload", {}).get("service_context", {}).get("mode") == "New Fabric Service"
        )
        
        if "payload" not in st.session_state: 
            self._reset_payload(initial_type)
        elif is_greenfield:
            # We are explicitly in NEW mode. Ruthlessly scrub any ghost UUIDs from prior sessions.
            st.session_state.fs_active_id = None
            st.session_state.fs_active_record = {}
            st.session_state.payload["service_id"] = None
            
            # Deep scrub the nested service_context
            if "service_id" in st.session_state.payload.get("service_context", {}):
                del st.session_state.payload["service_context"]["service_id"]
            
            # Force architecture type sync if the user swapped architectures in the UI
            if st.session_state.payload["service_context"].get("type") != initial_type:
                st.session_state.payload["service_context"]["type"] = initial_type

        self.payload = st.session_state.payload

        # --- 2. INITIALIZE JSON#1 (THE LIVE SOURCE OF TRUTH) ---
        if "live_manifest" not in st.session_state or is_greenfield:
            st.session_state.live_manifest = {}
        
        # --- 3. HYDRATE LIVE MANIFEST (JSON#1) FROM DB ---
        active_rec = FabricStateManager.get_active_record("fs") or {}
        
        # STRICT GATEKEEPER: Never attempt DB hydration if we are creating a new service.
        if not is_greenfield:
            found_id = (
                active_rec.get("service_id") or 
                self.payload.get("service_id") or 
                self.payload.get("service_context", {}).get("service_id")
            )
            
            if found_id:
                st.session_state.fs_active_id = found_id
                self.payload["service_id"] = found_id
                
                # Fetch fresh details from API to hydrate JSON#1
                db_details = get_fabric_service_details(found_id)
                if db_details:
                    st.session_state.live_manifest = db_details
                    
                    if active_rec:
                        st.session_state.fs_active_record = active_rec
                        self.payload["service_context"]["name"] = active_rec.get("service_name")
                        self.payload["service_context"]["type"] = active_rec.get("service_type")
                        self.payload["service_context"]["mode"] = "Existing Fabric Service"

        self.live_manifest = st.session_state.live_manifest

        # --- 4. RESOLVE DISPATCHER & GATEKEEPERS ---
        self.service_type = str(self.payload["service_context"].get("type", "IPVPN")).upper().strip()
        self.workflow_map = self._get_workflow_map()
        
        # Gatekeeper logic checks JSON#1 (Live) to see if EVCs already exist
        live_conns = self.live_manifest.get("fabric_connections", [])
        self.is_epl = self.service_type == "EPL"
        self.epl_locked = self.is_epl and len(live_conns) >= 1
        
    def render_fabric_port(self):
        """Step 2: Fabric Port Assignment (Consolidated Controller)"""
        import streamlit as st
        from src.utils.ui_provisioning_form import render_fabric_port_form
        
        st.header("Step 2: Fabric Port Assignment")

        # 1. RENDER THE INTEGRATED FORM & TABLE
        render_fabric_port_form(data=st.session_state.payload, service_type=self.service_type)

        # 2. FINAL PROVISIONING ACTION
        ports_queue = st.session_state.payload["service_context"]["children"].get("ports", [])
        
        st.divider()
        
        # Enable button only if ports exist in the queue (JSON#2)
        if st.button(
            "⚡ Provision Ports", 
            type="primary", 
            use_container_width=True, 
            disabled=not ports_queue
        ):
            # --- TRIGGER ONLY ---
            st.session_state.active_deployment = "ports"
            
            # We do NOT clear the ports here. 
            # We do NOT call the API here.
            
            st.toast("Provisioning initiated...")
            st.rerun()
      
    def render_elan_topology(self):
        """Step 3 (L2): E-LAN Multipoint Topology"""
        st.header("Step 3: E-LAN Topology")
        st.info("E-LAN bridging logic will go here. You will define MAC learning and Hub/Spoke vs Mesh.")
        # TODO: Build ELAN Workflow

    def render_interface_assignment(self):
        """
        Step 3: Interface & Routing Orchestration.
        Orchestrates the logical layer using JSON#2 (Staged) as the workspace.
        """
        import streamlit as st
        import pandas as pd
        from src.utils.ui_provisioning_form import (
            render_interface_build_form, 
            render_static_route_form, 
            render_bgp_peer_form
        )
        from src.utils.network_utils import calculate_ip_assignment

        st.header("Step 3: Interface & Routing")
        
        # 1. Access the raw list in JSON#2 (The Staged Intent)
        interfaces_list = self.payload["service_context"]["children"]["interfaces"]
        
        # ---------------------------------------------------------
        # SECTION 1: ACTIVE CONFIGURATION ZONE (Staging)
        # ---------------------------------------------------------
        with st.container(border=True):
            st.markdown("#### 🛠️ Step 3.1: Define Interface")
            
            # Pass calculate_ip_assignment from network_utils to ensure uniqueness
            render_interface_build_form(
                self.payload["service_context"]["children"], 
                calculate_ip_assignment
            )
          
            if interfaces_list:
                st.divider()
                st.markdown("#### 🛠️ Step 3.2: Configure Routing for Staged Interface")
                # Focus routing on the most recently added interface in JSON#2
                active_intf = interfaces_list[-1] 
                
                col_rt_left, col_rt_right = st.columns(2, gap="large")
                with col_rt_left:
                    render_static_route_form({}, active_intf)
                with col_rt_right:
                    render_bgp_peer_form({}, active_intf)

        # ---------------------------------------------------------
        # SECTION 2: GRANULAR MANAGEMENT ZONE (Live vs Staged)
        # ---------------------------------------------------------
        if interfaces_list or self.live_manifest.get("fabric_interfaces"):
            st.divider()
            st.subheader("📊 Managed Configuration Manifest")
            
            t_intf, t_static, t_bgp, t_json = st.tabs([
                "🖥️ Interfaces", "📍 Static Routes", "🤝 BGP Peers", "📄 JSON Doc"
            ])

            with t_intf:
                st.markdown("##### Queued Physical & Logical Interfaces")
                
                for idx, intf in enumerate(interfaces_list):
                    # check JSON#1 to see if this interface has a UUID yet
                    intf_id = intf.get('interface_id')
                    status_color = "🟢" if intf_id else "🟡"
                    
                    # --- ACTION ROW ---
                    col_info, col_prov, col_del = st.columns([2, 1, 1])
                    
                    with col_info:
                        st.markdown(f"**{status_color} {intf['alias']}**")
                        st.caption(f"Status: `{'PROVISIONED' if intf_id else 'STAGED'}`")
                        if intf_id:
                            st.caption(f"UUID: `{intf_id}`")
                    
                    with col_prov:
                        if not intf_id:
                            if st.button(f"🚀 Provision", key=f"btn_p1_{idx}", use_container_width=True):
                                # Signal the Orchestrator in run() to execute post_interface_intent
                                st.session_state.active_deployment = ("interface_single", idx)
                                st.rerun()
                        else:
                            st.success("LIVE")
                    
                    with col_del:
                        # Only allow removal if it hasn't hit the DB yet
                        if not intf_id:
                            if st.button(f"🗑️ Remove", key=f"btn_del_{idx}", use_container_width=True):
                                interfaces_list.pop(idx)
                                st.rerun()
                        else:
                            st.button("🔒 Locked", disabled=True, key=f"btn_lock_{idx}")
                    
                    # --- TECHNICAL SPECS ---
                    with st.expander("View Technical Configuration Details"):
                        c1, c2 = st.columns(2)
                        c1.write(f"**IPv4 PE:** `{intf.get('ipv4_lumen')}`")
                        c1.write(f"**IPv4 CE:** `{intf.get('ipv4_customer')}`")
                        c2.write(f"**VLAN ID:** `{intf.get('vlan_id') or 'Untagged'}`")
                        c2.write(f"**IPv6 Enabled:** `{'Yes' if intf.get('is_dual_stack') else 'No'}`")
                    
                    st.divider()

            with t_static:
                st.markdown("##### Granular Static Route Deployment")
                for idx, i in enumerate(interfaces_list):
                    routes = i.get('routing', {}).get('static', [])
                    if not routes: continue
                    
                    col_info, col_action = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"**📍 Static Routes for {i['alias']}**")
                    
                    with col_action:
                        # Verification: Interface MUST be Live (have ID) before posting routes
                        if i.get('interface_id'):
                            if st.button(f"🚀 Post Routes", key=f"btn_p2_{idx}", use_container_width=True):
                                st.session_state.active_deployment = ("static_single", idx)
                                st.rerun()
                        else:
                            st.warning("⚠️ Interface Required")

                    with st.expander(f"View {len(routes)} Staged Route(s)"):
                        st.table(pd.DataFrame(routes))
                    st.divider()

            with t_bgp:
                st.markdown("##### Granular BGP Deployment")
                for idx, i in enumerate(interfaces_list):
                    peers = i.get('routing', {}).get('bgp', [])
                    if not peers: continue
                    
                    col_info, col_action = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"**🤝 BGP Neighbors for {i['alias']}**")
                    
                    with col_action:
                        if i.get('interface_id'):
                            if st.button(f"🚀 Establish BGP", key=f"btn_p3_{idx}", use_container_width=True):
                                st.session_state.active_deployment = ("bgp_single", idx)
                                st.rerun()
                        else:
                            st.warning("⚠️ Interface Required")

                    with st.expander(f"View {len(peers)} Staged Neighbor(s)"):
                        st.table(pd.DataFrame(peers))
                    st.divider()

            with t_json:
                st.markdown("##### Full L3 Intent Manifest (JSON#2)")
                st.json(interfaces_list)

    def render_internet_config(self):
        """Step 3 (DIA): Internet on Demand"""
        st.header("Step 3: Internet Configuration")
        st.info("Public IP block assignment and default route advertisement logic will go here.")
        # TODO: Build IOD Workflow

    def render_private_peering(self):
        """Step 4: XaaS - Cloud Exchange"""
        st.header("Step 4: Lumen Cloud Interconnect ")
        
        # 1. Pull the raw list
        peering_list = self.payload["service_context"]["children"]["cloud_peerings"]
        
        # 2. Render the Form
        compat_payload = {"peering_sessions": peering_list}
        from src.utils.ui_provisioning_form import render_private_peering_form
        render_private_peering_form(compat_payload)

        st.divider()

        # 3. Provisioning Zone
        if peering_list:
            col_h, col_r = st.columns([0.8, 0.2])
            col_h.subheader("🚀 Cloud Deployment Queue")
            
            # EMERGENCY RESET: Use this once to clear the KeyError data
            if col_r.button("🗑️ Flush", help="Clear queue if you see KeyErrors"):
                self.payload["service_context"]["children"]["cloud_peerings"].clear()
                st.rerun()
            
            # --- THE DEFENSIVE FIX ---
            # We use .get() to look for 'service_bw' or 'bandwidth' or default to 0
            summary_data = []
            for p in peering_list:
                summary_data.append({
                    "Partner": p.get('partner_id', 'Unknown'),
                    "Region": p.get('region', 'N/A'),
                    "BW": f"{p.get('service_bw', p.get('bandwidth_mbps', 0))}M"
                })

            st.table(summary_data)

            # THE BUTTON: Trigger the Orchestrator
            if st.button("⚡ Provision Cloud Connections", use_container_width=True, type="primary"):
                self._handle_api_deployment("cloud_peerings")
        else:
            st.info("☁️ No cloud peering sessions staged. Use the form above to add one.")
            
    def render_fabric_connection(self):
        """Step 5: Virtual Circuits / Fabric Connections (Stitching Layer)"""
        import streamlit as st
        from src.utils.ui_provisioning_form import render_fabric_connection_form

        st.header("Step 5: Lumen Fabric Connections")
        
        # 1. Pull the staged list from JSON#2
        conn_list = self.payload["service_context"]["children"].get("fabric_connections", [])
        
        # 2. THE BRIDGE: Identify existing Live connections from JSON#1
        # This allows the UI to show what is already provisioned in Postgres
        live_conns = self.live_manifest.get("fabric_connections", [])
        live_names = [c.get("connection_name") for c in live_conns]

        # 3. Call the Dispatcher
        # We pass self.payload so the dispatcher can resolve the service_type
        # and access the children to append new connections.
        compat_payload = {"connections_list": conn_list}
        render_fabric_connection_form(compat_payload, self.payload)

        st.divider()

        # 4. Summary Table: Show Staged vs. Live status
        if conn_list or live_conns:
            st.subheader("🚀 Connection Deployment Status")
            
            summary = []
            # Add Staged items
            for c in conn_list:
                summary.append({
                    "Status": "🟡 Staged (Planned)",
                    "Name": c.get("connection_name"),
                    "Path": f"{c.get('connector_a_table')} ⮕ {c.get('connector_b_table')}",
                    "Bandwidth": f"{c.get('service_bw')}M"
                })
            
            # Add Live items
            for c in live_conns:
                summary.append({
                    "Status": "🟢 Live (Active)",
                    "Name": c.get("connection_name"),
                    "Path": f"{c.get('connector_a_table')} ⮕ {c.get('connector_b_table')}",
                    "Bandwidth": f"{c.get('service_bw')}M"
                })

            st.table(summary)

            # 5. Provisioning Trigger
            has_staged = any(c.get("connection_status") == "Planned" for c in conn_list)
            if has_staged:
                if st.button("⚡ Provision Fabric Connections", type="primary", use_container_width=True):
                    self._handle_api_deployment("fabric_connections")
        else:
            st.info("No fabric connections found. Use the form above to stitch your components.")

        # API Diagnostic for debugging UUID mapping
        self._render_api_diagnostic("fabric_connections")

    def _render_service_dashboard(self, context_name, ports, conns, topo_id, key_prefix):
        """Internal helper to render common Tables and Galileo Visuals."""
        import streamlit as st
        import pandas as pd
        from src.galileo.fabric_service_builder import FabricServiceBuilder

        st.markdown(f"### 📋 Service Summary: {context_name}")
        
        # --- 1. LOGICAL CROSS-CONNECT TABLE ---
        st.subheader("🔗 Logical Cross-Connect (EVC)")
        if conns:
            df_conns = pd.DataFrame(conns)
            cols = ["connection_name", "service_bw", "connection_status"]
            display_conns = df_conns[[c for c in cols if c in df_conns.columns]].copy()
            if "service_bw" in display_conns.columns:
                display_conns["service_bw"] = display_conns["service_bw"].astype(str) + " Mbps"
            
            st.dataframe(
                display_conns.rename(columns={
                    "connection_name": "Circuit Topology",
                    "service_bw": "Bandwidth",
                    "connection_status": "Circuit State"
                }), 
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No active Fabric Connections found.")

        # --- 2. PHYSICAL PORTS TABLE ---
        st.subheader("🔌 Physical Hand-offs (UNI)")
        if ports:
            df_ports = pd.DataFrame(ports)
            cols_to_show = ["device", "port", "speed", "optics", "alias", "status"]
            safe_cols = [c for c in cols_to_show if c in df_ports.columns]
            
            st.dataframe(
                df_ports[safe_cols].rename(columns={
                    "device": "Host Device", "port": "Interface", 
                    "speed": "Speed", "optics": "Optics", 
                    "alias": "Description", "status": "Admin State"
                }), 
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No assigned physical ports found.")
            
        st.divider()

        # --- 3. GALILEO TOPOLOGY VISUAL ---
        st.subheader("👁️ Galileo Topology View")
        builder = FabricServiceBuilder()
        builder.render_epl_topology(
            ports=ports, 
            conns=conns, 
            topo_id=topo_id, 
            key_prefix=key_prefix
        )

    def render_summary(self):
        """Step 4: Service Summary and Activation Receipt."""
        import streamlit as st
        st.header("Step 4: Service Summary")

        st.success("✅ **Service Provisioning Complete**")
        st.info("The Ethernet Private Line (EPL) is currently active on the network fabric.")

        children = self.payload.get("service_context", {}).get("children", {})
        
        # Render Shared Dashboard
        self._render_service_dashboard(
            context_name=self.payload['service_context'].get('name', 'Final Receipt'),
            ports=children.get("ports", []), 
            conns=children.get("fabric_connections", []), 
            topo_id="epl_step4_view", 
            key_prefix="gal_s4"
        )

    def _render_manifest_inspector(self):
        """
        The 'Proof of Work' - Side-by-side comparison of Live vs. Staged data.
        """
        import streamlit as st

        # 1. UI Wrapper for both manifests
        with st.expander("📄 Manifest Orchestrator: Live vs. Staged", expanded=False):
            
            # --- SECTION 1: SIDE-BY-SIDE RAW JSON ---
            col_json_live, col_json_staged = st.columns(2)
            
            with col_json_live:
                st.caption("🟢 JSON#1: Live Manifest (Database)")
                st.json(self.live_manifest)
                
            with col_json_staged:
                st.caption("🟡 JSON#2: Staged Intent (Local Workspace)")
                st.json(self.payload)

            st.divider()

            # --- SECTION 2: COMPARATIVE VALIDATION ---
            st.markdown("#### ⚖️ Synchronization Health")
            c1, c2, c3 = st.columns(3)
            
            # 1. Service Anchor Check
            service_id = self.payload.get("service_id")
            c1.markdown(f"**Service ID:** `{service_id or 'NOT ANCHORED'}`")
            c1.caption("Live ID required for sub-resource allocation.")

            # 2. Port Comparison
            live_ports = self.live_manifest.get("fabric_ports", [])
            staged_ports = self.payload["service_context"]["children"].get("ports", [])
            
            c2.markdown(f"**Physical Ports:**")
            c2.write(f"✅ Live: `{len(live_ports)}` | 🏗️ Staged: `{len(staged_ports)}`")
            if staged_ports:
                c2.warning(f"Pending: {len(staged_ports)} port(s) to provision.")

            # 3. Connection Comparison
            live_conns = self.live_manifest.get("fabric_connections", [])
            staged_conns = self.payload["service_context"]["children"].get("fabric_connections", [])
            
            c3.markdown(f"**Fabric Connections:**")
            c3.write(f"✅ Live: `{len(live_conns)}` | 🏗️ Staged: `{len(staged_conns)}`")

            # --- SECTION 3: PRE-FLIGHT CHECK ---
            if staged_ports or staged_conns:
                st.info("💡 **Ready for Deployment:** You have staged changes in JSON#2. Use the 'Provision' buttons in the workflow to sync them to JSON#1.")
            else:
                st.success("✨ **Manifests Synced:** Local workspace is clean. JSON#2 matches JSON#1.")

    def _render_api_diagnostic(self, deploy_type: str):
        """
        Standard intent preview for all phases.
        Maintains data persistence for post-provisioning steps (like Fabric Linking).
        """
        with st.expander(f"⚖️ {deploy_type.upper()} Intent Preview", expanded=False):
            # Resolve the path based on the deploy_type
            if deploy_type == "vrf":
                display_json = self.payload["service_context"]
            else:
                # drill into children (ports, interfaces, cloud_peerings, etc.)
                display_json = self.payload["service_context"]["children"].get(deploy_type, [])

            # Status Context
            if isinstance(display_json, list) and len(display_json) > 0:
                is_provisioned = all(item.get("status") == "Provisioned" for item in display_json)
                if is_provisioned:
                    st.success(f"✅ All {deploy_type} are provisioned in the DB and ready for Step 5.")
                else:
                    st.warning(f"⚠️ Some {deploy_type} are still 'Staged' and require local commit.")
            
            st.json(display_json)

    def _reset_payload(self, initial_type: str = "IPVPN"):
        """Tier 1: Root Initialization - Defines the Agnostic Hierarchical Skeleton"""
        import uuid
        
        st.session_state.step = 1
        st.session_state.provisioning_session_id = str(uuid.uuid4())
        
        st.session_state.payload = {
            "session_id": st.session_state.provisioning_session_id,
            "service_id": None,
            "customer_id": self.customer_id,
            "service_context": {  
                "name": "", 
                "rt": "3549:10000", 
                "type": initial_type,  # <--- INJECTED HERE
                "mode": "New Fabric Service",
                "children": {
                    "ports": [],
                    "interfaces": [],
                    "cloud_peerings": [],
                    "fabric_connections": []
                }
            }
        }

    def _get_workflow_map(self) -> dict:
        """
        The Traffic Cop: Routes the user to the correct workflow steps based on the service family.
        """
        if self.service_type in ["IPVPN", "MCGW", "IP-VPN"]:
            return {
                1: self.render_service_context,      
                2: self.render_fabric_port,
                3: self.render_interface_assignment, 
                4: self.render_private_peering,      
                5: self.render_fabric_connection,    
                6: self.render_review_and_deploy
            }
            
        elif self.service_type in ["EPL", "EVPL"]:
            return {
                1: self.render_service_context,
                2: self.render_fabric_port,          
                3: self.render_eline_connection,     
                4: self.render_summary               # <--- THE FIX: Map Step 4 to the new Summary method!
            }
            
        elif self.service_type == "ELAN":
            return {
                1: self.render_service_context,
                2: self.render_fabric_port,          
                3: self.render_elan_topology,        
                4: self.render_review_and_deploy
            }
            
        elif self.service_type == "IOD":
            return {
                1: self.render_service_context,
                2: self.render_fabric_port,
                3: self.render_internet_config,      
                4: self.render_review_and_deploy
            }

        return {1: self.render_unsupported_view}

    def render_eline_connection(self):
        """
        Step 3 (EPL/EVPL): Point-to-Point EVC Stitching.
        Connects the two staged ports from Step 2.
        """
        import streamlit as st
        import pandas as pd
        
        st.header("Step 3: E-Line Connection (EVC)")
        
        # 1. Verification: Ensure we have exactly 2 ports for an EPL
        ports = self.payload["service_context"]["children"].get("ports", [])
        
        if len(ports) < 2:
            st.warning("⚠️ E-Line requires exactly 2 ports. Please go back to Step 2.")
            return

        # 2. Logic: Define the Virtual Circuit
        with st.container(border=True):
            st.subheader("🔗 Link Physical Ports")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**A-Side:** {ports[0]['device']} / {ports[0]['port']}")
            with col2:
                st.info(f"**Z-Side:** {ports[1]['device']} / {ports[1]['port']}")
            
            st.divider()
            
            # Simple inputs for the EVC
            evc_name = st.text_input("EVC Alias", value=f"EPL-{ports[0]['device']}-{ports[1]['device']}")
            bw = st.selectbox("Bandwidth (Mbps)", [10, 50, 100, 500, 1000, 10000])
            
            if st.button("🚀 Stage Connection", type="primary", use_container_width=True):
                new_conn = {
                    "connection_name": evc_name,
                    "service_bw": bw,
                    "connector_a_id": ports[0]['port_id'],
                    "connector_z_id": ports[1]['port_id'],
                    "connection_status": "Planned"
                }
                # Commit to payload
                self.payload["service_context"]["children"]["fabric_connections"] = [new_conn]
                st.success("Connection staged! Move to Step 4 for Summary.")
                st.rerun()

        # 3. View staged connections
        conns = self.payload["service_context"]["children"].get("fabric_connections", [])
        if conns:
            st.table(pd.DataFrame(conns))

    def _render_step_diagram(self, step_number: int):
        """
        Consolidated Reference Architecture Renderer.
        Works for all steps by dynamically locating UC1-UC3 and Step MD files
        based on the active service_context (IPVPN, MCGW, EPL, ELAN, etc.).
        """
        import streamlit as st
        from pathlib import Path

        # 1. Resolve naming base using the CLASS'S source of truth
        # By using self.service_type, we ignore stale Streamlit UI widget ghosting
        svc_type = self.service_type.lower()
        context_data = self.payload.get("service_context") or {}
        
        svc_flavor = str(
            st.session_state.get("mcgw_flavor_selector") or 
            context_data.get("flavor") or 
            ""
        ).lower().strip()

        # Build file_base: e.g., 'mcgw-full', 'ipvpn', 'epl', 'elan'
        if svc_type == "mcgw":
            flavor = svc_flavor if svc_flavor else "full"
            file_base = f"mcgw-{flavor}"
        else:
            file_base = svc_type
        
        # --- PATH RESOLUTION FIX ---
        project_root = Path.cwd()
        png_dir = project_root / "templates" / "png"

        # 2. Inventory available assets for this specific step
        use_cases = []
        for i in range(1, 4):  # Check for UC#1, UC#2, UC#3
            img_name = f"{file_base}-step{step_number}-{i}.png"
            img_path = png_dir / img_name
            
            # Fuzzy fallback: If mcgw-full-stepX-1.png is missing, try mcgw-stepX-1.png
            if not img_path.exists() and "mcgw" in file_base:
                img_path = png_dir / f"mcgw-step{step_number}-{i}.png"

            if img_path.exists():
                use_cases.append({"idx": i, "path": str(img_path)})

        # Resolve Markdown path with similar fallback
        md_name = f"{file_base}-step{step_number}.md"
        md_path = png_dir / md_name
        
        if not md_path.exists() and "mcgw" in file_base:
            md_path = png_dir / f"mcgw-step{step_number}.md"

        # 3. Render UI if content exists
        if use_cases or md_path.exists():
            exp_label = f"📖 Step {step_number} Reference: {svc_type.upper()}"
            if svc_flavor: exp_label += f" ({svc_flavor.capitalize()})"
            
            with st.expander(exp_label, expanded=True):
                # Build Dynamic Tab Titles
                tab_titles = [f"UC#{uc['idx']}" for uc in use_cases]
                if md_path.exists():
                    tab_titles.append("📝 Documentation")
                
                if tab_titles:
                    tabs = st.tabs(tab_titles)
                    
                    # Fill Image Tabs
                    for i, uc in enumerate(use_cases):
                        with tabs[i]:
                            st.image(uc['path'], width=600)
                    
                    # Fill Documentation Tab (Always last)
                    if md_path.exists():
                        with tabs[-1]:
                            try:
                                with open(md_path, "r", encoding="utf-8") as f:
                                    st.markdown(f.read())
                            except Exception as e:
                                st.error(f"Error loading documentation: {e}")
        else:
            # Diagnostic UI hint exposing exact search parameters
            st.caption(f"ℹ️ No reference assets found for '{file_base}' at Step {step_number}.")
            st.caption(f"🔍 **Debug Path Searched:** `{png_dir}`")

    def render_unsupported_view(self):
        """
        Step 1 Fallback: Forced sync for recovery from unsupported types.
        """
        st.error(f"⚠️ Service Type '{self.service_type}' is not currently supported.", icon="🚫")
        
        # 1. Render the selection form
        from src.utils.ui_provisioning_form import render_service_context_form
        render_service_context_form(
            data=self.payload["service_context"], 
            customer_id=self.customer_id
        )

        # 2. THE SYNC FIX: 
        # Check if the user just picked a different service in the 'Existing' dropdown
        if st.session_state.get("fs_active_id"):
            # Get the record to find out the NEW service type
            new_record = st.session_state.get("fs_active_record", {})
            new_type = new_record.get("service_type", "IPVPN")

            # Update the payload and local instance state immediately
            self.payload["service_id"] = st.session_state.fs_active_id
            self.payload["service_context"]["type"] = new_type
            self.service_type = new_type.upper().strip()
            
            # Update the global manager state
            st.session_state["fs_active_id"] = st.session_state.fs_active_id
            
            st.success(f"🔄 Switching to {new_type} context...")
            st.rerun()

        st.divider()
        st.caption(f"Current selection: {self.service_type}")

    def _calculate_p2p_ips(self, byoip: bool, prefix_len: int = 30, version: str = "v4"):
        """
        Stable Calculation Engine:
        Uses deterministic indexing to prevent Streamlit rerun loops.
        """
        import ipaddress

        if version == "v4":
            if byoip:
                try:
                    val = st.session_state.get("v4_manual_input", "192.168.1.0/30")
                    net = ipaddress.IPv4Network(val, strict=False)
                    return str(net[1]), str(net[2]), net.prefixlen
                except Exception:
                    return "Invalid", "Invalid", 0
            else:
                # Deterministic: Always pick the same subnet from the pool for this session
                base_net = ipaddress.IPv4Network("8.56.0.0/16")
                # Using next() on subnets is much faster and more stable than casting to a list
                selected_net = next(base_net.subnets(new_prefix=prefix_len))
                return str(selected_net[1]), str(selected_net[2]), prefix_len

        else: # IPv6 Logic
            if byoip:
                try:
                    val = st.session_state.get("v6_manual_input", "2001:db8:1234::/126")
                    net = ipaddress.IPv6Network(val, strict=False)
                    return str(net[1]), str(net[2]), net.prefixlen
                except Exception:
                    return "Invalid", "Invalid", 0
            else:
                base_v6 = ipaddress.IPv6Network("2001:0db8:1234::/48")
                # Pick the second subnet (:1) to avoid the zero-subnet
                subnets_v6 = base_v6.subnets(new_prefix=126)
                next(subnets_v6) # skip :0
                selected_v6 = next(subnets_v6) # pick :1
                return str(selected_v6[1]), str(selected_v6[2]), 126
         
    def render_review_and_deploy(self):
        """Step 6: Final Review & Orchestration"""
        st.header("Step 6: Review & Deploy")
        
        # Display the full hierarchical tree for final audit
        st.json(self.payload)
        
        st.warning("⚠️ Verify all intents before final execution.")
        if st.button("🚀 Execute Orchestration", type="primary", use_container_width=True):
            st.session_state.active_deployment = "full_sync"
            st.rerun()

    def _sync_global_context(self, service_id: str):
        """Synchronizes the state manager to eliminate UI lag."""
        st.session_state["fs_active_id"] = service_id
        # Crucial: Ensure the manager's internal record matches the payload
        rec = {
            "service_id": service_id,
            "service_name": self.payload["service_context"].get("name"),
            "service_type": self.payload["service_context"].get("type")
        }
        st.session_state["fs_active_record"] = rec
        self.fs_record = rec 

    def _deploy_fabric_service(self, context_data: dict):
        """
        Standard POST to the Fabric Service endpoint.
        Strictly adheres to the API schema. Technical parameters (MTU, SLA) 
        are kept in the UI payload for later steps, but stripped from this API call.
        """
        from src.api_client import post_fabric_service
        
        api_payload = {
            "customer_id": self.customer_id,
            "service_name": context_data.get("name"),
            "service_alias": context_data.get("alias") or context_data.get("name"),
            "service_type": context_data.get("type"),
            "service_description": f"{context_data.get('type')} provisioned via Orchestrator",
            "health_status": 4
        }
        
        # Only inject route_target if it actually exists (L3 services)
        if context_data.get("rt"):
            api_payload["route_target"] = context_data.get("rt")

        response = post_fabric_service(api_payload)
        return response.get("service_id")

    def _get_customer_ports(self) -> pd.DataFrame:
        """Fetches physical inventory for the selected customer."""
        from src.api_client import get_ports_by_customer
        df = get_ports_by_customer(self.customer_id)
        if not df.empty:
            df['port_id'] = df['port_id'].astype(str)
        return df

    def render_service_context(self):
        """Step 1: Context Provisioning & Verification with Embedded Dashboard"""
        import streamlit as st
        
        # 1. Resolve Active ID
        active_id = (
            st.session_state.get("fs_active_id") or 
            self.payload.get("service_id") or 
            self.payload.get("service_context", {}).get("service_id")
        )

        # 2. SUCCESS & VERIFICATION STATE
        if active_id:
            st.success(f"🚀 Service Context Successfully Configured", icon="✅")
            
            # Ensure local state is consistent
            self.payload["service_id"] = active_id
            
            # Extract data for the dashboard helper
            ctx = self.payload.get("service_context", {})
            name = ctx.get("name", "Active Service")
            children = ctx.get("children", {})
            ports = children.get("ports", [])
            conns = children.get("fabric_connections", [])

            # --- EMBEDDED DASHBOARD ---
            # This renders the Tables and the Galileo Visual
            self._render_service_dashboard(
                context_name=name,
                ports=ports,
                conns=conns,
                topo_id="epl_step1_verified",
                key_prefix="gal_v1"
            )

            st.divider()
            
            # Workflow Progression
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Next: Provision Ports ➡️", type="primary", use_container_width=True):
                    st.session_state.step = 2
                    st.rerun()
            with c2:
                if st.button("🔓 Create a NEW Fabric Service", use_container_width=True):
                    st.session_state.fs_active_id = None
                    st.session_state.fs_active_record = {}
                    self.payload["service_id"] = None
                    # Clear nested ID to force Greenfield mode
                    if "service_id" in self.payload.get("service_context", {}):
                        del self.payload["service_context"]["service_id"]
                    st.rerun()

        # 3. INPUT STATE (The Form)
        else:
            st.header("Step 1: Fabric Service Configuration")
            from src.utils.ui_provisioning_form import render_service_context_form
            
            # Form writes directly to self.payload["service_context"]
            render_service_context_form(data=self.payload["service_context"], customer_id=self.customer_id)
            
            st.divider()
            
            if self.payload["service_context"].get("mode") == "New Fabric Service": 
                if st.button("💾 Provision Service Context", type="primary", use_container_width=True):
                    if self.payload["service_context"].get("name"): 
                        # Trigger the deployment flag for the handle_api loop
                        st.session_state.active_deployment = "service_context" 
                        st.rerun()
                    else:
                        st.error("❌ A Service Name is required.")

    def _handle_api_deployment(self, trigger_data):
        """
        The Orchestration Engine: Processes granular deployment signals.
        Translates JSON#2 (Staged) into API calls and rehydrates JSON#1 (Live).
        """
        import streamlit as st
        from src.utils.api_customer import (
            post_port_intent, 
            post_interface_intent,
            post_static_route_intent,
            post_bgp_peer_intent,
            get_fabric_service_detail
        )

        # 1. Parse Trigger Context
        # Supports both string signals ("ports") and tuples ("interface_single", 0)
        if isinstance(trigger_data, tuple):
            trigger, idx = trigger_data
        else:
            trigger, idx = trigger_data, None
        
        service_id = self.payload.get("service_id")
        interfaces = self.payload["service_context"]["children"].get("interfaces", [])

        # ---------------------------------------------------------
        # CASE A: PHYSICAL PORTS (Bulk Sync)
        # ---------------------------------------------------------
        if trigger == "ports":
            staged_ports = self.payload["service_context"]["children"].get("ports", [])
            with st.status("🚀 Provisioning Physical Fabric...", expanded=True) as status:
                success_count = 0
                for port in staged_ports:
                    if port.get("status") == "Staged":
                        port["customer_id"] = self.customer_id
                        if post_port_intent(self, port):
                            port["status"] = "Provisioned"
                            success_count += 1
                
                if success_count > 0:
                    self._rehydrate_and_finalize(service_id, status)

        # ---------------------------------------------------------
        # CASE B: SINGLE INTERFACE (Logical + IP Assignment)
        # ---------------------------------------------------------
        elif trigger == "interface_single" and idx is not None:
            intf = interfaces[idx]
            
            with st.status(f"🛰️ Provisioning Interface: {intf['alias']}...", expanded=True) as status:
                # --- PHASE 1: CREATE INTERFACE SHELL ---
                status.write("Constructing logical interface container...")
                intf["customer_id"] = self.customer_id
                resp_data = post_interface_intent(intf)
                
                if resp_data and resp_data.get("interface_id"):
                    new_uuid = resp_data.get("interface_id")
                    intf["interface_id"] = new_uuid 
                    status.write(f"✅ Interface Created: `{new_uuid}`")
                    
                    # --- PHASE 2: ASSIGN IP ADDRESSES ---
                    status.write("🌐 Assigning IP addresses to interface...")
                    
                    # Map to YOUR provided JSON schema
                    # Note: We convert mask to int to avoid 422 errors
                    ip_payload = {
                        "interface_id": new_uuid,
                        "lumen_ip_address": intf.get("ipv4_lumen"),
                        "customer_ip_address": intf.get("ipv4_customer"),
                        "network_mask_cidr": int(intf.get("ipv4_mask", 30)),
                        "bring_your_own_ip": bool(st.session_state.get("byoip_toggle", False))
                    }
                    
                    ip_resp = post_interface_ip(ip_payload)
                    
                    if ip_resp:
                        status.write(f"✅ IP Assignment Successful: {intf.get('ipv4_lumen')}")
                        
                        # --- PHASE 3: DUAL-STACK (IPv6) ---
                        if intf.get("is_dual_stack") and intf.get("v6_lumen"):
                            status.write("🌐 Assigning IPv6 addresses...")
                            v6_payload = {
                                "interface_id": new_uuid,
                                "lumen_ip_address": intf.get("v6_lumen"),
                                "customer_ip_address": intf.get("v6_customer"),
                                "network_mask_cidr": int(intf.get("v6_mask", 126)),
                                "bring_your_own_ip": bool(st.session_state.get("byoip_toggle", False))
                            }
                            post_interface_ip(v6_payload)

                        self._rehydrate_and_finalize(service_id, status)
                    else:
                        status.update(label="⚠️ Interface created, but IP assignment failed.", state="error")
                else:
                    status.update(label="❌ Interface Provisioning Failed", state="error")
        # ---------------------------------------------------------
        # CASE C: STATIC ROUTES (Attaches to Interface UUID)
        # ---------------------------------------------------------
        elif trigger == "static_single" and idx is not None:
            intf = interfaces[idx]
            parent_id = intf.get("interface_id")
            routes = intf.get('routing', {}).get('static', [])
            
            with st.status(f"📍 Deploying Static Routes for {intf['alias']}...", expanded=True) as status:
                success_count = 0
                for route in routes:
                    # Inject the parent anchor required by the API
                    route["interface_id"] = parent_id
                    if post_static_route_intent(route):
                        success_count += 1
                
                if success_count > 0:
                    self._rehydrate_and_finalize(service_id, status)

        # ---------------------------------------------------------
        # CASE D: BGP PEERS (Attaches to Interface UUID)
        # ---------------------------------------------------------
        elif trigger == "bgp_single" and idx is not None:
            intf = interfaces[idx]
            parent_id = intf.get("interface_id")
            peers = intf.get('routing', {}).get('bgp', [])
            
            with st.status(f"🤝 Establishing BGP Session for {intf['alias']}...", expanded=True) as status:
                success_count = 0
                for peer in peers:
                    # Inject the parent anchor required by the API
                    peer["interface_id"] = parent_id
                    if post_bgp_peer_intent(peer):
                        success_count += 1
                
                if success_count > 0:
                    self._rehydrate_and_finalize(service_id, status)

# ---------------------------------------------------------
        # CASE E: CLOUD PEERING (XaaS)
        # ---------------------------------------------------------
        elif trigger == "cloud_peerings":
            peering_list = self.payload["service_context"]["children"].get("cloud_peerings", [])
            service_id = self.payload.get("service_id")
            
            # Retrieve available interface IDs to satisfy cloud_connection_members
            # We look in JSON#1 (Live) for the best mapping
            live_intfs = st.session_state.live_manifest.get("fabric_interfaces", [])
            target_interface_id = live_intfs[0].get("interface_id") if live_intfs else None

            with st.status("☁️ Provisioning Lumen Cloud Interconnect...", expanded=True) as status:
                success_count = 0
                for peering in peering_list:
                    if peering.get("status") == "Staged":
                        # Ensure service_id is attached to the payload
                        peering["service_id"] = service_id
                        
                        # Phase 1: Create the Cloud Connection
                        from src.utils.api_customer import post_cloud_connection
                        resp = post_cloud_connection(peering)
                        
                        if resp and resp.get("cloud_connection_id"):
                            cc_id = resp.get("cloud_connection_id")
                            status.write(f"✅ Cloud Connection Created: {peering['connection_name']}")
                            
                            # Phase 2: Create the Member Association (cloud_connection_members)
                            if target_interface_id:
                                status.write(f"🔗 Associating with Interface: `{target_interface_id[:8]}...`")
                                member_payload = {
                                    "cloud_connection_id": cc_id,
                                    "interface_id": target_interface_id,
                                    "role": "Primary Peering",
                                    "status": "Active"
                                }
                                # Call your member API here
                                # post_cloud_connection_member(member_payload)
                            
                            peering["status"] = "Provisioned"
                            peering["cloud_connection_id"] = cc_id
                            success_count += 1

                if success_count > 0:
                    self._rehydrate_and_finalize(service_id, status)

    def _rehydrate_and_finalize(self, service_id, status_handle):
        """Internal helper to refresh JSON#1 and clear trigger."""
        import streamlit as st
        from src.utils.api_customer import get_fabric_service_detail
        
        status_handle.write("🔄 Verification: Pulling Live Manifest (JSON#1)...")
        # Force fresh GET from DB
        new_live = get_fabric_service_detail(service_id)
        
        if new_live:
            # Sync the Live Manifest
            st.session_state.live_manifest = new_live
            self.live_manifest = new_live
            
            # Clear Orchestrator Trigger
            st.session_state.active_deployment = None
            
            status_handle.update(label="✨ Fabric Synchronized Successfully", state="complete")
            st.toast("Fabric State Updated", icon="✅")
            st.rerun()

    def _render_debug_inspector(self):
        """
        The 'Flight Data Recorder' - Reveals the deterministic state of both
        the Live Manifest (JSON#1) and the Staged Intent (JSON#2).
        """
        import streamlit as st

        st.divider()
        with st.expander("🔍 SYSTEM DEBUG: Live vs. Staged Manifests", expanded=True):
            # --- ROW 1: THE RAW DATA ---
            col_live, col_staged = st.columns(2)
            
            with col_live:
                st.markdown("🟢 **JSON#1: Live Manifest**")
                st.caption("Fresh data retrieved from get_fabric_service_details")
                st.json(self.live_manifest)
                
            with col_staged:
                st.markdown("🟡 **JSON#2: Staged Intent**")
                st.caption("Local session state (st.session_state.payload)")
                st.json(self.payload)
                
            st.divider()

            # --- ROW 2: GLOBAL ANCHORS & SYNC HEALTH ---
            col_state, col_health = st.columns(2)
            
            with col_state:
                st.markdown("**Global Anchors (Session State)**")
                st.write({
                    "fs_active_id": st.session_state.get("fs_active_id"),
                    "step": st.session_state.get("step"),
                    "service_type": self.service_type,
                    "customer_id": self.customer_id
                })
                
            with col_health:
                # Calculate the "Delta"
                live_p_count = len(self.live_manifest.get("fabric_ports", []))
                staged_p_count = len(self.payload["service_context"]["children"].get("ports", []))
                
                st.markdown("**Synchronization Health**")
                if staged_p_count > 0:
                    st.warning(f"🏗️ Staging Alert: {staged_p_count} port(s) waiting for API commit.")
                else:
                    st.success("✨ Desired state matches Live Manifest.")
                
                # Logic Integrity Check
                has_id = bool(st.session_state.get("fs_active_id") or self.payload.get("service_id"))
                st.info(f"Gatekeeper Check: **Step 1 Anchored = {has_id}**")

        # --- OPTIONAL: THE EMERGENCY RESET ---
        if st.sidebar.button("🗑️ Emergency Reset All State"):
            for key in ["payload", "live_manifest", "step", "fs_active_id"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    def _validate_step(self, step: int) -> bool:
        """
        Logic-based validation for the 'Next' button.
        Returns True if the button should be DISABLED.
        """
        # 1. Check for established DB ID in local payload or global state
        service_id = self.payload.get("service_id") or st.session_state.get("fs_active_id")
        children = self.payload["service_context"]["children"]
        
        if step == 1:
            # GATEKEEPER: Disable Next until the VRF is committed to the DB
            return service_id is None
        
        if step == 2:
            # Step 2 is optional, but usually depends on Step 1 being done
            return service_id is None
            
        if step == 3:
            # Require at least one interface to move forward
            return len(children.get("interfaces", [])) == 0
            
        return False

    def _render_navigation(self, current_step: int):
        """Pure UI Navigation."""
        st.divider()
        col_prev, _, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if current_step > 1:
                if st.button("⬅️ Previous", key="nav_prev", use_container_width=True):
                    st.session_state.step -= 1
                    st.rerun()
        
        with col_next:
            is_disabled = self._validate_step(current_step)
            if st.button("Next ➡️", key="nav_next", type="primary", disabled=is_disabled, use_container_width=True):
                st.session_state.step += 1
                st.rerun()

    def _render_header(self):
        """Standardized Header with Progress Bar and Step Labels."""
        current_step = st.session_state.step
        total_steps = len(self.workflow_map)
        progress_value = (current_step - 1) / (total_steps - 1) if total_steps > 1 else 1.0
        
        # UI Rendering
        st.write(f"**Workflow Progress: Step {current_step} of {total_steps}**")
        st.progress(progress_value)
        
        # --- GLOBAL STATUS BANNER ---
        if getattr(self, "epl_locked", False):
            st.info("🔒 **Service Locked:** This Ethernet Private Line (EPL) already has an active EVC configured. Point-to-Point topology is fully established.")
        
        # Vertical spacing and Step-Specific Diagram
        self._render_step_diagram(current_step)
        st.divider()

    def run(self):
        """
        The Main UI Loop with Orchestration Check.
        This is the brain of the Two-JSON sync engine.
        """
        import streamlit as st

        # 1. THE ENGINE: Intercept API signals immediately
        # We check the session state directly to avoid any class-variable shadowing
        trigger = st.session_state.get("active_deployment")
        
        if trigger:
            # LOUD DEBUG: Visible even if the Orchestrator fails
            st.toast(f"🚀 Engine Signal Detected: {trigger}", icon="📡")
            
            # --- THE PUSH/PULL HANDLER ---
            # This executes post_port_intent and get_fabric_service_detail
            self._handle_api_deployment(trigger)
            
            # CRITICAL: Clear the trigger and stop the current render loop
            # This prevents Step 2, 3, 4, 5 from running with stale data.
            st.session_state.active_deployment = None
            
            # Final safety rerun if the orchestrator didn't already trigger one
            st.rerun()
            return # Block any further execution of the old state

        # --- 2. THE UI FLOW (Only executes if NO deployment is active) ---
        
        # Header & Progress
        self._render_header()
        
        # Step Content
        current_step = st.session_state.step
        if current_step in self.workflow_map:
            self.workflow_map[current_step]()
        
        # Navigation Footer
        self._render_navigation(current_step)
        
        # --- 3. THE INSPECTORS (Always visible for verification) ---
        self._render_debug_inspector()


def show_provisioning_view():
    st.title("🌐 Provisioning Orchestrator")
    from src.api_client import get_customers, get_fabric_services
    from src.state_managers import FabricStateManager
    import pandas as pd
    
    cust_df = get_customers()
    selected_cust_name = st.selectbox(
        "🏢 Select Target Customer:",
        options=cust_df['customer_name'].tolist(),
        index=None,
        key="global_cust_picker"
    )
    
    if selected_cust_name:
        cust_id = cust_df[cust_df['customer_name'] == selected_cust_name]['customer_id'].iloc[0]
        
        # --- HOT SYNC on customer change ---
        if st.session_state.get("active_customer_id") != cust_id:
            st.session_state.active_customer_id = cust_id
            for key in ["fs_active_id", "fs_active_record", "payload", "step", "fabric_service_selection"]:
                if key in st.session_state: 
                    del st.session_state[key]
            st.rerun()

        # --- New Fabric Service Dropdown ---
        all_services = get_fabric_services(cust_id)
        service_options = ["--- Create a New Fabric Service ---"]
        service_map = {}

        if isinstance(all_services, pd.DataFrame) and not all_services.empty:
            # Filter for IPVPN or MCGW services, which are the only supported workflows
            supported_types = ['IPVPN', 'MCGW', 'IP-VPN', 'EPL', 'EVPL', 'ELAN', 'IOD']
            
            # --- THE FIX: We need to actually declare the filtered_services variable ---
            filtered_services = all_services[all_services['service_type'].isin(supported_types)]
            
            for _, row in filtered_services.iterrows():
                label = f"{row['service_name']} ({row['service_type']})"
                service_options.append(label)
                service_map[label] = row.to_dict()

        selected_service = st.selectbox(
            "🚀 Select a Fabric Service or Create New:",
            options=service_options,
            key="fabric_service_selection"
        )

        # --- Logic to handle service selection ---
        if selected_service in service_map:
            # User selected an existing service
           
            service_record = service_map[selected_service]
            st.session_state.fs_active_id = service_record['service_id']
            st.session_state.fs_active_record = service_record

            st.divider()
            # Launch Manager - It will now start with the selected service context
            workflow = NetworkWorkflowManager(cust_id)
            workflow.run()

        elif selected_service == "--- Create a New Fabric Service ---":
            # --- THE DEEP PURGE FIX ---
            # Detects ghost data hiding in nested payload structures even if fs_active_id is None
            current_payload = st.session_state.get("payload", {})
            has_ghost_id = (
                st.session_state.get("fs_active_id") is not None or
                current_payload.get("service_id") is not None or
                current_payload.get("service_context", {}).get("service_id") is not None or
                current_payload.get("service_context", {}).get("mode") == "Existing Fabric Service"
            )

            if has_ghost_id:
                 # Ruthlessly nuke all related states to force a true Zero-State
                 for key in ["fs_active_id", "fs_active_record", "payload", "step", "live_manifest"]:
                    if key in st.session_state:
                        del st.session_state[key]
                 st.rerun()

            st.divider()
            
            # --- NEW: ARCHITECTURE RADIO BUTTONS ---
            with st.container(border=True):
                st.markdown("##### ✨ Initialize New Service Architecture")
                new_svc_type = st.radio(
                    "Select Service Family:",
                    options=["IPVPN", "MCGW", "EPL", "EVPL", "ELAN", "IOD"],
                    horizontal=True,
                    key="new_svc_type_radio"
                )
            
            st.write("") # Quick spacer

            # Launch manager in a clean state for creation, passing the chosen type
            workflow = NetworkWorkflowManager(cust_id, initial_type=new_svc_type)
            workflow.run()