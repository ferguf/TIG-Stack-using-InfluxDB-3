import streamlit as st

class FabricStateManager:
    """
    Centralized State Manager for the 4-Tier Fabric Hierarchy.
    Tier 1: Customer (cust)
    Tier 2: Fabric Service (fs)
    Tier 3: Fabric Connection (fc)
    Tier 3 (Parallel): Ports (port)
    """

    @classmethod
    def initialize(cls):
        """Initializes all required keys in st.session_state if they don't exist."""
        keys = {
            "cust_active_record": None, "cust_active_id": None, 
            "cust_show_create": False, "cust_show_update": False, "cust_confirm_delete": False,
            "customer_df": None,
            "fs_active_record": None, "fs_active_id": None, 
            "fs_show_provision": False, "fs_show_update": False, "fs_confirm_delete": False,
            "fc_active_record": None, "fc_active_id": None, 
            "conn_show_provision": False, "conn_show_update": False, "conn_confirm_delete": False,
            "port_active_record": None, "port_active_id": None, 
            "port_show_assign": False, "port_show_update": False, "port_confirm_delete": False
        }
        for key, default in keys.items():
            if key not in st.session_state:
                st.session_state[key] = default

    @classmethod
    def set_active(cls, prefix: str, entity_id: str, record: dict = None):
        """
        Manually sets an active ID and record. 
        Used to 'rehydrate' dashboard state from the Provisioning Wizard.
        """
        current_id = st.session_state.get(f"{prefix}_active_id")
        
        # Only update if the ID has changed to avoid unnecessary reruns
        if str(entity_id) != str(current_id):
            st.session_state[f"{prefix}_active_id"] = entity_id
            st.session_state[f"{prefix}_active_record"] = record
            cls._reset_toggles(prefix)
            
            # Cascade clearing of downstream tiers to maintain data integrity
            if prefix == "cust":
                cls._clear_tier("fs")
                cls._clear_tier("fc")
                cls._clear_tier("port")
                cls._clear_caches(["svc_cache_", "conn_cache_", "port_cache_"])
            elif prefix == "fs":
                cls._clear_tier("fc")
                cls._clear_tier("port")
                cls._clear_caches(["conn_cache_", "port_cache_"])

    @classmethod
    def sync_selection(cls, prefix: str, selection: dict, id_key: str) -> bool:
        """Syncs a UI selection (e.g., from a dataframe) into the global state."""
        new_id = selection.get(id_key) if selection else None
        return cls.set_active(prefix, new_id, selection)

    @classmethod
    def _clear_tier(cls, prefix: str):
        """Resets state for a specific tier."""
        st.session_state[f"{prefix}_active_id"] = None
        st.session_state[f"{prefix}_active_record"] = None
        cls._reset_toggles(prefix)

    @classmethod
    def _reset_toggles(cls, prefix: str):
        """Resets all UI boolean flags for a specific tier."""
        toggles = {
            "cust": ["cust_show_create", "cust_show_update", "cust_confirm_delete"],
            "fs": ["fs_show_provision", "fs_show_update", "fs_confirm_delete"],
            "fc": ["conn_show_provision", "conn_show_update", "conn_confirm_delete"],
            "port": ["port_show_assign", "port_show_update", "port_confirm_delete"]
        }
        for t in toggles.get(prefix, []):
            st.session_state[t] = False

    @classmethod
    def _clear_caches(cls, prefixes: list):
        """Clears temporary session caches matching specific prefix strings."""
        for key in list(st.session_state.keys()):
            if any(key.startswith(p) for p in prefixes):
                del st.session_state[key]

    @classmethod
    def get_active_record(cls, prefix: str):
        """Getter for the active dictionary record."""
        return st.session_state.get(f"{prefix}_active_record")

    @classmethod
    def get_active_id(cls, prefix: str):
        """Getter for the active UUID/ID."""
        return st.session_state.get(f"{prefix}_active_id")
