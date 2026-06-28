import streamlit as st
import pandas as pd
import math # <-- Add this to the top of your file

from src.ui_components import UI
from src.api_client import post_location, get_locations

def get_static_location_data():
    """
    Returns data from session state if a file was uploaded, 
    otherwise returns a small sample for UI initialization.
    """
    if "staged_df" in st.session_state:
        return st.session_state["staged_df"]
    
    return pd.DataFrame([{
        "location_code": "STAGING-01",
        "short_name": "SAMPLE",
        "location_name": "Upload a file to begin...",
        "city": "N/A",
        "country": "N/A"
    }])


def run_bulk_post_loop(df):
    """
    Iterates through the dataframe, scrubs NaNs, posts to API, and captures 
    detailed error messages for any failed rows. Includes state persistence.
    """
    total = len(df)
    
    # GUARDRAIL: Prevent division by zero
    if total == 0:
        st.warning("⚠️ No records found in the dataframe to process.")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()
    success_count = 0
    failure_log = []
    
    records = df.to_dict('records')

    # --- FOOLPROOF JSON SCRUBBER ---
    # Pandas coerces None back to NaN in float columns. 
    # We must clean the raw Python dictionaries to ensure valid JSON 'null's.
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                record[key] = None

    for i, record in enumerate(records):
        loc_code = record.get("location_code", f"Row {i}")
        try:
            # Call the API client
            post_location(record)
            success_count += 1
        except Exception as e:
            # Capture the exact failure reason
            failure_log.append({
                "location_code": loc_code,
                "error_reason": str(e)
            })

        # Update Progress UI
        progress = (i + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"Uploading: {i+1} of {total}...")

    status_text.empty()
    progress_bar.empty()

    # NDT STATE SYNC: Record metrics for global state awareness
    st.session_state['last_upload_success_count'] = success_count
    st.session_state['last_upload_failure_count'] = len(failure_log)

    # Final Feedback Report
    if success_count > 0:
        st.success(f"✨ Successfully added {success_count} records to production!")
        
    if failure_log:
        st.error(f"❌ {len(failure_log)} records failed to upload.")
        with st.expander("🔍 View Detailed Error Log", expanded=True):
            st.table(pd.DataFrame(failure_log))
    
    if success_count > 0 or failure_log:
        if st.button("Refresh View"):
            st.cache_data.clear()
            st.rerun()

def apply_filters(df):
    """Adds filter widgets and returns the filtered dataframe."""
    with st.container(border=True):
        st.markdown("##### 🔍 Filter Records")
        col1, col2, col3 = st.columns(3)
        
        # Use existing unique values from the DB to populate filters
        with col1:
            countries = sorted(df['country'].dropna().unique()) if 'country' in df.columns else []
            selected_countries = st.multiselect("Country", options=countries)
            
        with col2:
            states = sorted(df['state'].dropna().unique()) if 'state' in df.columns else []
            selected_states = st.multiselect("State", options=states)
            
        with col3:
            cities = sorted(df['city'].dropna().unique()) if 'city' in df.columns else []
            selected_cities = st.multiselect("City", options=cities)

    # Chain the filters
    filtered_df = df.copy()
    if selected_countries:
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]
    if selected_states:
        filtered_df = filtered_df[filtered_df['state'].isin(selected_states)]
    if selected_cities:
        filtered_df = filtered_df[filtered_df['city'].isin(selected_cities)]
        
    return filtered_df

def render_locations_table(df: pd.DataFrame):
    """
    Standalone module for rendering the production locations table.
    Includes selection state handling and detailed JSON record inspection.
    """
    import streamlit as st
    from src.ui_components import UI
    
    # Standardized Table Component
    selection = UI.render_selectable_table(
        df=df,
        key_prefix="production_locations",
        id_column_to_hide="location_id"
    )
    
    if selection:
        with st.expander("🔍 Selected Record Details", expanded=True):
            st.json(selection)

