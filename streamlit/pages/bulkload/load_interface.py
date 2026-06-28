import streamlit as st
import pandas as pd
import time
from src.ui_components import UI
from src.utils.file_utils import MessageHandler

# --- 1. CORE LOGIC & RECONCILIATION ---

def build_interface_preview(df_raw):
    """
    Validates CSV data and checks for existing logical interfaces.
    Standardizes on 'device_name : port_name (ip_address)' description format.
    """
    preview_data = []
    # Fetch existing state for 'Last Look' verification (Mocked)
    # existing_interfaces = get_device_interfaces() 
    
    for _, row in df_raw.iterrows():
        # TODO: Implement Port UUID Resolution logic based on device/port name
        port_id = "port-uuid-placeholder"
        
        # Standardized Interface Description Formatting
        dev_name = row.get('device_name', 'Unknown_Dev')
        port_name = row.get('port_name', 'Unknown_Port')
        ip_addr = row.get('ip_address', 'Unnumbered')
        formatted_desc = f"{dev_name} : {port_name} ({ip_addr})"
        
        preview_data.append({
            "Action": str(row.get('action', 'ADD')).upper(),
            "Status": "🔍 interface not found",
            "description": formatted_desc,
            "ip_address": ip_addr,
            "subnet_mask": row.get('subnet_mask', '255.255.255.0'),
            "mtu": row.get('mtu', 1500),
            "admin_state": row.get('admin_state', 'up'),
            "port_id": port_id,
            "device_name": dev_name,
            "port_name": port_name
        })
    return pd.DataFrame(preview_data)

# --- 2. CONTAINER DEFINITIONS (1:4:4 Design) ---

def render_int_container_1(ctx):
    """ROW 1: Interface Verification logic and status."""
    with st.container(border=True):
        st.markdown("### 🛠️ Interface Logic Verification")
        if not st.session_state.get(f"{ctx}_verified"):
            if UI.button("🔍 Run Interface Verification", color="orange", key="btn_verify_int"):
                with st.spinner("Reconciling Logical Interfaces..."):
                    time.sleep(0.5)
                    st.session_state[f"{ctx}_preview"] = build_interface_preview(st.session_state[f"{ctx}_df"])
                    st.session_state[f"{ctx}_verified"] = True
                    st.rerun()
        else:
            st.success("✅ Interface Logic Verified: Ready for Configuration Push")

def render_int_container_2(ctx, adds, upds, dels):
    """ROW 2: 4-Column Batch Interface Operations."""
    with st.container(border=True):
        st.markdown("### ⚡ Batch Operations")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            btn_label = f"➕ Create ({len(adds)})"
            if UI.button(btn_label, color="green", key="int_add", use_container_width=True):
                # execute_interface_batch(adds, "ADD", ctx)
                st.toast("Interface Creation Initiated")
                st.rerun()
        with c2:
            btn_label = f"🔄 Update ({len(upds)})"
            if UI.button(btn_label, color="blue", key="int_upd", use_container_width=True):
                st.toast("Interface Updates Initiated")
                st.rerun()
        with c3:
            btn_label = f"🗑️ Remove ({len(dels)})"
            if UI.button(btn_label, color="red", key="int_del", use_container_width=True):
                st.toast("Interface Removal Initiated")
                st.rerun()
        with c4:
            if UI.button("🧹 Clear Staging", key="int_clear", use_container_width=True):
                st.session_state[f"{ctx}_df"] = None
                st.session_state[f"{ctx}_preview"] = None
                st.session_state[f"{ctx}_verified"] = False
                st.rerun()

def render_int_container_3(df_preview):
    """ROW 3: 4-Column Interface Utilities."""
    with st.container(border=True):
        st.markdown("### 📊 Interface Utilities")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            csv_data = df_preview.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Config Map", data=csv_data, 
                               file_name="interface_config_export.csv", 
                               mime="text/csv", use_container_width=True)
        with c2:
            st.button("📋 Validate IP Plan", key="int_ip_val", use_container_width=True)
        with c3:
            st.button("📡 Check Link Status", key="int_link_check", use_container_width=True)
        with c4:
            st.button("⚙️ Apply ACLs", key="int_acl_push", use_container_width=True)

# --- 3. MAIN ORCHESTRATOR ---

def render_interface_view():
    """Main UI for Interface Orchestrator."""
    st.title("🔗 Interface Manager")
    
    # Initialize Message Handler
    MessageHandler.render(key_suffix="int_mgr_view")

    ctx = "int_mgr_v1"
    
    # Session State Initialization
    if f"{ctx}_verified" not in st.session_state:
        st.session_state[f"{ctx}_verified"] = False
    if f"{ctx}_preview" not in st.session_state:
        st.session_state[f"{ctx}_preview"] = None

    # --- FILE UPLOADER ---
    st.subheader("📥 Bulk Interface Import")
    uploaded_file = st.file_uploader("Upload Interface CSV", type=["csv"], key=f"{ctx}_uploader")

    if uploaded_file:
        if st.session_state.get(f"{ctx}_df") is None or st.session_state.get(f"{ctx}_filename") != uploaded_file.name:
            df_raw = pd.read_csv(uploaded_file)
            df_raw.columns = [c.lower().strip() for c in df_raw.columns]
            st.session_state[f"{ctx}_df"] = df_raw
            st.session_state[f"{ctx}_filename"] = uploaded_file.name
            st.session_state[f"{ctx}_verified"] = False

        # --- ROW 1: Verification ---
        render_int_container_1(ctx)

        df_preview = st.session_state.get(f"{ctx}_preview")
        
        if df_preview is not None and st.session_state.get(f"{ctx}_verified"):
            
            # Prepare data subsets
            adds = df_preview[df_preview['Action'] == 'ADD'].to_dict('records')
            upds = df_preview[df_preview['Action'] == 'UPDATE'].to_dict('records')
            dels = df_preview[df_preview['Action'] == 'DELETE'].to_dict('records')

            # --- ROW 2: Batch Actions ---
            render_int_container_2(ctx, adds, upds, dels)

            # --- ROW 3: Utilities ---
            render_int_container_3(df_preview)

            # --- PREVIEW TABLE ---
            st.divider()
            st.subheader("📋 Interface Staging Preview")
            display_cols = ["Action", "Status", "device_name", "port_name", "ip_address", "description"]
            valid_cols = [c for c in display_cols if c in df_preview.columns]
            UI.render_selectable_table(df_preview[valid_cols], f"{ctx}_table", "device_name")

    # --- ACTIVE INVENTORY ---
    st.divider()
    st.subheader("🗄️ Active Logical Interfaces")
    st.info("Live logical interface configurations will appear here.")

if __name__ == "__main__":
    render_interface_view()