class NetworkWorkflowManager:
    def __init__(self, customer_id: str, initial_type: str = "IPVPN"):
        self.customer_id = customer_id
        
        # Ensure State Manager is initialized
        FabricStateManager.initialize()

        if "step" not in st.session_state: st.session_state.step = 1
        
        # 1. INIT OR SYNC PAYLOAD
        if "payload" not in st.session_state: 
            self._reset_payload(initial_type)
        elif st.session_state.payload.get("service_context", {}).get("mode") == "New Fabric Service":
            if st.session_state.payload["service_context"].get("type") != initial_type:
                st.session_state.payload["service_context"]["type"] = initial_type

        self.payload = st.session_state.payload
        
        # 2. PULL GLOBAL STATE (The Hoisting Logic)
        active_rec = FabricStateManager.get_active_record("fs") or {}
        found_id = (
            active_rec.get("service_id") or 
            self.payload.get("service_id") or 
            self.payload.get("service_context", {}).get("service_id")
        )
        
        if found_id:
            st.session_state.fs_active_id = found_id
            self.payload["service_id"] = found_id
            
            if active_rec:
                st.session_state.fs_active_record = active_rec
                self.payload["service_context"]["name"] = active_rec.get("service_name")
                self.payload["service_context"]["type"] = active_rec.get("service_type")

        # 3. RESOLVE DISPATCHER MAP
        self.service_type = str(self.payload["service_context"].get("type", "IPVPN")).upper().strip()
        self.workflow_map = self._get_workflow_map()
        
        # --- NEW: EVC-DRIVEN GATEKEEPER ---
        # The ultimate source of truth for an EPL is the Fabric Connection
        conn_list = self.payload.get("service_context", {}).get("children", {}).get("fabric_connections", [])
        
        self.is_epl = self.service_type == "EPL"
        # If the service already has an EVC, it is completely locked down!
        self.epl_locked = self.is_epl and len(conn_list) >= 1

    def _reset_payload(self, initial_type: str):
        """Initializes the payload structure."""
        st.session_state.payload = {
            "service_id": None,
            "service_context": {
                "mode": "New Fabric Service",
                "type": initial_type,
                "name": "",
                "alias": "",
                "flavor": "",
                "children": {
                    "ports": [],
                    "interfaces": [],
                    "cloud_peerings": [],
                    "fabric_connections": []
                }
            }
        }

    def _get_workflow_map(self):
        """Returns the appropriate workflow steps based on service type."""
        # Adjust these mappings based on your full architecture
        if self.service_type == "EPL":
            return {
                1: self.render_service_context,
                2: self.render_fabric_port,
                3: self.render_eline_connection,
                4: self.render_summary # Or whatever your step 4 is
            }
        else:
            return {
                1: self.render_service_context,
                2: self.render_fabric_port,
                3: self.render_interface_build,
                4: self.render_private_peering,
                5: self.render_fabric_connection
            }

    def _render_header(self):
        """Standardized Header with Progress Bar and Global Banners."""
        current_step = st.session_state.step
        total_steps = len(self.workflow_map)
        progress_value = (current_step - 1) / (total_steps - 1) if total_steps > 1 else 1.0
        
        st.write(f"**Workflow Progress: Step {current_step} of {total_steps}**")
        st.progress(progress_value)
        
        # --- GLOBAL STATUS BANNER ---
        if getattr(self, "epl_locked", False):
            st.info("🔒 **Service Locked:** This Ethernet Private Line (EPL) already has an active EVC configured. Point-to-Point topology is fully established.")
        
        st.divider()

    def run(self):
        """Executes the workflow runner."""
        self._render_header()
        current_step = st.session_state.step
        
        if current_step in self.workflow_map:
            self.workflow_map[current_step]()
        else:
            st.error(f"Invalid workflow step: {current_step}")

    # ==========================================
    # WORKFLOW STEPS
    # ==========================================

    def render_service_context(self):
        """Step 1: Service Definition"""
        # ... Your existing Step 1 code goes here ...
        st.write("Step 1 Form...")

    def render_fabric_port(self):
        """Step 2: Fabric Port Assignment"""
        st.header("Step 2: Fabric Port Assignment")
        
        # --- THE EVC GATEKEEPER ---
        if getattr(self, "epl_locked", False):
            st.success("✅ **EPL Ports Allocated**")
            st.info("🔒 This Ethernet Private Line (EPL) already has an active cross-connect (EVC). The physical ports are already allocated to this service.")
            
            if st.button("➡️ Proceed to Step 3", type="primary", use_container_width=True):
                st.session_state.step = 3 if not isinstance(st.session_state.get("step"), int) else st.session_state.step + 1
                st.rerun()
            return # Block the port selection form!

        # --- STANDARD PORT FORM ---
        children = self.payload.get("service_context", {}).get("children", {})
        ports_list = children.setdefault("ports", [])
        
        compat_payload = {
            "port_queue": ports_list,
            "service_type": self.service_type  
        }
        
        # df_inventory = self._get_customer_ports() # Uncomment and implement this helper
        df_inventory = pd.DataFrame() 
        
        from src.utils.ui_provisioning_form import render_fabric_port_form
        render_fabric_port_form(compat_payload, df_inventory)
        
        # --- THE COMMIT ZONE ---
        if ports_list:
            st.divider()
            staged_ports = [p for p in ports_list if p.get("status") == "Staged"]
            if len(staged_ports) > 0:
                st.warning(f"⚠️ **Action Required:** {len(staged_ports)} queued port(s) must be provisioned.")
                if st.button("⚡ Provision Ports", type="primary", use_container_width=True):
                    st.session_state.active_deployment = "ports"
                    st.rerun()
            else:
                st.success("✅ All physical ports are actively provisioned and ready.")

        # self._render_api_diagnostic("ports") # Uncomment if you have this diagnostic

    def render_eline_connection(self):
        """Step 3: Ethernet Virtual Circuits / Ethernet Fabric Connect"""
        st.header("Step 3: Ethernet Fabric Connect")
        
        conn_list = self.payload.get("service_context", {}).get("children", {}).get("fabric_connections", [])
        
        # --- THE EVC GATEKEEPER ---
        if getattr(self, "epl_locked", False):
            st.success("✅ **EPL Circuit Established**")
            st.info("🔒 This Ethernet Private Line (EPL) already has an active cross-connect. Point-to-Point services only support a single EVC.")
            
            if conn_list:
                display_df = pd.DataFrame(conn_list)[["connection_name", "connector_a_id", "connector_b_id", "service_bw", "connection_status"]]
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            if st.button("➡️ Proceed to Step 4", type="primary", use_container_width=True):
                st.session_state.step = 4 if not isinstance(st.session_state.get("step"), int) else st.session_state.step + 1
                st.rerun()
            return # Block the EVC selection form!

        # --- STANDARD EVC FORM ---
        from src.utils.ui_provisioning_form import render_eline_connection_form
        render_eline_connection_form(self)
        
        # --- THE COMMIT ZONE ---
        if conn_list:
            st.divider()
            staged_conns = [c for c in conn_list if c.get("connection_status") == "Planned"]
            
            if staged_conns:
                st.warning("⚠️ **Action Required:** Provision the queued EVC to establish Port-to-Port connectivity.")
                if st.button("⚡ Provision Ethernet Virtual Circuit", type="primary", use_container_width=True):
                    st.session_state.active_deployment = "fabric_connections"
                    st.rerun()
            else:
                st.success("✅ All EVCs are actively provisioned.")
                st.divider()
                st.info("🔗 The EPL circuit is fully established across the backbone.")
                
                if st.button("➡️ Proceed to Step 4", type="primary", use_container_width=True):
                    if isinstance(st.session_state.get("step"), int):
                        st.session_state.step += 1
                    else:
                        st.session_state.step = 4 
                    st.rerun()

        # self._render_api_diagnostic("fabric_connections") # Uncomment if you have this diagnostic

    def render_summary(self):
        st.header("Step 4: Service Summary")
        st.success("EPL Provisioning Complete!")

    def render_interface_build(self): pass
    def render_private_peering(self): pass
    def render_fabric_connection(self): pass


