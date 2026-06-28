import streamlit as st
import pandas as pd
from src.ui_components import UI
from src.utils.file_utils import (
    normalize_dataframe_columns, 
    MessageHandler, 
    sanitize_for_api
)
from src.utils.api_network import get_devices, get_port_by_device_name, get_device_by_id
from src.utils.api_patch_panel import (
    update_panel_port, 
    get_patch_panels_for_device_name, 
    get_panel_ports
)

def render_connectivity_view():
    """Main View: Ingestion -> Preview -> Execution Workflow."""
    
    # 1. Setup Debugging & Console
    MessageHandler.render_debug_controls()
    MessageHandler.render_ui_logs(key_suffix="patch_conn")

    st.markdown("### 📤 1. Bulk Connectivity Ingestion")
    conn_file = st.file_uploader("Drop connectivity CSV here", type=["csv"], key="conn_bulk_upload")

    if conn_file:
        # --- AUTOMATION STEP: File Tracking ---
        if "last_loaded_conn" not in st.session_state or st.session_state.last_loaded_conn != conn_file.name:
            df_raw = pd.read_csv(conn_file)
            st.session_state.df_norm = process_raw_dataframe(df_raw)
            st.session_state.conn_preview = None  # Reset preview to force auto-resolve
            st.session_state.last_loaded_conn = conn_file.name

        if st.session_state.df_norm is not None:
            st.divider()
            
            # --- AUTOMATION STEP: Auto-Resolve UUIDs ---
            if st.session_state.conn_preview is None:
                with st.spinner("🔄 Automatically resolving UUIDs & building Use Cases..."):
                    df_preview = build_preview_dataframe(st.session_state.df_norm)
                    st.session_state.conn_preview = df_preview
                    st.rerun() # Refresh to show table immediately

            # 3. Execution Phase
            if "conn_preview" in st.session_state:
                render_execution_area(st.session_state.conn_preview)

def process_raw_dataframe(df_raw):
    """Handles column mapping and initial cleanup."""
    df_norm = normalize_dataframe_columns(df_raw)
    cols = df_norm.columns.tolist()

    map_a = next((c for c in cols if c in ['device_a', 'devicea', 'source_device']), None)
    map_b = next((c for c in cols if c in ['device_b', 'deviceb', 'dest_device']), None)

    if not map_a or not map_b:
        st.error("❌ Could not identify Device columns (device_a/device_b).")
        return None

    df_norm = df_norm.rename(columns={map_a: 'device_a', map_b: 'device_b'})
    
    if 'port_name.1' in df_norm.columns:
        df_norm = df_norm.rename(columns={'port_name': 'port_a', 'port_name.1': 'port_b'})
    else:
        df_norm = df_norm.rename(columns={'port_name': 'port_a'})
    
    return df_norm

def resolve_port_id(device_name, port_identifier, is_patch_panel=True):
    dev_name = str(device_name).strip()
    port_name = str(port_identifier).strip()
    
    try:
        if is_patch_panel:
            response_data = get_patch_panels_for_device_name(dev_name)
            if not response_data: return None
            
            pp_obj = response_data[0] if isinstance(response_data, list) else response_data
            pp_uuid = pp_obj.get('device_id')
            if not pp_uuid: return None

            ports = get_panel_ports(pp_uuid)
            port_match = next((p for p in ports if str(p.get('port_name')) == port_name), None)
            
            if port_match:
                return str(port_match.get('port_id'))
            return None
        else:
            port_data = get_port_by_device_name(dev_name, port_name)
            if isinstance(port_data, dict):
                return str(port_data.get('port_id'))
            return None
    except Exception as e:
        return None

def build_preview_dataframe(df_norm):
    preview_data = []
    for idx, row in df_norm.iterrows():
        dev_a = str(row.get('device_a', '')).strip()
        port_a = str(row.get('port_a', '')).strip()
        dev_b = str(row.get('device_b', '')).strip()
        port_b = str(row.get('port_b', '')).strip()

        is_b_pp = dev_b.upper().startswith("PP")

        uuid_a = resolve_port_id(dev_a, port_a, is_patch_panel=True)
        uuid_b = resolve_port_id(dev_b, port_b, is_patch_panel=is_b_pp)

        preview_data.append({
            "Source": f"{dev_a} [{port_a}]",
            "Dest": f"{dev_b} [{port_b}]",
            "Resolved_ID_A": uuid_a,
            "Resolved_ID_B": uuid_b,
            "Is_B_Patch_Panel": is_b_pp,
            "Proposed_Description": f"{dev_a}::{port_a} -> {dev_b}::{port_b}",
            "Status": "✅ Ready" if (uuid_a and uuid_b) else "❌ Failed"
        })
    return pd.DataFrame(preview_data)

def render_execution_area(df_preview):
    """Table and primary button for final database updates."""
    st.subheader("📋 3. Staged Connection Manager")
    
    # We keep the selectable table so users can still see the data, 
    # but the logic below now defaults to 'Execute All'
    selection = UI.render_selectable_table(df_preview, "conn_exec_table", "Proposed_Description")
    
    t1, t2 = st.tabs(["🚀 Connect ", "📄 Raw Metadata"])
    
    with t1:
        st.info("Ready to commit connections to the database. This will process all resolved rows.")
        
        # Centering the primary action button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Replaced with UI.button as requested
            if UI.button("Connect All", color="green", key="exec_all_final"):
                # Convert the entire preview dataframe to a list of dicts for processing
                all_rows = df_preview.to_dict('records')
                process_execution(all_rows, mode="Bulk")

    with t2:
        st.dataframe(df_preview, use_container_width=True)
def connect_router_to_patch(patch_port_id: str, router_port_id: str, description: str):
    payload = {
        "local_port": router_port_id,
        "description": description,
        "status": "Patched"
    }
    return update_panel_port(patch_port_id, payload)

def connect_patch_to_patch(port_a_id: str, port_b_id: str, description: str):
    # Side A
    payload_a = {"remote_port": port_b_id, "status": "Connected", "description": description}
    success_a, msg_a = update_panel_port(port_a_id, payload_a)
    if not success_a: return False, msg_a

    # Side B (The Symmetrical Update)
    payload_b = {"remote_port": port_a_id, "status": "Connected", "description": description}
    return update_panel_port(port_b_id, payload_b)

def process_execution(rows, mode):
    # SAFETY GUARD: Prevent NoneType Error
    if rows is None:
        st.warning("⚠️ No rows selected.")
        return

    selected_list = [rows] if isinstance(rows, dict) else rows
    if not selected_list: return

    success_count = 0
    for row in selected_list:
        id_a = row.get("Resolved_ID_A")
        id_b = row.get("Resolved_ID_B")
        desc = row.get("Proposed_Description")
        is_b_pp = str(row.get("Is_B_Patch_Panel")).lower() == 'true'

        try:
            if is_b_pp:
                success, msg = connect_patch_to_patch(id_a, id_b, desc)
            elif id_b and id_b != "None":
                success, msg = connect_router_to_patch(id_a, id_b, desc)
            else:
                success, msg = connect_Xconnect_to_patch(id_a, {})

            if success: success_count += 1
        except Exception as e:
            MessageHandler.add(f"❌ Error: {e}", "error")

    if success_count > 0:
        st.success(f"Processed {success_count} connections.")
        st.session_state.conn_preview = None # Force refresh on next load
        st.rerun()

def connect_Xconnect_to_patch(port_a_id: str, metadata: dict):
    return True, "UC#3 Placeholder"