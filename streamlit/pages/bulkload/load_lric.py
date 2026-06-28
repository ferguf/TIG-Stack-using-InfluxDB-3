import streamlit as st
import pandas as pd
import time
from src.ui_components import UI
from src.utils.file_utils import MessageHandler

# --- 1. CORE LOGIC & RECONCILIATION ---

def build_lric_preview(df_raw):
    """
    Validates LRIC CSV data and reconciles circuit IDs.
    Standardized description: 'vendor_name : circuit_id (cost_center)'
    """
    preview_data = []
    # Fetch existing LRIC records from DB (Mocked)
    # existing_lric = get_lric_records() 
    
    for _, row in df_raw.iterrows():
        # TODO: Implement Circuit/Service UUID Resolution
        circuit_id = row.get('circuit_id', 'Unknown_CKT')
        vendor = row.get('vendor_name', 'Generic_Vendor')
        cost_center = row.get('cost_center', 'Admin')
        
        # Standardized LRIC Description Formatting
        formatted_desc = f"{vendor} : {circuit_id} ({cost_center})"
        
        preview_data.append({
            "Action": str(row.get('action', 'ADD')).upper(),
            "Status": "🔍 record not found",
            "description": formatted_desc,
            "circuit_id": circuit_id,
            "monthly_cost": row.get('monthly_cost', 0.0),
            "vendor_name": vendor,
            "cost_center": cost_center,
            "contract_end": row.get('contract_end', '2026-12-31'),
            "currency": row.get('currency', 'USD')
        })
    return pd.DataFrame(preview_data)

# --- 2. CONTAINER DEFINITIONS (1:4:4 Design) ---

def render_lric_container_1(ctx):
    """ROW 1: LRIC Verification logic and financial validation."""
    with st.container(border=True):
        st.markdown("### 🛠️ LRIC Financial Verification")
        if not st.session_state.get(f"{ctx}_verified"):
            if UI.button("🔍 Run Financial Verification", color="orange", key="btn_verify_lric"):
                with st.spinner("Calculating Cost Increments..."):
                    time.sleep(0.5)
                    st.session_state[f"{ctx}_preview"] = build_lric_preview(st.session_state[f"{ctx}_df"])
                    st.session_state[f"{ctx}_verified"] = True
                    st.rerun()
        else:
            st.success("✅ Financial Logic Verified: Ready for Cost Ingestion")

def render_lric_container_2(ctx, adds, upds, dels):
    """ROW 2: 4-Column Batch Financial Operations."""
    with st.container(border=True):
        st.markdown("### ⚡ Batch Operations")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            btn_label = f"➕ Commit ({len(adds)})"
            if UI.button(btn_label, color="green", key="lric_add", use_container_width=True):
                # execute_lric_batch(adds, "ADD", ctx)
                st.toast("Cost Records Committed")
                st.rerun()
        with c2:
            btn_label = f"🔄 Adjust ({len(upds)})"
            if UI.button(btn_label, color="blue", key="lric_upd", use_container_width=True):
                st.toast("Pricing Adjustments Applied")
                st.rerun()
        with c3:
            btn_label = f"🗑️ Retire ({len(dels)})"
            if UI.button(btn_label, color="red", key="lric_del", use_container_width=True):
                st.toast("Records Retired")
                st.rerun()
        with c4:
            if UI.button("🧹 Clear Staging", key="lric_clear", use_container_width=True):
                st.session_state[f"{ctx}_df"] = None
                st.session_state[f"{ctx}_preview"] = None
                st.session_state[f"{ctx}_verified"] = False
                st.rerun()

def render_lric_container_3(df_preview):
    """ROW 3: 4-Column Financial Utilities."""
    with st.container(border=True):
        st.markdown("### 📊 Financial Utilities")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            csv_data = df_preview.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Cost Report", data=csv_data, 
                               file_name="lric_cost_export.csv", 
                               mime="text/csv", use_container_width=True)
        with c2:
            st.button("📋 Validate GL Codes", key="lric_gl_val", use_container_width=True)
        with c3:
            st.button("📉 Variance Analysis", key="lric_variance", use_container_width=True)
        with c4:
            st.button("⚙️ Vendor Sync", key="lric_vendor_sync", use_container_width=True)

# --- 3. MAIN ORCHESTRATOR ---

def render_lric_view():
    """Main UI for LRIC Orchestrator."""
    st.title("💰 LRIC Cost Manager")
    
    # Initialize Message Handler
    MessageHandler.render(key_suffix="lric_mgr_view")

    ctx = "lric_mgr_v1"
    
    # Session State Initialization
    if f"{ctx}_verified" not in st.session_state:
        st.session_state[f"{ctx}_verified"] = False
    if f"{ctx}_preview" not in st.session_state:
        st.session_state[f"{ctx}_preview"] = None

    # --- FILE UPLOADER ---
    st.subheader("📥 Bulk LRIC Import")
    uploaded_file = st.file_uploader("Upload LRIC CSV", type=["csv"], key=f"{ctx}_uploader")

    if uploaded_file:
        if st.session_state.get(f"{ctx}_df") is None or st.session_state.get(f"{ctx}_filename") != uploaded_file.name:
            df_raw = pd.read_csv(uploaded_file)
            df_raw.columns = [c.lower().strip() for c in df_raw.columns]
            st.session_state[f"{ctx}_df"] = df_raw
            st.session_state[f"{ctx}_filename"] = uploaded_file.name
            st.session_state[f"{ctx}_verified"] = False

        # --- ROW 1: Verification ---
        render_lric_container_1(ctx)

        df_preview = st.session_state.get(f"{ctx}_preview")
        
        if df_preview is not None and st.session_state.get(f"{ctx}_verified"):
            
            # Prepare data subsets
            adds = df_preview[df_preview['Action'] == 'ADD'].to_dict('records')
            upds = df_preview[df_preview['Action'] == 'UPDATE'].to_dict('records')
            dels = df_preview[df_preview['Action'] == 'DELETE'].to_dict('records')

            # --- ROW 2: Batch Actions ---
            render_lric_container_2(ctx, adds, upds, dels)

            # --- ROW 3: Utilities ---
            render_lric_container_3(df_preview)

            # --- PREVIEW TABLE ---
            st.divider()
            st.subheader("📋 LRIC Staging Preview")
            display_cols = ["Action", "Status", "vendor_name", "circuit_id", "monthly_cost", "description"]
            valid_cols = [c for c in display_cols if c in df_preview.columns]
            UI.render_selectable_table(df_preview[valid_cols], f"{ctx}_table", "vendor_name")

    # --- ACTIVE INVENTORY ---
    st.divider()
    st.subheader("🗄️ Active LRIC Ledger")
    st.info("Live LRIC cost records and financial mappings will appear here.")

if __name__ == "__main__":
    render_lric_view()