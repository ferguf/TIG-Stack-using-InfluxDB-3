import streamlit as st
import pandas as pd
from src.state_managers import FabricStateManager
from src.api_client import (
    get_ports_by_customer, 
    update_port_assignment,
    get_all_devices, 
    get_ports_by_device,
    get_connections_by_service,
    update_fabric_connection
)
from src.ui_components import UI
from src.ui_messages import MessageCenter

def prepare_display_df(df_raw):
    """Utility to filter and rename columns for the Port table UI."""
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    display_cols = {
        "device_name": "Device",
        "port_name": "Port",
        "port_speed": "Speed",
        "port_type": "Type",
        "port_service_status": "Service Status",
        "port_health_status": "Health",
        "physical_type": "Structure", 
        "port_id": "port_id"
    }
    existing_cols = [c for c in display_cols.keys() if c in df_raw.columns]
    return df_raw[existing_cols].copy().rename(columns=display_cols)

def render_management_view(record, customer_id):
    """Tier 3: Port Management (Configure / Unassign)."""
    pid = record.get("port_id")
    device = record.get('device_name', 'Unknown')
    port = record.get('port_name', 'Unknown')
    display_name = f"{device} - {port}"
    
    st.info(f"📍 Selected Port: **{display_name}**")
    
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        if UI.button("🔄 Configure", color="amber", key=f"port_upd_{pid}"):
            st.session_state["port_show_update"] = True
            st.rerun()
    with col2:
        if UI.button("🗑️ Unassign", color="red", key=f"port_del_{pid}"):
            st.session_state["port_confirm_delete"] = True
            st.rerun()

    if st.session_state.get("port_confirm_delete"):
        st.divider()
        with st.container(border=True):
            st.error(f"⚠️ Confirm Removal: Unassign **{display_name}**?")
            c1, c2, _ = st.columns([1, 1, 2])
            with c1:
                if UI.button("Yes, Unassign", color="red", key=f"conf_del_{pid}"):
                    try:
                        payload = {
                            "customer_id": None,
                            "port_service_status": "Available",
                            "port_type": "Physical"
                        }
                        update_port_assignment(pid, payload)
                        
                        # FIX: Clear Global Inspector State for Tier 4
                        manager = FabricStateManager()
                        manager.sync_selection("port", None, "port_id")
                        st.session_state["port_active_record"] = None
                        
                        if f"port_cache_{customer_id}" in st.session_state:
                            del st.session_state[f"port_cache_{customer_id}"]
                        
                        MessageCenter.set_success(f"🗑️ Port {display_name} unassigned.")
                        st.session_state["port_confirm_delete"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Unassign failed: {e}")
            with c2:
                if UI.button("Cancel", color="blue", key=f"can_del_{pid}"):
                    st.session_state["port_confirm_delete"] = False
                    st.rerun()

def render_configure_view(port_record, customer_id):
    """Tier 4: Port Configuration View. Links a physical Port to a logical Connection."""
    manager = FabricStateManager()
    pid = port_record.get("port_id")
    device = port_record.get('device_name', 'N/A')
    port_name = port_record.get('port_name', 'N/A')

    st.markdown(f"### ⚙️ Configure Port: {device} - {port_name}")
    
    active_service_id = manager.get_active_id("fs")
    
    if not active_service_id or str(active_service_id) == "None":
        st.warning("⚠️ **Service Context Missing.**")
        st.info("Please select a Fabric Service in the 'Services' tab first.")
        if st.button("⬅️ Back to Port List", key="port_cfg_back_no_fs"):
            st.session_state["port_show_update"] = False
            st.rerun()
        return

    try:
        raw_conns = get_connections_by_service(active_service_id)
        connections = raw_conns if isinstance(raw_conns, list) else ([raw_conns] if raw_conns else [])
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return

    if not connections:
        st.error(f"❌ No Fabric Connections found for Service: {active_service_id}")
        if st.button("⬅️ Back to Port List", key="port_cfg_back_no_conn"):
            st.session_state["port_show_update"] = False
            st.rerun()
        return

    conn_options = {c['connection_name']: c for c in connections if 'connection_name' in c}
    selected_conn_name = st.selectbox("Select Target Fabric Connection", options=list(conn_options.keys()))
    selected_conn = conn_options[selected_conn_name]
    side = st.radio("Assign to side:", ["Connector A", "Connector B"], horizontal=True)

    st.divider()
    col1, col2, _ = st.columns([1.5, 1, 3])

    with col1:
        if UI.button("🚀 Activate & Map Port", color="green", key=f"conf_act_{pid}"):
            try:
                # Update Port
                port_payload = {"customer_id": customer_id, "port_service_status": "Active", "port_type": "Fabric Port"}
                update_port_assignment(pid, port_payload)

                # Update Connection
                conn_id = selected_conn['connection_id']
                conn_update_payload = dict(selected_conn)
                if side == "Connector A":
                    conn_update_payload["connector_a_id"] = pid
                    conn_update_payload["connector_a_table"] = "ports"
                else:
                    conn_update_payload["connector_b_id"] = pid
                    conn_update_payload["connector_b_table"] = "ports"
                
                conn_update_payload.pop("Select", None)
                update_fabric_connection(conn_id, conn_update_payload)

                # Invalidate caches
                if f"port_cache_{customer_id}" in st.session_state:
                    del st.session_state[f"port_cache_{customer_id}"]
                if f"conn_cache_{active_service_id}" in st.session_state:
                    del st.session_state[f"conn_cache_{active_service_id}"]
                
                # Update Inspector Record
                st.session_state["port_active_record"] = {**port_record, **port_payload}
                
                MessageCenter.set_success(f"✅ Success! {port_name} Active on {selected_conn_name}")
                st.session_state["port_show_update"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Configuration Failed: {str(e)}")

    with col2:
        if UI.button("Cancel", color="amber", key=f"conf_can_{pid}"):
            st.session_state["port_show_update"] = False
            st.rerun()

def render_assignment_view(customer_id):
    """Workflow to assign a new port from device inventory."""
    st.subheader("🚀 Assign New Port to Customer")
    
    if not st.session_state.get("port_show_assign"):
        if UI.button("➕ Assign New Port", color="green", key="port_t3_btn_new"):
            st.session_state["port_show_assign"] = True
            st.rerun()
    else:
        with st.container(border=True):
            try:
                devices = get_all_devices()
                device_options = {d['device_name']: d['device_id'] for d in devices}
                selected_device_name = st.selectbox("1️⃣ Select Host Device", options=list(device_options.keys()))
                device_id = device_options[selected_device_name]

                if device_id:
                    all_device_ports = get_ports_by_device(device_id)
                    cols = all_device_ports.columns.tolist()
                    cust_key = "customer_id" if "customer_id" in cols else "cusotmer_id"
                    
                    mask = (
                        (all_device_ports['port_service_status'].isin(['Staged', 'Available', 'Ready For Use'])) & 
                        (all_device_ports[cust_key].isna() | (all_device_ports[cust_key] == ""))
                    )                    
                    available_ports = all_device_ports[mask].copy()

                    if available_ports.empty:
                        st.warning(f"No assignable ports found on {selected_device_name}.")
                    else:
                        port_selection = UI.render_selectable_table(
                            df=available_ports[['port_name', 'port_speed', 'port_type', 'port_id']],
                            key_prefix="port_assign_table", id_column_to_hide="port_id"
                        )

                        if port_selection:
                            if UI.button("Confirm Assignment", color="green", key="port_assign_confirm"):
                                payload = {
                                    "customer_id": customer_id, 
                                    "port_service_status": "Assigned", 
                                    "port_type": "Fabric Port"
                                }
                                update_port_assignment(port_selection['port_id'], payload)
                                
                                if f"port_cache_{customer_id}" in st.session_state:
                                    del st.session_state[f"port_cache_{customer_id}"]
                                
                                # Clear active record to force fresh selection
                                st.session_state["port_active_record"] = None
                                st.session_state["port_show_assign"] = False
                                MessageCenter.set_success("Port assigned successfully.")
                                st.rerun()
            except Exception as e:
                st.error(f"Error filtering inventory: {str(e)}")           
                
def show_ports(customer_id):
    """Main Entry Point for Port Tab."""
    manager = FabricStateManager()
    manager.initialize()
    
    fs_record = manager.get_active_record("fs")
    fc_record = manager.get_active_record("fc")

    if not UI.render_service_context(fs_record, fc_record):
        return 

    st.divider()

    cache_key = f"port_cache_{customer_id}"
    if cache_key not in st.session_state:
        df = get_ports_by_customer(customer_id)
        if df is not None and not df.empty:
            df['port_id'] = df['port_id'].astype(str)
        st.session_state[cache_key] = df

    df_raw = st.session_state[cache_key]

    if df_raw is not None and not df_raw.empty:
        selection = UI.render_selectable_table(
            df=prepare_display_df(df_raw), 
            key_prefix="port_t3_main", 
            id_column_to_hide="port_id" 
        )

        if selection:
            selected_id = str(selection.get("port_id"))
            raw_match = df_raw[df_raw['port_id'].astype(str) == selected_id].to_dict('records')
            if raw_match:
                # FIX: Sync the FULL RECORD for the Debugger
                if manager.sync_selection("port", raw_match[0], "port_id"):
                    st.session_state["port_active_record"] = raw_match[0]
                    st.rerun()
        else:
            if manager.sync_selection("port", None, "port_id"):
                st.session_state["port_active_record"] = None
                st.rerun()
    else:
        if manager.sync_selection("port", None, "port_id"):
            st.session_state["port_active_record"] = None
        st.info("ℹ️ No ports currently assigned to this customer.")

    active_port = manager.get_active_record("port")
    
    is_valid_active = False
    if active_port and df_raw is not None and not df_raw.empty:
        is_valid_active = str(active_port['port_id']) in df_raw['port_id'].values

    if is_valid_active:
        if st.session_state.get("port_show_update"):
            render_configure_view(active_port, customer_id)
        else:
            render_management_view(active_port, customer_id)
    else:
        render_assignment_view(customer_id)