import re 
import streamlit as st
from src.ui_components import UI

BW_OPTIONS = {
    "10M": 10, "20M": 20, "30M": 30, "50M": 50, "100M": 100, 
    "200M": 200, "300M": 300, "500M": 500, "1G": 1000, 
    "2G": 2000, "3G": 3000, "5G": 5000, "10G": 10000, 
    "20G": 20000, "30G": 30000, "50G": 50000, "100G": 100000
}

def create_customer_form():
    """Renders the UI for creating a new customer with custom colored buttons."""
    with st.expander("📝 Create New Customer", expanded=True):
        # Using a container with a border instead of st.form
        with st.container(border=True):
            st.markdown("### Customer Details")
            
            # Note: We add keys to inputs to preserve state outside of a form
            name = st.text_input("Customer Name", placeholder="e.g. Acme Corp", key="create_cust_name")
            acc_id = st.text_input("Account ID", placeholder="e.g. ACC-12345", key="create_cust_acc")
            
            st.markdown("---")
            col1, col2, _ = st.columns([1, 1, 3])
            
            with col1:
                # Save button using your UI class (Green)
                if UI.button("Save", color="green", key="save_new_customer"):
                    if name and acc_id:
                        return {"customer_name": name, "account_id": acc_id}
                    else:
                        st.warning("All fields are required.")
            
            with col2:
                # Cancel button using your UI class (Red)
                if UI.button("Cancel", color="red", key="cancel_new_customer"):
                    st.session_state["show_create_form"] = False
                    st.rerun()
                
    return None

def update_customer_form(record):
    """Renders the UI for updating an existing customer with styled buttons."""
    if not record:
        return None

    with st.expander(f"🔄 Editing: {record['account_id']}", expanded=True):
        with st.container(border=True):
            st.markdown("### Update Details")
            
            # Using keys derived from account_id to ensure state uniqueness
            name = st.text_input(
                "Customer Name", 
                value=record.get("customer_name", ""), 
                key=f"upd_name_{record['account_id']}"
            )
            acc_id = st.text_input(
                "Account ID", 
                value=record.get("account_id", ""), 
                disabled=True,
                key=f"upd_acc_{record['account_id']}"
            )
            
            st.markdown("---")
            col1, col2, _ = st.columns([1, 1, 3])
            
            with col1:
                # Save changes is Green
                if UI.button("Save Changes", color="green", key=f"save_upd_{record['account_id']}"):
                    if name:
                        return {"customer_name": name, "account_id": acc_id}
                    else:
                        st.warning("Customer Name cannot be empty.")
            
            with col2:
                # Cancel update is Amber
                if UI.button("Cancel", color="amber", key=f"cancel_upd_{record['account_id']}"):
                    st.session_state["show_update_form"] = False
                    st.rerun()
                    
    return None

def create_fabric_service_form():
    """
    Renders the UI for provisioning a new Fabric Service using container/border 
    style to support custom colored UI buttons.
    """
    with st.expander("🚀 Provision New Fabric Service", expanded=True):
        with st.container(border=True):
            st.markdown("### Service Details")
            
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Service Name*", placeholder="e.g.,Finn tech  L3VPN Prod", key="fab_prov_name")
                s_type = st.selectbox("Service Type", ["IPVPN","MCGW", "Eline EVPL", "Eline EPL", "EVPLAN","EPLAN", "DIA", "IOD" ], key="fab_prov_type")
            with col2:
                alias = st.text_input("Alias", key="fab_prov_alias")
                rt = st.text_input("Route Target", placeholder="3549:100001", key="fab_prov_rt")
            
            desc = st.text_area("Description", key="fab_prov_desc")
            
            st.markdown("---")
            col1, col2, _ = st.columns([1, 1, 3])
            
            with col1:
                # Save/Launch button (Green)
                if UI.button("Create Fabric Service", color="green", key="btn_confirm_launch_fab"):
                    if name:
                        return {
                            "service_name": name,
                            "service_type": s_type,
                            "service_alias": alias,
                            "route_target": rt,
                            "service_description": desc,
                            "health_status": 4
                        }
                    else:
                        st.warning("Service Name is required.")
            
            with col2:
                # Cancel button (Red)
                if UI.button("Cancel", color="red", key="btn_cancel_launch_fab"):
                    st.session_state["fab_show_provision"] = False
                    st.rerun()
                    
    return None

