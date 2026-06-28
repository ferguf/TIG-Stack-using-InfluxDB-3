from anyio import current_time
import streamlit as st
from src.utils.doc_manager import DocManager


st.set_page_config(layout="wide", page_title="Route Vision")

# --- Navigation Method (The Dispatcher) ---
def navigate_to(target):
    """
    Global method to handle hyperlinks from nodes/links.
    Target can be a Map ID or an external URL.
    """
    if not target:
        return

    if target.startswith(("http://", "https://")):
        # For external links, we use a markdown anchor or js 
        # (Plotly usually handles these if opened in new tab, 
        # but here we can provide a UI hint)
        st.sidebar.info(f"External Link: [Open Reference]({target})")
    else:
        # Internal Drill-down logic
        st.session_state["current_topo_id"] = target
        # Optional: Force navigation to the Topology Explorer page if not already there
        # This is useful if a link in 'Documentation' points to a 'Network' map
        st.success(f"Loading Map: {target}")
        st.rerun()

# Initialize Session State
if "current_topo_id" not in st.session_state:
    st.session_state["current_topo_id"] = "ROOT_GALAXY"

def show_docs_page():
    DocManager.render_full_page()

# --- Main Navigation ---
pg = st.navigation({
    "Fabric Services": [
        st.Page("pages/customer/customer_main.py", title="Customer Center", icon="👥"),
    ],
    "Networks": [
        st.Page("pages/network/net_3356_main.py", title="3356 network", icon="🌐"),
        st.Page("pages/network/net_209_main.py", title="AS209 network", icon="🌐"),
        st.Page("pages/network/net_3549_main.py", title="3549 network", icon="🌐"),   
        st.Page("pages/network/metro_main.py", title="Metro network", icon="🌐")     
     ],
     "Locations": [
         st.Page("pages/bulkload/load_main.py", title="Bulk Load Data", icon="📥"),
     ],
    "Visualization": [
        st.Page("pages/topology/topo_main.py", title="Topology Explorer", icon="🌐"),
    ],
    "Business Operations": [
        st.Page("pages/billing/billing_main.py", title="Billing & Revenue", icon="💸"),
    ],
    "Documentation Center": [
        st.Page(show_docs_page, title="Documentation Center", icon="📖"),
    ]
})

pg.run()