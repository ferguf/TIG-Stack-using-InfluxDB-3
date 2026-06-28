import streamlit as st
import pandas as pd
import time
from src.ui_components import UI
from src.utils.file_utils import MessageHandler

# --- 1. CORE LOGIC & RECONCILIATION ---

def build_hardware_preview(df_raw):
    """
    Validates Hardware CSV data and checks for existing serial numbers.
    Standardized description: 'model_name (serial_number) @ location'
    """
    preview_data = []
    # Fetch existing hardware from DB (Mocked)
    # existing_hw = get_hardware_inventory() 
    
    for _, row in df_raw.iterrows():
        # TODO: Implement Device UUID Resolution if this hardware is already racked
        device_id = "device-uuid-placeholder"
        
        # Standardized Hardware Description Formatting
        model = row.get('model_name', 'Unknown_Model')
        sn = row.get('serial_number', 'No_SN')
        loc = row.get('location', 'Warehouse')
        formatted_desc = f"{model} ({sn}) @ {loc}"
        
        preview_data.append({
            "Action": str(row.get('action', 'ADD')).upper(),
            "Status": "🔍 asset not found",
            "description": formatted_desc,
            "serial_number": sn,
            "asset_tag": row.get('asset_tag', 'N/A'),
            "model_name": model,
            "location": loc,
            "hardware_role": row.get('role', 'Spare'),
            "device_id": device_id
        })
    return pd.DataFrame(preview_data)

# --- 2. CONTAINER DEFINITIONS (1:4:4 Design) ---

def render_hw_container_1(ctx):
    """ROW 1: Hardware Verification logic and status."""
    with st.container(border=True):
        st.markdown("### 🛠️ Hardware Asset Verification")
        if not st.session_state.get(f"{ctx}_verified"):
            if UI.button("🔍 Run Asset Verification", color="orange", key="btn_verify_hw"):
                with st.spinner("Checking Serial Number Registry..."):
                    time.sleep(0.5)
                    st.session_state[f"{ctx}_preview"] = build_hardware_preview(st.session_state[f"{ctx}_df"])
                    st.session_state[f"{ctx}_verified"] = True
                    st.rerun()
        else:
            st.success("✅ Asset Logic Verified: Ready for Inventory Load")

def render_hw_container_2(ctx, adds, upds, dels):
    """ROW 2: 4-Column Batch Hardware Operations."""
    with st.container(border=True):
        st.markdown("### ⚡ Batch Operations")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            btn_label = f"➕ Register ({len(adds)})"
            if UI.button(btn_label, color="green", key="hw_add", use_container_width=True):
                # execute_hardware_batch(adds, "ADD", ctx)
                st.toast("Registration Initiated")
                st.rerun()
        with c2:
            btn_label = f"🔄 Update ({len(upds)})"
            if UI.button(btn_label, color="blue", key="hw_upd", use_container_width=True):
                st.toast("Asset Records Updated")
                st.rerun()
        with c3:
            btn_label = f"🗑️ Decommission ({len(dels)})"
            if UI.button(btn_label, color="red", key="hw_del", use_container_width=True):
                st.toast("Asset Removal Initiated")
                st.rerun()
        with c4:
            if UI.button("🧹 Clear Staging", key="hw_clear", use_container_width=True):
                st.session_state[f"{ctx}_df"] = None
                st.session_state[f"{ctx}_preview"] = None
                st.session_state[f"{ctx}_verified"] = False
                st.rerun()

def render_hw_container_3(df_preview):
    """ROW 3: 4-Column Hardware Utilities."""
    with st.container(border=True):
        st.markdown("### 📊 Asset Utilities")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            csv_data = df_preview.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Asset List", data=csv_data, 
                               file_name="hardware_inventory_export.csv", 
                               mime="text/csv", use_container_width=True)
        with c2:
            st.button("📋 Validate Warranty", key="hw_warranty_val", use_container_width=True)
        with c3:
            st.button("🏷️ Print Asset Tags", key="hw_tag_print", use_container_width=True)
        with c4:
            st.button("⚙️ Audit History", key="hw_audit_log", use_container_width=True)

# --- 3. MAIN ORCHESTRATOR ---

def render_hardware_view():
    """Main UI for Hardware Orchestrator."""
    st.title("🛡️ Hardware Asset Manager")
    
    # Initialize Message Handler
    MessageHandler.render(key_suffix="hw_mgr_view")

    ctx = "hw_mgr_v1"
    
    # Session State Initialization
    if f"{ctx}_verified" not in st.session_state:
        st.session_state[f"{ctx}_verified"] = False
    if f"{ctx}_preview" not in st.session_state:
        st.session_state[f"{ctx}_preview"] = None

    # --- FILE UPLOADER ---
    st.subheader("📥 Bulk Asset Import")
    uploaded_file = st.file_uploader("Upload Hardware CSV", type=["csv"], key=f"{ctx}_uploader")

    if uploaded_file:
        if st.session_state.get(f"{ctx}_df") is None or st.session_state.get(f"{ctx}_filename") != uploaded_file.name:
            df_raw = pd.read_csv(uploaded_file)
            df_raw.columns = [c.lower().strip() for c in df_raw.columns]
            st.session_state[f"{ctx}_df"] = df_raw
            st.session_state[f"{ctx}_filename"] = uploaded_file.name
            st.session_state[f"{ctx}_verified"] = False

        # --- ROW 1: Verification ---
        render_hw_container_1(ctx)

        df_preview = st.session_state.get(f"{ctx}_preview")
        
        if df_preview is not None and st.session_state.get(f"{ctx}_verified"):
            
            # Prepare data subsets
            adds = df_preview[df_preview['Action'] == 'ADD'].to_dict('records')
            upds = df_preview[df_preview['Action'] == 'UPDATE'].to_dict('records')
            dels = df_preview[df_preview['Action'] == 'DELETE'].to_dict('records')

            # --- ROW 2: Batch Actions ---
            render_hw_container_2(ctx, adds, upds, dels)

            # --- ROW 3: Utilities ---
            render_hw_container_3(df_preview)

            # --- PREVIEW TABLE ---
            st.divider()
            st.subheader("📋 Hardware Staging Preview")
            display_cols = ["Action", "Status", "model_name", "serial_number", "asset_tag", "description"]
            valid_cols = [c for c in display_cols if c in df_preview.columns]
            UI.render_selectable_table(df_preview[valid_cols], f"{ctx}_table", "model_name")

    # --- ACTIVE INVENTORY ---
    st.divider()
    st.subheader("🗄️ Active Hardware Inventory")
    st.info("Live hardware asset registry will appear here.")

if __name__ == "__main__":
    render_hardware_view()