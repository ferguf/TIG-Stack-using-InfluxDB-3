import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
from src.utils.api_network import get_network_devices # Adjust import path as needed

# ==========================================
# 1. STATE & STYLING
# ==========================================

def init_session_state():
    """Initializes global session state variables for dashboard filters and network targeting."""
    if "target_asn" not in st.session_state: st.session_state["target_asn"] = "AS209" # Dynamic Network Target
    if "inv_f_role" not in st.session_state: st.session_state["inv_f_role"] = "PCOR"
    if "inv_f_vendor" not in st.session_state: st.session_state["inv_f_vendor"] = "All"
    if "inv_f_model" not in st.session_state: st.session_state["inv_f_model"] = "All"
    if "inv_f_search" not in st.session_state: st.session_state["inv_f_search"] = ""
    # Used for true lazy-loading view toggles
    if "inv_view_mode" not in st.session_state: st.session_state["inv_view_mode"] = "📋 Filtered Inventory"
    
def inject_custom_css():
    """Injects custom CSS for metric cards."""
    st.markdown("""
    <style>
    .metric-card {
        background-color: rgba(25, 28, 36, 0.7); 
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 5px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .metric-title {
        font-size: 0.95rem;
        color: #A0A0A0;
        font-weight: 500;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #B0B0B0;
        margin-top: 8px;
    }
    .border-blue { border-top: 4px solid #0078D7; }
    .border-purple { border-top: 4px solid #8E44AD; }
    .border-teal { border-top: 4px solid #1ABC9C; }
    .border-orange { border-top: 4px solid #F39C12; }
    .border-green { border-top: 4px solid #2ECC71; }
    .border-pink { border-top: 4px solid #E84393; }
    .border-cyan { border-top: 4px solid #00CECB; }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# 2. DATA LAYER
# ==========================================

@st.cache_data(ttl=300)
def fetch_inventory_data(asn: str) -> pd.DataFrame:
    """Fetches and normalizes raw network device data for the specified ASN."""
    raw_data = get_network_devices(asn)
    if not raw_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    return df


# ==========================================
# 3. METRICS & OVERVIEW COMPONENTS
# ==========================================

def render_network_summary(df: pd.DataFrame):
    """Renders the top-level aggregate network metrics."""
    st.markdown("##### 📊 Network Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card border-blue"><div class="metric-title">Total Devices</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card border-purple"><div class="metric-title">Unique Locations</div><div class="metric-value">{df["location_id"].nunique()}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card border-teal"><div class="metric-title">Hardware Models</div><div class="metric-value">{df["device_model"].nunique()}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card border-orange"><div class="metric-title">NOS Versions</div><div class="metric-value">{df["nos_version"].nunique()}</div></div>', unsafe_allow_html=True)

def render_role_breakdown(df: pd.DataFrame):
    """Renders the role-based breakdown and drill-down buttons in a strict 4-column grid."""
    with st.expander("📡 Role Breakdown", expanded=True):
        role_stats = df.groupby('device_role', dropna=False).agg(
            total_count=('device_id', 'count'),
            unique_models=('device_model', 'nunique'),
            unique_nos=('nos_version', 'nunique')
        ).reset_index().sort_values('total_count', ascending=False)

        if not role_stats.empty:
            palette = ["border-green", "border-cyan", "border-pink", "border-blue", "border-purple"]
            chunk_size = 4
            role_chunks = [role_stats.iloc[i:i + chunk_size] for i in range(0, len(role_stats), chunk_size)]
            
            for chunk in role_chunks:
                role_cols = st.columns(chunk_size)
                
                for j, (idx, row) in enumerate(chunk.iterrows()):
                    role_name = row['device_role'] if pd.notna(row['device_role']) else "Unknown"
                    color_class = palette[idx % len(palette)] 
                    
                    with role_cols[j]:
                        st.markdown(f"""
                            <div class="metric-card {color_class}">
                                <div class="metric-title">{role_name}</div>
                                <div class="metric-value">{row['total_count']}</div>
                                <div class="metric-sub" style="font-size: 0.8rem;">HW Models: <b>{row['unique_models']}</b> | NOS: <b>{row['unique_nos']}</b></div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"🎯 Filter: {role_name}", key=f"drill_role_{role_name}_{idx}", use_container_width=True):
                            st.session_state["inv_f_role"] = role_name
                            st.session_state["inv_f_vendor"] = "All" 
                            st.session_state["inv_f_model"] = "All"
                            st.session_state["inv_f_search"] = ""    
                            st.rerun()

