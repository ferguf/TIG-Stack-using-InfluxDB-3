import streamlit as st
import pandas as pd
import plotly.express as px

# --- IMPORT THE HARDENED API CALL ---
from src.utils.api_network import get_devices

def render_device_dashboard():
    """Renders the main layout and visualizations for the device inventory."""
    st.set_page_config(page_title="Network Device Inventory", layout="wide")
    
    st.title("📡 Network Device Inventory")
    
    # --- UTILITY ROW ---
    col_refresh, _ = st.columns([1, 6])
    with col_refresh:
        if st.button("🔄 Refresh Data", use_container_width=True):
            # Clear the cache from the imported function
            get_devices.clear()
            st.rerun()
            
    st.divider()

    # --- FETCH DATA ---
    raw_data = get_devices()
    
    if not raw_data:
        st.warning("No device data returned from the API. Please ensure the backend is running.")
        return

    df = pd.DataFrame(raw_data)

    # --- TOP METRICS ---
    st.subheader("Global Hardware Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Devices", len(df))
    m2.metric("Unique Locations", df['location'].nunique() if 'location' in df.columns else 0)
    m3.metric("Hardware Roles", df['device_role'].nunique() if 'device_role' in df.columns else 0)
    m4.metric("Hardware Models", df['device_model'].nunique() if 'device_model' in df.columns else 0)
    
    st.write("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📑 TAB NAVIGATION
    # ==========================================
    tab_overview, tab_inventory = st.tabs(["📊 Overview & Analytics", "🗄️ Full Inventory"])

    # --- TAB 1: OVERVIEW & ANALYTICS ---
    with tab_overview:
        # ROW 1: ROLE COUNTS & LOCATION SPLIT
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**1. Device Count by Role**")
            with st.container(border=True):
                if 'device_role' in df.columns:
                    role_counts = df['device_role'].value_counts().reset_index()
                    role_counts.columns = ['Role', 'Count']
                    fig1 = px.pie(
                        role_counts, names='Role', values='Count', hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig1.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("Missing 'device_role' key in data.")

        with c2:
            st.markdown("**2. Distribution by Location & Role**")
            with st.container(border=True):
                if 'location' in df.columns and 'device_role' in df.columns:
                    loc_role = df.groupby(['location', 'device_role']).size().reset_index(name='Count')
                    fig2 = px.bar(
                        loc_role, x='location', y='Count', color='device_role',
                        barmode='group', text_auto=True,
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig2.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350, xaxis_title="Location")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Missing 'location' or 'device_role' key in data.")

        # ROW 2: MODEL SPLIT & PLANNING STATUS
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("**3. Hardware Models by Role**")
            with st.container(border=True):
                if 'device_role' in df.columns and 'device_model' in df.columns:
                    role_model = df.groupby(['device_role', 'device_model']).size().reset_index(name='Count')
                    fig3 = px.bar(
                        role_model, x='device_role', y='Count', color='device_model',
                        barmode='stack', text_auto=True,
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    fig3.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350, xaxis_title="Device Role")
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("Missing 'device_model' key in data.")

        with c4:
            st.markdown("**4. Planning Status by Role**")
            with st.container(border=True):
                if 'device_role' in df.columns and 'planning_status' in df.columns:
                    role_plan = df.groupby(['device_role', 'planning_status']).size().reset_index(name='Count')
                    fig4 = px.bar(
                        role_plan, x='device_role', y='Count', color='planning_status',
                        barmode='group', text_auto=True,
                        color_discrete_sequence=px.colors.qualitative.Vivid
                    )
                    fig4.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350, xaxis_title="Device Role")
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Missing 'planning_status' key in data.")

    # --- TAB 2: FULL INVENTORY TABLE ---
    with tab_inventory:
        st.markdown("### 🗄️ Searchable Device Directory")
        
        # Real-time search bar
        search_query = st.text_input(
            "🔍 Search devices...", 
            placeholder="Type a location (e.g., DEN1), vendor (e.g., Juniper), or floor...",
            key="device_search_bar"
        )
        
        # Filtering Logic
        if search_query:
            # Cast all to string safely, then check if query is in any column
            mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            filtered_df = df[mask]
        else:
            filtered_df = df
            
        st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** total devices.")
        
        # Reorder columns for readability (operational data first, system metadata last)
        display_order = [
            "device_name", "location", "device_role", "device_model", "device_vendor", 
            "planning_status", "lifecycle_status", "health_status", "floor", "aisle", "rack", 
            "network", "device_description", "created_at", "updated_at", "device_id"
        ]
        
        # Ensure we only display columns that actually exist in the payload
        available_cols = [col for col in display_order if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[available_cols], 
            use_container_width=True, 
            hide_index=True,
            height=600 
        )

if __name__ == "__main__":
    render_device_dashboard()