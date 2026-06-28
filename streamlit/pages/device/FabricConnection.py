import streamlit as st
from streamlit_extras.colored_header import colored_header
from api_client import get_services
from ui_components import render_table

colored_header("FAbric Connection", "Stuff", color_name="purple-70")

with st.sidebar.expander("Service Endpoints", expanded=False):
    if st.button("Get All Services"):
        try:
            df = get_services()
            st.session_state["service_df"] = df
        except Exception as e:
            st.error(f"Failed to fetch services: {e}")

if "service_df" in st.session_state and st.session_state["service_df"] is not None:
    render_table(st.session_state["service_df"], "All Services")
else:
    st.info("No service data loaded yet. Use the sidebar to fetch services.")
