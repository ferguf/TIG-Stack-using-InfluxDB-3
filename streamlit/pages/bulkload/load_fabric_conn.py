import streamlit as st
import pandas as pd
import time
from src.ui_components import UI
from src.utils.file_utils import MessageHandler

# --- 1. CORE LOGIC & RECONCILIATION ---

def build_fabric_preview(df_raw):
    """
    Validates CSV data and checks for existing fabric links.
    Standardizes on the 'device_a:port_a <-> device_b:port_b' description format.
    """
    preview_data = []
    # Fetch existing state for 'Last Look' verification (Mocked for skeleton)
    # existing_links = get_fabric_connections() 
    
    for _, row in df_raw.iterrows():
        # TODO: Implement Port/Node UUID Resolution logic
        id_a = "uuid-a-placeholder"
        id_b = "uuid-b-placeholder"
        
        # Standardized Description Formatting
        formatted_desc = f"{row.get('source_node')}:{row.get('source_port')} <-> {row.get('dest_node')}:{row.get('dest_port')}"
        
        preview_data.append({
            "Action": str(row.get('action', 'ADD')).upper(),
            "Status": "🔍 link not found",
            "description": formatted_desc,
            "fabric_type": row.get('type', 'Spine-Leaf'),
            "bandwidth": row.get('bandwidth', '100G'),
            "Internal_ID_A": id_a,
            "Internal_ID_B": id_b,
            "source_node": row.get('source_node'),
            "source_port": row.get('source_port'),
            "dest_node": row.get('dest_node'),
            "dest_port": row.get('dest_port')
        })
    return pd.DataFrame(preview_data)

# --- 2. CONTAINER DEFINITIONS (1:4:4 Design) ---

def render_fc_container_1(ctx):
    """ROW 1: System Verification logic and status."""
    with st.container(border=True):
        st.markdown("### 🛠️ System Verification")
        if not st.session_state.get(f"{ctx}_verified"):
            if UI.button("🔍 Run Logic Verification", color="orange", key="btn_verify_fab"):
                with st.spinner("Reconciling Fabric Nodes..."):
                    # Simulate API delay
                    time.sleep(0.5)
                    st.session_state[f"{ctx}_preview"] = build_fabric_preview(st.session_state[f"{ctx}_df"])
                    st.session_state[f"{ctx}_verified"] = True
                    st.rerun()
        else:
            st.success("✅ Logic Verified: Ready for Batch Processing")

def render_fc_container_2(ctx, adds, upds, dels):
    """ROW 2: 4-Column Batch Lifecycle Operations."""
    with st.container(border=True):
        st.markdown("### ⚡ Batch Operations")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            btn_label = f"➕ Add ({len(adds)})"
            if UI.button(btn_label, color="green", key="fab_add", use_container_width=True):
                # execute_fabric_batch(adds, "ADD", ctx)
                st.toast("Fabric Adds Processed")
                st.rerun()
        with c2:
            btn_label = f"🔄 Update ({len(upds)})"
            if UI.button(btn_label, color="blue", key="fab_upd", use_container_width=True):
                # execute_fabric_batch(upds, "UPDATE", ctx)
                st.toast("Fabric Updates Processed")
                st.rerun()
        with c3:
            btn_label = f"🗑️ Delete ({len(dels)})"
            if UI.button(btn_label, color="red", key="fab_del", use_container_width=True):
                # execute_fabric_batch(dels, "DELETE", ctx)
                st.toast("Fabric Deletes Processed")
                st.rerun()
        with c4:
            if UI.button("🧹 Clear Staging", key="fab_clear", use_container_width=True):
                st.session_state[f"{ctx}_df"] = None
                st.session_state[f"{ctx}_preview"] = None
                st.session_state[f"{ctx}_verified"] = False
                st.rerun()

def render_fc_container_3(df_preview):
    """ROW 3: 4-Column Data Utilities and Exports."""
    with st.container(border=True):
        st.markdown("### 📊 Data Utilities")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            csv_data = df_preview.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", data=csv_data, 
                               file_name="fabric_staging_export.csv", 
                               mime="text/csv", use_container_width=True)
        with c2:
            st.button("📋 Validate UUIDs", key="fab_uuid_val", use_container_width=True)
        with c3:
            st.button("📡 Sync Telemetry", key="fab_tel_sync", use_container_width=True)
        with c4:
            st.button("⚙️ Config Push", key="fab_cfg_push", use_container_width=True)

# --- 3. MAIN ORCHESTRATOR ---

def render_fabric_connections_view():
    """Main UI for Fabric Connections Orchestrator."""
    st.title("🔗 Fabric Connection Manager")
    
    # Initialize Message Handler
    MessageHandler.render(key_suffix="fabric_conn_view")

    ctx = "fabric_v3"
    
    # Session State Initialization
    if f"{ctx}_verified" not in st.session_state:
        st.session_state[f"{ctx}_verified"] = False
    if f"{ctx}_preview" not in st.session_state:
        st.session_state[f"{ctx}_preview"] = None

    # --- FILE UPLOADER ---
    st.subheader("📥 Bulk Fabric Import")
    uploaded_file = st.file_uploader("Upload Fabric Connection CSV", type=["csv"], key=f"{ctx}_uploader")

    if uploaded_file:
        # Load file into state if new
        if st.session_state.get(f"{ctx}_df") is None or st.session_state.get(f"{ctx}_filename") != uploaded_file.name:
            df_raw = pd.read_csv(uploaded_file)
            df_raw.columns = [c.lower().strip() for c in df_raw.columns]
            st.session_state[f"{ctx}_df"] = df_raw
            st.session_state[f"{ctx}_filename"] = uploaded_file.name
            st.session_state[f"{ctx}_verified"] = False

        # --- ROW 1: Verification ---
        render_fc_container_1(ctx)

        df_preview = st.session_state.get(f"{ctx}_preview")
        
        if df_preview is not None and st.session_state.get(f"{ctx}_verified"):
            
            # Prepare data subsets for the dispatcher
            adds = df_preview[df_preview['Action'] == 'ADD'].to_dict('records')
            upds = df_preview[df_preview['Action'] == 'UPDATE'].to_dict('records')
            dels = df_preview[df_preview['Action'] == 'DELETE'].to_dict('records')

            # --- ROW 2: Batch Actions ---
            render_fc_container_2(ctx, adds, upds, dels)

            # --- ROW 3: Utilities ---
            render_fc_container_3(df_preview)

            # --- PREVIEW TABLE ---
            st.divider()
            st.subheader("📋 Preview Staging Table")
            display_cols = ["Action", "Status", "description", "fabric_type", "bandwidth"]
            # Ensure only existing columns are rendered
            valid_cols = [c for c in display_cols if c in df_preview.columns]
            UI.render_selectable_table(df_preview[valid_cols], f"{ctx}_table", "fabric_type")

    # --- ACTIVE INVENTORY ---
    st.divider()
    st.subheader("🗄️ Active Fabric Map")
    st.info("Direct database inventory of Fabric Connections will appear here.")

if __name__ == "__main__":
    render_fabric_connections_view()