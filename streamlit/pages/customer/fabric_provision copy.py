import streamlit as st
import pandas as pd
import random
import ipaddress
from src.ui_components import UI
from src.utils.ui_provisioning_form import render_vrf_context_form,render_fabric_port_form
from src.api_client import (
    get_ports_by_customer, 
    get_all_devices, 
    get_ports_by_device
)
from src.ui_messages import MessageCenter
from src.state_managers import FabricStateManager

# --- THE HAMMER ---
if "active_deployment" in st.session_state and st.session_state.active_deployment is not None:
    # This will stay on screen until we manually clear it
    st.sidebar.error(f"🚨 CRITICAL DEBUG: Trigger Found: {st.session_state.active_deployment}")
    
    # If we are stuck, this button will save us
    if st.sidebar.button("🗑️ Force Clear Trigger"):
        st.session_state.active_deployment = None
        st.rerun()

class NetworkWorkflowManager:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.manager = FabricStateManager()
        
        # 1. Ensure the payload is anchored to this specific customer
        if 'payload' not in st.session_state or st.session_state.payload.get("customer_id") != self.customer_id:
            self._reset_payload()
        
        self.payload = st.session_state.payload
        self.fs_record = self.manager.get_active_record("fs") or {}
        self.service_type = str(self.fs_record.get("service_type", "IPVPN")).upper().strip()
        self.workflow_map = self._get_workflow_map()

        # 2. Observer for Micro-Intents
        trigger = st.session_state.get("active_deployment")
        if trigger:
            self._handle_api_deployment(trigger)   # --- ZONE 1: STATE & INTENT MANAGEMENT ---

    def _hydrate_brownfield_payload(self, svc_data: dict):
        """Ensures the Manager's local state and UI state are perfectly synced."""
        self.payload["vrf"].update({
            "service_id": svc_data.get("service_id"),
            "name": svc_data.get("service_name"),
            "mode": "Existing Fabric Service"
        })
        # Explicitly set the widget state so Step 1 'Next' button enables
        st.session_state["vrf_name_input"] = svc_data.get("service_name")
        self._sync_global_context(svc_data.get("service_id"))

    def _get_workflow_map(self) -> dict:
        l3_types = ["IPVPN", "MCGW", "IP-VPN"]
        # Now self.service_type exists, so this won't crash
        if any(x in self.service_type for x in l3_types):
            return {
                1: self.render_vrf_context,
                2: self.render_fabric_port,
                3: self.render_interface_assignment,
                4: self.render_private_peering,
                5: self.render_fabric_connection,
                6: self.render_review_and_deploy
            }
        return {1: self.render_unsupported_view}

    def _reset_payload(self):
        """Tier 1: Root Initialization - Defines the Hierarchical Skeleton"""
        import uuid
        st.session_state.provisioning_session_id = str(uuid.uuid4())
        
        st.session_state.payload = {
            "session_id": st.session_state.provisioning_session_id,
            "service_id": self.manager.get_active_id("fs"),
            "customer_id": self.customer_id,
            "vrf": {
                "name": "", 
                "rt": "3549:10000", 
                "type": "IPVPN",
                "mode": "New Fabric Service",
                # This is the node your renderers are looking for
                "children": {
                    "ports": [],              # Step 2
                    "interfaces": [],         # Step 3
                    "cloud_peerings": [],     # Step 4
                    "fabric_connections": []  # Step 5
                }
            }
        }
    
    def _ensure_payload_integrity(self):
        """Forces a reset if the state doesn't match the new hierarchical schema."""
        if 'payload' not in st.session_state:
            return self._reset_payload()
            
        # Check for the specific key that caused your crash
        if "children" not in st.session_state.payload.get("vrf", {}):
            st.warning("🔄 Upgrading Provisioning Session to Hierarchical Schema...")
            self._reset_payload()
            
    # --- ZONE 2: API ORCHESTRATION ---

    def render_interface_assignment(self):
        st.header("Step 3: Interface & Routing")
        
        # 1. Show the Forms (Builder, Static, BGP)
        # ... form rendering code ...

        # 2. Show the Diagnostic Launchpad
        # This now contains the three separate buttons
        self._render_api_diagnostic("interfaces")

    def _post_static_route_to_api(self, route_data: dict):
        """
        Bridge to Phase 2: Static Route Database Entry.
        Hardened to handle multiple key variations and force string casting.
        """
        from src.utils.api_customer import post_static_route
        
        # 1. Scrape Prefix (Try API key first, then UI key, then split network)
        ip = route_data.get("ip_prefix") or route_data.get("prefix")
        mask = route_data.get("prefix_mask") or route_data.get("mask")
        
        if not ip and "network" in route_data:
            raw_net = str(route_data.get("network", ""))
            if "/" in raw_net:
                ip, mask = raw_net.split("/")
            else:
                ip, mask = raw_net, "32"

        # 2. Scrape Next Hop
        nh = route_data.get("next_hop_ip") or route_data.get("next_hop")

        # 3. Construct Payload with STRICT string casting for FastAPI
        payload = {
            "interface_id": route_data.get("interface_id"),
            "ip_prefix": str(ip) if ip else None,
            "prefix_mask": str(mask) if mask else "32",
            "next_hop_ip": str(nh) if nh else None,
            "metric": int(route_data.get("metric", 0)),
            "community": str(route_data.get("community", "3549:100"))
        }

        # Safety Intercept: Don't POST if we are missing required fields
        if not payload["ip_prefix"] or not payload["next_hop_ip"]:
            st.error(f"❌ Mapping Error: Missing IP or Next Hop in {route_data}")
            return None

        return post_static_route(payload)

    def _post_bgp_neighbor_to_api(self, bgp_data: dict):
        from src.utils.api_customer import post_bgp_neighbor
        
        # DEBUG 1: Is the bridge even being called?
        st.sidebar.write("🟢 Bridge Called for:", bgp_data.get('neighbor_ip'))

        payload = {
            "interface_id": bgp_data.get("interface_id"),
            "neighbor_ip": str(bgp_data.get("neighbor_ip")),
            "remote_asn": int(bgp_data.get("customer_as", 0)),
            # ... rest of your mapping ...
        }

        # DEBUG 2: What does the final payload look like?
        st.sidebar.json(payload)

        if not payload["neighbor_ip"] or payload["remote_asn"] == 0:
            # DEBUG 3: If this triggers, the POST never happens
            st.error(f"❌ Safety Stop: IP is {payload['neighbor_ip']} or ASN is {payload['remote_asn']}")
            return None

        return post_bgp_neighbor(payload)

    def _post_cloud_connection_to_api(self, peering_data: dict):
        """
        Bridge to Step 4.
        Strictly aligned with DB Check Constraint: ['Active', 'Planned', 'Capped']
        """
        from src.utils.api_customer import post_cloud_connection
        
        payload = {
            "partner_id": peering_data.get("partner_id"), 
            "connection_name": peering_data.get("name", f"Cloud-{peering_data.get('provider')}"),
            "service_type": peering_data.get("peering_type", "Layer3"),
            
            # FIXED: 'Planned' is the valid constraint value for new builds
            "service_status": "Planned", 
            
            "region": peering_data.get("region"),
            "service_bw": int(peering_data.get("bandwidth", 1000)),
            "redundancy_model": peering_data.get("redundancy", "Single"),
            "description": peering_data.get("description", "Galileo Cloud Peering")
        }
        
        if not payload["partner_id"]:
            import streamlit as st
            st.error("❌ Cloud Peering Error: Missing partner_id.")
            return None

        return post_cloud_connection(payload)

    def _post_fabric_connection_to_api(self, conn_data: dict):
        """
        Final Bridge for Step 5: Fabric Connections.
        Fully aligned with 'fabric_connections' DB schema.
        """
        from src.utils.api_customer import post_fabric_connection
        
        # Pull the parent service ID
        service_id = self.payload.get("service_id") or st.session_state.get("fs_active_id")

        payload = {
            "service_id": str(service_id),
            "connection_name": conn_data.get("connection_name") or "GALILEO-STITCH",
            "connector_a_id": str(conn_data.get("connector_a_id")),
            "connector_b_id": str(conn_data.get("connector_b_id")),
            "connector_a_table": conn_data.get("connector_a_table", "interfaces"),
            "connector_b_table": conn_data.get("connector_b_table", "cloud_connections"),
            "connection_status": "Planned",
            "vrf_name": self.payload["vrf"].get("name"),
            "service_bw": int(conn_data.get("service_bw", 1000)),
            "s_vlan": int(conn_data.get("s_vlan", 0)),
            "c_vlan_list": str(conn_data.get("c_vlan_list", "")),
            "health_status": 4
        }
        
        if not payload["service_id"] or payload["service_id"] == "None":
            st.error("❌ Orchestration Error: Parent Service ID is missing.")
            return None

        return post_fabric_connection(payload)

    def _handle_api_deployment(self, trigger):
        """
        Main Orchestrator for Galileo API calls.
        Now with LOUD diagnostics to troubleshoot BGP 'silence'.
        """
        # 1. Unpack the trigger type
        if isinstance(trigger, tuple):
            deploy_type, idx = trigger
        else:
            deploy_type, idx = trigger, None

        # Reset state immediately to prevent loop
        st.session_state.active_deployment = None
        
        try:
            with st.status(f"🚀 Deploying {deploy_type.upper()}...") as status:
                
                # --- PHASE 1: VRF / SERVICE ROOT ---
                if deploy_type == "vrf":
                        new_id = self._deploy_fabric_service(self.payload["vrf"])
                        if new_id:
                            # This updates fs_active_id and the local payload
                            self._sync_global_context(new_id)
                            self.payload["service_id"] = new_id
                            
                            # The requested success feedback
                            st.toast(f"Provisioned {self.payload['vrf'].get('name')} successfully!", icon="✅")
                            
                            # CRITICAL: Do NOT increment step. Just rerun to show success bar.
                            st.rerun()


                # --- PHASE 2: PHYSICAL PORTS ---
                elif deploy_type == "ports":
                    for port in self.payload["vrf"]["children"]["ports"]:
                        self._post_port_intent(port)
                    st.session_state.step = 3

                # --- PHASE 3A: BULK STATIC ROUTES ---
                elif deploy_type == "static_routes":
                    routes = [r for i in self.payload["vrf"]["children"]["interfaces"] 
                             for r in i.get("routing", {}).get("static", [])]
                    for route in routes:
                        self._post_static_route_to_api(route)
                        st.write(f"✅ Route {route.get('network')} posted.")

                # --- PHASE 3B: BULK BGP PEERS (CRITICAL FIX) ---
                elif deploy_type == "bgp_peers":
                    peers = [b for i in self.payload["vrf"]["children"]["interfaces"] 
                            for b in i.get("routing", {}).get("bgp", [])]
                    
                    if not peers:
                        st.error("❌ No BGP peers found in memory tree.")
                    
                    for peer in peers:
                        # Ensure we have the parent interface UUID
                        # If you haven't posted the interface yet, this will be None
                        if not peer.get("interface_id"):
                            st.warning(f"⚠️ Skipping {peer.get('neighbor_ip')}: Missing Interface UUID. Provision the interface first!")
                            continue
                            
                        st.write(f"📡 Attempting BGP Post for: {peer.get('neighbor_ip') or 'Unknown IP'}")
                        res = self._post_bgp_neighbor_to_api(peer)
                        if res:
                            st.write(f"🤝 BGP Peer {peer.get('neighbor_ip')} posted.")

                # --- PHASE 3C: GRANULAR SINGLE INTERFACE ---
                elif deploy_type == "interface_single":
                    intf = self.payload["vrf"]["children"]["interfaces"][idx]
                    db_intf = self._post_interface_intent(intf)
                    if db_intf:
                        # Capture UUID for child routing objects
                        intf["interface_id"] = db_intf.get("interface_id")
                        # Also inject the ID into children immediately so they are ready
                        for r in intf.get("routing", {}).get("static", []): r["interface_id"] = intf["interface_id"]
                        for b in intf.get("routing", {}).get("bgp", []): b["interface_id"] = intf["interface_id"]
                        st.write(f"✅ {intf['alias']} is now Live.")

                # --- PHASE 3D: GRANULAR SINGLE ROUTE SET ---
                elif deploy_type == "static_single":
                    intf = self.payload["vrf"]["children"]["interfaces"][idx]
                    for route in intf.get("routing", {}).get("static", []):
                        route["interface_id"] = intf.get("interface_id")
                        self._post_static_route_to_api(route)
                    st.write(f"✅ Static routes for {intf['alias']} posted.")

                # --- PHASE 3E: GRANULAR BGP PEER (SINGLE) ---
                elif deploy_type == "bgp_single":
                    intf = self.payload["vrf"]["children"]["interfaces"][idx]
                    for peer in intf.get("routing", {}).get("bgp", []):
                        peer["interface_id"] = intf.get("interface_id")
                        self._post_bgp_neighbor_to_api(peer)
                    st.write(f"🤝 BGP Neighbor for {intf['alias']} posted.")

                # --- PHASE 5: Cloud Peering (SINGLE) ---
                elif deploy_type == "cloud_peerings":
                    peerings = self.payload["vrf"]["children"].get("cloud_peerings", [])
                    
                    for peer in peerings:
                        st.write(f"☁️ Provisioning Cloud Connection: {peer.get('name')}...")
                        res = self._post_cloud_connection_to_api(peer)
                        
                        if res:
                            # Capture the ID returned by the API for Step 5
                            peer["cloud_connection_id"] = res.get("cloud_connection_id")
                            st.write(f"✅ Cloud Peering Live! ID: {peer['cloud_connection_id']}")
                        else:
                            st.error(f"❌ Failed to provision {peer.get('name')}")
                # --- PHASE 5: Cloud Peering (SINGLE) ---

                elif deploy_type == "fabric_connections":
                    conns = self.payload["vrf"]["children"].get("fabric_connections", [])
                    
                    # Filter out any 'ghost' or empty rows from the UI
                    valid_conns = [c for c in conns if c.get("connector_a_id") and c.get("connector_b_id")]
                    
                    if not valid_conns:
                        st.error("❌ No valid Fabric Connections found to deploy.")
                        return 

                    processed_count = 0
                    for conn in valid_conns:
                        st.write(f"🔗 Stitching: {conn.get('connection_name', 'Unnamed')}")
                        res = self._post_fabric_connection_to_api(conn)
                        if res:
                            processed_count += 1
                            st.success(f"✅ Successfully stitched {conn.get('connection_name')}")

                    if processed_count > 0:
                        st.session_state.step = 6
                        st.rerun()
                status.update(label=f"{deploy_type.replace('_', ' ').title()} Successful!", state="complete")
                st.rerun()

        except Exception as e:
            # We add a toast so you see the error even if the page refreshes
            st.toast(f"🚨 Deployment Error: {str(e)}")
            st.error(f"❌ Deployment Failed: {e}")

    def _post_interface_intent(self, intf_data: dict):
        """Bridge to Phase 1: Logical Interface Database Entry"""
        from src.utils.api_customer import post_interface 
        
        # Prepare the flat payload for the API curl definition
        payload = {
            "port_id": intf_data.get("port_id"), # Linked from Step 2
            "interface_name": intf_data.get("alias"),
            "description": f"Service Interface for {self.payload['vrf'].get('name')}",
            "interface_type": "L3",
            "svlan_id": int(intf_data.get("vlan", 0)),
            "status": "Staged"
        }
        return post_interface(payload)

    def _post_static_route_intent(self, route_data: dict):
        """Bridge to Phase 2: Static Route Database Entry"""
        from src.utils.api_customer import post_static_route
        # Maps UI data to API schema
        payload = {
            "interface_id": route_data.get("interface_id"),
            "destination_prefix": route_data.get("prefix"),
            "next_hop": route_data.get("next_hop"),
            "description": route_data.get("description", "Galileo Static Route")
        }
        return post_static_route(payload)