def update_fabric_service_form(record):
    """Simple UI for updating an existing Fabric Service."""
    sid = record.get("service_id")
    
    with st.expander(f"⚙️ Edit {record.get('service_name')}", expanded=True):
        with st.container(border=True):
            # Fields
            new_name = st.text_input("Service Name*", value=record.get("service_name", ""), key=f"un_{sid}")
            new_alias = st.text_input("Alias", value=record.get("service_alias", ""), key=f"ua_{sid}")
            new_rt = st.text_input("Route Target", value=record.get("route_target", ""), key=f"urt_{sid}")
            new_desc = st.text_area("Description", value=record.get("service_description", ""), key=f"ud_{sid}")
            
            # Simple 0-4 Slider
            new_health = st.slider("Health Metric", 0, 4, value=int(record.get("health_status", 4)), key=f"uh_{sid}")

            st.markdown("---")
            col1, col2, _ = st.columns([1, 1, 3])
            
            with col1:
                if UI.button("Update", color="green", key=f"bs_{sid}"):
                    if new_name:
                        return {
                            "service_name": new_name,
                            "service_type": record.get("service_type"),
                            "service_alias": new_alias,
                            "route_target": new_rt,
                            "service_description": new_desc,
                            "health_status": int(4)
                        }
                    else:
                        st.warning("Name is required.")
            
            with col2:
                if UI.button("Cancel", color="red", key=f"bc_{sid}"):
                    st.session_state["fs_show_update"] = False
                    st.rerun()
    return None

def parse_vlan_input(input_str: str) -> str:
    """
    Standardizes inputs like '1, 2, 3', '1-100', or '[1,2,4]' 
    into a clean comma-separated string: '1,2,4' or '1-100'.
    """
    if not input_str or input_str.lower() == "not configured":
        return ""
    
    # Remove brackets if user provided [1,2,4]
    sanitized = input_str.replace("[", "").replace("]", "")
    
    # Remove extra whitespace
    sanitized = "".join(sanitized.split())
    
    return sanitized

def create_fabric_connection_form(service_id, parent_service_record):
    """
    Renders a simplified UI for initiating a new Fabric Connection.
    Now uses the BW_OPTIONS selectbox for bandwidth.
    """
    parent_type = parent_service_record.get("service_type", "IPVPN")
    parent_name = parent_service_record.get("service_name", "Default_Service")

    with st.expander(f"🚀 Initialize Connection for {parent_name}", expanded=True):
        with st.container(border=True):
            st.markdown("### Primary Connection Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(
                    "Connection Name*", 
                    value=f"{parent_type}_Conn", 
                    key="f_conn_name"
                )
            
            with col2:
                # NEW: Using BW_OPTIONS selectbox
                bw_label = st.selectbox(
                    "Service Bandwidth*", 
                    options=list(BW_OPTIONS.keys()), 
                    index=4, # Defaults to 100M
                    key="f_conn_bw_labels"
                )

            st.markdown("---")
            btn_col1, btn_col2, _ = st.columns([1.5, 1, 3])
            
            with btn_col1:
                if UI.button("Initialize Connection", color="green", key="btn_submit_conn"):
                    if name:
                        return {
                            "service_id": service_id,
                            "connection_name": name,
                            "service_bw": BW_OPTIONS[bw_label], # Save integer value
                            "connector_a_id": "00000000-0000-0000-0000-000000000000",
                            "connector_b_id": "00000000-0000-0000-0000-000000000000",
                            "connector_a_table": "ports",
                            "connector_b_table": "ports",
                            "vrf_name": parent_name,
                            "connection_status": "Not Configured",
                            "s_vlan": 0,
                            "c_vlan_list": "",
                            "health_status": 4
                        }
                    else:
                        st.warning("Please provide a valid Connection Name.")
            
            with btn_col2:
                if UI.button("Cancel", color="red", key="btn_cancel_conn"):
                    st.session_state["conn_show_provision"] = False
                    st.rerun()
                    
    return None

