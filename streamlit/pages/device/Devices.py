import streamlit as st
from streamlit_extras.colored_header import colored_header
from api_client import get_devices, post_device
from ui_components import render_device_table




# -----------------------------
# Page Header
# -----------------------------
colored_header("Customer Dashboard", "View and manage customer data", color_name="blue-70")

# -----------------------------
# Sidebar Controls
# -----------------------------
with st.sidebar.expander("Device Endpoints", expanded=False):
    # --- READ ---
    if st.button("Get Devices", key="btn_get_devices"):
        try:
            df = get_devices()   # <-- call your FastAPI client wrapper
            st.session_state["device_df"] = df
        except Exception as e:
            st.error(f"Failed to fetch devices: {e}")


    # --- CREATE ---

st.text_input("Device Name", key="new_device_name")
st.text_input("location", key="new_location")
st.text_input("Device Role", key="new_device_role")
st.text_input("Device Vendor", key="new_device_vendor")
st.text_input("Device Model (auto populate ports)", key="new_device_model")
st.text_input("Planning Status", key="new_planning_status")
st.text_input("Device Serial (unique)", key="new_serial_number")
st.text_input("Device Description", key="new_device_description")
st.number_input("Health Status", key="new_health_status", min_value=0, max_value=10, step=1)

if st.button("Add Device", key="btn_add_device"):
    try:
        new_device = post_device(
            st.session_state["new_device_name"],
            st.session_state.get("new_location"),
            st.session_state.get("new_device_role"),
            # st.session_state.get("new_device_vendor"),
            # st.session_state.get("new_device_model"),
            # st.session_state.get("new_planning_status"),
            st.session_state.get("new_serial_number"),
            # st.session_state.get("new_device_description"),
            # st.session_state.get("new_health_status"),
        )
        st.success(f"Device created: {new_device['device_name']}")
        st.session_state["device_df"] = get_devices()
    except Exception as e:
        st.error(f"Failed to add device: {e}")

    # --- UPDATE ---
    # st.text_input("Device ID to update", key="update_device_id")
    st.text_input("Device Name", key="update_device_name")
    st.text_input("Device Alias", key="update_device_alias")
    st.text_input("Device Type", key="update_device_type")
    st.text_input("Device Description", key="update_device_description")
    st.text_input("Planning status", key="update_planning_status")
    st.number_input("New Health Status", key="update_device_health", min_value=0, max_value=4, step=1)

    if st.button("Update Device", key="btn_update_device"):
        try:
            updated_device = put_device(
                st.session_state["update_device_id"],
                st.session_state.get("update_device_name"),
                st.session_state.get("update_device_alias"),
                st.session_state.get("update_device_type"),
                st.session_state.get("update_device_description"),
                st.session_state.get("update_device_health"),
            )
            st.success(f"Device updated: {updated_device['device_name']}")
            # Refresh list
            st.session_state["device_df"] = get_devices()
        except Exception as e:
            st.error(f"Failed to update device: {e}")

if "device_df" in st.session_state and st.session_state["device_df"] is not None:
    render_device_table(st.session_state["device_df"])
else:
    st.info("No customer data loaded yet. Use the sidebar to fetch customers.")