import streamlit as st
import pandas as pd
from src.state_managers import FabricStateManager
from src.api_client import (
    delete_fabric_service, 
    post_fabric_service, 
    get_fabric_services, 
    update_fabric_service
)
from src.ui_forms import create_fabric_service_form, update_fabric_service_form
from src.ui_components import UI
from src.ui_messages import MessageCenter

def render_provisioning_view(customer_id):
    """View logic for creating a new service when none exist or are selected."""
    st.subheader("🚀 Provision Fabric Service")
    
    # Use namespaced toggle
    if not st.session_state.get("fs_show_provision"):
        if UI.button("➕ Create New Service", color="green", key="fs_t2_btn_open_prov"):
            st.session_state["fs_show_provision"] = True
            st.rerun()
    else:
        with st.container(border=True):
            st.markdown("### Service Details")
            form_data = create_fabric_service_form()
            
            if form_data:
                form_data["customer_id"] = customer_id
                try:
                    post_fabric_service(form_data)
                    MessageCenter.set_success(f"✅ Provisioning {form_data['service_name']}...")
                    st.session_state["fs_show_provision"] = False
                    
                    # Clear cache to force refresh on next run
                    if f"svc_cache_{customer_id}" in st.session_state:
                        del st.session_state[f"svc_cache_{customer_id}"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Provisioning Failed: {e}")
            
            if st.button("⬅️ Cancel", key="fs_t2_btn_cancel_prov"):
                st.session_state["fs_show_provision"] = False
                st.rerun()

def render_management_view(record, customer_id):
    """View logic for Update/Delete of an existing service."""
    sid = record.get("service_id")
    name = record.get('service_name', 'Unnamed Service')
    
    st.info(f"📍 Managing Service: **{name}**")
    
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        if UI.button("🔄 Update", color="amber", key=f"fs_t2_btn_upd_{sid}"):
            st.session_state["fs_show_update"] = True
            st.session_state["fs_confirm_delete"] = False
            st.rerun()
    with col2:
        if UI.button("🗑️ Delete", color="red", key=f"fs_t2_btn_del_{sid}"):
            st.session_state["fs_confirm_delete"] = True
            st.session_state["fs_show_update"] = False
            st.rerun()

    # --- Update Branch ---
    if st.session_state.get("fs_show_update"):
        st.divider()
        updated = update_fabric_service_form(record)
        if updated:
            try:
                payload = {**record, **updated}
                payload.pop("Select", None) 
                update_fabric_service(sid, payload)
                
                # Update local state immediately
                st.session_state["fs_active_record"] = payload
                MessageCenter.set_success(f"✅ {name} updated.")
                st.session_state["fs_show_update"] = False
                
                # Invalidate cache
                if f"svc_cache_{customer_id}" in st.session_state:
                    del st.session_state[f"svc_cache_{customer_id}"]
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

    # --- Delete Branch ---
    if st.session_state.get("fs_confirm_delete"):
        st.divider()
        with st.container(border=True):
            st.error(f"⚠️ Confirm Delete: **{name}**?")
            c1, c2, _ = st.columns([1, 1, 2])
            if c1.button("Yes, Delete", key=f"fs_t2_conf_del_{sid}"):
                try:
                    delete_fabric_service(sid)
                    MessageCenter.set_success("🗑️ Service removed.")
                    # Explicitly clear selection
                    st.session_state["fs_active_id"] = None
                    st.session_state["fs_active_record"] = None
                    if f"svc_cache_{customer_id}" in st.session_state:
                        del st.session_state[f"svc_cache_{customer_id}"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Deletion failed: {e}")
            if c2.button("Cancel", key=f"fs_t2_can_del_{sid}"):
                st.session_state["fs_confirm_delete"] = False
                st.rerun()

def prepare_service_display_df(df_raw):
    """Utility to filter and rename columns for the Service table UI."""
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    # Define the specific mapping you requested
    display_cols = {
        "service_name": "Service",
        "service_alias": "Alias",
        "service_type": "Type",
        "service_description": "Description",
        "route_target": "Route Target",
        "service_id": "service_id"  # Keep hidden for selection logic
    }
    
    # Filter to only requested columns that actually exist in the raw data
    existing_cols = [c for c in display_cols.keys() if c in df_raw.columns]
    
    # Create the display version
    df_display = df_raw[existing_cols].copy()
    return df_display.rename(columns=display_cols)

def show_fabric_service(customer_id):
    """Main entry point for Tab 2 (Tier 2)."""
    manager = FabricStateManager()
    manager.initialize()

    # 1. State Retrieval
    active_record = manager.get_active_record("fs")
    active_conn = manager.get_active_record("fc")

    # 2. RENDER HEADER FIRST
    if active_record:
        UI.render_service_context(active_record, active_conn)
        st.divider()

    # 3. Fetch Data with Cache Logic
    cache_key = f"svc_cache_{customer_id}"
    if cache_key not in st.session_state:
        df_raw = get_fabric_services(customer_id)
        if df_raw is not None and not df_raw.empty:
            for col in df_raw.columns:
                if any(k in col.lower() for k in ['id', 'uuid', 'at']):
                    df_raw[col] = df_raw[col].astype(str)
        st.session_state[cache_key] = df_raw

    df_raw = st.session_state[cache_key]

    # 4. Render Table (using the new filter/rename logic)
    if df_raw is not None and not df_raw.empty:
        df_display = prepare_service_display_df(df_raw)
        
        selection = UI.render_selectable_table(
            df=df_display, 
            key_prefix=f"fs_t2_table_{customer_id}", 
            id_column_to_hide="service_id"
        )

        # 5. Synchronize Selection
        # We look up the raw record so the manager has full metadata (not just display cols)
        if selection:
            selected_id = str(selection.get("service_id"))
            raw_match = df_raw[df_raw['service_id'].astype(str) == selected_id].to_dict('records')
            if raw_match:
                if manager.sync_selection("fs", raw_match[0], "service_id"):
                    st.rerun()
        else:
            if manager.sync_selection("fs", None, "service_id"):
                st.rerun()

    st.divider()

    # 6. View Routing
    if df_raw is None or df_raw.empty or not active_record:
        render_provisioning_view(customer_id)
    else:
        render_management_view(active_record, customer_id)