def create_fabric_connection_form(service_id, parent_service_record):
    """
    Renders UI for initiating a new Fabric Connection.
    """
    parent_type = parent_service_record.get("service_type", "IPVPN")
    parent_name = parent_service_record.get("service_name", "Default_Service")

    with st.expander(f"🚀 Initialize Connection for {parent_name}", expanded=True):
        with st.container(border=True):
            st.markdown("### Primary Connection Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Connection Name*", value=f"{parent_type}_Conn", key="f_conn_name")
            
            with col2:
                # Use global BW_OPTIONS
                bw_label = st.selectbox(
                    "Service Bandwidth*", 
                    options=list(BW_OPTIONS.keys()), 
                    index=4, 
                    key="f_conn_bw_labels"
                )

            st.markdown("---")
            btn_col1, btn_col2, _ = st.columns([1.5, 1, 3])
            
            with btn_col1:
                if UI.button("Initialize Connection", color="green", key="btn_submit_conn"):
                    if name:
                        return {
                            "service_id": service_id,
                            "connection_name": name,
                            "service_bw": BW_OPTIONS[bw_label],
                            "connector_a_id": "00000000-0000-0000-0000-000000000000",
                            "connector_b_id": "00000000-0000-0000-0000-000000000000",
                            "connector_a_table": "ports",
                            "connector_b_table": "ports",
                            "vrf_name": parent_name,
                            "connection_status": "Not Configured",
                            "s_vlan": 0,
                            "c_vlan_list": "",
                            "health_status": 4
                        }
                    else:
                        st.warning("Please provide a valid Connection Name.")
            
            with btn_col2:
                if UI.button("Cancel", color="red", key="btn_cancel_conn"):
                    st.session_state["conn_show_provision"] = False
                    st.rerun()
                    
    return None

def update_fabric_connection_form(record):
    """
    Form to update an existing Fabric Connection.
    Uses BW_OPTIONS and a local REVERSE_BW map to pre-populate selection.
    """
    # Create the reverse mapping locally to avoid scope errors
    reverse_bw = {v: k for k, v in BW_OPTIONS.items()}

    st.markdown("### 📝 Update Connection Parameters")

    # 1. Bandwidth Selection Logic
    raw_bw = record.get("service_bw")
    try:
        # Robust conversion to int
        if raw_bw is None or str(raw_bw).strip().lower() in ["none", "null", ""]:
            current_val = 100
        else:
            current_val = int(float(raw_bw))
    except (ValueError, TypeError):
        current_val = 100

    # Match numeric value to label. Default to 100M if value not found in dict.
    current_label = reverse_bw.get(current_val, "100M")
    bw_keys = list(BW_OPTIONS.keys())
    
    try:
        bw_idx = bw_keys.index(current_label)
    except ValueError:
        bw_idx = 4 

    # 2. Health Status Safety
    raw_health = record.get("health_status")
    try:
        curr_health = int(raw_health) if raw_health is not None else 4
    except (ValueError, TypeError):
        curr_health = 4

    # 3. Form Layout
    with st.form(key=f"upd_fc_form_{record.get('connection_id')}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Connection Name", value=record.get("connection_name", ""))
            selected_bw_label = st.selectbox("Service Bandwidth", options=bw_keys, index=bw_idx)
            new_vrf = st.text_input("VRF Name", value=record.get("vrf_name", "") if record.get("vrf_name") else "")

        with col2:
            status_options = ["Pending", "Provisioning", "Active", "Down", "Degraded"]
            current_status = record.get("connection_status", "Pending")
            
            try:
                status_idx = status_options.index(current_status)
            except ValueError:
                status_idx = 0
                
            new_status = st.selectbox("Connection Status", options=status_options, index=status_idx)
            new_svlan = st.text_input("S-VLAN", value=record.get("s_vlan", "") if record.get("s_vlan") else "")
            new_health = st.slider("Health Status Score", 0, 5, value=curr_health)

        st.divider()
        new_cvlan = st.text_area("C-VLAN List", value=record.get("c_vlan_list", "not configured"))

        submit = st.form_submit_button("Save Connection Changes", type="primary")

        if submit:
            return {
                "connection_name": new_name,
                "service_bw": BW_OPTIONS[selected_bw_label],
                "vrf_name": new_vrf if new_vrf else None,
                "connection_status": new_status,
                "s_vlan": new_svlan if new_svlan else None,
                "c_vlan_list": new_cvlan,
                "health_status": new_health
            }
    
    return None