# --- ZONE 1: STATE & INTENT MANAGEMENT ---

    def render_vrf_context(self):
        """
        Step 1: Parent VRF Context.
        Logic: Top Message -> Input Form -> Separate Commit Button.
        """
        st.header("Step 1: VRF & Service Context")
        
        # 1. Message(s) at the top: Check for existing Service ID
        service_id = self.payload.get("service_id") or st.session_state.get("fs_active_id")
        
        if service_id:
            st.success(f"Provisioned VRF: **{self.payload['vrf'].get('name')}** (ID: {service_id})", icon="✅")
        else:
            st.info("Define the VRF parameters below. You must **Commit** to establish the service record.", icon="ℹ️")

        # 2. Render the Input Form
        from src.utils.ui_provisioning_form import render_vrf_context_form
        render_vrf_context_form(
            data=self.payload["vrf"], 
            customer_id=self.customer_id
        )

        st.divider()

        # 3. SEPARATE COMMIT BUTTON
        # This button is local to Step 1 and only handles the database post.
        if not service_id:
            if st.button("💾 Commit VRF to Database", type="primary", use_container_width=True):
                if not self.payload["vrf"].get("name"):
                    st.error("❌ A VRF Name is required to commit.")
                else:
                    # Sets trigger for handle_api_deployment observer
                    st.session_state.active_deployment = "vrf"
                    st.rerun()
        else:
            # Persistent feedback that the database work is done
            st.button("✅ VRF Record Locked & Committed", disabled=True, use_container_width=True)
            st.caption("Database transaction complete. Proceed to Step 2.")

    def normalize_vrf_payload(self, raw_vrf: dict) -> dict:
        """Determines if the API should perform a POST (New) or target an ID (Existing)."""
        normalized = {
            "customer_id": self.customer_id,
            "service_name": raw_vrf.get("name"),
            "service_alias": raw_vrf.get("alias"),
            "service_type": raw_vrf.get("type"),
            "route_target": raw_vrf.get("rt"),
            "health_status": 4
        }
        # If it's brownfield, we must pass the ID back to the API
        if raw_vrf.get("mode") == "Existing Fabric Service":
            normalized["service_id"] = raw_vrf.get("service_id")
        
        return normalized
    
    def _sync_global_context(self, service_id: str):
        """Synchronizes the state manager to eliminate UI lag."""
        st.session_state["fs_active_id"] = service_id
        # Crucial: Ensure the manager's internal record matches the payload
        rec = {
            "service_id": service_id,
            "service_name": self.payload["vrf"].get("name"),
            "service_type": self.payload["vrf"].get("type")
        }
        st.session_state["fs_active_record"] = rec
        self.fs_record = rec # Update the local instance attribute

    # --- ZONE 2: UPDATED API BRIDGES ---
   
    def render_fabric_port(self):
        """Step 2: Fabric Port Assignment (Hierarchical compatible)"""
        st.header("Step 2: Fabric Port Assignment")
        
        # 1. Access the raw list in the tree
        ports_list = self.payload["vrf"]["children"]["ports"]
        
        # 2. THE BRIDGE: Wrap the list in the dict structure the Form expects
        compat_payload = {"port_queue": ports_list}
        
        # 3. Fetch Inventory using the API Client method
        df_inventory = self._get_customer_ports()
        
        from src.utils.ui_provisioning_form import render_fabric_port_form
        
        # Pass the bridged dict. Changes to 'port_queue' update your tree by reference.
        render_fabric_port_form(compat_payload, df_inventory)
        
        self._render_api_diagnostic("ports")

    def _render_api_diagnostic(self, deploy_type: str):
        """
        Unified Diagnostic UI with granular triggers for Step 3.
        Enhanced with debug counters to troubleshoot silent BGP failures.
        """
        if deploy_type == "interfaces":
            st.divider()
            st.subheader("🚀 Granular Routing Deployment")
            
            c1, c2 = st.columns(2)
            
            with c1:
                with st.expander("📍 Static Route Intent", expanded=False):
                    static_intent = [r for i in self.payload["vrf"]["children"]["interfaces"] 
                                    for r in i.get("routing", {}).get("static", [])]
                    
                    st.metric("Queued Routes", len(static_intent))
                    st.json(static_intent)
                    
                    if st.button("🚀 Post Static Routes", key="btn_post_static", use_container_width=True):
                        if not static_intent:
                            st.warning("No static routes found to deploy.")
                        else:
                            st.session_state.active_deployment = "static_routes"
                            st.rerun()

            with c2:
                with st.expander("🤝 BGP Neighbor Intent", expanded=True): # Expanded for visibility
                    bgp_intent = [b for i in self.payload["vrf"]["children"]["interfaces"] 
                                 for b in i.get("routing", {}).get("bgp", [])]
                    
                    # DEBUG: Monitor the count
                    st.metric("Queued Neighbors", len(bgp_intent))
                    
                    if bgp_intent:
                        st.json(bgp_intent)
                    else:
                        st.info("No BGP neighbors staged in the payload tree.")

                    if st.button("🚀 Post BGP Neighbors", key="btn_post_bgp", use_container_width=True, type="primary"):
                        if not bgp_intent:
                            st.error("Cannot post: BGP intent list is empty.")
                        else:
                            # Verify trigger in sidebar if 'The Hammer' is active
                            st.session_state.active_deployment = "bgp_peers"
                            st.toast("Triggering BGP Deployment...")
                            st.rerun()
        else:
            # Standard logic for Step 1 and 2
            with st.expander(f"⚖️ {deploy_type.upper()} Intent Preview"):
                display_json = self.payload["vrf"] if deploy_type == "vrf" else self.payload["vrf"]["children"].get(deploy_type, {})
                st.json(display_json)
                if st.button(f"🚀 Confirm Live {deploy_type.upper()} Post", use_container_width=True):
                    st.session_state.active_deployment = deploy_type
                    st.rerun()

    def _calculate_p2p_ips(self, byoip: bool, prefix_len: int = 30, version: str = "v4"):
        """
        Segmented Calculation Engine:
        v4 Base: 8.56.0.0/16 (Slices: /30, /29, /28)
        v6 Base: 2001:0db8:1234::/48 (Default: /128)
        """
        import ipaddress
        import random

        if version == "v4":
            if byoip:
                try:
                    val = st.session_state.get("v4_manual_input", "192.168.1.0/30")
                    net = ipaddress.IPv4Network(val, strict=False)
                    return str(net[1]), str(net[2]), str(net.netmask)
                except Exception:
                    return "Invalid", "Invalid", "Invalid"
            else:
                # Deterministic Logic for Lumen-Assigned Pool
                base_net = ipaddress.IPv4Network("8.56.0.0/16")
                
                # We pick a random start point within the /16 based on the requested prefix_len
                # In a production DB, you'd fetch the next available index.
                # Here we simulate by picking a random subnet of the requested size:
                subnets = list(base_net.subnets(new_prefix=prefix_len))
                selected_net = random.choice(subnets[:1000]) # Limit range for speed
                
                return str(selected_net[1]), str(selected_net[2]), str(selected_net.netmask)

        else: # IPv6 Logic
            if byoip:
                try:
                    val = st.session_state.get("v6_manual_input", "2001:db8:1234::/126")
                    net = ipaddress.IPv6Network(val, strict=False)
                    return str(net[1]), str(net[2]), "126"
                except Exception:
                    return "Invalid", "Invalid", "Invalid"
            else:
                # v6 Default Assignment (Host Route /128)
                # Slicing a /48 into /128s
                base_v6 = ipaddress.IPv6Network("2001:0db8:1234::/48")
                # Picking a pseudo-random /128 within the /48
                suffix = random.getrandbits(80) 
                selected_ip = base_v6.network_address + suffix
                
                # PE is typically .1, CE is typically .2 within a virtual segment
                return str(selected_ip + 1), str(selected_ip + 2), "128"
  
    def _post_interface_intent(self, interface_data: dict):
        """
        POSTs a logical interface to the backend.
        Binds the interface to the active service_id.
        """
        from src.utils.api_customer import post_interface # Ensure this exists in your client
        
        # 1. Ensure the interface knows its parent service context
        interface_data["service_id"] = self.payload.get("service_id")
        
        # 2. Extract the physical port_id if it exists (linked from Step 2)
        # If the user skipped Step 2, this might be null/None
        
        try:
            response = post_interface(interface_data)
            return response
        except Exception as e:
            st.error(f"Failed to push interface {interface_data.get('alias')}: {e}")
            return None   

    def render_interface_assignment(self):
        """
        Step 3: Interface & Routing Orchestration.
        Now featuring Granular Deployment buttons per Interface.
        """
        st.header("Step 3: Interface & Routing")
        
        # 1. Access the raw list in the hierarchical tree
        interfaces_list = self.payload["vrf"]["children"]["interfaces"]
        
        from src.utils.ui_provisioning_form import (
            render_interface_build_form, 
            render_static_route_form, 
            render_bgp_peer_form
        )

        # ---------------------------------------------------------
        # SECTION 1: ACTIVE CONFIGURATION ZONE
        # ---------------------------------------------------------
        with st.container(border=True):
            st.markdown("#### 🛠️ Step 3.1: Define Interface")
            render_interface_build_form({"interface_queue": interfaces_list}, self._calculate_p2p_ips)
            
            if interfaces_list:
                st.divider()
                st.markdown("#### 🛠️ Step 3.2: Configure Routing for Active Interface")
                active_intf = interfaces_list[-1] 
                
                col_rt_left, col_rt_right = st.columns(2, gap="large")
                with col_rt_left:
                    render_static_route_form({}, active_intf)
                with col_rt_right:
                    render_bgp_peer_form({}, active_intf)

        # ---------------------------------------------------------
        # SECTION 2: GRANULAR MANAGEMENT ZONE
        # ---------------------------------------------------------
        if interfaces_list:
            st.divider()
            st.subheader("📊 Managed Configuration Manifest")
            
            # Using Tabs for Organization, but adding Granular Actions inside
            t_intf, t_static, t_bgp, t_json = st.tabs([
                "🖥️ Interfaces", "📍 Static Routes", "🤝 BGP Peers", "📄 JSON Doc"
            ])

            with t_intf:
                st.markdown("##### Queued Physical & Logical Interfaces")
                for idx, intf in enumerate(interfaces_list):
                    # Unique identification for the UI
                    intf_id = intf.get('interface_id')
                    status_color = "🟢" if intf_id else "⚪"
                    
                    with st.expander(f"{status_color} Interface: {intf['alias']} | ID: {intf_id or 'PENDING'}", expanded=True):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        
                        # Data summary
                        c1.write(f"**IP:** {intf.get('ipv4_lumen')} | **VLAN:** {intf.get('vlan_id')}")
                        
                        # Phase 1: Provision the Interface
                        if not intf_id:
                            if c2.button(f"🚀 Provision {intf['alias']}", key=f"btn_p1_{idx}"):
                                st.session_state.active_deployment = ("interface_single", idx)
                                st.rerun()
                        else:
                            c2.success("Interface Live")

                        # Remove from local queue if not deployed
                        if not intf_id:
                            if c3.button("🗑️ Remove", key=f"btn_del_{idx}"):
                                interfaces_list.pop(idx)
                                st.rerun()

            with t_static:
                st.markdown("##### Granular Static Route Deployment")
                for idx, i in enumerate(interfaces_list):
                    routes = i.get('routing', {}).get('static', [])
                    if routes:
                        with st.expander(f"📍 Routes for {i['alias']} ({len(routes)})", expanded=True):
                            st.table(pd.DataFrame(routes))
                            # Only allow posting routes if the parent interface exists
                            if i.get('interface_id'):
                                if st.button(f"🚀 Post Static Routes for {i['alias']}", key=f"btn_p2_{idx}"):
                                    st.session_state.active_deployment = ("static_single", idx)
                                    st.rerun()
                            else:
                                st.warning("⚠️ Provision Interface first to enable Routing deployment.")

            with t_bgp:
                st.markdown("##### Granular BGP Deployment")
                for idx, i in enumerate(interfaces_list):
                    peers = i.get('routing', {}).get('bgp', [])
                    if peers:
                        with st.expander(f"🤝 BGP Peers for {i['alias']} ({len(peers)})", expanded=True):
                            st.table(pd.DataFrame(peers))
                            if i.get('interface_id'):
                                if st.button(f"🚀 Post BGP Neighbors for {i['alias']}", key=f"btn_p3_{idx}"):
                                    st.session_state.active_deployment = ("bgp_single", idx)
                                    st.rerun()
                            else:
                                st.warning("⚠️ Provision Interface first to enable BGP deployment.")

            with t_json:
                st.markdown("##### Full L3 Intent Manifest")
                st.json(interfaces_list)

        # Global diagnostic removed or moved to sidebar to prevent clutter
        # self._render_api_diagnostic("interfaces")
    
    def render_private_peering(self):
        """Step 4: XaaS - Private Peering (Cloud Exchange)"""
        st.header("Step 4: Private Peering")
        
        # 1. Pull the raw list from the nested hierarchy
        peering_list = self.payload["vrf"]["children"]["cloud_peerings"]
        
        # 2. THE BRIDGE: Wrap the list in the dictionary key the Form utility expects
        # This prevents the TypeError: list indices must be integers or slices
        compat_payload = {"peering_sessions": peering_list}
        
        from src.utils.ui_provisioning_form import render_private_peering_form
        
        # 3. Pass the wrapped dictionary
        render_private_peering_form(compat_payload)
        
        self._render_api_diagnostic("cloud_peerings")

    def render_fabric_connection(self):
        """Step 5: Virtual Circuits / Fabric Connections"""
        st.header("Step 5: Fabric Connections")
        
        # 1. Pull the raw list from the nested hierarchy
        conn_list = self.payload["vrf"]["children"]["fabric_connections"]
        
        # 2. THE BRIDGE: Wrap the list in the dictionary key the Form utility expects
        # This fixes the TypeError: list indices must be integers or slices
        compat_payload = {"connections_list": conn_list}
        
        from src.utils.ui_provisioning_form import render_fabric_connection_form
        
        # 3. Pass the wrapped dictionary and the full payload for context
        render_fabric_connection_form(compat_payload, self.payload)
        
        self._render_api_diagnostic("fabric_connections")

    def render_review_and_deploy(self):
        """Step 6: Final Review & Orchestration"""
        st.header("Step 6: Review & Deploy")
        
        # Display the full hierarchical tree for final audit
        st.json(self.payload)
        
        st.warning("⚠️ Verify all intents before final execution.")
        if st.button("🚀 Execute Orchestration", type="primary", use_container_width=True):
            st.session_state.active_deployment = "full_sync"
            st.rerun()

    def render_unsupported_view(self):
        st.error(f"Service Type '{self.service_type}' is not currently supported by this workflow.")

    def run(self):
        """The Main UI Loop."""
        # Check for deployment triggers first
        trigger = st.session_state.get("active_deployment")
        if trigger:
            self._handle_api_deployment(trigger)

        # Render Progress UI
        self._render_header()
        
        # Render the form from the map
        current_step = st.session_state.step
        self.workflow_map[current_step]()
        
        # Render Navigation
        self._render_navigation(current_step)

    def _render_header(self):
        """Standardized Header with Progress Bar and Step Labels."""
        current_step = st.session_state.step
        total_steps = len(self.workflow_map)
        progress_value = (current_step - 1) / (total_steps - 1) if total_steps > 1 else 1.0
        
        # UI Rendering
        st.write(f"**Workflow Progress: Step {current_step} of {total_steps}**")
        st.progress(progress_value)
        
        # Vertical spacing and Step-Specific Diagram
        self._render_step_diagram(current_step)
        st.divider()

    def _render_step_diagram(self, step_number: int):
        """
        Consolidated Reference Architecture Renderer.
        Works for all steps (1-6) by dynamically locating UC1-UC3 and Step MD files.
        """
        import os
        import streamlit as st

        # 1. Resolve naming base from current UI state
        # Priority: Widget Session State -> Payload Cache -> Default
        vrf_data = self.payload.get("vrf", {})
        svc_type = (st.session_state.get("service_type_selector") or 
                    vrf_data.get("type", "IPVPN")).lower().strip()
        svc_flavor = (st.session_state.get("mcgw_flavor_selector") or 
                      vrf_data.get("flavor", "")).lower().strip()

        # Build file_base: e.g., 'mcgw-full', 'mcgw-limited', or 'ipvpn'
        file_base = f"mcgw-{svc_flavor}" if svc_type == "mcgw" and svc_flavor else svc_type
        
        # 2. Inventory available assets for this specific step
        use_cases = []
        for i in range(1, 4):  # Check for UC#1, UC#2, UC#3
            img_name = f"{file_base}-step{step_number}-{i}.png"
            img_path = f"templates/png/{img_name}"
            
            # Fuzzy fallback: If mcgw-full-stepX-1.png is missing, try mcgw-stepX-1.png
            if not os.path.exists(img_path) and "mcgw" in file_base:
                img_path = f"templates/png/mcgw-step{step_number}-{i}.png"

            if os.path.exists(img_path):
                use_cases.append({"idx": i, "path": img_path})

        # Resolve Markdown path with similar fallback
        md_path = f"templates/png/{file_base}-step{step_number}.md"
        if not os.path.exists(md_path) and "mcgw" in file_base:
            md_path = f"templates/png/mcgw-step{step_number}.md"

        # 3. Render UI if content exists
        if use_cases or os.path.exists(md_path):
            exp_label = f"📖 Step {step_number} Reference: {svc_type.upper()}"
            if svc_flavor: exp_label += f" ({svc_flavor.capitalize()})"
            
            with st.expander(exp_label, expanded=True):
                # Build Dynamic Tab Titles
                tab_titles = [f"UC#{uc['idx']}" for uc in use_cases]
                if os.path.exists(md_path):
                    tab_titles.append("📝 Documentation")
                
                if tab_titles:
                    tabs = st.tabs(tab_titles)
                    
                    # Fill Image Tabs
                    for i, uc in enumerate(use_cases):
                        with tabs[i]:
                            st.image(uc['path'], use_container_width=True)
                    
                    # Fill Documentation Tab (Always last)
                    if os.path.exists(md_path):
                        with tabs[-1]:
                            try:
                                with open(md_path, "r") as f:
                                    st.markdown(f.read())
                            except Exception as e:
                                st.error(f"Error loading documentation: {e}")
        else:
            # Helpful hint for Fergus during development
            st.caption(f"ℹ️ No reference assets found for '{file_base}' at Step {step_number}")

    def _validate_step(self, step: int) -> bool:
        """
        Logic-based validation for the 'Next' button.
        Returns True if the button should be DISABLED.
        """
        # 1. Check for established DB ID in local payload or global state
        service_id = self.payload.get("service_id") or st.session_state.get("fs_active_id")
        children = self.payload["vrf"]["children"]
        
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
        """
        Standardized Navigation Logic.
        In the Micro-Intent model, this handles pure UI transitions.
        """
        st.divider()
        col_prev, _, col_next = st.columns([1, 2, 1])
        
        # --- LEFT: Previous Button ---
        with col_prev:
            if current_step > 1:
                if st.button("⬅️ Previous", key="nav_prev", use_container_width=True):
                    st.session_state.step -= 1
                    st.rerun()
        
        # --- RIGHT: Next Button ---
        with col_next:
            # Use the service_id check from the validator
            is_disabled = self._validate_step(current_step)
            
            # Label is simplified; Step 6 remains the final review
            label = "Final Review ➡️" if current_step == 5 else "Next ➡️"
            
            if st.button(label, key="nav_next", type="primary", disabled=is_disabled, use_container_width=True):
                # Pure UI transition
                st.session_state.step += 1
                st.rerun()

    def _step_requires_api(self, step: int) -> bool:
        """Determines if a step needs a micro-intent commit before advancing."""
        vrf_mode = self.payload["vrf"].get("mode")
        
        if step == 1:
            # Only POST if it's a brand new Greenfield service
            return vrf_mode == "New Fabric Service"
        
        if step == 2:
            # Only POST if ports were actually added to the queue
            return len(self.payload["vrf"]["children"].get("ports", [])) > 0
            
        return False

    def _get_deploy_type_for_step(self, step: int) -> str:
        """Maps step numbers to deployment triggers."""
        mapping = {1: "vrf", 2: "ports"}
        return mapping.get(step)
    
    def _get_deploy_type_for_step(self, step: int) -> str:
        """Maps step numbers to deployment triggers."""
        mapping = {1: "vrf", 2: "ports", 3: "interfaces"}
        return mapping.get(step)

    def _deploy_fabric_service(self, vrf_data: dict):
        """Standard POST to the VRF Micro-intent endpoint."""
        from src.api_client import post_fabric_service
        # Pass the payload through normalization to match API schema
        api_payload = self.normalize_vrf_payload(vrf_data)
        response = post_fabric_service(api_payload)
        return response.get("service_id")

    def _post_port_intent(self, port_data: dict):
        """Standard POST to the Port assignment micro-intent endpoint."""
        from src.utils.api_customer import post_port_intent
        # Ensure the child knows who its parent is
        port_data["service_id"] = self.payload["service_id"]
        return post_port_intent(port_data)

    def _get_customer_ports(self) -> pd.DataFrame:
        """
        Segmented Data Fetcher: Wraps the API call with a 
        Streamlit session-state cache.
        """
        import pandas as pd
        # Import your existing function from the api_client file
        from src.api_client import get_ports_by_customer

        cache_key = f"port_cache_{self.customer_id}"
        
        # 1. Return from cache if we already have it
        if cache_key in st.session_state:
            return st.session_state[cache_key]

        # 2. Otherwise, use your function to fetch
        try:
            df = get_ports_by_customer(self.customer_id)
            
            if not df.empty:
                # IMPORTANT: Ensure ID columns are strings to prevent 
                # Streamlit/Pandas from treating UUIDs as objects/floats
                if 'port_id' in df.columns:
                    df['port_id'] = df['port_id'].astype(str)
                
                st.session_state[cache_key] = df
                return df
            
        except Exception as e:
            st.error(f"UI Error sourcing customer ports: {e}")
            
        # Fallback to empty DF with matching schema
        return pd.DataFrame(columns=['port_id', 'device_name', 'port_name'])
  
    def _post_cloud_connection_intent(self, peer_data: dict):
        from src.utils.api_customer import post_cloud_connection
        return post_cloud_connection(peer_data)

    def _post_fabric_connection_intent(self, conn_data: dict):
        from src.utils.api_customer import post_fabric_connection
        return post_fabric_connection(conn_data)
 
