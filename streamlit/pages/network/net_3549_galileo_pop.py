import streamlit as st
import pandas as pd
import logging

# --- IMPORT DATA CONTROLLER ---
from pages.network import net_3356_data as data_ctrl

logger = logging.getLogger(__name__)

def render_pop_view():
    """Renders the Point of Presence (PoP) specific drill-down view."""
    st.title("📍 PoP Inspection & Inventory")
    st.markdown("Select a geographical region and a specific Point of Presence to view site-level hardware and telemetry.")

    # --- 1. DATA ACQUISITION ---
    with st.spinner("Synchronizing Global PoP Database..."):
        # Fetch the flattened PoP data from the controller
        state = data_ctrl.regional_detail_summary()

    if "error" in state:
        st.error(f"⚠️ {state['error']}")
        return

    df_pops = state["df_pops"]

    if df_pops.empty:
        st.warning("No PoP data found in the API payload.")
        return

    st.divider()

    # --- 2. CASCADING UI CONTROLS ---
    st.markdown("### 🎛️ Site Selector")
    
    with st.container(border=True):
        # Dynamically extract available regions
        available_regions = sorted(df_pops['region'].unique())
        
        # Row 1: Region Radio
        selected_region = st.radio(
            "🌍 **1. Select Operating Region**", 
            options=available_regions, 
            horizontal=True
        )
        
        # Filter the dataframe down to just the selected region
        df_filtered_region = df_pops[df_pops['region'] == selected_region]
        
        # Dynamically extract available PoPs for the dropdown
        available_pops = sorted(df_filtered_region['pop_id'].unique())
        
        # Row 2: PoP Dropdown (Searchable by default in Streamlit)
        selected_pop_id = st.selectbox(
            "🏢 **2. Select or Search PoP Site**", 
            options=available_pops,
            help="Type to search for a specific PoP identifier (e.g., 'ams1')"
        )

    # --- 3. SITE INSPECTION CARD ---
    if selected_pop_id:
        st.divider()
        
        # Extract the specific row for the selected PoP
        pop_data = df_filtered_region[df_filtered_region['pop_id'] == selected_pop_id].iloc[0]
        
        st.markdown(f"### 📊 Site Overview: `{pop_data['pop_id'].upper()}`")
        
        # Site KPIs
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Location", f"{pop_data.get('city', 'Unknown')}, {pop_data.get('country', '')}")
        m2.metric("Primary Provider", pop_data.get('provider', 'Unknown'))
        m3.metric("Hardware Nodes", pop_data.get('router_count', 0))
        m4.metric("Status", "🟢 Active")
        
        st.write("") # Spacer
        
        # --- 4. HARDWARE INVENTORY TABLE ---
        st.markdown("#### 🖥️ Routing Hardware Inventory")
        
        routers = pop_data.get('routers', [])
        
        if routers:
            df_routers = pd.DataFrame(routers)
            
            # Format table for clean UI presentation
            st.dataframe(
                df_routers,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "router": st.column_config.TextColumn("Hostname (FQDN)", width="large"),
                    "router_type": st.column_config.TextColumn("Hardware Role", width="medium")
                }
            )
        else:
            st.info(f"No specific hardware nodes reported for {selected_pop_id.upper()} in the current telemetry batch.")

if __name__ == "__main__":
    render_pop_view()