from statistics import mode
import uuid
import streamlit as st
import pandas as pd
import os
import random
from src.utils.api_customer import get_fabric_services, get_fabric_service_detail
from src.galileo.galileo_templates import get_base64_image
from src.utils.ui_provisioning_form import render_cloud_provisioning_form,_render_epl_context,_render_mcgw_context,_render_ipvpn_context,_render_evpl_context
from src.utils.ui_routing import render_bgp_launcher_tile, render_builder_workflow


CARD_HEIGHT = 440

def inject_provisioning_styles():
    """Consolidated Galileo Design System CSS."""
    st.markdown("""
        <style>
        /* Primary Actions: Light Green */
        div.stButton > button[kind="primary"] {
            background-color: #90EE90 !important;
            color: black !important;
            border: none; 
            font-weight: bold; 
            height: 3em;
        }
        /* Mode Toggles: Orange */
        div.stButton > button[kind="secondary"] {
            background-color: #FFA500 !important;
            color: white !important;
            border: none;
        }
        div.stButton > button:hover {
            opacity: 0.85; 
            transition: 0.2s; 
            border: 1px solid #333;
        }
        </style>
    """, unsafe_allow_html=True)

def show_wizard():
    """
    Orchestrates the Inventory and Provisioning Workspace.
    Utilizes a native Tab layout to guarantee the BGP Builder isolates cleanly.
    """
    import streamlit as st
    from src.utils.api_customer import get_customers
    from src.state_managers import FabricStateManager
    import pages.customer.fabric_service as fs_tier
    from src.utils.ui_routing import render_builder_workflow # Ensure this is imported!

    st.title("🌐 Fabric Services Orchestrator")

    # 1. Fetch Data
    df_customers = get_customers()
    if df_customers.empty:
        st.warning("⚠️ No customers available in the database.")
        return
    
    # 2. Map Names to IDs
    cust_map = {row['customer_name']: row['customer_id'] for _, row in df_customers.iterrows()}
    options = ["-- Select --"] + list(cust_map.keys())
    
    # 3. UI Selection
    selected_name = st.selectbox(
        "👤 Active Customer Context", 
        options=options, 
        key="wizard_active_cust_selectbox"
    )

    if selected_name == "-- Select --":
        FabricStateManager.set_active("cust", None)
        st.info("💡 Select a customer context to begin orchestrating fabric resources.")
        return
    
    customer_id = cust_map[selected_name]

    # --- CONTEXT FIREWALL ---
    # Hard reset on customer switch to prevent state bleed
    if st.session_state.get("current_wizard_cust_id") != customer_id:
        st.session_state.current_wizard_cust_id = customer_id
        st.session_state.show_launcher = True
        st.session_state.prov_mode = None
        st.session_state.prov_step = 1
        st.session_state.prov_data = {}
        st.session_state.selected_svc_id = None
        st.session_state.pop("bgp_builder", None) # Wipe the BGP form state

    # 4. Sync Global State
    FabricStateManager.set_active("cust", customer_id)

    # --- 5. THE TABBED ARCHITECTURE ---
    # This physically separates the Master Router from the BGP Builder.
    tab_prov, tab_bgp = st.tabs(["🚀 Provisioning Center", "📜 BGP Policy Builder"])
    
    with tab_prov:
        # The standard 6-step wizard and dashboard tiles live here
        render_master_provisioning(customer_id, selected_name)
        
    with tab_bgp:
        # Directly launch the BGP Builder UI, bypassing the master router entirely.
        build_dir = st.session_state.get("bgp_builder_mode", "Import")
        render_builder_workflow(customer_id=customer_id, direction=build_dir)

def render_master_provisioning(customer_id: str, customer_name: str):
    """
    Main Entry Point for Visual Provisioning Center (NDT).
    Features a bulletproof string-cleaning intercept for the BGP Builder
    and namespaced sub-workflows to prevent duplicate element keys.
    """
    import streamlit as st
    
    # ==========================================
    # 🛑 THE BULLETPROOF INTERCEPT 🛑
    # Clean the string to prevent silent whitespace failures
    # ==========================================
    current_mode = str(st.session_state.get("prov_mode", "")).strip()
    
    if current_mode == "bgp_builder":
        st.success("✅ ROUTER INTERCEPT CAUGHT BGP MODE. Loading form...")
        
        try:
            from src.utils.ui_routing import render_builder_workflow
            build_dir = st.session_state.get("bgp_builder_mode", "Import")
            
            # Launch the Form
            render_builder_workflow(customer_id=customer_id, direction=build_dir)
            
        except Exception as e:
            st.error(f"🚨 FORM CRASH: {str(e)}")
            
        return  # Terminates execution to focus entirely on BGP

    # ==========================================
    # 1. INITIALIZE DASHBOARD STATE
    # ==========================================
    from src.utils.api_customer import get_fabric_services
    from src.utils.ui_routing import render_bgp_launcher_tile
    from src.utils.service_wizards import render_sub_wizard_logic
    
    if "show_launcher" not in st.session_state:
        st.session_state.show_launcher = True
    if "prov_mode" not in st.session_state:
        st.session_state.prov_mode = None

    # ==========================================
    # 2. GLOBAL HEADER & ESCAPE HATCH
    # ==========================================
    h_col, t_col = st.columns([4, 1])
    h_col.markdown(f"### 🚀 Provisioning Center: {customer_name}")
    
    if not st.session_state.show_launcher:
        # Use customer_id in the key to prevent duplicates during state transitions
        if t_col.button("⚙️ Change Mode", use_container_width=True, type="secondary", key=f"btn_mode_swap_{customer_id}"):
            st.session_state.show_launcher = True
            st.session_state.prov_mode = None
            st.session_state.prov_step = 1
            st.rerun()

    st.divider()

    # ==========================================
    # 3. STANDARD ROUTING (Dashboard vs Wizard)
    # ==========================================
    if st.session_state.show_launcher:
        # --- PATH A: DASHBOARD TILES ---
        df_services = get_fabric_services(customer_id)
        
        st.markdown("#### 🛠️ Core Services & Infrastructure")
        col_svc, col_cloud = st.columns(2, gap="large")
        with col_svc:
            # Added customer_id to prevent duplicate keys in blueprint selection
            _render_new_service_workflow(col_svc, customer_id) 
        with col_cloud:
            safe_prefix = f"cloud_launch_{customer_id}"
            _render_cloud_workflow(col_cloud, df_services, unique_prefix=safe_prefix)
                
        st.divider()
        st.markdown("#### 🔌 Port Management")
        cp1, cp2, cp3 = st.columns(3, gap="large")
        with cp1:
            _render_port_workflow(cp1, df_services)     
        with cp2:
            _render_add_new_port_workflow(cp2)          
        with cp3:
            _render_modify_port_workflow(cp3)          
         
        st.divider()
        st.markdown("#### 🧩 Advanced Integrations & Routing")
        cr, cb, cm = st.columns(3, gap="large")
        with cr:
            _render_modify_routing_workflow(cr, df_services) 
        with cb:
            # The tile handles its own namespacing via customer_id
            render_bgp_launcher_tile(customer_id) 
        with cm:
            _render_mcgw_integrator_workflow(cm, df_services) 

    else:
        # --- PATH B: THE 6-STEP WIZARD ---
        render_sub_wizard_logic(customer_id)

