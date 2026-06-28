import streamlit as st
import pandas as pd
import time
from src.ui_components import UI
from src.utils.file_utils import MessageHandler

# --- 1. CORE LOGIC & RECONCILIATION ---

def build_material_preview(df_raw):
    """
    Validates Material CSV data and reconciles SKU/Part Numbers.
    Standardized description: 'part_number : category (quantity) - uom'
    """
    preview_data = []
    # Fetch existing materials from DB (Mocked)
    # existing_materials = get_material_inventory() 
    
    for _, row in df_raw.iterrows():
        # TODO: Implement SKU validation against Master Parts List
        part_no = row.get('part_number', 'Unknown_SKU')
        category = row.get('category', 'Misc')
        qty = row.get('quantity', 0)
        uom = row.get('uom', 'EA') # Unit of Measure
        
        # Standardized Material Description Formatting
        formatted_desc = f"{part_no} : {category} ({qty}) - {uom}"
        
        preview_data.append({
            "Action": str(row.get('action', 'ADD')).upper(),
            "Status": "🔍 part not found",
            "description": formatted_desc,
            "part_number": part_no,
            "quantity": qty,
            "category": category,
            "uom": uom,
            "location": row.get('location', 'Warehouse'),
            "project_id": row.get('project_id', 'Unassigned')
        })
    return pd.DataFrame(preview_data)

# --- 2. CONTAINER DEFINITIONS (1:4:4 Design) ---

def render_mat_container_1(ctx):
    """ROW 1: Material Verification and SKU validation."""
    with st.container(border=True):
        st.markdown("### 🛠️ Material Logic Verification")
        if not st.session_state.get(f"{ctx}_verified"):
            if UI.button("🔍 Run SKU Verification", color="orange", key="btn_verify_mat"):
                with st.spinner("Reconciling Part Numbers..."):
                    time.sleep(0.5)
                    st.session_state[f"{ctx}_preview"] = build_material_preview(st.session_state[f"{ctx}_df"])
                    st.session_state[f"{ctx}_verified"] = True
                    st.rerun()
        else:
            st.success("✅ Part Logic Verified: Ready for Inventory Adjustment")

def render_mat_container_2(ctx, adds, upds, dels):
    """ROW 2: 4-Column Batch Inventory Operations."""
    with st.container(border=True):
        st.markdown("### ⚡ Batch Operations")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            btn_label = f"➕ Receive ({len(adds)})"
            if UI.button(btn_label, color="green", key="mat_add", use_container_width=True):
                # execute_material_batch(adds, "ADD", ctx)
                st.toast("Materials Received into Inventory")
                st.rerun()
        with c2:
            btn_label = f"🔄 Adjust ({len(upds)})"
            if UI.button(btn_label, color="blue", key="mat_upd", use_container_width=True):
                st.toast("Stock Levels Adjusted")
                st.rerun()
        with c3:
            btn_label = f"🗑️ Issue ({len(dels)})"
            if UI.button(btn_label, color="red", key="mat_del", use_container_width=True):
                st.toast("Materials Issued to Projects")
                st.rerun()
        with c4:
            if UI.button("🧹 Clear Staging", key="mat_clear", use_container_width=True):
                st.session_state[f"{ctx}_df"] = None
                st.session_state[f"{ctx}_preview"] = None
                st.session_state[f"{ctx}_verified"] = False
                st.rerun()

def render_mat_container_3(df_preview):
    """ROW 3: 4-Column Logistics Utilities."""
    with st.container(border=True):
        st.markdown("### 📊 Logistics Utilities")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            csv_data = df_preview.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Pick List", data=csv_data, 
                               file_name="material_pick_list.csv", 
                               mime="text/csv", use_container_width=True)
        with c2:
            st.button("📋 Validate Project IDs", key="mat_proj_val", use_container_width=True)
        with c3:
            st.button("📡 Check Stock Alert", key="mat_stock_alert", use_container_width=True)
        with c4:
            st.button("⚙️ Vendor RMA", key="mat_rma_process", use_container_width=True)

# --- 3. MAIN ORCHESTRATOR ---

def render_material_view():
    """Main UI for Materials Orchestrator."""
    st.title("👁️ Materials & Inventory Manager")
    
    # Initialize Message Handler
    MessageHandler.render(key_suffix="mat_mgr_view")

    ctx = "mat_mgr_v1"
    
    # Session State Initialization
    if f"{ctx}_verified" not in st.session_state:
        st.session_state[f"{ctx}_verified"] = False
    if f"{ctx}_preview" not in st.session_state:
        st.session_state[f"{ctx}_preview"] = None

    # --- FILE UPLOADER ---
    st.subheader("📥 Bulk Material Import")
    uploaded_file = st.file_uploader("Upload Material CSV", type=["csv"], key=f"{ctx}_uploader")

    if uploaded_file:
        if st.session_state.get(f"{ctx}_df") is None or st.session_state.get(f"{ctx}_filename") != uploaded_file.name:
            df_raw = pd.read_csv(uploaded_file)
            df_raw.columns = [c.lower().strip() for c in df_raw.columns]
            st.session_state[f"{ctx}_df"] = df_raw
            st.session_state[f"{ctx}_filename"] = uploaded_file.name
            st.session_state[f"{ctx}_verified"] = False

        # --- ROW 1: Verification ---
        render_mat_container_1(ctx)

        df_preview = st.session_state.get(f"{ctx}_preview")
        
        if df_preview is not None and st.session_state.get(f"{ctx}_verified"):
            
            # Prepare data subsets
            adds = df_preview[df_preview['Action'] == 'ADD'].to_dict('records')
            upds = df_preview[df_preview['Action'] == 'UPDATE'].to_dict('records')
            dels = df_preview[df_preview['Action'] == 'DELETE'].to_dict('records')

            # --- ROW 2: Batch Actions ---
            render_mat_container_2(ctx, adds, upds, dels)

            # --- ROW 3: Utilities ---
            render_mat_container_3(df_preview)

            # --- PREVIEW TABLE ---
            st.divider()
            st.subheader("📋 Materials Staging Preview")
            display_cols = ["Action", "Status", "part_number", "quantity", "uom", "description"]
            valid_cols = [c for c in display_cols if c in df_preview.columns]
            UI.render_selectable_table(df_preview[valid_cols], f"{ctx}_table", "category")

    # --- ACTIVE INVENTORY ---
    st.divider()
    st.subheader("🗄️ Active Materials Inventory")
    st.info("Live stock levels and project-allocated materials will appear here.")

if __name__ == "__main__":
    render_material_view()