def show_provisioning_view():
    """The Global Entry Point: Selecting the Customer Anchor."""
    st.title("🌐 Galileo Network Provisioning")

    # 1. Fetch Customers from API
    from src.api_client import get_all_customers 
    customers_df = get_all_customers()

    if customers_df.empty:
        st.warning("No customers found in the database. Please check API connectivity.")
        return

    # 2. Customer Selection UI
    with st.container(border=True):
        st.subheader("🏢 Step 0: Select Customer Anchor")
        
        # Create a search-friendly label
        customers_df['label'] = customers_df['customer_name'] + " (" + customers_df['customer_id'].str[:8] + ")"
        
        selected_label = st.selectbox(
            "Select a Customer to begin provisioning:",
            options=customers_df['label'].tolist(),
            index=None,
            placeholder="Search by name or ID...",
            key="global_customer_selector"
        )

    # 3. Drive the rest of the flow only if a customer is selected
    if selected_label:
        selected_row = customers_df[customers_df['label'] == selected_label].iloc[0]
        customer_id = selected_row['customer_id']
        customer_name = selected_row['customer_name']

        # Clear session if switching customers
        if st.session_state.get("active_customer_id") != customer_id:
            st.session_state.active_customer_id = customer_id
            st.session_state.step = 1
            # We don't reset the whole payload here to keep persistence, 
            # but we could call self._reset_payload() if desired.
        
        st.sidebar.success(f"**Target:** {customer_name}")
        
        # 4. Launch the Workflow Manager
        workflow = NetworkWorkflowManager(customer_id)
        workflow.run()
    else:
        st.info("👈 Please select a customer to initialize the provisioning workflow.")