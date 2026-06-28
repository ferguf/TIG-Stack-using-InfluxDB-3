import streamlit as st
import pandas as pd
import time
import os
from src.ui_components import UI

# API Methods
from src.utils.api_network import (
    get_devices, 
    post_device, 
    update_device, 
    delete_device
)
from src.utils.api_patch_panel import (
    post_panel_port, 
    get_panel_ports, 
    update_panel_port
)

# File and UI Utilities
from src.utils.file_utils import (
    find_and_read_role_file, 
    normalize_dataframe_columns, 
    sanitize_for_api, 
    MessageHandler,
    clean_device_payload
)
from src.utils.ui_network_forms import apply_device_filters, render_edit_location_form
from pages.bulkload.load_patch_panel_connect import render_connectivity_view
# ----------------------------------------------------------------------
# Logic Orchestration
# ----------------------------------------------------------------------

def run_full_ingestion_chain(row: pd.Series):
    """Creates device shell and iterates through port template."""
    dev_name = str(row.get("device_name", "Unknown"))
    model_name = str(row.get("device_model", "Unknown"))
    
    try:
        payload = clean_device_payload(row.to_dict())
        payload["device_role"] = "FDP"
        
        MessageHandler.add(f"📡 API REQ: Creating device '{dev_name}'", "info")
        res = post_device(payload)
        
        if res:
            dev_id = res.get("device_id") if isinstance(res, dict) else res
            MessageHandler.add(f"✅ API SUCCESS: Device '{dev_name}' created (ID: {dev_id})", "success")
            
            df_ports, filename = find_and_read_role_file(model_name, role="roles")
            
            if df_ports is not None:
                port_payloads = sanitize_for_api(df_ports).to_dict(orient="records")
                port_count = 0
                total_to_add = len(port_payloads)
                
                for i, p in enumerate(port_payloads):
                    p["device_id"] = dev_id
                    success, reason = post_panel_port(p)
                    if success: port_count += 1
                
                msg = f"🔌 RESULT: {port_count}/{total_to_add} ports added to {dev_name}."
                MessageHandler.add(msg, "success" if port_count == total_to_add else "warning")
                return True, msg
            return True, "⚠️ Device created, but blueprint missing."
    except Exception as e:
        MessageHandler.add(f"🔥 CRITICAL EXCEPTION: {str(e)}", "error")
        return False, str(e)
    return False, "❌ Shell creation failed."

def run_full_action_chain(row: pd.Series, existing_records: list):
    """Central router for Add/Update/Delete actions."""
    action = str(row.get("action", "add")).strip().lower()
    dev_name = str(row.get("device_name", "Unknown"))
    device_id = row.get("device_id")
    
    if not device_id and action in ["delete", "remove", "change", "update"]:
        match = next((r for r in existing_records if r.get("device_name") == dev_name), None)
        device_id = match.get("device_id") if match else None

    if action in ["add", "new"]: 
        return run_full_ingestion_chain(row)
    
    if action in ["delete", "remove"]:
        if device_id:
            if delete_device(device_id):
                MessageHandler.add(f"🗑️ Deleted '{dev_name}'", "success")
                return True, "Deleted"
        else:
            MessageHandler.add(f"⚠️ DELETE FAILED: Device '{dev_name}' does not exist.", "error")
            return False, "Not Found"
            
    if action in ["change", "update"]:
        if device_id:
            if update_device(device_id, clean_device_payload(row.to_dict())):
                MessageHandler.add(f"✅ Updated '{dev_name}'", "success")
                return True, "Updated"
        else:
            MessageHandler.add(f"❌ UPDATE FAILED: '{dev_name}' not found. Try 'ADD' instead.", "error")
            return False, "Update Fail"
            
    return False, "Unknown Action"

# ----------------------------------------------------------------------
# UI Sections
# ----------------------------------------------------------------------