def render_sub_wizard_logic(customer_id: str):
    """
    Unified Provisioning Router.
    Orchestrates the 6-step provisioning flow with specific diagram mapping.
    Updated: Features the Cache Buster and Force-Refresh Handshake.
    """
    import streamlit as st
    from src.state_managers import FabricStateManager
    from src.utils.api_customer import get_fabric_service_detail
    from src.utils.ui_debug import render_debug_inspector
    from src.utils.service_wizards import _render_step_diagram 

    # --- 0. ENCAPSULATED DEBUGGER ---
    with st.expander("🛠️ System Debugger", expanded=False):
        st.write(f"**Show Launcher:** `{st.session_state.get('show_launcher')}`")
        st.write(f"**Mode:** `{st.session_state.get('prov_mode')}`")
        st.write(f"**Step:** `{st.session_state.get('prov_step')}`")
        st.write(f"**Service ID:** `{st.session_state.get('selected_svc_id')}`")
    
    # --- 1. STANDARDIZE STATE ---
    FabricStateManager.initialize()
    
    raw_step = st.session_state.get("prov_step", 1)
    if raw_step == "SUCCESS" or raw_step == 6:
        step = 6 
    else:
        try:
            step = int(raw_step)
        except:
            step = 1
        
    mode = st.session_state.get("prov_mode")
    data = st.session_state.get("prov_data", {})
    
    # --- 2. GLOBAL EXIT ---
    if st.button("⬅️ Exit to Operations Dashboard", key="global_wizard_exit"):
        st.session_state.show_launcher = True
        st.session_state.prov_mode = None
        st.session_state.prov_step = 1
        st.session_state.selected_svc_id = None
        # Clean up stale memory on hard exit
        st.session_state.pop("active_service_detail", None)
        st.rerun()

    st.divider()

    # --- 3. THE SYNC HANDSHAKE (Updated for State Alignment) ---
    fs_detail = st.session_state.get("active_service_detail")
    
    # 🛑 ALIGNMENT FIX: Prioritize 'active_service_id' (set by our child forms)
    service_id = (
        st.session_state.get("active_service_id") or 
        st.session_state.get("selected_svc_id") or 
        data.get("service_id")
    )

    if service_id:
        # Lock all pointers to the exact same UUID so the debugger and backend stay perfectly synced
        st.session_state.selected_svc_id = service_id
        st.session_state.active_service_id = service_id
        st.session_state["active_fs"] = service_id
        
        needs_refresh = st.session_state.get("force_fs_refresh", False)

        # 🛑 IF missing, OR ID changed, OR a child form forced a refresh -> Fetch!
        if not fs_detail or str(fs_detail.get("service_id")) != str(service_id) or needs_refresh:
            with st.spinner("🛰️ Syncing Live Fabric Manifest..."):
                
                # The Cache Buster
                if hasattr(get_fabric_service_detail, "clear"):
                    get_fabric_service_detail.clear(service_id)
                    
                fs_detail = get_fabric_service_detail(service_id)
                
                if fs_detail:
                    st.session_state.active_service_detail = fs_detail
                    FabricStateManager.set_active("fs", service_id, fs_detail)
                    
                # Reset the trigger
                if needs_refresh:
                    st.session_state.force_fs_refresh = False

    # Normalize Service Type
    svc_type = str(fs_detail.get("service_type", "IPVPN")).upper() if fs_detail else "UNKNOWN"
    svc_type_norm = svc_type.replace("EPLAN", "EP-LAN").replace("EVP-LLAN", "EVP-LAN")

    # --- 4. RENDER DEBUGGER ---
    render_debug_inspector()

    # Workflow Definitions
    L2_TYPES = ["EPL", "EVPL", "EP-LAN", "EVP-LAN", "LAN"]
    L3_TYPES = ["IPVPN", "MCGW", "IOD"]

    # ==========================================
    # 🏗️ WORKFLOW: ATTACH PORT / CLOUD ON-RAMP
    # ==========================================
    if mode in ["ATTACH_PORT", "CLOUD_ONRAMP"]:
        from src.utils.service_wizards import render_workflow_progress
        
        # 🛑 SYNC L2/L3 CLASSIFICATION (Matches the Digital Twin engine exactly)
        svc_type_norm = str(fs_detail.get("service_type", "")).upper().replace("EPLAN", "EP-LAN").replace("EVP-LLAN", "EVP-LAN")
        is_l2_evc = any(x in svc_type_norm for x in ["EPL", "EVPL", "EP-LAN", "EVP-LAN"])
        is_l3_vpn = any(x in svc_type_norm for x in ["IPVPN", "L3VPN", "INTERNET", "MCGW"])

        render_workflow_progress(current_step=step, svc_type=svc_type_norm)
        
        # 🎨 DIAGRAM PERSPECTIVE MAPPING
        if step < 6:
            diagram_step = step # Default
            
            # Map functional step to architectural diagram step per user request
            if mode == "ATTACH_PORT" and step == 2:
                diagram_step = 2
            elif mode == "CLOUD_ONRAMP" and step == 2:
                diagram_step = 5
            elif step in [3, 5]:
                diagram_step = 3
                
            _render_step_diagram(step_number=diagram_step, mode=mode, svc_detail=fs_detail)
        
        # 🧠 LOGIC FLOW ORCHESTRATION
        if step == 1:
            from src.utils.service_wizards import render_fabric_service_overview
            render_fabric_service_overview(fs_detail=fs_detail)
            
        elif step == 2:
            if mode == "CLOUD_ONRAMP":
                from src.utils.service_wizards import render_cloud_onramp_logic
                # Ensure customer_id is passed successfully
                render_cloud_onramp_logic(svc_detail=fs_detail, customer_id=customer_id)
            else:
                from src.utils.service_wizards import render_port_attachment_logic
                render_port_attachment_logic(fs_detail=fs_detail, customer_id=customer_id)
                
        elif step == 3:
            if is_l2_evc:
                from src.utils.service_wizards import render_logical_attachment_logic
                render_logical_attachment_logic(fs_detail=fs_detail, customer_id=customer_id)
            elif is_l3_vpn:
                from src.utils.service_wizards import render_interface_attachment_logic
                render_interface_attachment_logic(fs_detail=fs_detail, customer_id=customer_id)
                
        elif step == 4:
            if is_l3_vpn:
                from src.utils.service_wizards import render_routing_attachment_logic
                render_routing_attachment_logic(fs_detail=fs_detail, customer_id=customer_id)
                
        elif step == 5:
            from src.utils.service_wizards import render_logical_attachment_logic
            render_logical_attachment_logic(fs_detail=fs_detail, customer_id=customer_id)
            
        elif step == 6:
            from src.utils.service_wizards import render_provisioning_success_view
            # FIX: Prevented NameError by changing 'data' to 'fs_detail'
            receipt_data = st.session_state.get("prov_receipt", fs_detail)
            render_provisioning_success_view(receipt_data)
            
    # ==========================================
    # 🌱 WORKFLOW: NEW LOGICAL SERVICE (Decoupled)
    # ==========================================
    elif mode == "CREATE_SERVICE":
        # 100% Autonomous Workflow. 
        # Once the anchor is provisioned, it becomes a Brownfield service.
        # Therefore, this mode strictly contains Step 1 (Form) and Step 6 (Receipt).
        
        if step == 6 or str(st.session_state.get("prov_step")) == "SUCCESS":
            from src.utils.service_wizards import render_provisioning_success_view
            receipt_data = st.session_state.get("prov_data", data)
            render_provisioning_success_view(receipt_data)
            
        else:
            # Force diagram to Step 1. There are no Steps 2-5 in Greenfield anymore.
            _render_step_diagram(step_number=1, mode=mode, svc_detail=fs_detail) 
            
            from src.utils.ui_provisioning_form import render_service_context_form
            render_service_context_form(data, customer_id)
           