def render_locations_map(df: pd.DataFrame):
    """
    Standalone module for rendering the rich Plotly Mapbox of locations.
    Features composite legend labels (Short Name + Location Code + Address), 
    unique coloring, auto-zoom calibration, and dynamic tooltips.
    Includes performance guardrails to prevent browser crashes on large datasets.
    """
    import streamlit as st
    import pandas as pd
    import math
    import plotly.express as px

    # --- SAFETY GUARDRAIL: NEVER LOAD ALL DATA ---
    MAX_POINTS = 1000
    if len(df) > MAX_POINTS:
        st.warning(f"⚠️ Dataset contains {len(df)} records, which may cause performance issues or crashes.")
        
        # Attempt to default to Denver if the city column exists
        if 'city' in df.columns:
            df_denver = df[df['city'].astype(str).str.contains('Denver', case=False, na=False)].copy()
            
            if not df_denver.empty:
                st.success("📍 Automatically restricted map view to **Denver** to preserve performance.")
                df = df_denver
            else:
                st.info(f"📍 'Denver' not found in current filter. Truncating to the first {MAX_POINTS} records.")
                df = df.head(MAX_POINTS).copy()
        else:
            st.info(f"📍 City data unavailable. Truncating to the first {MAX_POINTS} records.")
            df = df.head(MAX_POINTS).copy()

    # --- MAP CONTROLS ---
    c1, c2 = st.columns([3, 1])
    with c1:
        map_bg = st.selectbox(
            "🗺️ Map Style", 
            options=["carto-darkmatter", "carto-positron", "open-street-map"],
            format_func=lambda x: "Dark Mode" if x == "carto-darkmatter" else "Light Mode" if x == "carto-positron" else "Detailed Maps",
            index=0,
            key="loc_map_style",
            help="Change the underlying map tile style."
        )
    with c2:
        dot_size = st.slider("🔘 Marker Size", min_value=3, max_value=25, value=12, key="loc_map_size")

    # Dynamic coordinate column discovery
    lat_col = next((c for c in df.columns if c.lower() in ['lat', 'latitude']), None)
    lon_col = next((c for c in df.columns if c.lower() in ['lon', 'longitude', 'lng']), None)

    if lat_col and lon_col:
        # Define the metadata columns we want to keep for the tooltip
        tooltip_cols = ['short_name', 'location_name', 'location_code', 'address', 'city', 'country']
        
        # Safely collect only the columns that actually exist in the dataframe
        cols_to_keep = [lat_col, lon_col] + [c for c in tooltip_cols if c in df.columns]

        df_map = df[cols_to_keep].copy()
        df_map.rename(columns={lat_col: 'lat', lon_col: 'lon'}, inplace=True)
        
        # Coerce coordinates and drop invalids
        df_map['lat'] = pd.to_numeric(df_map['lat'], errors='coerce')
        df_map['lon'] = pd.to_numeric(df_map['lon'], errors='coerce')
        df_map = df_map.dropna(subset=['lat', 'lon'])

        if not df_map.empty:
            
            # --- COMPOSITE LEGEND & TOOLTIP LOGIC ---
            if 'short_name' in df_map.columns:
                # Gracefully fallback if 'address' column doesn't exist
                address_fallback = df_map['address'] if 'address' in df_map.columns else df_map.get('city', df_map.get('location_name', ''))
                
                # Format the location_code (CLLI) to sit inside brackets
                if 'location_code' in df_map.columns:
                    loc_code_str = df_map['location_code'].fillna("").astype(str)
                    code_formatted = loc_code_str.apply(lambda x: f" [{x}]" if str(x).strip() else "")
                else:
                    code_formatted = ""
                
                # Build the composite label: "SHORTNAME [LOCATION_CODE] - ADDRESS"
                df_map['legend_label'] = df_map['short_name'].astype(str) + code_formatted + " - " + address_fallback.astype(str)
                
                hover_title = 'legend_label'
                color_param = 'legend_label'
            else:
                hover_title = None
                color_param = None
                
            # Filter out internal columns from the secondary tooltip list so they don't double-render
            hover_details = [c for c in df_map.columns if c not in ['lat', 'lon', hover_title, 'legend_label', 'short_name']]

            # --- AUTO-ZOOM ALGORITHM ---
            center_lat = df_map['lat'].mean()
            center_lon = df_map['lon'].mean()
            
            lat_spread = df_map['lat'].max() - df_map['lat'].min()
            lon_spread = df_map['lon'].max() - df_map['lon'].min()
            max_spread = max(lat_spread, lon_spread)
            
            if max_spread == 0:
                dynamic_zoom = 12 
            else:
                dynamic_zoom = max(1.0, 7.5 - math.log(max_spread, 2))

            # Render a rich Plotly Mapbox
            fig = px.scatter_mapbox(
                df_map, 
                lat="lat", 
                lon="lon",
                hover_name=hover_title,      
                hover_data=hover_details,    
                color=color_param, 
                center={"lat": center_lat, "lon": center_lon}, 
                zoom=dynamic_zoom, 
                height=600
            )
            
            # Apply uniform marker sizing across all categorical trace selections
            fig.update_traces(marker=dict(size=dot_size))
            
            # Stylize the legend layout to align with dark dashboard aesthetics
            fig.update_layout(
                mapbox_style=map_bg, 
                margin={"r":0,"t":0,"l":0,"b":0},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    title=dict(text="📍 Location Legend", font=dict(color="white")),
                    font=dict(color="white"),
                    bgcolor="rgba(14, 17, 23, 0.7)",
                    yanchor="top",
                    y=0.98,
                    xanchor="left",
                    x=0.02
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Filtered records exist, but none contain valid plotting coordinates.")
    else:
        st.info("💡 Map View requires coordinate data. Ensure your API payload returns 'latitude' and 'longitude' columns.")
def render_load_data_view():
    """
    Complete view for:
    1. Bulk Ingestion with 3-part composite duplicate detection.
    2. Production table with Country, State, and City filters.
    3. Rich Plotly Map visualization with Auto-Zoom and custom Backgrounds.
    """
    import streamlit as st
    import pandas as pd
    from src.api_client import get_locations # Ensure this import is valid for your structure

    # ==========================================
    # STAGE 1: INGESTION & DUPLICATE CHECK
    # ==========================================
    st.subheader("📥 Bulk Data Ingestion")
    
    # Pre-fetch database composite keys (Location Code + Location Name + Short Name)
    db_composite_keys = set()
    try:
        db_records = get_locations()
        if db_records:
            for r in db_records:
                l_code = str(r.get('location_code', '')).strip().upper()
                l_name = str(r.get('location_name', '')).strip().upper()
                s_name = str(r.get('short_name', '')).strip().upper()
                if l_code:
                    db_composite_keys.add(f"{l_code}|{l_name}|{s_name}")
    except Exception as e:
        st.error(f"API Connection Error: {e}")

    uploaded_file = st.file_uploader("Upload Location CSV", type=["csv"], key="loc_uploader")
    
    if uploaded_file:
        # --- ROBUST ENCODING HANDLING ---
        try:
            df_upload = pd.read_csv(uploaded_file)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            try:
                df_upload = pd.read_csv(uploaded_file, encoding='cp1252')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                try:
                    df_upload = pd.read_csv(uploaded_file, encoding='latin1')
                except Exception as e:
                    st.error(f"❌ CRITICAL ERROR: Unable to decode CSV file. Error details: {e}")
                    st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected error reading file: {e}")
            st.stop()
        # ------------------------------------

        df_upload.columns = [c.lower().replace(' ', '_').strip() for c in df_upload.columns]
        
        required_cols = ['location_code', 'location_name', 'short_name']
        missing_cols = [col for col in required_cols if col not in df_upload.columns]
        
        if missing_cols:
            st.error(f"CSV missing required columns: {', '.join(missing_cols)}")
        else:
            # Normalize and identify duplicates using the 3-part composite key
            df_upload = df_upload.dropna(subset=['location_code', 'location_name', 'short_name'])
            
            # Create a 3-part composite key column in the upload dataframe
            df_upload['composite_key'] = (
                df_upload['location_code'].astype(str).str.strip().str.upper() + "|" + 
                df_upload['location_name'].astype(str).str.strip().str.upper() + "|" +
                df_upload['short_name'].astype(str).str.strip().str.upper()
            )
            
            is_dup = df_upload['composite_key'].isin(db_composite_keys)
            df_existing = df_upload[is_dup].copy()
            df_new = df_upload[~is_dup].drop_duplicates(subset=['composite_key']).copy()

            # Feedback messages
            if not df_existing.empty:
                st.warning(f"🚨 Skipping {len(df_existing)} records already in database.")
            
            if not df_new.empty:
                st.success(f"✅ {len(df_new)} new unique records ready.")
                df_final = df_new.drop(columns=['composite_key']).where(pd.notnull(df_new), None)
                st.session_state["staged_df"] = df_final
                
                st.dataframe(df_final.head(10), width="stretch")

                if st.button(f"🚀 Post {len(df_final)} Records", type="primary"):
                    run_bulk_post_loop(df_final) # Ensure this function is defined above
                    
            else:
                st.info("No new unique records found in this file.")

    st.divider()

    # ==========================================
    # STAGE 2: PRODUCTION VIEW & FILTERING
    # ==========================================
    st.subheader("🗄️ Production Records")
    
    current_db = get_locations()
    if current_db:
        df_db = pd.DataFrame(current_db)
        
        # Apply extracted filtering logic
        df_filtered = apply_filters(df_db) # Ensure this function is defined above

        # --- REFRESH ---
        col_ref, col_count = st.columns([1, 5])
        if col_ref.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
        col_count.caption(f"Showing {len(df_filtered)} of {len(df_db)} records")

        # --- TABS IMPLEMENTATION ---
        tab_table, tab_map = st.tabs(["📋 Table View", "🗺️ Map View"])

        # TAB 1: Table Results (Delegated to Modular Function)
        with tab_table:
            render_locations_table(df_filtered)

        # TAB 2: Map Data (Delegated to Modular Function)
        with tab_map:
            render_locations_map(df_filtered)
                
    else:
        st.info("The production database is currently empty.")