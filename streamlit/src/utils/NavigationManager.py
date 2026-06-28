import streamlit as st
import requests
from urllib.parse import quote

def handle_map_navigation(target_id):
    """
    Determines if the clicked URL is a drill-down map 
    or an external reference.
    """
    if not target_id:
        return

    # Check if it's an external link
    if target_id.startswith(("http://", "https://")):
        # Since Streamlit can't force a new tab from a click event easily,
        # we display a link or use a JS snippet.
        st.info(f"Opening external reference: {target_id}")
        return

    # If it's a map ID, update the session state and rerun
    st.session_state.current_topo_id = target_id
    st.success(f"Drilling down into: {target_id}")
    st.rerun()

def can_add_fabric_connection(parent_service, current_connections_df):
    """
    Determines if a service is eligible to add another Fabric Connection 
    based on its service type and current connection count.
    
    Logic:
    - ELINE EPL: Max 1
    - E-LINE EVPL, EPLAN, EVPLAN: Max 250
    - IPVPN, MCGW: Unlimited (N)
    """
    if not parent_service:
        return False

    # Extract service type and normalize
    service_type = parent_service.get("service_type", "").upper().strip()
    current_count = len(current_connections_df) if current_connections_df is not None else 0

    # Business Logic Mapping
    if service_type == "ELINE EPL":
        return current_count < 1
    
    elif service_type in ["E-LINE EVPL", "EPLAN", "EVPLAN"]:
        return current_count < 250
    
    elif service_type in ["IPVPN", "MCGW"]:
        # Supports N Fabric Connections
        return True

    # Default fallback: If service type is unrecognized, 
    # we return True to avoid blocking valid workflows unless specified otherwise.
    return True