def _render_step_diagram(step_number: int, mode: str = None, svc_detail: dict = None):
    """
    Consolidated Reference Architecture Renderer (NDT).
    Updated to resolve 'full' and 'limited' file variants and 
    utilize PIL (Pillow) to bypass browser caching of stale images.
    """
    import os
    import streamlit as st
    from PIL import Image

    # 1. Determine Blueprint Base
    if svc_detail:
        raw_type = str(svc_detail.get("service_type", "MCGW")).lower().strip()
    else:
        context_data = st.session_state.get("prov_data") or {}
        raw_type = str(context_data.get("type") or st.session_state.get("sel_blueprint") or "MCGW").lower().strip()

    # THE FIX: Map "elan" to "evp-lan" so it finds your new files
    blueprint_map = {
        "l3vpn": "ipvpn", 
        "mcgw": "mcgw", 
        "evpn": "evpl", 
        "epl": "epl", 
        "elan": "elan",       # <--- Aliased here
        "ep-lan": "elan",
        "evp-lan": "elan",    # <--- Catch-all if DB returns evp-lan
        "iod": "iod"
    }
    
    file_base = blueprint_map.get(raw_type, raw_type)

    
    if mode == "ATTACH_PORT": display_title = f"{raw_type.upper()}: Port Attachment"
    elif mode == "PROVISION_CLOUD": display_title = f"{raw_type.upper()}: Cloud Onramp"
    else: display_title = raw_type.upper()

    # 2. Advanced Asset Discovery
    # We now check for multiple naming permutations per step
    use_cases = []
    missing_paths = []
    
    # Define possible naming patterns for this step
    patterns = [
        f"{file_base}-step{step_number}",          # Standard
        f"{file_base}-full-step{step_number}",     # Full Variant
        f"{file_base}-limited-step{step_number}"   # Limited Variant
    ]

    for base_pattern in patterns:
        # Generate an uppercase prefix variant (e.g., elan-step1 -> ELAN-step1)
        base_upper_prefix = base_pattern.replace(file_base, file_base.upper(), 1)
        
        # Check for standalone image
        standalone_lower = f"templates/png/{base_pattern}.png"
        standalone_upper = f"templates/png/{base_upper_prefix}.png"
        
        if os.path.exists(standalone_lower):
            label = base_pattern.split('-')[1].title() if 'step' not in base_pattern.split('-')[1] else "Primary"
            use_cases.append({"label": label, "path": standalone_lower})
        elif os.path.exists(standalone_upper):
            label = base_pattern.split('-')[1].title() if 'step' not in base_pattern.split('-')[1] else "Primary"
            use_cases.append({"label": label, "path": standalone_upper})
        else:
            missing_paths.append(standalone_lower)

        # Check for indexed images
        for i in range(1, 5):
            indexed_lower = f"templates/png/{base_pattern}-{i}.png"
            indexed_upper = f"templates/png/{base_upper_prefix}-{i}.png"
            
            if os.path.exists(indexed_lower):
                use_cases.append({"label": f"{base_pattern.split('-')[1].title()} #{i}", "path": indexed_lower})
            elif os.path.exists(indexed_upper):
                use_cases.append({"label": f"{base_pattern.split('-')[1].title()} #{i}", "path": indexed_upper})
            else:
                missing_paths.append(indexed_lower)
           
    md_path = f"templates/png/{file_base}-step{step_number}.md"
    md_exists = os.path.exists(md_path)

    # 3. Diagnostic Manifest
    with st.expander("🔍 NDT Asset Diagnostic Manifest", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.success("**✅ Found**")
            for uc in use_cases: st.caption(f"`{uc['path']}`")
            if md_exists: st.caption(f"MD: `{md_path}`")
            if not use_cases: st.write("None")
        with c2:
            st.error("**❌ Missing**")
            # Only show a subset to avoid clutter
            for m in missing_paths[:5]: st.caption(f"`{m}`")
            st.caption("...and other variant permutations.")

    # 4. Render the Component
    if use_cases or md_exists:
        exp_label = f"📖 Step {step_number} Reference Architecture: {display_title}"
        with st.expander(exp_label, expanded=True):
            # Create tabs based on found variants
            tab_titles = [uc['label'] for uc in use_cases]
            if md_exists: tab_titles.append("📝 Documentation")
            
            if tab_titles:
                tabs = st.tabs(tab_titles)
                for i, uc in enumerate(use_cases):
                    with tabs[i]: 
                        try:
                            # LOAD VIA PIL TO BYPASS BROWSER URL CACHE
                            img = Image.open(uc['path'])
                            st.image(img, width=650)
                            st.caption(f"Source: `{uc['path']}`")
                        except Exception as e:
                            st.error(f"Failed to load image via PIL: {str(e)}")
            
            if md_exists:
                with tabs[-1]:
                    with open(md_path, "r", encoding="utf-8") as f: 
                        st.markdown(f.read())
    else:
        st.warning(f"⚠️ **Architecture Assets Missing**: Checked variants for '{file_base}' at Step {step_number}.")
                    
def provision_fabric_service_api(customer_id: str, data: dict):
    """
    Generalized Provisioning Engine.
    Maps a dynamic 'prov_data' dictionary to the fixed fabric_services schema.
    Extra intent data is automatically serialized into the service_description field.
    """
    import streamlit as st
    from src.utils.api_customer import post_fabric_service

    # 1. GENERATE DYNAMIC DESCRIPTION
    # Collect all keys except the primary schema columns to store as metadata
    schema_cols = ['alias', 'type', 'rt', 'mode', 'service_id', 'name']
    metadata = [f"{k.replace('_', ' ').title()}: {v}" for k, v in data.items() if k not in schema_cols]
    
    description = " | ".join(metadata) if metadata else "No additional metadata provided."

    # 2. MAP PAYLOAD TO POSTGRES SCHEMA
    payload = {
        "customer_id": customer_id,
        "service_name": data.get("alias"),
        "service_alias": data.get("alias"),
        "service_type": data.get("type"),
        "service_description": description,
        "route_target": data.get("rt"),
        "health_status": 3  # Standard: 3 = Amber/Planned
    }
    
    try:
        with st.status(f"🛰️ Provisioning {payload['service_type']} Service...", expanded=True) as status:
            st.write(f"Pushing intent for {payload['service_name']} to Galileo Controller...")
            
            # Execute the API POST
            result = post_fabric_service(payload)
            
            st.write("Synchronizing Digital Twin and state tables...")
            status.update(label=f"✅ {payload['service_type']} Created Successfully!", state="complete", expanded=False)
            
            # Return the database-generated UUID
            return result.get("service_id")
            
    except Exception as e:
        st.error(f"Fabric Provisioning Failed: {str(e)}")
        return None
             
def render_port_attachment_logic(fs_detail: dict, customer_id: str):
    """
    Step 2 Logic: Physical Port Attachment.
    Features integrated architectural diagram (Step 2) as the primary reference anchor.
    Updated: Implements Drain-on-Success queue hydration and triggers the Cache Buster.
    """
    import streamlit as st
    from src.utils.ui_provisioning_form import render_fabric_port_form
    from src.utils.api_customer import post_port_intent
    from src.utils import network_utils

    # 1. Ensure all session queues are initialized
    network_utils.initialize_fabric_session()
    
    # --- Extract variables early ---
    service_id = fs_detail.get("service_id")
    svc_name = fs_detail.get("service_name", "Unknown")
    
    # 2. Retrieve the volatile Port Queue safely
    staged_payload = st.session_state.get("payload", {})
    service_context = staged_payload.get("service_context", {})
    children = service_context.get("children", {})
    ports_in_queue = children.get("ports", [])

    st.markdown(f"### 🔌 Step 2: Port Attachment")
    st.caption(f"Service: {svc_name} | ID: {service_id}")

    # Render the form (adds to ports_in_queue)
    render_fabric_port_form(fs_detail=fs_detail, namespace="active_wizard")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Back to Overview", type="primary", use_container_width=True):
            st.session_state.prov_step = 1
            st.rerun()

    with c2:
        if st.button("🚀 Commit Port Config", 
                     type="primary", 
                     use_container_width=True, 
                     disabled=len(ports_in_queue) == 0):
            
            success_count = 0
            failed_ports = [] # Track failures explicitly
            
            with st.spinner("Executing Port Intent..."):
                for port_intent in ports_in_queue:
                    port_intent["service_id"] = service_id
                    
                    # Execute API POST
                    api_response = post_port_intent(customer_id, port_intent)
                    
                    if api_response:
                        # Hydrate the stager with the database-generated UUID
                        network_utils.hydrate_stager_from_api('ports', api_response)
                        success_count += 1
                    else:
                        # Trap failed payloads to keep them in the queue
                        failed_ports.append(port_intent)

            # 3. THE HAND-OFF: Update Stager and Queue State
            if "ports" not in st.session_state.payload["service_context"]["children"]:
                st.session_state.payload["service_context"]["children"]["ports"] = []
                
            # Overwrite the session state queue to ONLY contain ports that failed
            st.session_state.payload["service_context"]["children"]["ports"] = failed_ports

            # 4. ROUTING LOGIC & SYNCHRONIZATION
            if success_count > 0 and len(failed_ports) == 0:
                st.success(f"Successfully provisioned {success_count} ports!")
                
                # 🛑 THE FIX: Trigger the cache buster in the orchestrator
                st.session_state.force_fs_refresh = True
                
                # Advance to Step 3: Interface Definition
                st.session_state.prov_step = 3
                st.rerun()
                
            elif success_count > 0 and len(failed_ports) > 0:
                # Partial Success: Trigger refresh for the successful ones, keep user on this step
                st.session_state.force_fs_refresh = True
                st.warning(f"⚠️ Partial Success: {success_count} provisioned, {len(failed_ports)} failed. Please review remaining ports.")
                
            else:
                st.error("❌ All ports failed to provision. Check API connectivity and logs.")

def render_logical_attachment_logic(fs_detail: dict, customer_id: str):
    """
    Orchestrates Step 5: Final Fabric Stitching.
    Delegates UI forms based on service type and strictly enforces Orchestrator state control.
    """
    import streamlit as st
    from src.utils.api_customer import post_fabric_connection, post_port_intent, get_fabric_service_detail
    from src.utils import ui_provisioning_form as forms

    service_id = fs_detail.get("service_id", "UNKNOWN")
    
    # ==========================================
    # 🛡️ THE GUARDED LIVE SYNC
    # ==========================================
    # Ensures we have the absolute latest ports from Step 2 without spamming the API
    sync_key = f"step5_synced_{service_id}"
    if not st.session_state.get(sync_key):
        with st.spinner("🔄 Fetching live fabric manifest..."):
            try:
                fresh_fs = get_fabric_service_detail(service_id)
                if fresh_fs:
                    fs_detail = fresh_fs
                    st.session_state.active_service_detail = fresh_fs
                    st.session_state[sync_key] = True 
            except Exception as e:
                st.error(f"🚨 API Failure during live sync: {e}")
    else:
        fs_detail = st.session_state.get("active_service_detail", fs_detail)

    svc_name = fs_detail.get("service_name", "Provisioning Target")
    svc_type = str(fs_detail.get("service_type", "")).upper().replace("EPLAN", "EP-LAN").replace("EVP-LLAN", "EVP-LAN")

    # Clean caption (Double-header bug removed)
    st.caption(f"Service Blueprint: **{svc_type}** | Anchor ID: `{service_id}`")
    
    # 1. EXTRACT STAGED ELEMENTS DIRECTLY FROM THE API MANIFEST
    staged_ports = fs_detail.get("fabric_ports", [])
    staged_intfs = fs_detail.get("fabric_interfaces", [])

    if not staged_ports:
        st.error(f"🚨 Missing Port Inventory. Ports must be bound to this {svc_type} service anchor in Step 2.")
        if st.button("🔄 Force Refresh Manifest", width="stretch"):
            # Clear the sync guard to force a true refresh on click
            st.session_state[sync_key] = False
            st.rerun()
        return

    # Safely handle key differences between the local stager vs the API payload
    port_map = {f"{p.get('port_name')} ({p.get('device_name', p.get('device', 'Unknown'))})": p for p in staged_ports}
    intf_map = {f"{i.get('interface_name', i.get('alias', 'Unknown'))}": i for i in staged_intfs}

    # 2. DELEGATE TO SPECIFIC UI FORMS
    with st.container(border=True):
        st.subheader("🔗 Fabric Connection Binding")
        
        stitch_params = None
        if svc_type in ["EPL", "EVPL"]:
            stitch_params = forms.render_p2p_stitch_form(port_map)
        elif svc_type in ["EP-LAN", "EVP-LAN", "ELAN"]:
            stitch_params = forms.render_multipoint_l2_stitch_form(port_map)
        else:
            stitch_params = forms.render_l3_stitch_form(port_map, intf_map)

    # 3. EXECUTION AND POSITIVE VERIFICATION
    if stitch_params is not None:
        if st.button("🚀 Finalize Fabric Connection", type="primary", width="stretch"):
            
            # Anti-loop check
            connector_a = stitch_params.get("connector_a_id")
            connector_b = stitch_params.get("connector_b_id")
            
            if connector_a and connector_b and (connector_a == connector_b):
                st.error("🚨 Connector A and Connector B cannot be the same physical port.")
                st.stop()

            vlan_tag = stitch_params.get("vlan_id", "UNTAGGED")
            
            # Assemble Final Payload (Unpack FIRST, Override LAST)
            stitch_payload = {
                **stitch_params, 
                "connection_name": f"CX-{svc_name[:10]}-V{vlan_tag}",
                "service_id": service_id,
                "status": "Provisioned", 
                "bandwidth": fs_detail.get("bandwidth", "10G") 
            }

            with st.spinner("🛰️ Writing Connection and Updating Port Statuses..."):
                api_response = post_fabric_connection(stitch_payload)
                
                if api_response:
                    # 1. Gather all UUIDs involved in this stitch
                    used_port_ids = []
                    if connector_a: used_port_ids.append(connector_a)
                    if connector_b: used_port_ids.append(connector_b)
                    if "port_ids" in stitch_params: used_port_ids.extend(stitch_params["port_ids"])
                    if "selected_ports" in stitch_params: used_port_ids.extend(stitch_params["selected_ports"])
                    used_port_ids = list(set(filter(None, used_port_ids)))
                    
                    # 2. Safely PUT using the FULL port dictionaries to prevent data loss
                    update_errors = 0
                    for pid in used_port_ids:
                        # Find the full original dictionary from the Stager Context
                        port_obj = next((p for p in staged_ports if p.get("port_id") == pid), None)
                        
                        if port_obj:
                            try:
                                # Overrides only the status, safely passing the rest of the payload
                                post_port_intent(customer_id, port_obj, status_override="Provisioned")
                            except Exception as e:
                                print(f"[API ERROR] Failed to update port {pid}: {e}")
                                update_errors += 1
                        else:
                            print(f"[WARN] Port {pid} not found in staged context.")
                            update_errors += 1
                            
                    if update_errors == 0:
                        st.success("✅ Connection created and all ports successfully advanced to 'Provisioned'!")
                    else:
                        st.warning(f"⚠️ Connection created, but {update_errors} port(s) failed state transition.")
                        
                    st.balloons()
                    
                    # Transition to Step 6
                    st.session_state.prov_receipt = stitch_payload
                    st.session_state.stager_queue = {"ports": [], "interfaces": [], "connections": []}
                    st.session_state.prov_step = 6
                    st.rerun()
                else:
                    st.error("Fabric Connection failed to write. Check API logs.")    

def render_interface_attachment_logic(fs_detail: dict, customer_id: str):
    """
    Orchestrates Step 3: Interface Definition.
    FIXED: Deep initialization of payload to prevent KeyError: 'interfaces'.
    """
    import streamlit as st
    from src.utils.ui_provisioning_form import render_interface_build_form
    from src.utils.network_utils import calculate_ip_assignment, initialize_fabric_session
    from src.utils.api_customer import post_interface_intent
    from src.utils import network_utils

    # 1. DEEP INITIALIZATION (The KeyError Fix)
    # This ensures the nested path payload['service_context']['children']['interfaces'] exists
    network_utils.initialize_fabric_session()
    
    payload = st.session_state.payload
    # Use setdefault recursively to guarantee the 'interfaces' key
    ctx = payload.setdefault("service_context", {})
    children = ctx.setdefault("children", {})
    intfs_in_queue = children.setdefault("interfaces", []) # This line kills the KeyError
    
    st.markdown(f"### 💻 Step 3: Interface Definition")
    st.caption(f"Service Context: {fs_detail.get('service_name')}")

    # 2. RENDER FORM
    # Now children['interfaces'] is guaranteed to exist for l3_data
    render_interface_build_form(
        l3_data=children, 
        calc_func=calculate_ip_assignment, 
        namespace="intf_wiz"
    )

    st.divider()

    # 3. COMMIT LOGIC
    if st.button("🚀 Commit Interface Config", type="primary", use_container_width=True, disabled=len(intfs_in_queue) == 0):
        
        success_count = 0
        with st.spinner("Provisioning Logical Interfaces..."):
            for intf in intfs_in_queue:
                intf["service_id"] = fs_detail.get("service_id")
                
                # Execute POST
                result = post_interface_intent(intf)
                
                if result:
                    # Update the intent with the real DB ID for the Stager
                    intf["interface_id"] = result.get("interface_id")
                    success_count += 1
        
        # 4. THE HAND-OFF: Update Stager and Clear Queue
        if success_count == len(intfs_in_queue) and success_count > 0:
            if network_utils.commit_queue_to_stager('interfaces'):
                st.success(f"Interfaces provisioned. Stager Queue updated.")
                
                # Advance to Routing or Connection
                st.session_state.prov_step = 4 
                st.rerun()
        else:
            st.error("Partial failure detected. Check Stager JSON.")

def render_routing_attachment_logic(fs_detail: dict, customer_id: str):
    """
    Orchestrates Step 4: Routing Protocol Configuration.
    STAGER DRIVEN: Pulls interfaces from the persistent Stager JSON 
    to bridge the hydration gap.
    """
    import streamlit as st
    from src.utils.ui_provisioning_form import render_static_route_form, render_bgp_peer_form
    from src.utils.api_customer import post_static_route_intent, post_bgp_peer_intent
    from src.utils import network_utils

    svc_name = fs_detail.get("service_name", "Unknown")
    st.markdown(f"### 🗺️ Step 4: Routing Configuration")
    st.caption(f"Service: {svc_name} | Establishing reachability via Staged Interfaces.")

    # 1. ACCESS THE STAGER CONTEXT (The IDs preserved from Step 3)
    _, interfaces = network_utils.get_stager_context()
    
    if not interfaces:
        st.warning("⚠️ No committed interfaces found in the Stager. Please return to Step 3.")
        if st.button("⬅️ Return to Interfaces", type="primary",use_container_width=True):
            st.session_state.prov_step = 3
            st.rerun()
        return

    # 2. INTERFACE SELECTOR
    # If Step 3 provisioned multiple interfaces, the user picks which one to route
    intf_map = {f"{i.get('alias')} ({i.get('ipv4_lumen')})": i for i in interfaces}
    selected_label = st.selectbox("🎯 Select Target Interface for Routing", options=list(intf_map.keys()))
    target_intf = intf_map[selected_label]
    interface_id = target_intf.get("interface_id")

    if not interface_id:
        st.error("❌ Critical Error: Interface ID missing from Stager. Check Step 3 API logs.")
        return

    # 3. RENDER INPUT FORMS
    # Note: These forms append to target_intf['routing']['bgp'|'static']
    tab1, tab2 = st.tabs(["🤝 BGP Peering", "📍 Static Routing"])
    with tab1:
        render_bgp_peer_form(placeholder_dict={}, target_intf=target_intf)
    with tab2:
        render_static_route_form(placeholder_dict={}, target_intf=target_intf)
        
    st.divider()
    
    # 4. NAVIGATION & COMMIT LOGIC
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Back to Interfaces (Step 3)",type="primary", use_container_width=True):
            st.session_state.prov_step = 3
            st.rerun()
            
    with c2:
        # Check if the user has staged any routing intents in the UI
        routing_manifest = target_intf.setdefault("routing", {"bgp": [], "static": []})
        has_routing = len(routing_manifest["bgp"]) > 0 or len(routing_manifest["static"]) > 0

        if st.button("🚀 Commit Routing & Proceed", type="primary", use_container_width=True):
            
            # If no routing is needed (e.g., L2 service or simple L3), just skip to Step 5
            if not has_routing:
                st.info("No routing protocols staged. Moving to Final Stitching...")
                st.session_state.prov_step = 5
                st.rerun()
                return

            success_count = 0
            total_intents = len(routing_manifest["bgp"]) + len(routing_manifest["static"])

            with st.spinner("Pushing Routing Intents to Fabric API..."):
                # --- COMMIT BGP NEIGHBORS ---
                for bgp in routing_manifest["bgp"]:
                    # Ensure database ID and API keys are mapped
                    bgp["interface_id"] = interface_id
                    bgp["remote_asn"] = bgp.get("customer_as")
                    bgp["local_asn"] = bgp.get("lumen_as")
                    bgp["bfd"] = bgp.get("bfd_enabled")
                    
                    if post_bgp_peer_intent(bgp):
                        success_count += 1
                
                # --- COMMIT STATIC ROUTES ---
                for route in routing_manifest["static"]:
                    route["interface_id"] = interface_id
                    
                    if post_static_route_intent(route):
                        success_count += 1

            # 5. FINAL TRANSITION
            if success_count == total_intents:
                st.success(f"Successfully provisioned {success_count} routing intents.")
                # We don't clear the stager here, as Step 5 needs the Port/Intf IDs
                st.session_state.prov_step = 5
                st.rerun()
            else:
                st.warning(f"Partial success: {success_count}/{total_intents} intents provisioned.")

def render_fabric_service_overview(fs_detail: dict, is_read_only: bool = False):
    """
    Renders a comprehensive overview of a Fabric Service.
    Leverages service-specific rule logic to drive UI states.
    """
    import streamlit as st
    from src.galileo.fabric_service_builder import render_twin_topology

    # --- 1. DATA EXTRACTION ---
    service_id = fs_detail.get("service_id")
    svc_name = fs_detail.get("service_name", "Unknown")
    svc_type_norm = str(fs_detail.get("service_type", "")).upper().replace("EPLAN", "EP-LAN")

    # --- 2. EXECUTE RULES (Centralized Logic) ---
    if svc_type_norm == "EPL":
        rules = rule_logic_EPL(fs_detail)
    # Add ELIFs for EVPL/L3 here as we build them...
    else:
        # Default placeholder rules
        rules = {"show_add_button": True, "ready_to_advance": False, "assigned_ports": []}

    # Extract UI states from rules
    show_add_button = rules.get("show_add_button", True)
    success_msg = rules.get("success_msg", None)
    validation_error = rules.get("validation_error", None)
    ready_to_advance = rules.get("ready_to_advance", False)
    assigned_ports = rules.get("assigned_ports", [])

    # --- 3. METRICS RENDER ---
    st.markdown(f"### 🛰️ Service Overview: {svc_name}")
    
    m1, m2, m3, m4, m5, m6 = st.columns([1.5, 1, 1, 1, 1, 1])
    
    # Status Metric
    is_stitched = any(c.get("connector_a_id") and c.get("connector_b_id") for c in fs_detail.get("fabric_connections", []))
    m1.metric("Status", "🟢 Active" if is_stitched else "🟠 Staging")
    
    m2.metric("Route Target", fs_detail.get("route_target", "N/A"))
    m3.metric("Service Ports", len(assigned_ports))
    
    speeds = list(set([str(p.get('port_speed', 'N/A')) for p in assigned_ports]))
    m4.metric("Line Speed", ", ".join(speeds) if speeds else "N/A")
    m5.metric("Connections", len(fs_detail.get("fabric_connections", [])))
    
    # Bandwidth
    bw_val = "N/A"
    if fs_detail.get("fabric_connections"):
        bw_val = f"{fs_detail['fabric_connections'][0].get('service_bw', 'N/A')} Mbps"
    m6.metric("Service BW", bw_val)

    # --- 4. NAVIGATION BAR ---
    if not is_read_only:
        st.divider()
        if validation_error: st.error(validation_error)
        elif success_msg: st.success(success_msg)

        btn_cols = st.columns([1, 1, 1]) if show_add_button else st.columns([1, 1])
        
        with btn_cols[0]:
            if st.button("⬅️ Back to Launcher",type="primary", use_container_width=True):
                st.session_state.show_launcher = True
                st.rerun()

        if show_add_button:
            with btn_cols[1]:
                if st.button("🔌 Add Fabric Port", use_container_width=True, type="primary"):
                    st.session_state.prov_step = 2 
                    st.rerun()
            next_idx = 2
        else:
            next_idx = 1

        with btn_cols[next_idx]:
            if st.button("Next Step (Logic) ➡️", 
                         use_container_width=True, 
                         type="primary" if not show_add_button else "secondary",
                         disabled=not ready_to_advance):
                st.session_state.prov_step = 3
                st.rerun()

    # --- 5. DIGITAL TWIN ---
    st.markdown("---")
    import uuid
    # 2. Generate a short unique string for this specific render cycle
    unique_salt = uuid.uuid4().hex[:6]
    
    # 3. Append the salt to the key_prefix
    render_twin_topology(
        fs_detail, 
        key_prefix=f"ov_{service_id}_{unique_salt}"
    )

def render_workflow_progress(current_step: int, svc_type: str):
    """
    Renders a dynamic visual progress bar based on the specific service type.
    Differentiates between complex L3 paths and streamlined L2 paths.
    """
    import streamlit as st

    # Normalize service type
    svc_type_norm = str(svc_type).upper().replace("EPLAN", "EP-LAN").replace("EVP-LLAN", "EVP-LAN")

    # Define the roadmap based on service type
    if svc_type_norm in ["IPVPN", "MCGW", "IOD", "DIA", "IP-VPN"]:
        roadmap = ["Overview", "Ports", "Interfaces", "Routing", "Connections"]
    else:
        # L2 Services (EPL, EVPL, E-LAN variants)
        roadmap = ["Overview", "Ports", "Connections"]

    # Build the visual elements
    md_parts = []
    for i, step_name in enumerate(roadmap):
        step_num = i + 1
        if step_num < current_step:
            # Completed Steps
            md_parts.append(f"**✅ <span style='color:#4CAF50'>{step_name}</span>**")
        elif step_num == current_step:
            # Active Step
            md_parts.append(f"**🔵 <span style='color:#2196F3; border-bottom: 2px solid #2196F3; padding-bottom: 2px;'>{step_name}</span>**")
        else:
            # Future Steps
            md_parts.append(f"<span style='color:gray'>⚪ {step_name}</span>")

    # Join the steps with an arrow
    progress_html = " &nbsp; ➔ &nbsp; ".join(md_parts)

    # Render inside a stylized container
    st.markdown(
        f"""
        <div style='
            padding: 15px; 
            border-radius: 8px; 
            background-color: rgba(128,128,128,0.05); 
            border: 1px solid rgba(128,128,128,0.2);
            text-align: center; 
            margin-bottom: 25px; 
            font-size: 15px;
            overflow-x: auto;
            white-space: nowrap;
        '>
            {progress_html}
        </div>
        """,
        unsafe_allow_html=True
    )

def _render_new_service_workflow(container, customer_id: str):
    """
    Dashboard Tile: New Service Builder.
    Captures the desired blueprint and hands off a clean state to the Orchestrator.
    """
    import streamlit as st
    
    with container:
        st.subheader("🆕 Initialize New Fabric Service")
        st.caption("Select a blueprint to begin the guided provisioning wizard.")

        # --- NAMESPACED BLUEPRINT SELECTION ---
        # Note: Aligned options with our Step 1 supported_types
        blueprint_options = ["IPVPN", "MCGW", "EVPL", "EPL", "ELAN", "IOD"]
        
        # Check the dynamic widget key first to maintain visual state across background reruns
        widget_key = f"launch_blueprint_{customer_id}"
        current_sel = st.session_state.get(widget_key) or st.session_state.get("sel_blueprint")
        
        if current_sel in blueprint_options:
            default_idx = blueprint_options.index(current_sel)
        else:
            default_idx = 0

        # Unique Key to avoid 'Shadow Render' collisions
        blueprint = st.selectbox(
            "Select Blueprint Type",
            options=blueprint_options,
            index=default_idx,
            key=widget_key
        )

        st.divider()
        
        # ==========================================
        # 🛑 THE STATE HANDOFF (Action Trigger)
        # ==========================================
        # CHANGED: width="stretch" to use_container_width=True
        if st.button("🚀 Launch Service Builder", type="primary", use_container_width=True, key=f"btn_launch_new_{customer_id}"):
            
            # 1. THE DEEP PURGE: Exorcise all global tracking IDs
            # This ensures the Sync Handshake in render_sub_wizard_logic starts entirely fresh.
            ghost_keys = [
                "selected_svc_id", 
                "active_service_id", 
                "active_fs", 
                "active_service_detail",
                "force_fs_refresh",
                "payload"  # <-- CRITICAL ADDITION: Purge the staging dictionary
            ]
            
            for key in ghost_keys:
                st.session_state.pop(key, None)
                
            # If FabricStateManager has a clear method, you could also invoke it here
            # FabricStateManager.clear_active("fs")

            # 2. Close the dashboard, open the wizard
            st.session_state.show_launcher = False
            
            # 3. Set the Orchestrator Routing
            st.session_state.prov_mode = "CREATE_SERVICE"
            st.session_state.prov_step = 1
            
            # 4. Clean Slate Hydration: Wipe out ghost states and prepopulate the form!
            st.session_state.prov_data = {
                "mode": "New Fabric Service",
                "type": blueprint  # Passes target directly to Step 1
            }
            
            # 5. Trigger the Master Orchestrator transition
            st.rerun()

def render_cloud_onramp_logic(svc_detail: dict, customer_id: str):
    """
    Orchestrates the Cloud Onramp phase of the wizard.
    Fully plumbed to use the modularized Cloud Provisioning Form.
    Updated: Features Drain-on-Success queue hydration and strict dashboard refresh on exit.
    """
    import streamlit as st
    from src.utils.ui_provisioning_form import render_cloud_provisioning_form
    
    # Lazy imports to handle API execution and staging
    from src.utils.api_customer import post_cloud_intent
    from src.utils import network_utils

    # 1. Ensure session queues are initialized
    network_utils.initialize_fabric_session()
    
    svc_name = svc_detail.get("service_name", "Unknown Service")
    service_id = svc_detail.get("service_id")
    
    # 2. Retrieve the volatile Cloud Queue safely
    staged_payload = st.session_state.get("payload", {})
    service_context = staged_payload.get("service_context", {})
    children = service_context.get("children", {})
    clouds_in_queue = children.get("cloud_interconnects", [])

    st.markdown(f"### ☁️ Cloud Staging: {svc_name}")
    st.caption("Configure Virtual Cross-Connects (VXCs) to Cloud Service Providers.")

    # Call the modular form (User interactions here will append to clouds_in_queue)
    render_cloud_provisioning_form(fs_detail=svc_detail, namespace="active_cloud_wizard")
            
    st.divider()
    
    # 3. EXECUTION LOGIC (The Commit Button)
    if len(clouds_in_queue) > 0:
        if st.button("🚀 Commit Cloud Config", type="primary", use_container_width=True):
            
            success_count = 0
            failed_clouds = []
            
            with st.spinner("Executing Cloud Interconnect Intent..."):
                for cloud_intent in clouds_in_queue:
                    # Bind to the active service anchor
                    cloud_intent["service_id"] = service_id
                    
                    # Execute API POST
                    api_response = post_cloud_intent(customer_id, cloud_intent)
                    
                    if api_response:
                        # Hydrate the stager with the database-generated UUIDs
                        network_utils.hydrate_stager_from_api('cloud_interconnects', api_response)
                        success_count += 1
                    else:
                        # Trap failed payloads to keep them in the UI queue for retry
                        failed_clouds.append(cloud_intent)

            # Drain successful items from the queue
            if "cloud_interconnects" not in st.session_state.payload["service_context"]["children"]:
                st.session_state.payload["service_context"]["children"]["cloud_interconnects"] = []
                
            st.session_state.payload["service_context"]["children"]["cloud_interconnects"] = failed_clouds

            # UX Feedback
            if success_count > 0 and len(failed_clouds) == 0:
                st.success(f"Successfully provisioned {success_count} Cloud Interconnect(s)!")
                # Optional: Force a micro-rerun here to clear the form visually
                st.rerun()
            elif success_count > 0 and len(failed_clouds) > 0:
                st.warning(f"⚠️ Partial Success: {success_count} provisioned, {len(failed_clouds)} failed.")
            else:
                st.error("❌ All cloud provisions failed. Check API connectivity and logs.")

    st.divider()

    # 4. NAVIGATION & STRICT REFRESH HANDOFF
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Back to Overview (Step 1)", use_container_width=True):
            st.session_state.prov_step = 1
            st.rerun()
            
    with c2:
        if st.button("🏠 Finish & Exit to Launcher", type="secondary", use_container_width=True):
            st.session_state.active_service_id = service_id
            st.session_state.show_launcher = True
            st.session_state.prov_mode = None
            st.session_state.prov_step = 1
            
            if "payload" in st.session_state:
                del st.session_state["payload"]
                
            # 👇 ADD THIS LINE 👇
            st.session_state.force_fs_refresh = True
            
            st.rerun()

def render_provisioning_success_view(data: dict):
    """
    Displays a success summary after a service or connection is provisioned.
    Dynamically adapts messaging based on the current provisioning mode.
    """
    import streamlit as st
    
    # 1. DETERMINE CONTEXT
    mode = st.session_state.get("prov_mode", "CREATE_SERVICE")
    service_id = data.get('service_id', 'UUID-PENDING')
    alias = data.get('alias') or data.get('service_alias') or 'Service'
    
    # 2. DYNAMIC MESSAGING
    if mode == "ATTACH_PORT":
        title = f"Fabric Connections Stitched!"
        msg = f"Physical interfaces have been successfully bound to **{alias}**."
        step_a_icon, step_a_title, step_a_desc = "☁️", "Cloud Layer", "Extend this fabric to AWS/Azure/GCP via Cloud Onramps."
        step_b_icon, step_b_title, step_b_desc = "🧩", "Routing & BGP", "Apply custom routing policies to these new connections."
        log_success = f"[SUCCESS] Fabric Connections provisioned for {service_id}."
    elif mode == "CLOUD_ONRAMP":
        title = f"Cloud Onramp Established!"
        msg = f"Your virtual circuit to the Cloud Provider is provisioned for **{alias}**."
        step_a_icon, step_a_title, step_a_desc = "👁️", "Route Vision", "Verify BGP propagation and latency in the Vision tab."
        step_b_icon, step_b_title, step_b_desc = "🛠️", "Policy Audit", "Review the security group and prefix-list filters."
        log_success = f"[SUCCESS] Cloud VXC provisioned for {service_id}."
    else:
        # Default to CREATE_SERVICE behavior
        title = f"{alias} ({data.get('type', 'IPVPN')}) is now Staged!"
        msg = "The logical service anchor is provisioned. Now you need to establish the physical and virtual paths:"
        step_a_icon, step_a_title, step_a_desc = "🔌", "Physical Layer", "Bind physical UNI/NNI interfaces to this service via **Fabric Connections**."
        step_b_icon, step_b_title, step_b_desc = "☁️", "Virtual Layer", "Connect to Cloud Service Providers via **Cloud Onramps**."
        log_success = f"[SUCCESS] Service ID {service_id} is now STAGED."

    # 3. VISUAL CELEBRATION
    st.balloons()
    st.success(f"### 🎉 {title}")
    st.info(f"**Galileo Service ID:** `{service_id}`")
    
    # Safe extraction of policy to prevent NameErrors
    existing_policy = data.get("existing_policy")
    if existing_policy:
        st.info(f"✅ Policy '{existing_policy}' has been successfully mapped.")
    
    # 4. NEXT STEPS UI
    with st.container(border=True):
        st.markdown("#### 🏁 Next Steps for Build-out")
        st.write(msg)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"##### {step_a_icon} {step_a_title}")
            st.write(step_a_desc)
            
        with col_b:
            st.markdown(f"##### {step_b_icon} {step_b_title}")
            st.write(step_b_desc)
        
        st.divider()
        
        # 🟢 The "Clean Slate" Button (UPDATED to width="stretch")
        if st.button("⬅️ Return to Provisioning Center", type="primary", width="stretch"):
            # Reset Navigation State
            st.session_state.show_launcher = True
            st.session_state.prov_mode = None
            st.session_state.prov_step = 1
            
            # Hard Clear the Data Dictionaries
            st.session_state.prov_data = {}
            if 'fc_queue' in st.session_state:
                st.session_state.fc_queue = [] 
            if 'payload' in st.session_state:
                st.session_state.payload = {}
                
            st.rerun()

    # 5. EXECUTION LOGS
    with st.expander("📝 View Deployment Logs"):
        st.caption("Galileo Controller Execution Summary:")
        st.code(f"""
        [INFO] Execution Mode: {mode}
        [INFO] Target Service: {alias}
        [INFO] Resource Allocation: Successfully mapped to PostgreSQL.
        {log_success}
        """, language="bash")                          