def render_hardware_breakdown(df: pd.DataFrame):
    """Renders the hardware model breakdown and drill-down buttons."""
    with st.expander("🖥️ Hardware Model Breakdown", expanded=False):
        model_stats = df.groupby('device_model', dropna=False).agg(
            total_count=('device_id', 'count')
        ).reset_index().sort_values('total_count', ascending=False)

        if not model_stats.empty:
            chunk_size = 4
            model_chunks = [model_stats.iloc[i:i + chunk_size] for i in range(0, len(model_stats), chunk_size)]
            for chunk in model_chunks:
                mod_cols = st.columns(chunk_size)
                for j, (idx, row) in enumerate(chunk.iterrows()):
                    model_name = row['device_model'] if pd.notna(row['device_model']) else "Unknown"
                    with mod_cols[j]:
                        st.markdown(f"""
                            <div class="metric-card border-teal">
                                <div class="metric-title" title="{model_name}">{model_name}</div>
                                <div class="metric-value">{row['total_count']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"🎯 Filter: {model_name}", key=f"drill_mod_{model_name}_{idx}", use_container_width=True):
                            st.session_state["inv_f_model"] = model_name
                            st.session_state["inv_f_role"] = "All" 
                            st.session_state["inv_f_vendor"] = "All" 
                            st.session_state["inv_f_search"] = ""    
                            st.rerun()


# ==========================================
# 4. FILTERS & SEARCH
# ==========================================

def render_global_filters(df: pd.DataFrame):
    """Renders the global search and dropdown filter inputs."""
    c_title, c_clear = st.columns([5, 1])
    c_title.markdown("##### 🔍 Global Filters")
    
    if c_clear.button("🔄 Reset Filters", use_container_width=True):
        st.session_state["inv_f_role"] = "All"
        st.session_state["inv_f_vendor"] = "All"
        st.session_state["inv_f_model"] = "All"
        st.session_state["inv_f_search"] = ""
        st.rerun()

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        roles = ["All"] + sorted(df['device_role'].dropna().unique().tolist())
        st.selectbox("Filter by Role", options=roles, key="inv_f_role")
    with f_col2:
        vendors = ["All"] + sorted(df['device_vendor'].dropna().unique().tolist())
        st.selectbox("Filter by Vendor", options=vendors, key="inv_f_vendor")
    with f_col3:
        models = ["All"] + sorted(df['device_model'].dropna().unique().tolist())
        st.selectbox("Filter by Model", options=models, key="inv_f_model")
    with f_col4:
        st.text_input("Search (City/Name)", placeholder="e.g., Dallas...", key="inv_f_search")

def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Applies the current session state filters to the dataframe."""
    filtered_df = df.copy()
    f_role = st.session_state["inv_f_role"]
    f_vendor = st.session_state["inv_f_vendor"]
    f_model = st.session_state["inv_f_model"]
    search_term = st.session_state["inv_f_search"]

    if f_role != "All": filtered_df = filtered_df[filtered_df['device_role'] == f_role]
    if f_vendor != "All": filtered_df = filtered_df[filtered_df['device_vendor'] == f_vendor]
    if f_model != "All": filtered_df = filtered_df[filtered_df['device_model'] == f_model]
    
    if search_term:
        search_mask = (
            filtered_df['device_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['city'].str.contains(search_term, case=False, na=False) |
            filtered_df['location_code'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
        
    return filtered_df


# ==========================================
# 5. DATA VIEWS (TABLE & MAP)
# ==========================================

def render_inventory_table(filtered_df: pd.DataFrame):
    """Renders the data table. Selections persist via the session_state key."""
    st.caption("💡 *Tip: Click the checkboxes on the left side of the table to isolate specific devices on the map.*")
    
    # We assign a key here so Streamlit tracks the row selection in st.session_state globally.
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="multi-row",
        on_select="rerun", 
        key="inventory_table_widget", # KEY ADDED FOR STATE PERSISTENCE
        column_order=[
            "device_name", "device_role", "device_vendor", "device_model", 
            "nos_version", "location_code", "city", "state"
        ],
        column_config={
            "device_name": st.column_config.TextColumn("Device Name", width="medium"),
            "device_role": st.column_config.TextColumn("Role", width="small"),
            "device_vendor": st.column_config.TextColumn("Vendor", width="small"),
            "device_model": st.column_config.TextColumn("Model", width="medium"),
            "nos_version": st.column_config.TextColumn("NOS Version", width="medium"),
            "location_code": st.column_config.TextColumn("Site Code", width="small"),
            "city": st.column_config.TextColumn("City", width="small"),
            "state": st.column_config.TextColumn("State", width="small")
        }
    )

def get_smart_map_bounds(map_data: pd.DataFrame):
    """Calculates optimal dynamic center and zoom level for Plotly map."""
    lat_spread = map_data['latitude'].max() - map_data['latitude'].min()
    lon_spread = map_data['longitude'].max() - map_data['longitude'].min()
    max_spread = max(lat_spread, lon_spread)
    
    if max_spread > 20:   return {"lat": 39.8283, "lon": -98.5795}, 3.5 
    elif max_spread > 5:  return {"lat": map_data['latitude'].mean(), "lon": map_data['longitude'].mean()}, 5.5
    elif max_spread > 0.5: return {"lat": map_data['latitude'].mean(), "lon": map_data['longitude'].mean()}, 8.0
    else:                return {"lat": map_data['latitude'].mean(), "lon": map_data['longitude'].mean()}, 11.0

def classify_site_tier(roles_series: pd.Series) -> str:
    """Classifies network sites hierarchically based on deployed equipment roles."""
    roles = set(str(r).upper().strip() for r in roles_series.dropna())
    
    if not roles: 
        return "Unknown"

    # --- Tier 1 Checks ---
    if 'SDR' in roles or 'PCOR' in roles: 
        return "Tier 1"
    if 'EBR' in roles: 
        return "Tier 1 / Tier 2"
        
    # --- Tier 2 Checks ---
    if 'SCR' in roles: 
        return "Tier 2"
        
    # --- Tier 3 Checks ---
    if 'CR' in roles: 
        return "Tier 3 /TWTC"
    if roles and roles.issubset({'BAR', 'BEAR'}): 
        return "Tier 3 Z"
        
    # --- Edge Cases & Warnings ---
    if roles == {'EAR'}: 
        return "⚠️ Problem!! (EAR Only)"
        
    # --- Catch-All Logic ---
    if 'PCOR' not in roles: 
        return "Tier 3"
        
    return ' + '.join(sorted(set(str(r).title().strip() for r in roles_series.dropna())))

def render_interactive_map(filtered_df: pd.DataFrame, selected_indices: list):
    """Renders the interactive geospatial map."""
    if selected_indices:
        active_map_df = filtered_df.iloc[selected_indices].copy()
        st.info(f"🎯 Map is synced to your {len(selected_indices)} selected row(s) from the Data Table.")
    else:
        active_map_df = filtered_df.copy()

    map_mode = st.radio(
        "📍 Select Map View Mode", 
        options=["🌍 Aggregated Location View (Site Tier)", "🎯 Filtered Device-Level View"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.divider()

    m1, m2 = st.columns([3, 1])
    with m1:
        map_bg = st.selectbox(
            "Map Style", 
            options=["carto-darkmatter", "carto-positron", "open-street-map"],
            format_func=lambda x: "Dark Mode" if x == "carto-darkmatter" else "Light Mode" if x == "carto-positron" else "Detailed Maps",
            index=0,
            key="net_map_style",
            label_visibility="collapsed"
        )
    with m2:
        dot_size = st.slider("Marker Size", min_value=5, max_value=35, value=15, key="net_map_size", label_visibility="collapsed")

    fig = None
    
    if map_mode == "🌍 Aggregated Location View (Site Tier)":
        loc_cols = ['location_name', 'city', 'state'] if 'location_name' in active_map_df.columns else ['city', 'state']
        loc_df = active_map_df.dropna(subset=['latitude', 'longitude']).groupby(loc_cols).agg(
            latitude=('latitude', 'mean'),  
            longitude=('longitude', 'mean'),
            total_devices=('device_id', 'count'),
            site_classification=('device_role', classify_site_tier)
        ).reset_index()

        if not loc_df.empty:
            if 'location_name' in loc_df.columns:
                loc_df['hover_label'] = loc_df['location_name'] + " (" + loc_df['city'] + ", " + loc_df['state'] + ")"
            else:
                loc_df['hover_label'] = loc_df['city'] + ", " + loc_df['state']
                
            dynamic_center, dynamic_zoom = get_smart_map_bounds(loc_df)
            fig = px.scatter_mapbox(
                loc_df, lat="latitude", lon="longitude", hover_name="hover_label",      
                hover_data={"site_classification": True, "total_devices": True, "latitude": False, "longitude": False},    
                color="site_classification", center=dynamic_center, zoom=dynamic_zoom, height=600,
                color_discrete_map={
                    "Tier 1": "#8E44AD",
                    "Tier 1 / Tier 2": "#0078D7", 
                    "Tier 2": "#F39C12",
                    "Tier 3": "#00CECB",
                    "Tier 3 /TWTC": "#2ECC71",
                    "Tier 3 Z": "#1ABC9C", 
                    "⚠️ Problem!! (EAR Only)": "#E74C3C"
                },
                color_discrete_sequence=px.colors.qualitative.Pastel 
            )
            fig.update_traces(marker=dict(size=dot_size, opacity=0.9))
        else:
            st.warning("⚠️ No valid geospatial coordinates found for the currently selected devices.")

    else:
        map_df = active_map_df.dropna(subset=['latitude', 'longitude'])
        if not map_df.empty:
            map_df['hover_label'] = map_df['device_name'] + " (" + map_df['device_model'] + ")"
            dynamic_center, dynamic_zoom = get_smart_map_bounds(map_df)
            fig = px.scatter_mapbox(
                map_df, lat="latitude", lon="longitude", hover_name="hover_label",      
                hover_data={"device_role": True, "device_model": True, "city": True, "state": True, "nos_version": True, "latitude": False, "longitude": False},    
                color="device_role", center=dynamic_center, zoom=dynamic_zoom, height=600,
                color_discrete_sequence=px.colors.qualitative.Set1 
            )
            fig.update_traces(marker=dict(size=dot_size, opacity=0.8))
        else:
            st.warning("⚠️ No valid geospatial coordinates found for the currently selected devices.")

    if fig:
        fig.update_layout(
            mapbox_style=map_bg, margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                title=dict(text="Site Classification" if map_mode.startswith("🌍") else "Device Role", font=dict(color="white")),
                font=dict(color="white"), bgcolor="rgba(14, 17, 23, 0.7)", yanchor="top", y=0.98, xanchor="left", x=0.02
            )
        )
        
        # --- THE CACHE BUSTER ---
        state_signature = f"{st.session_state['inv_f_role']}_{st.session_state['inv_f_vendor']}_{st.session_state['inv_f_model']}_{st.session_state['inv_f_search']}_{len(active_map_df)}_{map_bg}"
        cache_buster_key = f"map_{map_mode}_{hashlib.md5(state_signature.encode()).hexdigest()}"
        
        st.plotly_chart(fig, use_container_width=True, key=cache_buster_key)


# ==========================================
# 6. MAIN ORCHESTRATOR 
# ==========================================

def render_inventory_dashboard():
    """Renders the Unified Hardware Inventory and Interactive Map Dashboard."""
    init_session_state()
    inject_custom_css()

    # --- NEW: Dynamic Network Selector ---
    st.sidebar.markdown("### 🌐 Network Context")
    available_networks = ["AS3549", "AS3356", "AS359", "AS209"]
    
    current_index = available_networks.index(st.session_state["target_asn"]) if st.session_state["target_asn"] in available_networks else 0
    selected_asn = st.sidebar.selectbox(
        "Select Target Network", 
        options=available_networks,
        index=current_index,
        key="network_selector_widget"
    )
    
    # Check for network switch to clear stale filters
    if selected_asn != st.session_state["target_asn"]:
        st.session_state["target_asn"] = selected_asn
        st.session_state["inv_f_role"] = "All"
        st.session_state["inv_f_vendor"] = "All"
        st.session_state["inv_f_model"] = "All"
        st.session_state["inv_f_search"] = ""
        st.rerun()

    current_asn = st.session_state["target_asn"]
    # -------------------------------------

    st.subheader(f"📦 {current_asn} Network Intelligence")

    # Pass the dynamic parameter to the cached function
    df = fetch_inventory_data(current_asn)
    if df.empty:
        st.info(f"📂 No devices currently found in the {current_asn} network.")
        return

    # Render top components
    render_network_summary(df)
    render_role_breakdown(df)
    render_hardware_breakdown(df)

    st.divider()

    # Render dynamic filters
    render_global_filters(df)
    filtered_df = apply_filters(df)

    # TRUE LAZY LOADING
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} matching devices**")
    
    view_mode = st.radio(
        "Select Active View", 
        ["📋 Filtered Inventory", "🗺️ Interactive Map"], 
        horizontal=True, 
        label_visibility="collapsed",
        key="inv_view_mode"
    )

    # Safely retrieve selected row indices from session state if switching to Map view
    selected_indices = []
    if "inventory_table_widget" in st.session_state:
        selected_indices = st.session_state["inventory_table_widget"]["selection"]["rows"]

    # Conditional Execution Block
    if view_mode == "📋 Filtered Inventory":
        render_inventory_table(filtered_df)
    else:
        render_interactive_map(filtered_df, selected_indices)