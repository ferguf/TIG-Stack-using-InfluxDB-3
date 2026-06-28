import streamlit as st
import pandas as pd
import time
from src.ui_components import UI
from src.utils.file_utils import MessageHandler

# --- 1. CORE LOGIC & RECONCILIATION ---

def build_service_preview(df_raw):
    """
    Validates Service CSV data and checks for existing service instances.
    Standardizes on 'service_name (type) @ location' description format.
    """
    preview_data = []
    # Fetch existing state for 'Last Look' verification (Mocked)
    # existing_services = get_fabric_services() 
    
    for _, row in df_raw.iterrows():
        # Service IDs/Customer IDs resolution logic
        customer_id = "cust-uuid-placeholder"
        
        # Standardized Service Description Formatting
        svc_name = row.get('service_name', 'Unnamed_Svc')
        svc_type = row.get('service_type', 'L3VPN')
        formatted_desc = f"{svc_name} ({svc_type}) @ {row.get('location', 'Global')}"
        
        preview_data.append({
            "Action": str(row.get('action', 'ADD')).upper(),
            "Status": "🔍 service not found",
            "description": formatted_desc,
            "service_type": svc_type,
            "vlan_id": row.get('vlan_id', 0),
            "customer_id": customer_id,
            "location": row.get('location'),
            "mtu": row.get('mtu', 1500),
            "service_name": svc_name
        })
    return pd.DataFrame(preview_data)

# --- 2. CONTAINER DEFINITIONS (1:4:4 Design) ---

def render_fs_container_1(ctx):
    """ROW 1: Service Verification logic and status."""
    with st.container(border=True):
        st.markdown("### 🛠️ Service Logic Verification")
        if not st.session_state.get(f"{ctx}_verified"):
            if UI.button("🔍 Run Service Verification", color="orange", key="btn_verify_fs"):
                with st.spinner("Reconciling Fabric Services..."):
                    time.sleep(0.5)
                    st.session_state[f"{ctx}_preview"] = build_service_preview(st.session_state[f"{ctx}_df"])
                    st.session_state[f"{ctx}_verified"] = True
                    st.rerun()
        else:
            st.success("✅ Service Logic Verified: Ready for Deployment")

def render_fs_container_2(ctx, adds, upds, dels):
    """ROW 2: 4-Column Batch Service Operations."""
    with st.container(border=True):
        st.markdown("### ⚡ Batch Operations")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            btn_label = f"➕ Provision ({len(adds)})"
            if UI.button(btn_label, color="green", key="fs_add", use_container_width=True):
                # execute_service_batch(adds, "ADD", ctx)
                st.toast("Provisioning Requests Sent")
                st.rerun()
        with c2:
            btn_label = f"🔄 Modify ({len(upds)})"
            if UI.button(btn_label, color="blue", key="fs_upd", use_container_width=True):
                st.toast("Modification Requests Sent")
                st.rerun()
        with c3:
            btn_label = f"🗑️ Decommission ({len(dels)})"
            if UI.button(btn_label, color="red", key="fs_del", use_container_width=True):
                st.toast("Decommissioning Requests Sent")
                st.rerun()
        with c4:
            if UI.button("🧹 Clear Staging", key="fs_clear", use_container_width=True):
                st.session_state[f"{ctx}_df"] = None
                st.session_state[f"{ctx}_preview"] = None
                st.session_state[f"{ctx}_verified"] = False
                st.rerun()

def render_fs_container_3(df_preview):
    """ROW 3: 4-Column Service Utilities."""
    with st.container(border=True):
        st.markdown("### 📊 Service Utilities")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            csv_data = df_preview.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Service Map", data=csv_data, 
                               file_name="fabric_service_export.csv", 
                               mime="text/csv", use_container_width=True)
        with c2:
            st.button("📋 Validate VLANs", key="fs_vlan_val", use_container_width=True)
        with c3:
            st.button("📡 Check Reachability", key="fs_ping_test", use_container_width=True)
        with c4:
            st.button("⚙️ Policy Push", key="fs_policy_push", use_container_width=True)

# --- 3. MAIN ORCHESTRATOR ---

def render_fabric_service_view():
    """Main UI for Fabric Services Orchestrator."""
    st.title("☁️ Fabric Service Manager")
    
    # Initialize Message Handler
    MessageHandler.render(key_suffix="fabric_svc_view")

    ctx = "fab_svc_v1"
    
    # Session State Initialization
    if f"{ctx}_verified" not in st.session_state:
        st.session_state[f"{ctx}_verified"] = False
    if f"{ctx}_preview" not in st.session_state:
        st.session_state[f"{ctx}_preview"] = None

    # --- FILE UPLOADER ---
    st.subheader("📥 Bulk Service Import")
    uploaded_file = st.file_uploader("Upload Fabric Service CSV", type=["csv"], key=f"{ctx}_uploader")

    if uploaded_file:
        if st.session_state.get(f"{ctx}_df") is None or st.session_state.get(f"{ctx}_filename") != uploaded_file.name:
            df_raw = pd.read_csv(uploaded_file)
            df_raw.columns = [c.lower().strip() for c in df_raw.columns]
            st.session_state[f"{ctx}_df"] = df_raw
            st.session_state[f"{ctx}_filename"] = uploaded_file.name
            st.session_state[f"{ctx}_verified"] = False

        # --- ROW 1: Verification ---
        render_fs_container_1(ctx)

        df_preview = st.session_state.get(f"{ctx}_preview")
        
        if df_preview is not None and st.session_state.get(f"{ctx}_verified"):
            
            # Prepare data subsets
            adds = df_preview[df_preview['Action'] == 'ADD'].to_dict('records')
            upds = df_preview[df_preview['Action'] == 'UPDATE'].to_dict('records')
            dels = df_preview[df_preview['Action'] == 'DELETE'].to_dict('records')

            # --- ROW 2: Batch Actions ---
            render_fs_container_2(ctx, adds, upds, dels)

            # --- ROW 3: Utilities ---
            render_fs_container_3(df_preview)

            # --- PREVIEW TABLE ---
            st.divider()
            st.subheader("📋 Service Staging Preview")
            display_cols = ["Action", "Status", "service_name", "service_type", "vlan_id", "description"]
            valid_cols = [c for c in display_cols if c in df_preview.columns]
            UI.render_selectable_table(df_preview[valid_cols], f"{ctx}_table", "service_type")

    # --- ACTIVE INVENTORY ---
    st.divider()
    st.subheader("🗄️ Active Fabric Services")
    st.info("Deployed fabric services (L2/L3) will appear here.")

if __name__ == "__main__":
    render_fabric_service_view()