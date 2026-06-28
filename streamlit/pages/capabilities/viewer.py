import streamlit as st
import pandas as pd

class CapabilitiesViewerUI:
    
    def render_location_viewer(self):
        st.subheader("📍 Site Capability Aggregation")
        st.markdown("Simulate what the NDT Provisioning Wizard sees when a user selects a PoP. Driven by `vw_capabilities_location`.")
        
        mock_locations = {
            "Denver, CO (DEN-01)": "123e4567-e89b-12d3-a456-426614174000",
            "Ashburn, VA (IAD-03)": "987f6543-a21b-34c5-d678-987654321000"
        }
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_site = st.selectbox("Select Network Location", list(mock_locations.keys()), label_visibility="collapsed")
        with col2:
            trigger = st.button("🔍 Query API", type="primary", use_container_width=True)
            
        if trigger:
            # Mocking the JSON response from FastAPI
            mock_response = {
                "location_id": mock_locations[selected_site],
                "deployed_hardware": ["VAR MX10004", "ES ACX7100", "ES ACX5448"],
                "location_supported_ports": ["1G", "10G", "100G", "400G"],
                "location_supported_services": ["E-Line EVPL", "E-LAN", "IOD", "IPVPN", "MCGW"]
            }
            
            st.divider()
            
            # --- Visualizations & Metrics ---
            m1, m2, m3 = st.columns(3)
            m1.metric("Hardware Profiles Deployed", len(mock_response["deployed_hardware"]))
            m2.metric("Total Port Speeds Supported", len(mock_response["location_supported_ports"]))
            m3.metric("Total Service Types Supported", len(mock_response["location_supported_services"]))
            
            st.write("") # Spacer
            
            # --- Data Tables ---
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("**Available Services at Location**")
                    df_svc = pd.DataFrame({"Service Type": mock_response["location_supported_services"]})
                    st.dataframe(df_svc, hide_index=True, use_container_width=True)
            
            with c2:
                with st.container(border=True):
                    st.markdown("**Available Fabric Ports**")
                    # Visual trick: present arrays as tags in a table
                    df_ports = pd.DataFrame({"Port Speed": mock_response["location_supported_ports"]})
                    st.dataframe(df_ports, hide_index=True, use_container_width=True)
                    
            with st.expander("JSON Payload Inspection"):
                st.json(mock_response)

    def render_profile_viewer(self):
        st.subheader("🗄️ Hardware Profile Inspector")
        st.markdown("View the definitive capability constraints for a specific equipment role/model.")
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                test_role = st.selectbox("Role", ["VAR", "ES", "SDR", "SCR"], key="view_role")
            with col2:
                test_model = st.selectbox("Model", ["MX10004", "MX10003", "ACX7100"], key="view_model")
            with col3:
                st.write("") # Alignment spacing
                st.write("")
                trigger = st.button("Inspect Constraints", type="primary", use_container_width=True)
            
        if trigger:
            st.divider()
            
            # Mock Data Representation
            mock_services = [
                {"Service": "E-Line EVPL", "Supported Access Speeds": "50M, 100M, 1G, 10G, 100G"},
                {"Service": "IPVPN", "Supported Access Speeds": "1G, 10G"}
            ]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"#### {test_role} {test_model}")
                st.caption("Fabric Ports")
                st.dataframe(pd.DataFrame({"Speeds": ["100G", "400G"]}), hide_index=True, use_container_width=True)
                st.caption("Port Personalities")
                st.dataframe(pd.DataFrame({"Mode": ["UNI", "ENNI", "ILM"]}), hide_index=True, use_container_width=True)
                
            with c2:
                st.markdown("#### Service Matrix")
                st.dataframe(pd.DataFrame(mock_services), hide_index=True, use_container_width=True)

    def run(self):
        st.markdown("### 👁️ Matrix Explorer")
        st.markdown("Query the active database state via the FastAPI routing layer.")
        
        viewer_tabs = st.tabs(["📍 Location Aggregation", "🗄️ Hardware Profile Lookup"])
        
        with viewer_tabs[0]:
            self.render_location_viewer()
            
        with viewer_tabs[1]:
            self.render_profile_viewer()

def run_capabilities_viewer():
    ui = CapabilitiesViewerUI()
    ui.run()