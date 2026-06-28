import streamlit as st
import pandas as pd

# ==========================================
# 1. NDT HELPERS
# ==========================================

def parse_speed_to_gbps(raw_speed) -> float:
    """
    Safely parses assorted speed strings ('400G', '10Gbps', '200000000.0') 
    into a standardized Gbps float for sorting and display.
    """
    if pd.isna(raw_speed) or str(raw_speed).strip() == "":
        return 0.0
        
    speed_str = str(raw_speed).strip().upper()
    
    try:
        numeric_part = ''.join(c for c in speed_str if c.isdigit() or c == '.')
        if not numeric_part:
            return 0.0
            
        val = float(numeric_part)
        
        if 'T' in speed_str:
            return val * 1000.0
        elif 'G' in speed_str:
            return val
        elif 'M' in speed_str:
            return val / 1000.0
        else:
            return val / 1_000_000.0
    except Exception:
        return 0.0

# ==========================================
# 2. STATE LAYER
# ==========================================

def init_link_session_state():
    """Initializes global session state variables for link filters."""
    if "link_f_type" not in st.session_state: st.session_state["link_f_type"] = "All"
    if "link_f_loc" not in st.session_state: st.session_state["link_f_loc"] = "All"
    if "link_f_search" not in st.session_state: st.session_state["link_f_search"] = ""

# ==========================================
# 3. MAIN TABLE COMPONENT
# ==========================================

def render_link_table_view(asn: str, raw_df: pd.DataFrame):
    """
    Renders the interactive Link Data table and filter controls.
    Accepts pre-fetched API data (raw_df) to prevent redundant network calls.
    """
    init_link_session_state()
    
    if raw_df is None or raw_df.empty:
        st.info("📂 No link data currently available.")
        return

    # Prepare DataFrame specifically for the table view
    df = raw_df.copy()
    
    # Utilize the string parser for the speed column
    if 'a_port_speed' in df.columns:
        df['capacity_gbps'] = df['a_port_speed'].apply(parse_speed_to_gbps)
    else:
        df['capacity_gbps'] = 0.0
        
    # --- FILTERS ---
    c_title, c_clear = st.columns([5, 1])
    if c_clear.button("🔄 Reset Filters", use_container_width=True, key="reset_link_filters"):
        st.session_state["link_f_type"] = "All"
        st.session_state["link_f_loc"] = "All"
        st.session_state["link_f_search"] = ""
        st.rerun()

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        types = ["All"] + sorted(df['link_type'].dropna().astype(str).unique().tolist())
        st.selectbox("Filter by Link Type", options=types, key="link_f_type")
    with f_col2:
        # Cast to string before upper() to prevent NaN attribute errors
        locs = set(df['a_device_location'].dropna().astype(str).str.upper().unique()) | \
               set(df['b_device_location'].dropna().astype(str).str.upper().unique())
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
        filtered_df = filtered_df[
            (filtered_df['a_device_location'].astype(str).str.upper() == f_loc) | 
            (filtered_df['b_device_location'].astype(str).str.upper() == f_loc)
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