def render_fabric_connection_rules(fs_detail: dict):
    """
    The Single Source of Truth for Service Logic.
    Dispatches to isolated 'def' blocks based on service type.
    """
    import streamlit as st
    
    svc_type = str(fs_detail.get("service_type", "")).upper()
    
    if svc_type == "EPL":
        return rule_logic_EPL(fs_detail)
    elif svc_type == "EVPL":
        return rule_logic_EVPL(fs_detail)
    elif svc_type in ["IPVPN", "MCGW", "IOD"]:
        return rule_logic_L3_SERVICES(fs_detail)
    else:
        st.warning(f"⚠️ No logic defined for service type: {svc_type}")

def rule_logic_EPL(fs_detail: dict):
    """
    Refined EPL Logic for All-2-1-bundled ports in Staged status.
    Ensures ports are not already tied to an existing connection.
    """
    ports = fs_detail.get("fabric_ports", [])
    conns = fs_detail.get("fabric_connections", [])

    # 1. Filter for ports that are:
    # - Staged
    # - Tagged as All-2-1-bundled (Standard for EPL)
    # - Have NO active fabric_connection_ids (Available for stitching)
    assigned = [
        p for p in ports 
        if p.get("port_service_status") == "Staged" 
        and p.get("port_tagging") == "All-2-1-bundled"
        and not p.get("fabric_connection_ids")
    ]
    
    total_ports = len(assigned)
    
    # Check if a stitch already exists in the manifest
    has_stitch = len(conns) > 0
    
    # Speed Validation
    unique_speeds = list(set([p.get('port_speed') for p in assigned]))
    speed_mismatch = total_ports >= 2 and len(unique_speeds) > 1

    # --- RULES ENGINE ---
    show_add_button = True
    success_msg = None
    validation_error = None
    ready_to_advance = False

    if total_ports == 2:
        if speed_mismatch:
            validation_error = "🛑 **Speed Mismatch**: EPL ports must have identical line rates."
        else:
            success_msg = "✅ **EPL Pair Staged**: Ports are ready for cross-connect."
            ready_to_advance = True
            show_add_button = False
    
    elif total_ports > 2:
        success_msg = f"⚠️ **Multiple Ports Available**: {total_ports} ports are staged. Select a pair to stitch."
        ready_to_advance = True
        show_add_button = False

    elif total_ports < 2:
        validation_error = "ℹ️ **Selection Incomplete**: Please stage a second All-2-1-bundled port."

    return {
        "show_add_button": show_add_button,
        "success_msg": success_msg,
        "validation_error": validation_error,
        "ready_to_advance": ready_to_advance,
        "assigned_ports": assigned
    }

