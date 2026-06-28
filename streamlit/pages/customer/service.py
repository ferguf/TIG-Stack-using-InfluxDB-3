import streamlit as st
import pandas as pd
from src.api_client import post_customer, update_customer, get_customers, delete_customer
from src.ui_components import UI
from src.ui_forms import create_customer_form, update_customer_form
from src.ui_messages import MessageCenter
from src.state_managers import FabricStateManager

# --- DATA FETCHING ---

def sync_data():
    """Refreshes the customer dataframe in session state."""
    df = get_customers()
    if df is not None:
        # Standardize ID columns to strings for consistent comparison
        for col in df.columns:
            if any(k in col.lower() for k in ['id', 'uuid']):
                df[col] = df[col].astype(str)
    st.session_state["customer_df"] = df

def get_current_data():
    """Ensures data is loaded and returns it."""
    df = st.session_state.get("customer_df")
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        sync_data()
        return st.session_state.get("customer_df")
    return df

# --- ACTION HANDLERS ---

def handle_create():
    """Logic for adding a new customer (Provisioning)."""
    if not st.session_state.get("cust_show_create"):
        # Unique namespaced key for Tier 1
        if UI.button("➕ New Customer", color="green", key="cust_t1_btn_new_cust"):
            st.session_state["cust_show_create"] = True
            st.rerun()
    else:
        with st.container(border=True):
            st.markdown("### Provision New Customer")
            data = create_customer_form()
            if data:
                try:
                    post_customer(data["customer_name"], data["account_id"])
                    sync_data()
                    MessageCenter.set_success(f"✅ Created {data['customer_name']}")
                    st.session_state["cust_show_create"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Creation Error: {e}")
            
            if st.button("⬅️ Cancel", key="cust_t1_btn_cancel_create"):
                st.session_state["cust_show_create"] = False
                st.rerun()

def handle_update_delete(record):
    """Logic for modifying an existing customer context."""
    rec_id = record["customer_id"]
    st.info(f"📍 Context: **{record.get('customer_name')}**")
    
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        if UI.button("🔄 Update", color="amber", key=f"cust_t1_btn_upd_{rec_id}"):
            st.session_state["cust_show_update"] = True
            st.session_state["cust_confirm_delete"] = False
            st.rerun()
    with col2:
        if UI.button("🗑️ Delete", color="red", key=f"cust_t1_btn_del_{rec_id}"):
            st.session_state["cust_confirm_delete"] = True
            st.session_state["cust_show_update"] = False
            st.rerun()

    if st.session_state.get("cust_show_update"):
        _render_update_subform(record)
    
    if st.session_state.get("cust_confirm_delete"):
        _render_delete_confirmation(record)

# --- UI SUB-COMPONENTS ---

def _render_update_subform(record):
    st.divider()
    updated = update_customer_form(record)
    if updated:
        try:
            update_customer(record["customer_id"], record["account_id"], updated["customer_name"])
            sync_data()
            MessageCenter.set_success("✅ Updated!")
            st.session_state["cust_show_update"] = False
            st.rerun()
        except Exception as e:
            st.error(f"Update Failed: {e}")

def _render_delete_confirmation(record):
    st.divider()
    with st.container(border=True):
        st.error(f"Confirm Deletion of **{record['customer_name']}**?")
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if st.button("Yes, Delete", key=f"cust_t1_conf_del_{record['customer_id']}"):
                try:
                    delete_customer(record["customer_id"])
                    sync_data()
                    # Wipe global state for this tier
                    st.session_state["cust_active_id"] = None
                    st.session_state["cust_active_record"] = None
                    st.session_state["cust_confirm_delete"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Deletion failed: {e}")
        with c2:
            if st.button("Cancel", key=f"cust_t1_can_del_{record['customer_id']}"):
                st.session_state["cust_confirm_delete"] = False
                st.rerun()

# --- MAIN ENTRY POINT ---

def show_customers():
    """Entry point for the Customers Tab (Tier 1)."""
    manager = FabricStateManager()
    manager.initialize()
    MessageCenter.display_messages()
    
    # 1. Fetch current data
    df = get_current_data()
    
    # 2. Render Selection Table (Always Visible)
    selection = UI.render_selectable_table(
        df=df, 
        key_prefix="cust_t1_main_table", 
        id_column_to_hide="customer_id"
    )

    # 3. Handshake (Sync state with Global Manager)
    # This prefix "cust" triggers the Cascade Reset in FabricStateManager
    if manager.sync_selection("cust", selection, "customer_id"):
        st.rerun()

    st.divider()

    # 4. Contextual Rendering Logic
    active_cust = manager.get_active_record("cust")

    if active_cust:
        # If a row is checked, show management tools
        handle_update_delete(active_cust)
    else:
        # If no row is checked, show Provisioning/Create options
        handle_create()