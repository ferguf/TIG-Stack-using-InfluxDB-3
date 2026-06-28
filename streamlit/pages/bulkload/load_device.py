import streamlit as st
import pandas as pd
import time
from src.ui_components import UI

# 1. Import DATA-ONLY functions from Service Layer
from src.utils.api_network import (
    get_devices, 
    post_device, 
    post_device_ports,
    update_device,
    delete_device
)

# 2. Import UI COMPONENTS (Forms & Filters) from dedicated utility
from src.utils.ui_network_forms import (
    render_device_ports_table,
    render_edit_device_form, 
    render_edit_location_form,
    apply_device_filters
)

# 3. Import DATA PROCESSING from Utility Layer
from src.utils.file_utils import (
    find_and_read_role_file,
    normalize_dataframe_columns,
    get_new_records_only,
    sanitize_for_api,
    clean_device_payload,
    MessageHandler
)

# ----------------------------------------------------------------------
# Logic Orchestration
# ----------------------------------------------------------------------

def render_device_manager():
    """Main entry point for Device Lifecycle Management."""
    st.title("🔌 FDP Lifecycle Manager")
    
    # 1. Global Message/Log Feed
    MessageHandler.initialize()
    MessageHandler.render(key_suffix="device_lifecycle_main")

    # 2. Render the primary data view (formerly inside tabs)
    render_load_data_view()

# ----------------------------------------------------------------------
# Action Dispatcher Logic
# ----------------------------------------------------------------------

def render_site_metadata_display(search_term, site_info):
    """Renders site data using strictly lowercase keys from the API."""
    if not site_info:
        st.warning(f"⚠️ No site metadata found for: {search_term}")
        return

    with st.container(border=True):
        st.markdown(f"##### 📍 Facility Details: {(search_term or 'UNKNOWN').upper()}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CLLI", site_info.get("location_code", "N/A"))
        c2.metric("Type", site_info.get("facility_type", "N/A"))
        c3.metric("Lat", site_info.get("latitude", "N/A"))
        c4.metric("Lon", site_info.get("longitude", "N/A"))

        st.markdown("---")
        
        addr = site_info.get("address", "No address")
        city = site_info.get("city", "")
        state = site_info.get("state", "")
        
        full_address = f"{addr}, {city}, {state}".strip(", ")
        st.write(f"🏠 **Address:** {full_address}")

def render_device_port_logic(selection):
    """Safely renders the port table for a selected hardware device."""
    if selection and 'device_id' in selection:
        st.subheader(f"🔌 Port Inventory: {selection.get('device_name')}")
        render_device_ports_table(
            device_id=selection['device_id'],
            device_name=selection['device_name']
        )
    else:
        st.info("Select a device from the inventory above to view its port configuration.")

def execute_device_action(row_data: pd.Series):
    """Dispatcher: Identifies the action and executes the corresponding API call."""
    action = str(row_data.get("action", "add")).lower().strip()
    dev_name = str(row_data.get("device_name"))
    payload = clean_device_payload(row_data.to_dict())
    
    device_id = None
    if action in ["update", "delete"]:
        db_records = get_devices()
        match = next((d for d in db_records if d['device_name'] == dev_name), None)
        if match:
            device_id = match['device_id']
        else:
            MessageHandler.add(f"❌ Cannot {action}: {dev_name} not found in DB.", "error")
            return None

    if action == "delete":
        return delete_device(device_id)
    if action == "update":
        return update_device(device_id, payload)
    
    return post_device(payload)

def run_full_ingestion_chain(row: pd.Series):
    """Orchestrates Device and Port Template loading."""
    dev_name = str(row.get("device_name"))
    action = str(row.get("action", "add")).lower().strip()
    done_key = f"done_{dev_name.replace('.', '_')}"

    response = execute_device_action(row)
    
    if response:
        if action == "add":
            clean_id = response["device_id"] if isinstance(response, dict) else response
            current_role = str(row.get("device_role", "var")).lower().strip()
            current_model = str(row.get("device_model", "")).lower().strip()
            
            df_ports, template_path = find_and_read_role_file(current_model, role=current_role)
            
            if df_ports is not None:
                payload = sanitize_for_api(df_ports).to_dict(orient="records")
                if post_device_ports(clean_id, payload):
                    st.session_state[done_key] = True
                    MessageHandler.add(f"✅ {dev_name}: Device and Ports loaded.", "success")
                    return True
                else:
                    MessageHandler.add(f"⚠️ {dev_name}: Device created, but Port Load failed.", "warning")
            else:
                MessageHandler.add(f"❌ {dev_name}: Port Template not found ({current_role}_{current_model}.csv)", "error")
        else:
            st.session_state[done_key] = True
            return True
    return False