def rule_logic_EVPL(fs_detail: dict):
    """
    EVPL Rule Engine with Hybrid Personality Logic.
    - A21 <-> A21: 'EPL-Lite' (No CE-VLAN needed, limited to 2 ports)
    - Tagged <-> ANY: 'Multiplexed' (CE-VLAN enabled)
    """
    import streamlit as st
    service_id = fs_detail.get("service_id")
    customer_ports = fs_detail.get("fabric_ports", [])
    conns = fs_detail.get("fabric_connections", [])

    # 1. IDENTIFY ELIGIBLE INVENTORY (Same as before)
    eligible_ports = []
    for p in customer_ports:
        tagging = p.get("port_tagging")
        has_conns = len(p.get("fabric_connection_ids") or []) > 0
        if tagging == "Tagged" or (tagging == "All-2-1-bundled" and not has_conns):
            eligible_ports.append(p)
        elif service_id in (p.get("fabric_service_ids") or []):
            if p not in eligible_ports: eligible_ports.append(p)

    # 2. TOPOLOGY DETECTION (Look at existing or staged connections)
    # Default to Multiplex unless both sides of a potential stitch are A21
    multiplex_enabled = True
    topology_type = "Multiplexed"
    port_limit = 50 # Default for EVPL

    # If we have ports assigned, check if they are ALL A21
    assigned_ports = [p for p in eligible_ports if service_id in (p.get("fabric_service_ids") or [])]
    
    if len(assigned_ports) >= 2:
        all_a21 = all(p.get("port_tagging") == "All-2-1-bundled" for p in assigned_ports)
        if all_a21:
            multiplex_enabled = False
            topology_type = "Dedicated (A21-to-A21)"
            port_limit = 2

    return {
        "eligible_ports": eligible_ports,
        "assigned_ports": assigned_ports,
        "multiplex_enabled": multiplex_enabled,
        "topology_type": topology_type,
        "port_limit": port_limit,
        "used_ce_vlans": [str(c.get("c_vlan_list")) for c in conns if c.get("c_vlan_list")]
    }

