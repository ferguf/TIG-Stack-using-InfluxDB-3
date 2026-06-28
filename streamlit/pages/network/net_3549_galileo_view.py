import streamlit as st
import pandas as pd

# Adjust import path to your API utilities as needed
from src.utils.api_network import get_network_links_detail

# ==========================================
# 1. STATE & DATA LAYER
# ==========================================

def init_link_session_state():
    """Initializes global session state variables for link filters."""
    if "link_f_type" not in st.session_state: st.session_state["link_f_type"] = "All"
    if "link_f_loc" not in st.session_state: st.session_state["link_f_loc"] = "All"
    if "link_f_search" not in st.session_state: st.session_state["link_f_search"] = ""

@st.cache_data(ttl=300)
def fetch_link_data(asn: str) -> pd.DataFrame:
    """Fetches and normalizes raw network link data."""
    raw_data = get_network_links_detail()
    if not raw_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    
    # Filter for the target network if the payload contains multiple
    if 'a_network' in df.columns:
        df = df[df['a_network'] == asn]
        
    if not df.empty:
        # Convert raw speeds (assumed Kbps in API payload) to Gbps for readability
        if 'a_port_speed' in df.columns:
            df['capacity_gbps'] = pd.to_numeric(df['a_port_speed'], errors='coerce') / 1_000_000
        else:
            df['capacity_gbps'] = 0.0
            
    return df

# ==========================================
# 2. MAIN ORCHESTRATOR
# ==========================================

def render_link_table_view(asn: str):
    """Renders the interactive Link Data table and filter controls."""
    init_link_session_state()
    
    st.markdown(f"#### 🔗 {asn} Link Inventory")
    
    with st.spinner("Fetching link telemetry..."):
        df = fetch_link_data(asn)
        
    if df.empty:
        st.info("📂 No link data currently available from the API.")
        return
        
    # --- FILTERS ---
    c_title, c_clear = st.columns([5, 1])
    if c_clear.button("🔄 Reset Filters", use_container_width=True, key="reset_link_filters"):
        st.session_state["link_f_type"] = "All"
        st.session_state["link_f_loc"] = "All"
        st.session_state["link_f_search"] = ""
        st.rerun()

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        types = ["All"] + sorted(df['link_type'].dropna().unique().tolist())
        st.selectbox("Filter by Link Type", options=types, key="link_f_type")
    with f_col2:
        locs = set(df['a_device_location'].dropna().str.upper().unique()) | set(df['b_device_location'].dropna().str.upper().unique())
        locs_list = ["All"] + sorted(list(locs))
        st.selectbox("Filter by Location", options=locs_list, key="link_f_loc")
    with f_col3:
        st.text_input("Search (Description / Device)", placeholder="e.g., ae6.0...", key="link_f_search")

    # --- APPLY FILTERS ---
    filtered_df = df.copy()
    
    f_type = st.session_state["link_f_type"]
    f_loc = st.session_state["link_f_loc"]
    f_search = st.session_state["link_f_search"]
    
    if f_type != "All":
        filtered_df = filtered_df[filtered_df['link_type'] == f_type]
        
    if f_loc != "All":
        # Normalize to uppercase for safety against messy data
        filtered_df = filtered_df[
            (filtered_df['a_device_location'].str.upper() == f_loc) | 
            (filtered_df['b_device_location'].str.upper() == f_loc)
        ]
        
    if f_search:
        search_mask = (
            filtered_df['description'].str.contains(f_search, case=False, na=False) |
            filtered_df['a_device_name'].str.contains(f_search, case=False, na=False) |
            filtered_df['b_device_name'].str.contains(f_search, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]

    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} matching links**")

    # --- TABLE RENDER ---
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_order=[
            "link_type", "description", "capacity_gbps", 
            "a_device_name", "a_port_name", "a_port_service_status",
            "b_device_name", "b_port_name", "b_port_service_status"
        ],
        column_config={
            "link_type": st.column_config.TextColumn("Type", width="small"),
            "description": st.column_config.TextColumn("Description", width="medium"),
            "capacity_gbps": st.column_config.NumberColumn("Capacity (Gbps)", format="%.1f", width="small"),
            "a_device_name": st.column_config.TextColumn("A-Device", width="medium"),
            "a_port_name": st.column_config.TextColumn("A-Port", width="small"),
            "a_port_service_status": st.column_config.TextColumn("A-Status", width="small"),
            "b_device_name": st.column_config.TextColumn("Z-Device", width="medium"),
            "b_port_name": st.column_config.TextColumn("Z-Port", width="small"),
            "b_port_service_status": st.column_config.TextColumn("Z-Status", width="small"),
        }
    )