
import streamlit as st
from streamlit_extras.colored_header import colored_header
from api_client import get_customers
from ui_components import render_customer_table

# -----------------------------
# Page Header
# -----------------------------
colored_header(
    label="Device and Network Inventory",
    description="Manage Routers and switch",
    color_name="green-70",
)

# -----------------------------
# Sidebar Controls
# -----------------------------
with st.sidebar.expander("Customer Endpoints", expanded=False):
    if st.button("Get All Customers"):
        try:
            df = get_customers()
            st.session_state["customer_df"] = df
        except Exception as e:
            st.error(f"Failed to fetch customers: {e}")
        
# -----------------------------
# Main Panel Output
# -----------------------------
if "customer_df" in st.session_state and st.session_state["customer_df"] is not None:
    edited_df = render_customer_table(st.session_state["customer_df"])

    # Example: enforce single selection logic
    if "Select" in edited_df.columns:
        selected_rows = edited_df[edited_df["Select"] == True]
        if len(selected_rows) > 1:
            st.error("Please select only one customer.")
        elif len(selected_rows) == 1:
            selected_customer = selected_rows.iloc[0]
            st.success(
                f"Selected: {selected_customer['customer_name']} "
                f"(Account {selected_customer['account_id']})"
            )
else:
    st.info("No customer data loaded yet. Use the sidebar to fetch customers.")