def process_bulk_ingestion(df_devices: pd.DataFrame, all_db_records: list):
    """Renders the grid with UI.button color logic."""
    unprocessed = [idx for idx, r in df_devices.iterrows() if f"done_{idx}" not in st.session_state]
    if not unprocessed:
        st.success("✅ All pending actions from CSV processed.")
        return

    st.markdown("### 📋 Pending Action Queue")
    
    if UI.button("🚀 Execute All Actions", color="green", key="bulk_exec_all"):
        for idx in unprocessed:
            success, msg = run_full_action_chain(df_devices.loc[idx], all_db_records)
            if success: st.session_state[f"done_{idx}"] = True
        st.rerun()

    grid = st.columns(2)
    existing_names = [str(r.get("device_name", "")).strip().lower() for r in all_db_records]
    
    for i, idx in enumerate(unprocessed):
        row = df_devices.loc[idx]
        dev_name = str(row.get("device_name", "Unknown"))
        model_slug = str(row.get("device_model", "generic")).lower().replace(' ', '_')
        raw_action = str(row.get("action", "add")).lower()
        
        is_delete = any(x in raw_action for x in ["del", "rem"])
        is_update = any(x in raw_action for x in ["upd", "chan"])
        
        template_filename = f"fdp_{model_slug}.csv"
        file_exists = os.path.exists(f"templates/roles/{template_filename}")
        exists_in_db = dev_name.lower() in existing_names

        with grid[i % 2]:
            with st.container(border=True):
                col_text, col_btn = st.columns([3, 1])
                with col_text:
                    st.markdown(f"**{dev_name}**")
                    st.caption(f"Action: {raw_action.upper()}")
                    if not is_delete: 
                        st.caption(f"{'✅' if file_exists else '❌'} Template: {template_filename}")
                
                with col_btn:
                    st.write("")
                    button_disabled = (not is_delete and not file_exists) or (is_delete and not exists_in_db)
                    
                    if button_disabled:
                        st.button("Blocked", key=f"blk_{idx}", disabled=True)
                    else:
                        label, btn_color = ("Delete", "red") if is_delete else (("Update", "amber") if is_update else ("Add", "green"))
                        if UI.button(label, color=btn_color, key=f"btn_{idx}"):
                            success, _ = run_full_action_chain(row, all_db_records)
                            if success: 
                                st.session_state[f"done_{idx}"] = True
                                st.rerun()

def render_fdp_port_display(device_id: str, device_name: str):
    """Renders the numerical-sorted port table."""
    st.markdown(f"#### 🔌 Port Interfaces: {device_name}")
    ports_data = get_panel_ports(device_id)
    if not ports_data:
        st.warning("No ports found.")
        return
    df_ports = pd.DataFrame(ports_data)
    if "port_number" in df_ports.columns:
        df_ports["port_number"] = pd.to_numeric(df_ports["port_number"], errors='coerce')
        df_ports = df_ports.sort_values("port_number")
    st.dataframe(df_ports, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# View Orchestration
# ----------------------------------------------------------------------

def render_patchpanel_tabs():
    """Main entry point orchestrating the FDP Lifecycle tabs."""
    st.title("🔌 FDP Lifecycle Manager")
    
    # 1. Global Message/Log Feed (Rendered once at top level with unique key)
    MessageHandler.initialize()
    MessageHandler.render(key_suffix="patch_main")

    # 2. Create Primary Tabs
    tab1, tab2 = st.tabs(["📥 Load Patch Panel", "🔗 Connect Patch Panel"])

    with tab1:
        render_load_data_view()

    with tab2:
        render_connectivity_view()

def render_load_data_view():
    """Permanent Bulk Load + Inventory Management View."""
    # 1. Permanent Bulk Load Section
    st.markdown("### 📤 Bulk CSV Ingestion")
    uploaded_file = st.file_uploader("Drop device blueprint CSV here", type=["csv"], key="fdp_bulk_uploader")
    
    with st.spinner("Analyzing Database..."):
        all_db = get_devices() or []

    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        df_norm = normalize_dataframe_columns(df_upload)
        process_bulk_ingestion(df_norm, all_db)
    
    st.divider()

    # 2. Permanent Inventory Manager
    st.subheader("🗄️ Active FDP Inventory")
    fdp_records = [r for r in all_db if str(r.get('device_role', '')).upper() == "FDP"]
    
    if fdp_records:
        df_fdp = pd.DataFrame(fdp_records)
        df_filtered = apply_device_filters(df_fdp, "fdp_inv_main")
        
        if df_filtered is not None and not df_filtered.empty:
            selection = UI.render_selectable_table(df_filtered, "fdp_table", "device_id")
            
            if selection:
                st.divider()
                dev_id, dev_name = selection.get("device_id"), selection.get("device_name", "Unknown")
                t1, t2, t3 = st.tabs(["🔌 Ports", "📍 Location", "🛠️ Admin"])
                
                with t1: render_fdp_port_display(dev_id, dev_name)
                with t2: render_edit_location_form(selection)
                with t3: 
                    st.warning(f"Danger Zone: Deleting {dev_name}")
                    if st.checkbox("Confirm permanent deletion", key=f"conf_del_{dev_id}"):
                        if UI.button("🗑️ Delete Device", color="red", key=f"admin_del_{dev_id}"):
                            if delete_device(dev_id):
                                st.success("Deleted!")
                                st.rerun()
    else:
        st.info("No FDPs in database.")

if __name__ == "__main__":
    render_patchpanel_tabs()