def rule_logic_L3_SERVICES(fs_detail: dict):
    """
    L3 requires Port-to-VRF binding + BGP Routing Context.
    """
    import streamlit as st
    st.info("🚧 L3 Rules: Evaluating VRF Interface binding and BGP Neighbors.")

def _render_port_workflow(col, df_services):
    """
    Renders the 'Attach Port' launcher column.
    Enhanced for EPL: Initializes payload with both 'ports' and 'connections' queues.
    """
    import streamlit as st
    from src.galileo.galileo_templates import get_base64_image

    with col:
        # Note: Ensure CARD_HEIGHT is defined in your scope or imported
        with st.container(border=True, height=CARD_HEIGHT):
            img_port = get_base64_image("templates/png/FabricPort.png")
            if img_port: 
                st.image(img_port, width=150)
                
            st.subheader("Attach Port")
            st.write("Link physical hand-offs and define fabric connectivity.")
            
            if not df_services.empty:
                # 1. Map names to full records to access service_type and service_id
                svc_map = {row['service_name']: row for _, row in df_services.iterrows()}
                
                sel_svc_name = st.selectbox(
                    "Target Service", 
                    options=list(svc_map.keys()), 
                    key="sel_port_svc"
                )
                
                selected_svc_data = svc_map[sel_svc_name]
                svc_id = selected_svc_data['service_id']
                svc_type = str(selected_svc_data.get('service_type', 'IPVPN')).upper()
                
                # 🟢 THE FIX: Lock the target_id into the global state IMMEDIATELY!
                st.session_state["selected_svc_id"] = svc_id
                st.session_state["active_fs"] = svc_id
                
                # Ensure prov_data gets it too for the ATTACH_PORT routing
                if "prov_data" not in st.session_state:
                    st.session_state.prov_data = {}
                st.session_state.prov_data["service_id"] = svc_id
                
                if st.button("🔌 Add Fabric Port", use_container_width=True, type="primary"):
                    # 2. HYDRATION: Basic Context for the Wizard
                    st.session_state.prov_data["service_type"] = svc_type
                    st.session_state.prov_data["alias"] = sel_svc_name
                    st.session_state.prov_data["mode"] = "Attach Port"
                    
                    # 3. INITIALIZE COMPLEX PAYLOAD
                    # For EPL, we need 'ports' for the physical handoffs 
                    # and 'connections' to link the two ports together.
                    st.session_state.payload = {
                        "service_id": svc_id,
                        "service_type": svc_type,
                        "service_context": {
                            "children": {
                                "ports": [],       # Physical interface queue
                                "connections": []  # Logical cross-connect/backbone queue
                            }
                        }
                    }
                    
                    # 4. TRANSITION: Enter Wizard Step 1 (The Overview/Sync point)
                    st.session_state.prov_mode = "ATTACH_PORT"
                    st.session_state.prov_step = 1 
                    st.session_state.show_launcher = False
                    st.rerun()
            else: 
                st.warning("⚠️ No services found. Create a service first.") 
                