# =====================================================================
# 3. THE MAIN VIEW FUNCTION
# =====================================================================

def show_provisioning_view():
    st.title("🌐 Provisioning Orchestrator")
    
    cust_df = get_customers()
    selected_cust_name = st.selectbox(
        "🏢 Select Target Customer:",
        options=cust_df['customer_name'].tolist() if not cust_df.empty else [],
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
        supported_types = ['IPVPN', 'MCGW', 'IP-VPN', 'EPL', 'EVPL', 'ELAN', 'IOD']

        # SAFEGUARD: Handle both DataFrame and List formats from the API
        if isinstance(all_services, pd.DataFrame) and not all_services.empty:
            filtered_services = all_services[all_services['service_type'].isin(supported_types)]
            for _, row in filtered_services.iterrows():
                label = f"{row['service_name']} ({row['service_type']})"
                service_options.append(label)
                service_map[label] = row.to_dict()
                
        elif isinstance(all_services, list) and len(all_services) > 0:
            for s in all_services:
                if s.get('service_type') in supported_types:
                    label = f"{s.get('service_name')} ({s.get('service_type')})"
                    service_options.append(label)
                    service_map[label] = s

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
            workflow = NetworkWorkflowManager(cust_id)
            workflow.run()

        elif selected_service == "--- Create a New Fabric Service ---":
            # Ensure old anchors are gone to allow for a clean start
            if st.session_state.get("fs_active_id"):
                 for key in ["fs_active_id", "fs_active_record", "payload", "step"]:
                    if key in st.session_state:
                        del st.session_state[key]
                 st.rerun()

            st.divider()
            
            with st.container(border=True):
                st.markdown("##### ✨ Initialize New Service Architecture")
                new_svc_type = st.radio(
                    "Select Service Family:",
                    options=["IPVPN", "MCGW", "EPL", "EVPL", "ELAN", "IOD"],
                    horizontal=True,
                    key="new_svc_type_radio"
                )
            
            st.write("") # Quick spacer

            # Launch manager in a clean state for creation
            workflow = NetworkWorkflowManager(cust_id, initial_type=new_svc_type)
            workflow.run()