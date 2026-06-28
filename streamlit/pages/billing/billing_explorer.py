import streamlit as st
import pandas as pd
from src.utils import api_billing

# Must be the first Streamlit command if run as a standalone page
st.set_page_config(layout="wide", page_title="NDT Rate Card Explorer")

def inject_theme_css():
    """Injects custom CSS to theme buttons based on an adjacent hidden marker."""
    st.markdown("""
    <style>
    /* Amber Theme (Warnings, Edits) */
    .element-container:has(.theme-amber) + .element-container button {
        background-color: #FFBF00 !important;
        color: #000000 !important;
        border: 1px solid #FFBF00 !important;
        font-weight: 600 !important;
    }
    .element-container:has(.theme-amber) + .element-container button:hover {
        background-color: #E6AC00 !important;
    }

    /* Blue Theme (Standard Actions) */
    .element-container:has(.theme-blue) + .element-container button {
        background-color: #007BFF !important;
        color: #FFFFFF !important;
        border: 1px solid #007BFF !important;
        font-weight: 600 !important;
    }
    .element-container:has(.theme-blue) + .element-container button:hover {
        background-color: #0056b3 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def _themed_button(label, theme="blue", **kwargs):
    """Helper method to render a colored button."""
    st.markdown(f'<div class="theme-{theme}" style="display:none;"></div>', unsafe_allow_html=True)
    kwargs.pop("type", None)
    return st.button(label, **kwargs)

def render_rate_summary(rate_id: str):
    """Renders the nested composite JSON cleanly with defensive Pandas column slicing."""
    try:
        # Fallback to get_rate_summary if get_rate_card_composite is not available
        if hasattr(api_billing, 'get_rate_card_composite'):
            data = api_billing.get_rate_card_composite(rate_id)
        else:
            data = api_billing.get_rate_summary(rate_id)
    except Exception as e:
        st.error(f"Failed to fetch rate summary: {e}")
        return
        
    if not data:
        st.warning("No data returned for this rate card.")
        return

    st.subheader(f"📊 Summary: {data.get('rate_name', 'Rate Card Details')}")
    st.caption(f"Currency: {data.get('currency_code', 'USD')} | ID: {rate_id}")
    
    # High-level Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Physical Ports", len(data.get("ports", [])))
    c2.metric("Access Tiers", len(data.get("access_tiers", [])))
    c3.metric("BW Ladders", len(data.get("bandwidth_ladders", [])))
    c4.metric("Usage Tokens", len(data.get("usage_tokens", [])))
    
    st.divider()
    
    # ==========================================
    # 1. RENDER PHYSICAL PORTS (Defensive)
    # ==========================================
    with st.expander("🔌 Physical Ports", expanded=True):
        raw_ports = data.get("ports", [])
        if raw_ports:
            df_ports = pd.DataFrame(raw_ports)
            desired_port_cols = ["port_speed_mbps", "nrc_amount", "mrc_amount"]
            valid_port_cols = [col for col in desired_port_cols if col in df_ports.columns]
            st.dataframe(df_ports[valid_port_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No physical ports configured.")

    # ==========================================
    # 2. RENDER ACCESS TIERS (Defensive)
    # ==========================================
    with st.expander("🏢 Network Access Tiers"):
        raw_access = data.get("access_tiers", [])
        if raw_access:
            df_acc = pd.DataFrame(raw_access)
            desired_acc_cols = ["access_code", "location_type", "port_speed_mbps", "nrc_amount", "mrc_amount"]
            valid_acc_cols = [col for col in desired_acc_cols if col in df_acc.columns]
            st.dataframe(df_acc[valid_acc_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No access tiers mapped to this rate card.")

    # ==========================================
    # 3. RENDER BANDWIDTH LADDERS (Defensive)
    # ==========================================
    with st.expander("📈 Bandwidth Ladders"):
        raw_bw = data.get("bandwidth_ladders", [])
        if raw_bw:
            df_bw = pd.DataFrame(raw_bw)
            desired_bw_cols = ["service_type", "service_bw_mbps", "nrc_amount", "mrc_amount"]
            valid_bw_cols = [col for col in desired_bw_cols if col in df_bw.columns]
            st.dataframe(df_bw[valid_bw_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No bandwidth ladders mapped to this rate card.")

    # ==========================================
    # 4. RENDER USAGE TOKENS (Defensive)
    # ==========================================
    with st.expander("🪙 Usage Tokens"):
        raw_tokens = data.get("usage_tokens", [])
        if raw_tokens:
            df_tok = pd.DataFrame(raw_tokens)
            desired_tok_cols = ["service_type", "included_gb_per_month", "token_cost_per_gb", "mrc_amount"]
            valid_tok_cols = [col for col in desired_tok_cols if col in df_tok.columns]
            st.dataframe(df_tok[valid_tok_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No usage tokens mapped to this rate card.")


def run_catalog_explorer():
    """Main UI for the Catalog Explorer App."""
    inject_theme_css()
    st.title("🗂️ Rate Card Explorer")
    st.markdown("Auditing and read-only view of commercial contexts and catalog components.")
    
    tab_cust, tab_prov, tab_all = st.tabs(["🏢 Customer Lookup", "🔌 Provider Lookup", "🌐 Global Catalog"])
    
    # =========================================================
    # --- CUSTOMER LOOKUP ---
    # =========================================================
    with tab_cust:
        st.markdown("Enter a Customer ID to view their active commercial catalogs.")
        c1, c2 = st.columns([3, 1])
        with c1: 
            c_id = st.text_input("Customer UUID", key="exp_cust_id")
        with c2: 
            st.write("") # Spacing
            st.write("") # Spacing
            search_cust = _themed_button("🔍 Search Customer", theme="blue", use_container_width=True)

        if search_cust and c_id:
            rates_df = api_billing.get_customer_rates(c_id)
            if not rates_df.empty:
                event = st.dataframe(rates_df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tbl_c_rates")
                if event.selection.rows:
                    selected_rate = rates_df.iloc[event.selection.rows[0]]
                    st.divider()
                    render_rate_summary(str(selected_rate['id']))
            else:
                st.warning("No active rate cards found for this Customer.")

    # =========================================================
    # --- PROVIDER LOOKUP ---
    # =========================================================
    with tab_prov:
        st.markdown("Select a Provider to view their associated buy-rates.")
        try:
            prov_df = api_billing.get_billing_providers()
        except AttributeError:
            st.error("Missing api_billing.get_billing_providers(). Please implement in utils.")
            prov_df = pd.DataFrame()

        if not prov_df.empty:
            p_opts = {row['id']: f"{row['name']} ({row['code']})" for idx, row in prov_df.iterrows()}
            c1, c2 = st.columns([3, 1])
            with c1:
                selected_p_id = st.selectbox("Select Provider", options=list(p_opts.keys()), format_func=lambda x: p_opts[x], key="exp_prov_id")
            with c2:
                st.write("") 
                st.write("") 
                search_prov = _themed_button("🔍 Search Provider", theme="blue", use_container_width=True)
            
            if search_prov and selected_p_id:
                rates_df = api_billing.get_provider_rates(selected_p_id)
                if not rates_df.empty:
                    event = st.dataframe(rates_df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tbl_p_rates")
                    if event.selection.rows:
                        selected_rate = rates_df.iloc[event.selection.rows[0]]
                        st.divider()
                        render_rate_summary(str(selected_rate['id']))
                else:
                    st.info("No rate cards mapped to this Provider.")

    # =========================================================
    # --- GLOBAL CATALOG LOOKUP ---
    # =========================================================
    with tab_all:
        st.markdown("Browse the entire global catalog repository.")
        rates_df = api_billing.get_billing_rates()
        if not rates_df.empty:
            event = st.dataframe(
                rates_df, 
                use_container_width=True, 
                on_select="rerun", 
                selection_mode="single-row", 
                key="tbl_all_rates"
            )
            
            if event.selection.rows:
                selected_rate = rates_df.iloc[event.selection.rows[0]]
                st.divider()
                
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1: 
                        render_rate_summary(str(selected_rate['id']))
                    with c2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if _themed_button("✏️ Edit in Builder", theme="amber", use_container_width=True):
                            # Sync the selected rate card to the global session state
                            st.session_state.active_rate_id = str(selected_rate['id'])
                            st.session_state.active_rate_name = selected_rate['name']
                            st.session_state.billing_step = 1
                            
                            # Navigate to the Builder page 
                            try:
                                st.switch_page("pages/billing/billing_main.py")
                            except Exception as e:
                                st.error(f"Navigation failed: {e}")

if __name__ == "__main__":
    run_catalog_explorer()