def _render_cloud_workflow(col, df_services, unique_prefix="default"):
    """
    Renders the Cloud Onramp launcher tile. 
    Finalized to trigger the Step 2 Cloud Staging Form.
    """
    import streamlit as st
    from src.galileo.galileo_templates import get_base64_image

    # Use a cleaner keying strategy based on the prefix
    final_key = f"cloud_tile_{unique_prefix}"

    with col.container(border=True, height=450): 
        # --- Logo Display ---
        img_aws = get_base64_image("templates/png/AWS.png")
        img_gcp = get_base64_image("templates/png/GCP.png")
        img_azure = get_base64_image("templates/png/Azure.png")
        
        logo_cols = st.columns(3)
        with logo_cols[0]:
            if img_aws: st.image(img_aws, width=100)
        with logo_cols[1]:
            if img_gcp: st.image(img_gcp, width=100)
        with logo_cols[2]:
            if img_azure: st.image(img_azure, width=100)

        st.subheader("Attach Cloud Service Providers")

        # --- Service Selection ---
        cloud_capable_types = ["IPVPN", "MCGW", "IOD"]
        if not df_services.empty:
            valid_svcs = df_services[df_services['service_type'].str.upper().isin(cloud_capable_types)]
            
            if not valid_svcs.empty:
                service_map = {f"{row['service_name']} ({row['service_type']})": row['service_id'] 
                               for _, row in valid_svcs.iterrows()}
                
                selected_display = st.selectbox(
                    "Target Fabric Service (MCGW)",
                    options=list(service_map.keys()),
                    key=f"{final_key}_sel_svc"
                )
                target_id = service_map[selected_display]

                st.divider()

                # --- The "Add Cloud" Trigger ---
                if st.button("➕ Add Cloud Connection", key=f"{final_key}_btn_add", use_container_width=True, type="primary"):
                    # CRITICAL STATE HANDSHAKE
                    st.session_state.show_launcher = False
                    st.session_state.prov_mode = "CLOUD_ONRAMP"
                    st.session_state.selected_svc_id = target_id
                    # Move to Step 2 to skip the overview and go straight to the staging form
                    st.session_state.prov_step = 2 
                    st.rerun()
            else:
                st.info("No Cloud-capable (L3) services available.")
        else:
            st.warning("Please create a fabric service first.")

