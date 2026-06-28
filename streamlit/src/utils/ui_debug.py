import streamlit as st

def render_debug_inspector(live_manifest: dict = None, staged_payload: dict = None, service_type: str = "N/A"):
    """
    Enhanced Sidebar Debugger (Flight Data Recorder).
    Tracks live manifest tiers and volatile vs persistent stager queues.
    """
    st.sidebar.markdown("### 🛠️ Flight Data Recorder")
    
    # 1. LIVE CONTEXT (Tiers 1 & 2)
    with st.sidebar.expander("🌐 Live Tiers (Database)", expanded=False):
        st.markdown("**Tier 2: Service (Live)**")
        if live_manifest:
            st.json(live_manifest)
        else:
            st.caption("Empty or Undefined")

    # 2. THE VOLATILE QUEUES (Tier 5: Staged Intent)
    with st.sidebar.expander("📝 Tier 5: Form Queues (Volatile)", expanded=True):
        children = st.session_state.get("payload", {}).get("service_context", {}).get("children", {})
        
        st.write(f"**Ports Queued:** `{len(children.get('ports', []))}`")
        st.write(f"**Intfs Queued:** `{len(children.get('interfaces', []))}`")
        
        if st.checkbox("View Form JSON", key="chk_form_json"):
            st.json(children)

    # 3. THE HYDRATED STAGER (The API Results)
    with st.sidebar.expander("💾 Tier 5: Hydrated Stager (Persistent)", expanded=True):
        stager = st.session_state.get("stager_queue", {})
        
        ports_staged = stager.get("ports", [])
        intfs_staged = stager.get("interfaces", [])
        
        st.write(f"**Ports Hydrated:** `{len(ports_staged)}`")
        st.write(f"**Intfs Hydrated:** `{len(intfs_staged)}`")
        
        if ports_staged or intfs_staged:
            st.markdown("**(API Responses)**")
            st.json(stager)
        else:
            st.caption("Waiting for API POST & Hydration...")

def render_system_debugger(tiers_dict: dict, scope: str = "Default"):
    """
    Syntax-highlighted inspector for session state and backend payloads.
    Organizes data into logical tiers for network orchestration debugging.
    """
    if not tiers_dict:
        return

    with st.expander(f"🛠️ System State Inspector — Scope: {scope}", expanded=False):
        # 1. METRICS ROW
        m1, m2, m3 = st.columns(3)
        m1.caption(f"**Tiers Monitored:** {len(tiers_dict)}")
        m2.caption(f"**Scope Context:** {scope}")
        m3.caption(f"**Session:** {st.session_state.get('session_id', 'Local')[:8]}")

        st.divider()

        # 2. DATA TIERS
        num_tiers = len(tiers_dict)
        cols = st.columns(num_tiers)
        
        for i, (label, data) in enumerate(tiers_dict.items()):
            with cols[i]:
                st.markdown(f"**{label}**")
                if data:
                    st.json(data, expanded=False)
                else:
                    st.caption("_Empty or Undefined_")
        
        st.divider()
        
        # 3. CONTROLS
        if st.button("🔄 Force Refresh State", key=f"refresh_{scope}", use_container_width=True):
            st.rerun()

def render_global_system_debugger(manager, scope: str = "DashboardRoot"):
    """
    Top-level dashboard function that orchestrates the FabricStateManager 
    and session state for a complete NDT system audit.
    """
    staged_payload = st.session_state.get("payload", {})
    staged_children = staged_payload.get("service_context", {}).get("children", {})

    with st.expander("🛠️ System Debugger", expanded=True):
        # Calls the rendering engine with the hydrated NDT state map
        render_system_debugger({
            "Tier 1: Customer": {
                "Manager ID": manager.get_active_id("cust"),
                "Raw Session ID": st.session_state.get("active_cust")
            },
            "Tier 2: Service": {
                "Manager ID": manager.get_active_id("fs"),
                "Raw Session ID": st.session_state.get("active_fs")
            },
            "Tier 5: Wizard State": {
                "prov_step": st.session_state.get("prov_step", 1),
                "prov_mode": st.session_state.get("prov_mode"),
                "show_launcher": st.session_state.get("show_launcher", True)
            },
            "Staged Intent": {
                "Ports": len(staged_children.get("ports", [])),
                "VXCs": len(staged_children.get("connections", []))
            }
        }, scope=scope)
        
        # B. Full JSON Manifest Dump (As requested)
        live_manifest = st.session_state.get("active_service_detail")
        if live_manifest:
            st.divider()
            st.markdown("##### 📦 Tier 2: Live Fabric Manifest (`fs_detail`)")
            st.json(live_manifest, expanded=False)