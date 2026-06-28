import streamlit as st
import logging

# --- IMPORT SEPARATED VIEW MODULES ---
from pages.network import traffic_3356_global
from pages.network import traffic_3356_region
from pages.network import traffic_3356_pop
from pages.network import traffic_3356_router

logger = logging.getLogger(__name__)

# =============================================================================
# MAIN DASHBOARD ENTRY POINT (THE AGGREGATOR)
# =============================================================================

def render_traffic_dashboard():
    """
    Main view controller for the NDT Command Center.
    Imports and mounts the separated presentation modules into a tabbed interface.
    """
    
    # ---------------------------------------------------------
    # MASTER NAVIGATION 
    # ---------------------------------------------------------
    tab_global, tab_regional, tab_pop, tab_router = st.tabs([
        "🌍 Global Traffic", 
        "🗺️ Regional Traffic",
        "🔀 Pop Flow Analysis", 
        "🖥️ Router Flow Analysis"
    ])

    # Mount the isolated views into their respective tabs
    with tab_global:
        traffic_3356_global.render_global_view()
        
    with tab_regional:

       traffic_3356_region.render_regional_view()
        
    with tab_pop:

        traffic_3356_pop.render_pop_view()
        
    with tab_router:

        traffic_3356_router.render_router_view()