def _trigger_cloud_provisioning(service_id, provider):
    """
    Private helper to update session state and route to the Cloud Wizard.
    """
    import streamlit as st
    st.session_state.show_launcher = False
    st.session_state.prov_mode = "CLOUD_ONRAMP"
    st.session_state.cloud_provider = provider
    st.session_state.selected_svc_id = service_id
    st.session_state.prov_step = 1
    st.rerun()

def _launch_cloud_logic(service_id):
    """Helper to set state and rerun"""
    import streamlit as st
    st.session_state.show_launcher = False
    st.session_state.prov_mode = "CLOUD_ONRAMP"
    st.session_state.selected_svc_id = service_id
    st.session_state.prov_step = 1
    st.rerun()

def launch_cloud_form(service_id):
    """Helper to set state and rerun"""
    import streamlit as st
    st.session_state.show_launcher = False
    st.session_state.prov_mode = "CLOUD_ONRAMP"
    st.session_state.selected_svc_id = service_id
    st.session_state.prov_step = 1
    st.rerun()

def _render_add_new_port_workflow(col):
    """
    Scaffold for Ordering a New Physical Port.
    """
    import streamlit as st
    
    # Generate a random 6-character salt for the button key
    salt = uuid.uuid4().hex[:6]
    with col:
        with st.container(border=True,height=CARD_HEIGHT):
            img_port = get_base64_image("templates/png/FabricPort.png")
            if img_port: 
                st.image(img_port, width=150)
            st.markdown("##### ➕ Order this New Port")
            st.caption("Request a new physical port from the inventory for this service.")
            
            if st.button("Order Port", use_container_width=True, type="primary", key=f"btn_order_port_{salt}"):
                st.info("🚧 Port ordering workflow is under construction. Please check back later!")

def _render_modify_port_workflow(col):
    """
    Scaffold for Modifying an Existing Port.
    """
    import streamlit as st
    salt = uuid.uuid4().hex[:6]
    
    with col:
            with st.container(border=True,height=CARD_HEIGHT):
                img_port = get_base64_image("templates/png/FabricPort.png")
                if img_port: 
                    st.image(img_port, width=150)
                st.markdown("##### ➕ Modify Existing Port")
                st.caption("Change the physical port configuration.")
                
                if st.button("Modify existing Port", use_container_width=True, type="primary", key=f"btn_order_port_{salt}"):
                    st.info("🚧 Port Modification  workflow is under construction. Please check back later!")
  
def _render_mcgw_integrator_workflow(col, df_services):
    """
    Renders the BGP Policy Builder card in the visual launcher.
    Transitions app state to 'BUILD_BGP_POLICY' mode.
    """
    import streamlit as st

    with col.container(border=True, height=CARD_HEIGHT):
        st.markdown("##### 🤝 MCGW Integrator")
        st.caption("Configure BGP policies and route maps for your Cloud Gateway.")

        if df_services is not None and not df_services.empty:
            # Filter for MCGW services
            mcgw_services = df_services[df_services['service_type'].str.upper() == "MCGW"]
            if not mcgw_services.empty:
                svc_names = mcgw_services['service_name'].tolist()
                target_svc = st.selectbox("Target MCGW Service", options=svc_names, key="sel_mcgw_target")

                if st.button("🛠️ Configure MCGW", use_container_width=True, type="primary"):
                    target_row = mcgw_services[mcgw_services['service_name'] == target_svc].iloc[0]
                    
                    st.session_state.show_launcher = False
                    st.session_state.prov_mode = "CONFIGURE_MCGW"
                    st.session_state.prov_step = 1
                    st.session_state.prov_data = {
                        "mode": "MCGW Integrator",
                        "service_id": target_row['service_id'],
                        "service_name": target_row['service_name'],
                        "service_type": target_row['service_type']
                    }
                    st.rerun()
            else:
                st.info("No active MCGW services available for configuration.")
                st.button("🛠️ Configure MCGW", use_container_width=True, disabled=True)
        else:
            st.info("No active services available.")
            st.button("🛠️ Configure MCGW", use_container_width=True, disabled=True  )

def _render_modify_routing_workflow(col, df_services):
    
    """
    Scaffold for Modifying Routing (Static Routes, VRFs).
    """
    import streamlit as st
    salt = uuid.uuid4().hex[:6]
    
    with col.container(border=True):
        st.markdown("##### 🔀 Modify Routing")
        st.caption("Manage static routes, VRF settings, and logical routing policies.")
        
        # Optional: You can check df_services to disable the button if they have no L3 services
        has_l3_services = not df_services.empty and any(
            t in ["IPVPN", "MCGW", "IOD"] for t in df_services.get("service_type", [])
        )
        
        if st.button("Manage Routing", key=f"btn_modify_routing_{salt}",type="primary", use_container_width=True, disabled=not has_l3_services):
            st.session_state.show_launcher = False
            st.session_state.prov_mode = "MODIFY_ROUTING"
            st.session_state.prov_step = 1
            st.rerun()    