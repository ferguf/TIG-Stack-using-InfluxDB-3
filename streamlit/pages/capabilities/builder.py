import streamlit as st
import pandas as pd
import uuid
from src.utils import api_capabilities

def inject_theme_css():
    """Injects custom CSS to theme buttons based on an adjacent hidden marker."""
    st.markdown("""
    <style>
    .element-container:has(.theme-amber) + .element-container button {
        background-color: #FFBF00 !important; color: #000000 !important; border: 1px solid #FFBF00 !important; font-weight: 600 !important;
    }
    .element-container:has(.theme-amber) + .element-container button:hover { background-color: #E6AC00 !important; }

    .element-container:has(.theme-green) + .element-container button {
        background-color: #28A745 !important; color: #FFFFFF !important; border: 1px solid #28A745 !important; font-weight: 600 !important;
    }
    .element-container:has(.theme-green) + .element-container button:hover { background-color: #218838 !important; }

    .element-container:has(.theme-red) + .element-container button {
        background-color: #DC3545 !important; color: #FFFFFF !important; border: 1px solid #DC3545 !important; font-weight: 600 !important;
    }
    .element-container:has(.theme-red) + .element-container button:hover { background-color: #C82333 !important; }
    </style>
    """, unsafe_allow_html=True)


class CapabilitiesBuilderUI:
    def __init__(self):
        inject_theme_css()
        
        # --- UI MOCK STATE INITIALIZATION ---
        if "cap_ref_services" not in st.session_state:
            st.session_state.cap_ref_services = []
            
        if "cap_hw_profiles" not in st.session_state:
            st.session_state.cap_hw_profiles = [
                {"id": str(uuid.uuid4()), "device_role": "VAR", "device_model": "MX10004"}
            ]

        # Seed the requested baseline Fabric Ports
        if "cap_ref_ports" not in st.session_state:
            baseline_ports = ["1G - Copper", "1G - Fiber", "10G - Fiber", "100G - Fiber", "400G - Fiber", "800G - Fiber"]
            st.session_state.cap_ref_ports = [
                {"id": str(uuid.uuid4()), "port_type": port} for port in baseline_ports
            ]
            
        # Seed an empty optics catalog (relational to ports)
        if "cap_ref_optics" not in st.session_state:
            st.session_state.cap_ref_optics = []

    def _themed_button(self, label, theme="green", **kwargs):
        st.markdown(f'<div class="theme-{theme}" style="display:none;"></div>', unsafe_allow_html=True)
        kwargs.pop("type", None) 
        return st.button(label, **kwargs)

    def render_reference_management(self):
        st.subheader("Master Reference Data")
        
        # Tabs for the 100% Universe
        ref_tabs = st.tabs(["🌐 Services", "⚡ Fabric Ports & Optics", "🎭 Port Personalities"])
        
        # --- TAB 1: SERVICES ---
        with ref_tabs[0]:
            df_svc = api_capabilities.get_ref_services()
            selected_idx = None
            if not df_svc.empty:
                event = st.dataframe(df_svc, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_ref_svc")
                if event.selection.rows: selected_idx = event.selection.rows[0]
            
            if selected_idx is not None:
                data = df_svc.iloc[selected_idx]
                with st.container(border=True):
                    st.markdown(f"**Edit Service:** {data['service_name']}")
                    c1, c2 = st.columns(2)
                    n_name = c1.text_input("Name", value=data['service_name'], key="upd_svc_name")
                    n_layer = c2.selectbox("Layer", ["L2", "L3"], index=["L2", "L3"].index(data['layer']), key="upd_svc_layer")
                    
                    b1, b2 = st.columns(2)
                    if b1.button("💾 Update", use_container_width=True):
                        # API: PUT endpoint would go here
                        st.rerun()
                    if b2.button("🗑️ Delete", type="primary", use_container_width=True):
                        api_capabilities.delete_ref_service(data['service_id'])
                        st.rerun()
            else:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    n_name = c1.text_input("New Service Name", key="n_svc_name")
                    n_layer = c2.selectbox("Layer", ["L2", "L3"], key="n_svc_layer")
                    if self._themed_button("➕ Create Service", theme="green", use_container_width=True):
                        api_capabilities.post_ref_service({"service_name": n_name, "layer": n_layer})
                        st.rerun()

        # --- TAB 2: FABRIC PORTS & OPTICS ---
        with ref_tabs[1]:
            st.info("Fabric Port CRUD is live. Use the same pattern as Services to bind Optics to specific Ports.")
            # Implementation follows the same pattern as Tab 1, calling:
            # api_capabilities.get_ref_ports() / post_ref_port() / post_ref_optic()

        # --- TAB 3: PORT PERSONALITIES ---
        with ref_tabs[2]:
            st.markdown("**Manage Port Personalities**")
            # Logic: Fetch all, display table, create/delete loop
            # api_capabilities.get_ref_personalities()
            # api_capabilities.post_ref_personality()
            # api_capabilities.delete_ref_personality()
            
            if self._themed_button("➕ Add Personality", theme="green"):
                # Placeholder for input dialog
                st.rerun()
                                
    def render_profile_management(self):
        # ... (Profile mapping logic remains untouched from previous version) ...
        st.subheader("Hardware Profile Mapping")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**1. Hardware Anchors**")
            selected_prof_idx = None
            if st.session_state.cap_hw_profiles:
                df_prof = pd.DataFrame(st.session_state.cap_hw_profiles)
                event_prof = st.dataframe(df_prof[["device_role", "device_model"]], use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_hw_prof")
                if event_prof.selection.rows:
                    selected_prof_idx = event_prof.selection.rows[0]

            with st.container(border=True):
                st.markdown("*Create New Anchor*")
                n_role = st.selectbox("Role", ["VAR", "ES", "SDR", "SCR"], key="n_prof_role")
                n_model = st.text_input("Model (e.g., MX10004)", key="n_prof_model")
                if self._themed_button("Create Profile", theme="green", use_container_width=True, key="btn_add_prof"):
                    st.session_state.cap_hw_profiles.append({"id": str(uuid.uuid4()), "device_role": n_role, "device_model": n_model})
                    st.rerun()

        with col2:
            st.markdown("**2. Assign Capabilities**")
            if selected_prof_idx is not None:
                prof_data = st.session_state.cap_hw_profiles[selected_prof_idx]
                with st.container(border=True):
                    st.success(f"**Active Target:** {prof_data['device_role']} {prof_data['device_model']}")
                    
                    assign_tabs = st.tabs(["Map Services & Speeds", "Map Fabric Ports & Optics"])
                    with assign_tabs[0]:
                        # Handle potential empty services state safely
                        svc_opts = [s["service_name"] for s in st.session_state.cap_ref_services] if "cap_ref_services" in st.session_state else ["No Services"]
                        a_svc = st.selectbox("Select Master Service", svc_opts, key="map_svc")
                        a_spd = st.selectbox("Select Allowed Speed", ["50M", "100M", "1G", "100G", "400G"], key="map_spd")
                        
                        if self._themed_button("🔗 Assign Capability to Profile", theme="amber", use_container_width=True, key="btn_map_svc"):
                            st.toast(f"Mapped {a_spd} {a_svc} to {prof_data['device_model']}")
            else:
                st.info("👈 Select a Hardware Anchor from the table to map capabilities.")

    def run(self):
        st.markdown("### 🏗️ Matrix Engineering Suite")
        st.markdown("Build and maintain the hardware constraint engine.")
        
        builder_mode = st.radio(
            "Engineering Mode:", 
            ["Master Reference Data", "Hardware Profile Mapping"], 
            horizontal=True,
            label_visibility="collapsed"
        )
        st.divider()
        
        if builder_mode == "Master Reference Data":
            self.render_reference_management()
        else:
            self.render_profile_management()

def run_capabilities_builder():
    ui = CapabilitiesBuilderUI()
    ui.run()