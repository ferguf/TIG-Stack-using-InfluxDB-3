import streamlit as st
import pandas as pd
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
    Iterates through the dataframe, posts to API, and captures 
    detailed error messages for any failed rows.
    """
    total = len(df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    success_count = 0
    failure_log = []
    
    records = df.to_dict('records')

    for i, record in enumerate(records):
        loc_code = record.get("location_code", f"Row {i}")
        try:
            # Call the API client
            post_location(record)
            success_count += 1
        except Exception as e:
            # Capture the exact failure reason (e.g., 422, 500, or connection error)
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

    # Final Feedback Report
    if success_count > 0:
        st.success(f"✨ Successfully added {success_count} records to production!")
        
    if failure_log:
        st.error(f"❌ {len(failure_log)} records failed to upload.")
        with st.expander("🔍 View Detailed Error Log (Why records didn't load)", expanded=True):
            st.table(pd.DataFrame(failure_log))
    
    if success_count > 0 or failure_log:
        if st.button("Refresh View"):
            st.cache_data.clear()
            st.rerun()

def render_load_data_view():
    """
    Complete view for:
    1. Bulk Ingestion with duplicate detection.
    2. Production table with Country, State, and City filters.
    """
    # ==========================================
    # STAGE 1: INGESTION & DUPLICATE CHECK
    # ==========================================
    st.subheader("📥 Bulk Data Ingestion")
    
    # Pre-fetch database codes for comparison
    db_codes = set()
    try:
        db_records = get_locations()
        if db_records:
            db_codes = {str(r['location_code']).strip().upper() for r in db_records if r.get('location_code')}
    except Exception as e:
        st.error(f"API Connection Error: {e}")

    uploaded_file = st.file_uploader("Upload Location CSV", type=["csv"], key="loc_uploader")
    
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        df_upload.columns = [c.lower().replace(' ', '_').strip() for c in df_upload.columns]
        
        if 'location_code' not in df_upload.columns:
            st.error("CSV missing 'location_code' column.")
        else:
            # Normalize and identify duplicates
            df_upload = df_upload.dropna(subset=['location_code'])
            df_upload['norm_code'] = df_upload['location_code'].astype(str).str.strip().str.upper()
            
            is_dup = df_upload['norm_code'].isin(db_codes)
            df_existing = df_upload[is_dup].copy()
            df_new = df_upload[~is_dup].drop_duplicates(subset=['norm_code']).copy()

            # Feedback messages
            if not df_existing.empty:
                st.warning(f"🚨 Skipping {len(df_existing)} records already in database.")
            
            if not df_new.empty:
                st.success(f"✅ {len(df_new)} new unique records ready.")
                df_final = df_new.drop(columns=['norm_code']).where(pd.notnull(df_new), None)
                st.session_state["staged_df"] = df_final
                
                st.dataframe(df_final.head(10), width="stretch")

                if st.button(f"🚀 Post {len(df_final)} Records", type="primary"):
                    run_bulk_post_loop(df_final)
                    st.cache_data.clear()
                    st.rerun()
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
        
        # --- FILTER UI ---
        with st.container(border=True):
            st.markdown("##### 🔍 Filter Records")
            f_col1, f_col2, f_col3 = st.columns(3)
            
            with f_col1:
                countries = sorted(df_db['country'].dropna().unique()) if 'country' in df_db.columns else []
                sel_country = st.multiselect("Country", options=countries)
            with f_col2:
                states = sorted(df_db['state'].dropna().unique()) if 'state' in df_db.columns else []
                sel_state = st.multiselect("State", options=states)
            with f_col3:
                cities = sorted(df_db['city'].dropna().unique()) if 'city' in df_db.columns else []
                sel_city = st.multiselect("City", options=cities)

        # Apply Filtering Logic
        df_filtered = df_db.copy()
        if sel_country:
            df_filtered = df_filtered[df_filtered['country'].isin(sel_country)]
        if sel_state:
            df_filtered = df_filtered[df_filtered['state'].isin(sel_state)]
        if sel_city:
            df_filtered = df_filtered[df_filtered['city'].isin(sel_city)]

        # --- REFRESH & TABLE ---
        col_ref, col_count = st.columns([1, 5])
        if col_ref.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
        col_count.caption(f"Showing {len(df_filtered)} of {len(df_db)} records")

        # Standardized Table Component
        selection = UI.render_selectable_table(
            df=df_filtered,
            key_prefix="production_locations",
            id_column_to_hide="location_id"
        )
        
        if selection:
            with st.expander("🔍 Selected Record Details", expanded=True):
                st.json(selection)
    else:
        st.info("The production database is currently empty.")

def apply_filters(df):
    """Adds filter widgets and returns the filtered dataframe."""
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

# End of File