# ----------------------------------------------------------------------
# Ingestion UI Component
# ----------------------------------------------------------------------

def process_bulk_ingestion(df_devices: pd.DataFrame):
    """The Ingestion Queue UI Manager."""
    st.subheader("🛠️ Lifecycle Action Queue")
    
    unprocessed = [
        idx for idx, row in df_devices.iterrows() 
        if f"done_{str(row['device_name']).replace('.', '_')}" not in st.session_state
    ]

    if not unprocessed:
        st.info("✅ All staged actions in this file have been processed.")
        return

    if UI.button(f"🔥 Process All {len(unprocessed)} Pending Actions", color="blue", key="bulk_exec_devices"):
        progress_bar = st.progress(0)
        for i, idx in enumerate(unprocessed):
            run_full_ingestion_chain(df_devices.loc[idx])
            progress_bar.progress((i + 1) / len(unprocessed))
        st.success("🏁 Bulk processing complete!")
        st.rerun()

    st.divider()

    for idx in unprocessed:
        row = df_devices.loc[idx]
        dev_name = str(row.get("device_name", "Unknown"))
        action = str(row.get("action", "add")).lower().strip()
        btn_color = "green" if action == "add" else "orange" if action == "update" else "red"
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**:{btn_color}[{action.upper()}]** | **{dev_name}** | {row.get('device_model')}")
                st.caption(f"Location: {row.get('location')} | Aisle: {row.get('aisle')} | Rack: {row.get('rack')}")
            with col2:
                if UI.button(action.upper(), color=btn_color, key=f"q_btn_{idx}_{action}"):
                    if run_full_ingestion_chain(row):
                        st.rerun()

# ----------------------------------------------------------------------
# Main Dashboard View
# ----------------------------------------------------------------------

def render_load_data_view():
    """Primary entry point for Device Management Inventory."""
    st.subheader("📥 Device Bulk Lifecycle")
    
    db_records = get_devices()
    uploaded_file = st.file_uploader("Upload lifecycle CSV", type=["csv"], key="uploader_lifecycle")
    
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file)
        df_clean = normalize_dataframe_columns(df_raw)
        if not df_clean.empty:
            process_bulk_ingestion(sanitize_for_api(df_clean))

    st.divider()

    st.subheader("🗄️ Device Inventory")
    if db_records:
        df_db = pd.DataFrame(db_records)
        df_filtered = apply_device_filters(df_db, "All")
        
        selection = UI.render_selectable_table(
            df=df_filtered, 
            key_prefix="inv_main", 
            id_column_to_hide="device_id"
        )
        
        if selection:
            st.markdown(f"### ⚙️ Managing: **{selection.get('device_name')}**")
            
            # Contextual Management Tabs
            t_ports, t_site, t_edit = st.tabs([
                "🔌 Port Inventory", 
                "🏢 Site Information", 
                "📝 Device Edit"
            ])
            
            with t_ports:
                render_device_port_logic(selection)

            with t_site:
                # 1. Pull directly from the router payload! No secondary API calls needed.
                loc_id = selection.get('location_id')
                loc_key = selection.get('location', 'UNKNOWN')
                
                # 2. Check the session state cache
                site_data = st.session_state.get("cached_site_info")
                
                # 3. Fetch rich facility data ONLY if the UUID doesn't match the cache
                if not site_data or site_data.get('location_id') != loc_id:
                    from src.utils.api_network import get_location_by_id
                    
                    if loc_id:
                        site_data = get_location_by_id(loc_id)
                        st.session_state["cached_site_info"] = site_data
                    else:
                        st.warning("⚠️ This device has not been assigned to a location yet.")
                        site_data = {}
                
                # 4. Render the UI
                if site_data:
                    render_site_metadata_display(loc_key, site_data)
                
            with t_edit:
                st.markdown("#### 🛠️ Update Device Records")
                render_edit_location_form(selection)
                st.divider()
                render_edit_device_form(selection, network_label="3549")
    else:
        st.info("📂 No devices currently in database.")

if __name__ == "__main__":
    render_device_manager()