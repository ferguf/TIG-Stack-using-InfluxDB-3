import streamlit as st
import pandas as pd
import datetime
import uuid
import math
from src.utils import api_billing
from pages.billing.billing_explorer import run_catalog_explorer

# --- NEW EXTERNAL FILE IMPORTS ---
# Ensure these files and functions exist in your project structure
from pages.capabilities.builder import run_capabilities_builder
from pages.capabilities.viewer import run_capabilities_viewer

# Must be the first Streamlit command
st.set_page_config(layout="wide", page_title="NDT Billing Engine")

def inject_theme_css():
    """Injects custom CSS to theme buttons based on an adjacent hidden marker."""
    st.markdown("""
    <style>
    .element-container:has(.theme-amber) + .element-container button {
        background-color: #FFBF00 !important; color: #000000 !important; border: 1px solid #FFBF00 !important; font-weight: 600 !important;
    }
    .element-container:has(.theme-amber) + .element-container button:hover { background-color: #E6AC00 !important; }

    .element-container:has(.theme-green) + .element-container button {
        background-color: #28A745 !important; color: #FFFFFF !important; border: 1px solid #28A745 !important; font-weight: 600 !important;
    }
    .element-container:has(.theme-green) + .element-container button:hover { background-color: #218838 !important; }

    .element-container:has(.theme-red) + .element-container button {
        background-color: #DC3545 !important; color: #FFFFFF !important; border: 1px solid #DC3545 !important; font-weight: 600 !important;
    }
    .element-container:has(.theme-red) + .element-container button:hover { background-color: #C82333 !important; }
    </style>
    """, unsafe_allow_html=True)


class BillingCatalogWizard:
    def __init__(self):
        inject_theme_css()
        
        if "billing_step" not in st.session_state:
            st.session_state.billing_step = 1
        self.current_step = st.session_state.billing_step

        if "active_rate_id" not in st.session_state:
            st.session_state.active_rate_id = None
            st.session_state.active_rate_name = "Unassigned"
            try:
                rates_df = api_billing.get_billing_rates()
                if not rates_df.empty:
                    st.session_state.active_rate_id = str(rates_df.iloc[0]['id'])
                    st.session_state.active_rate_name = rates_df.iloc[0]['name']
            except Exception: pass

        if "staged_catalog" not in st.session_state:
            st.session_state.staged_catalog = {"ports": [], "access": [], "bw_ladders": [], "tokens": [], "providers": []}

        # =========================================================
        # --- COMPOSITE API INTEGRATION ---
        # =========================================================
        self.live_data = {}
        if st.session_state.active_rate_id:
            try:
                # Fetching the entire catalog structure in a single highly-efficient call
                self.live_data = api_billing.get_rate_card_composite(st.session_state.active_rate_id) or {}
            except Exception as e: 
                # Optional fallback if the composite endpoint fails
                try:
                    self.live_data = api_billing.get_rate_summary(st.session_state.active_rate_id) or {}
                except:
                    pass

    def _themed_button(self, label, theme="green", **kwargs):
        st.markdown(f'<div class="theme-{theme}" style="display:none;"></div>', unsafe_allow_html=True)
        kwargs.pop("type", None) 
        return st.button(label, **kwargs)

    # =========================================================
    # --- CORE LAYOUT & NAVIGATION ---
    # =========================================================
    def _render_header(self):
        st.title("💸 Canonical Catalog Builder & Editor")
        with st.expander("🛠️ Session Inspector"):
            st.write(f"Current Step: {st.session_state.billing_step}")
            st.write(f"Active Rate ID: {st.session_state.active_rate_id}")
            st.json(st.session_state.staged_catalog)
        
        total_steps = 7
        st.progress((self.current_step - 1) / (total_steps - 1) if total_steps > 1 else 0.0)
        
        if st.session_state.active_rate_id:
            st.success(f"🔗 **Active Commercial Context:** {st.session_state.active_rate_name}")
        else:
            st.warning("⚠️ **No Active Rate Card.** Define a commercial context in Step 1.")
        st.divider()

    def _render_navigation(self):
        st.divider()
        col1, _, col2 = st.columns([1, 4, 1])
        with col1:
            if self.current_step > 1:
                if self._themed_button("⬅️ Previous", theme="amber", use_container_width=True):
                    st.session_state.billing_step -= 1
                    st.rerun()
        with col2:
            is_disabled = (self.current_step == 1 and not st.session_state.active_rate_id)
            if self.current_step < 7:
                if self._themed_button("Next ➡️", theme="amber", disabled=is_disabled, use_container_width=True):
                    st.session_state.billing_step += 1
                    st.rerun()

    # =========================================================
    # --- STEP 1: RATE CARD COMPONENTS ---
    # =========================================================
    def step_1_rate_card(self):
        st.header("Step 1: Define or Select Rate Card")
        rates_df = api_billing.get_billing_rates()
        selected_rate = None
        
        if not rates_df.empty:
            st.subheader("Existing Rate Cards")
            event = st.dataframe(rates_df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_rates")
            if event.selection.rows:
                selected_rate = rates_df.iloc[event.selection.rows[0]]
                st.session_state.active_rate_id = str(selected_rate['id'])
                st.session_state.active_rate_name = selected_rate['name']
                st.success(f"✅ Context locked to: {selected_rate['name']}")
        
        st.divider()
        def_name, def_curr, def_start = "", "USD", datetime.date.today()
        if selected_rate is not None:
            st.subheader("Edit Selected Rate Card")
            def_name = selected_rate.get('name', '')
            def_curr = selected_rate.get('currency_code', 'USD')
            try:
                start_ts = selected_rate.get('effective_start_ts')
                if start_ts: def_start = pd.to_datetime(start_ts).date()
            except Exception: pass
        else:
            st.subheader("Create New Rate Card")

        with st.container(border=True):
            r_name = st.text_input("Rate Card Name", value=def_name)
            curr_idx = ["USD", "EUR", "GBP"].index(def_curr) if def_curr in ["USD", "EUR", "GBP"] else 0
            r_curr = st.selectbox("Currency", ["USD", "EUR", "GBP"], index=curr_idx)
            r_start = st.date_input("Effective Start Date", value=def_start)
            
            if selected_rate is None:
                if self._themed_button("💾 Create & Select Rate Card", theme="green", use_container_width=True):
                    if r_name:
                        payload = {"name": r_name, "currency_code": r_curr, "effective_start_ts": r_start.isoformat() + "T00:00:00Z", "is_active": True}
                        resp = api_billing.post_billing_rate(payload)
                        st.session_state.active_rate_id, st.session_state.active_rate_name = resp["id"], resp["name"]
                        st.rerun()
            else:
                c1, c2 = st.columns(2)
                with c1:
                    if self._themed_button("💾 Update Rate Card", theme="amber", use_container_width=True):
                        payload = {"name": r_name, "currency_code": r_curr, "effective_start_ts": r_start.isoformat() + "T00:00:00Z", "is_active": True}
                        api_billing.put_billing_rate(str(selected_rate['id']), payload)
                        st.rerun()
                with c2:        
                    if self._themed_button("🗑️ Delete Rate Card", theme="red", use_container_width=True):
                        api_billing.delete_billing_rate(str(selected_rate['id']))
                        st.session_state.active_rate_id = None
                        st.rerun()

    # =========================================================
    # --- STEP 2: PORT COMPONENTS ---
    # =========================================================
    def _render_live_ports(self):
        live_items = self.live_data.get("ports", [])
        if not live_items: return
        
        st.subheader("🟢 Live Database Ports")
        df = pd.DataFrame(live_items)
        valid_cols = [c for c in ["id", "port_speed_mbps", "nrc_amount", "mrc_amount"] if c in df.columns]
        event = st.dataframe(df[valid_cols], use_container_width=True, on_select="rerun", selection_mode="single-row", key="live_ports")
        
        if event.selection.rows:
            sel_item = live_items[event.selection.rows[0]]
            with st.container(border=True):
                st.markdown(f"**Edit Live Record:** {sel_item['port_speed_mbps']} Mbps Port")
                c1, c2 = st.columns(2)
                with c1: nrc = st.number_input("NRC Amount ($)", value=float(sel_item.get("nrc_amount", 0)), key="lp_nrc")
                with c2: mrc = st.number_input("MRC Amount ($)", value=float(sel_item["mrc_amount"]), key="lp_mrc")
                
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Live Port", theme="amber", use_container_width=True, key="lp_upd"):
                        payload = {"rate_id": st.session_state.active_rate_id, "port_speed_mbps": sel_item['port_speed_mbps'], "nrc_amount": nrc, "mrc_amount": mrc}
                        api_billing.put_billing_port(sel_item["id"], payload)
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Live Port", theme="red", use_container_width=True, key="lp_del"):
                        api_billing.delete_billing_port(sel_item["id"])
                        st.rerun()
        st.divider()

    def step_2_port_pricing(self):
        st.header("Step 2: Physical Port Catalog")
        
        # 1. Live Data at the Top
        self._render_live_ports()
        
        # 2. Staged Data Table
        selected_index = None
        if st.session_state.staged_catalog["ports"]:
            c1, c2 = st.columns([4, 1])
            with c1: st.subheader("Staged Port Tiers")
            with c2: 
                if self._themed_button("🗑️ Clear All Ports", theme="amber", key="clear_ports", use_container_width=True):
                    st.session_state.staged_catalog["ports"] = []
                    st.rerun()
            df = pd.DataFrame(st.session_state.staged_catalog["ports"])
            event = st.dataframe(df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_ports")
            if event.selection.rows: selected_index = event.selection.rows[0]
            if self._themed_button("🚀 Post Staged Ports to Database", theme="green", key="commit_ports", use_container_width=True):
                for p in st.session_state.staged_catalog["ports"]: api_billing.post_billing_port(p)
                st.session_state.staged_catalog["ports"] = []
                st.rerun()
            st.divider()

        # 3. Form Component
        self._render_port_form(selected_index)

    def _render_port_form(self, selected_index):
        if selected_index is not None:
            data = st.session_state.staged_catalog["ports"][selected_index]
            with st.container(border=True):
                st.markdown("**Update Staged Port**")
                c1, c2, c3 = st.columns(3)
                speed_opts = [1000, 10000, 100000, 400000]
                idx = speed_opts.index(data["port_speed_mbps"]) if data["port_speed_mbps"] in speed_opts else 0
                with c1: speed = st.selectbox("Port Speed (Mbps)", speed_opts, index=idx, key="p_spd_edit")
                with c2: nrc = st.number_input("NRC Amount ($)", value=float(data["nrc_amount"]), key="p_nrc_edit")
                with c3: mrc = st.number_input("MRC Amount ($)", value=float(data["mrc_amount"]), key="p_mrc_edit")
                
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Staged Selection", theme="amber", use_container_width=True):
                        st.session_state.staged_catalog["ports"][selected_index] = {"rate_id": st.session_state.active_rate_id, "port_speed_mbps": speed, "nrc_amount": nrc, "mrc_amount": mrc}
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Staged Selection", theme="red", use_container_width=True):
                        st.session_state.staged_catalog["ports"].pop(selected_index)
                        st.rerun()
        else:
            st.subheader("Stage Port Pricing")
            tab_auto, tab_manual = st.tabs(["⚡ Auto-Generate Tiers", "➕ Single Entry"])
            with tab_auto:
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: base_mrc = st.number_input("Base 1G MRC ($)", value=500.0, step=50.0, key="auto_mrc")
                    with c2: multiplier = st.number_input("Growth Factor", value=2.0, step=0.1, key="auto_mult")
                    with c3: base_nrc = st.number_input("Universal NRC ($)", value=0.0, step=50.0, key="auto_nrc")
                    if self._themed_button("⚡ Generate Port Catalog", theme="green", use_container_width=True):
                        speeds = [1000, 10000, 100000, 400000]
                        current_mrc = base_mrc
                        for i, speed in enumerate(speeds):
                            calc_mrc = current_mrc if i == 0 else math.floor((current_mrc * multiplier) / 10) * 10
                            current_mrc = calc_mrc
                            st.session_state.staged_catalog["ports"].append({"rate_id": st.session_state.active_rate_id, "port_speed_mbps": speed, "nrc_amount": base_nrc, "mrc_amount": calc_mrc})
                        st.rerun()
            with tab_manual:
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: speed = st.selectbox("Port Speed (Mbps)", [1000, 10000, 100000, 400000], key="man_spd")
                    with c2: nrc = st.number_input("NRC Amount ($)", value=0.0, key="man_nrc")
                    with c3: mrc = st.number_input("MRC Amount ($)", value=150.0, key="man_mrc")
                    if self._themed_button("➕ Stage Single Port", theme="green", use_container_width=True):
                        st.session_state.staged_catalog["ports"].append({"rate_id": st.session_state.active_rate_id, "port_speed_mbps": speed, "nrc_amount": nrc, "mrc_amount": mrc})
                        st.rerun()
    # =========================================================
    # --- STEP 3: ACCESS COMPONENTS ---
    # =========================================================
    def _render_live_access(self):
        live_items = self.live_data.get("access_tiers", [])
        
        st.subheader("🟢 Live Database Access Tiers")
        
        # CHANGED: Added explicit empty state instead of a silent return
        if not live_items:
            st.info("No live access tiers found for this commercial context. Stage and commit access tiers below to populate the database.")
            st.divider()
            return
            
        df = pd.DataFrame(live_items)
        valid_cols = [c for c in ["id", "access_code", "location_type", "port_speed_mbps", "nrc_amount", "mrc_amount"] if c in df.columns]
        event = st.dataframe(df[valid_cols], use_container_width=True, on_select="rerun", selection_mode="single-row", key="live_acc")
        
        if event.selection.rows:
            sel_item = live_items[event.selection.rows[0]]
            with st.container(border=True):
                st.markdown(f"**Edit Live Record:** {sel_item['access_code']} ({sel_item['port_speed_mbps']} Mbps)")
                c1, c2 = st.columns(2)
                with c1: nrc = st.number_input("NRC Amount ($)", value=float(sel_item["nrc_amount"]), key="la_nrc")
                with c2: mrc = st.number_input("MRC Amount ($)", value=float(sel_item["mrc_amount"]), key="la_mrc")
                
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Live Access", theme="amber", use_container_width=True, key="la_upd"):
                        payload = {"rate_id": st.session_state.active_rate_id, "access_code": sel_item['access_code'], "location_type": sel_item['location_type'], "port_speed_mbps": sel_item['port_speed_mbps'], "nrc_amount": nrc, "mrc_amount": mrc}
                        api_billing.put_billing_access(sel_item["id"], payload)
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Live Access", theme="red", use_container_width=True, key="la_del"):
                        api_billing.delete_billing_access(sel_item["id"])
                        st.rerun()
        st.divider()

    def step_3_access_pricing(self):
        st.header("Step 3: Network Access Catalog")
        self._render_live_access()
        idx = self._render_access_table()
        st.divider()
        self._render_access_form(idx)
    
    def _render_access_table(self):
        selected_index = None
        
        # CHANGED: Headers and buttons are always rendered to prevent UI jumping
        c1, c2 = st.columns([4, 1])
        with c1: st.subheader("Staged Access Pricing")
        with c2:
            has_staged = bool(st.session_state.staged_catalog["access"])
            if self._themed_button("🗑️ Clear All Access", theme="amber", key="clear_access", use_container_width=True, disabled=not has_staged):
                st.session_state.staged_catalog["access"] = []
                st.rerun()
                
        # CHANGED: Explicit empty state for staging
        if st.session_state.staged_catalog["access"]:
            df = pd.DataFrame(st.session_state.staged_catalog["access"])
            event = st.dataframe(df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_acc")
            if event.selection.rows: selected_index = event.selection.rows[0]
            if self._themed_button("🚀 Post Staged Access to Database", theme="green", key="commit_access", use_container_width=True):
                for a in st.session_state.staged_catalog["access"]: api_billing.post_billing_access(a)
                st.session_state.staged_catalog["access"] = []
                st.rerun()
        else:
            st.info("No access tiers currently staged. Use the tools below to generate access pricing.")
            
        return selected_index

    def _render_access_form(self, selected_index):
        ALL_SPEEDS = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 400000]
        if selected_index is not None:
            data = st.session_state.staged_catalog["access"][selected_index]
            with st.container(border=True):
                st.markdown("**Update Staged Access**")
                c1, c2, c3 = st.columns(3)
                with c1: access = st.selectbox("Access Code", ["ONNET", "OFFNET"], index=["ONNET", "OFFNET"].index(data["access_code"]), key="a_acc_edit")
                with c2: provider = st.text_input("Provider Tag", value=data["location_type"], key="a_prov_edit")
                with c3: speed = st.selectbox("Speed (Mbps)", ALL_SPEEDS, index=ALL_SPEEDS.index(data["port_speed_mbps"]), key="a_spd_edit")
                c4, c5 = st.columns(2)
                with c4: nrc = st.number_input("NRC Amount ($)", value=float(data["nrc_amount"]), key="a_nrc_edit")
                with c5: mrc = st.number_input("MRC Amount ($)", value=float(data["mrc_amount"]), key="a_mrc_edit")
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Staged Selection", theme="amber", use_container_width=True):
                        st.session_state.staged_catalog["access"][selected_index] = {"rate_id": st.session_state.active_rate_id, "access_code": access, "location_type": provider, "port_speed_mbps": speed, "nrc_amount": nrc, "mrc_amount": mrc}
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Staged Selection", theme="red", use_container_width=True):
                        st.session_state.staged_catalog["access"].pop(selected_index)
                        st.rerun()
        else:
            st.subheader("Stage Access Pricing")
            tab_batch, tab_manual = st.tabs(["⚡ Batch Offnet Tiers", "➕ Single Entry"])
            with tab_batch:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1: provider_tag = st.text_input("Provider / Location Tag", value="AT&T", key="a_prov_batch")
                    with c2: base_nrc = st.number_input("Universal NRC ($)", value=0.0, step=50.0, key="a_nrc_batch")
                    selected_speeds = st.multiselect("Select Speeds", options=ALL_SPEEDS, default=[50, 100, 200, 500, 1000, 10000, 100000])
                    c3, c4 = st.columns(2)
                    with c3: base_mrc = st.number_input("Base MRC ($)", value=500.0, step=50.0, key="a_mrc_base_batch")
                    with c4: multiplier = st.number_input("Growth Factor", value=1.4, step=0.05, key="a_mult_batch")
                    if self._themed_button("⚡ Generate Matrix", theme="green", use_container_width=True):
                        current_mrc = base_mrc
                        for i, speed in enumerate(sorted(selected_speeds)):
                            calc_mrc = current_mrc if i == 0 else math.floor((current_mrc * multiplier) / 10) * 10
                            current_mrc = calc_mrc
                            st.session_state.staged_catalog["access"].append({"rate_id": st.session_state.active_rate_id, "access_code": "OFFNET", "location_type": provider_tag, "port_speed_mbps": speed, "nrc_amount": base_nrc, "mrc_amount": calc_mrc})
                        st.rerun()
            with tab_manual:
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: access = st.selectbox("Access Code", ["ONNET", "OFFNET"], key="a_acc_man")
                    with c2: provider = st.text_input("Provider Tag", value="DEFAULT", key="a_prov_man")
                    with c3: speed = st.selectbox("Speed (Mbps)", ALL_SPEEDS, index=4, key="a_spd_man")
                    c4, c5 = st.columns(2)
                    with c4: nrc = st.number_input("NRC Amount ($)", value=0.0, key="a_nrc_man")
                    with c5: mrc = st.number_input("MRC Amount ($)", value=500.0, key="a_mrc_man")
                    if self._themed_button("➕ Stage Single Access", theme="green", use_container_width=True):
                        st.session_state.staged_catalog["access"].append({"rate_id": st.session_state.active_rate_id, "access_code": access, "location_type": provider, "port_speed_mbps": speed, "nrc_amount": nrc, "mrc_amount": mrc})
                        st.rerun()
    # =========================================================
    # --- STEP 4: BANDWIDTH COMPONENTS ---
    # =========================================================
    def _render_live_bw(self):
        live_items = self.live_data.get("bandwidth_ladders", [])
        
        st.subheader("🟢 Live Database BW Ladders")
        
        # CHANGED: Added explicit empty state instead of a silent return
        if not live_items:
            st.info("No live bandwidth ladders found for this commercial context. Stage and commit bandwidth tiers below to populate the database.")
            st.divider()
            return
            
        df = pd.DataFrame(live_items)
        valid_cols = [c for c in ["id", "service_type", "service_bw_mbps", "nrc_amount", "mrc_amount"] if c in df.columns]
        event = st.dataframe(df[valid_cols], use_container_width=True, on_select="rerun", selection_mode="single-row", key="live_bw")
        
        if event.selection.rows:
            sel_item = live_items[event.selection.rows[0]]
            with st.container(border=True):
                st.markdown(f"**Edit Live Record:** {sel_item['service_type']} ({sel_item['service_bw_mbps']} Mbps)")
                c1, c2 = st.columns(2)
                with c1: nrc = st.number_input("NRC Amount ($)", value=float(sel_item.get("nrc_amount", 0)), key="lbw_nrc")
                with c2: mrc = st.number_input("MRC Amount ($)", value=float(sel_item["mrc_amount"]), key="lbw_mrc")
                
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Live BW", theme="amber", use_container_width=True, key="lbw_upd"):
                        payload = {"rate_id": st.session_state.active_rate_id, "service_type": sel_item['service_type'], "service_bw_mbps": sel_item['service_bw_mbps'], "nrc_amount": nrc, "mrc_amount": mrc}
                        api_billing.put_billing_bw(sel_item["id"], payload)
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Live BW", theme="red", use_container_width=True, key="lbw_del"):
                        api_billing.delete_billing_bw(sel_item["id"])
                        st.rerun()
        st.divider()

    def step_4_bandwidth_ladders(self):
        st.header("Step 4: Bandwidth Ladders")
        self._render_live_bw()
        idx = self._render_bw_table()
        st.divider()
        self._render_bw_form(idx)

    def _render_bw_table(self):
        selected_index = None
        
        # CHANGED: Headers and buttons are always rendered to prevent UI jumping
        c1, c2 = st.columns([4, 1])
        with c1: st.subheader("Staged Bandwidth Tiers")
        with c2:
            has_staged = bool(st.session_state.staged_catalog["bw_ladders"])
            if self._themed_button("🗑️ Clear All BW", theme="amber", key="clear_bw", use_container_width=True, disabled=not has_staged):
                st.session_state.staged_catalog["bw_ladders"] = []
                st.rerun()
                
        # CHANGED: Explicit empty state for staging
        if st.session_state.staged_catalog["bw_ladders"]:
            df = pd.DataFrame(st.session_state.staged_catalog["bw_ladders"])
            event = st.dataframe(df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_bw")
            if event.selection.rows: selected_index = event.selection.rows[0]
            if self._themed_button("🚀 Post Staged BW to Database", theme="green", key="commit_bw", use_container_width=True):
                for bw in st.session_state.staged_catalog["bw_ladders"]: api_billing.post_billing_bw(bw)
                st.session_state.staged_catalog["bw_ladders"] = []
                st.rerun()
        else:
            st.info("No bandwidth tiers currently staged. Use the tools below to generate bandwidth pricing.")
            
        return selected_index

    def _render_bw_form(self, selected_index):
        SERVICES = {"IOD": ["Best Effort"], "IPVPN": ["6Q-Multi-COS"], "MCGW": ["Best Effort", "6Q-Multi-COS", "Dedicated"]}
        ALL_SPEEDS = [50, 100, 200, 500, 1000, 10000, 100000]
        if selected_index is not None:
            data = st.session_state.staged_catalog["bw_ladders"][selected_index]
            with st.container(border=True):
                st.markdown("**Update Staged BW**")
                c1, c2 = st.columns(2)
                with c1: nrc = st.number_input("NRC Amount ($)", value=float(data["nrc_amount"]), key="bw_nrc_edit")
                with c2: mrc = st.number_input("MRC Amount ($)", value=float(data["mrc_amount"]), key="bw_mrc_edit")
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Selection", theme="amber", use_container_width=True):
                        st.session_state.staged_catalog["bw_ladders"][selected_index]["nrc_amount"] = nrc
                        st.session_state.staged_catalog["bw_ladders"][selected_index]["mrc_amount"] = mrc
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Selection", theme="red", use_container_width=True):
                        st.session_state.staged_catalog["bw_ladders"].pop(selected_index)
                        st.rerun()
        else:
            st.subheader("Stage Bandwidth")
            tab_manual, = st.tabs(["➕ Single Entry"])
            with tab_manual:
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: man_svc = st.selectbox("Service Type", list(SERVICES.keys()), key="bw_man_svc")
                    with c2: man_cos = st.selectbox("Class of Service", SERVICES[man_svc], key="bw_man_cos")
                    with c3: man_bw = st.selectbox("Service BW (Mbps)", ALL_SPEEDS, index=4, key="bw_man_bw")
                    c4, c5 = st.columns(2)
                    with c4: man_nrc = st.number_input("NRC ($)", value=0.0, key="bw_man_nrc")
                    with c5: man_mrc = st.number_input("MRC ($)", value=100.0, key="bw_man_mrc")
                    if self._themed_button("➕ Stage Entry", theme="green", use_container_width=True):
                        st.session_state.staged_catalog["bw_ladders"].append({"rate_id": st.session_state.active_rate_id, "service_type": f"{man_svc} - {man_cos}", "service_bw_mbps": man_bw, "nrc_amount": man_nrc, "mrc_amount": man_mrc})
                        st.rerun()
    # =========================================================
    # --- STEP 5: TOKEN COMPONENTS ---
    # =========================================================
    def _render_live_tokens(self):
        live_items = self.live_data.get("usage_tokens", [])
        
        st.subheader("🟢 Live Database Tokens")
        
        # CHANGED: Added explicit empty state instead of a silent return
        if not live_items:
            st.info("No live usage tokens found for this commercial context. Stage and commit tokens below to populate the database.")
            st.divider()
            return
            
        df = pd.DataFrame(live_items)
        valid_cols = [c for c in ["id", "service_type", "included_gb_per_month", "token_cost_per_gb", "mrc_amount"] if c in df.columns]
        event = st.dataframe(df[valid_cols], use_container_width=True, on_select="rerun", selection_mode="single-row", key="live_tok")
        
        if event.selection.rows:
            sel_item = live_items[event.selection.rows[0]]
            with st.container(border=True):
                st.markdown(f"**Edit Live Record:** {sel_item['service_type']} ({sel_item['included_gb_per_month']} GB)")
                c1, c2 = st.columns(2)
                with c1: cgb = st.number_input("Effective Cost ($/GB)", value=float(sel_item["token_cost_per_gb"]), format="%.4f", key="lt_cgb")
                with c2: mrc = st.number_input("Final MRC Amount ($)", value=float(sel_item["mrc_amount"]), key="lt_mrc")
                
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Live Token", theme="amber", use_container_width=True, key="lt_upd"):
                        payload = {"rate_id": st.session_state.active_rate_id, "service_type": sel_item['service_type'], "included_gb_per_month": sel_item['included_gb_per_month'], "token_cost_per_gb": cgb, "mrc_amount": mrc}
                        api_billing.put_billing_token(sel_item["id"], payload)
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Live Token", theme="red", use_container_width=True, key="lt_del"):
                        api_billing.delete_billing_token(sel_item["id"])
                        st.rerun()
        st.divider()

    def step_5_usage_tokens(self):
        st.header("Step 5: Usage Tokens")
        self._render_live_tokens()
        idx = self._render_token_table()
        st.divider()
        self._render_token_form(idx)    

    def _render_token_table(self):
        selected_index = None
        
        # CHANGED: Headers and buttons are always rendered to prevent UI jumping
        c1, c2 = st.columns([4, 1])
        with c1: st.subheader("Staged Token Models")
        with c2:
            has_staged = bool(st.session_state.staged_catalog["tokens"])
            if self._themed_button("🗑️ Clear All Tokens", theme="amber", key="clear_tokens", use_container_width=True, disabled=not has_staged):
                st.session_state.staged_catalog["tokens"] = []
                st.rerun()
                
        # CHANGED: Explicit empty state for staging
        if st.session_state.staged_catalog["tokens"]:
            df = pd.DataFrame(st.session_state.staged_catalog["tokens"])
            event = st.dataframe(df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_tok")
            if event.selection.rows: selected_index = event.selection.rows[0]
            if self._themed_button("🚀 Post Staged Tokens to Database", theme="green", key="commit_tokens", use_container_width=True):
                for t in st.session_state.staged_catalog["tokens"]: api_billing.post_billing_token(t)
                st.session_state.staged_catalog["tokens"] = []
                st.rerun()
        else:
            st.info("No tokens currently staged. Use the tools below to generate token pricing.")
            
        return selected_index

    def _render_token_form(self, selected_index):
        SERVICES = {"IOD": ["Best Effort"], "IPVPN": ["6Q-Multi-COS"]}
        CONSUMPTION_VOLUMES = [100000, 200000, 500000, 1000000, 5000000, 10000000]
        if selected_index is not None:
            data = st.session_state.staged_catalog["tokens"][selected_index]
            with st.container(border=True):
                st.markdown("**Update Staged Token**")
                c1, c2 = st.columns(2)
                with c1: cost_gb = st.number_input("Cost ($/GB)", value=float(data["token_cost_per_gb"]), format="%.4f", key="t_cgb_edit")
                with c2: mrc = st.number_input("Final MRC ($)", value=float(data["mrc_amount"]), key="t_mrc_edit")
                b1, b2 = st.columns(2)
                with b1:
                    if self._themed_button("💾 Update Selection", theme="amber", use_container_width=True):
                        st.session_state.staged_catalog["tokens"][selected_index]["token_cost_per_gb"] = cost_gb
                        st.session_state.staged_catalog["tokens"][selected_index]["mrc_amount"] = mrc
                        st.rerun()
                with b2:
                    if self._themed_button("🗑️ Delete Selection", theme="red", use_container_width=True):
                        st.session_state.staged_catalog["tokens"].pop(selected_index)
                        st.rerun()
        else:
            st.subheader("Stage Usage Tokens")
            tab_manual, = st.tabs(["➕ Single Entry"])
            with tab_manual:
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: man_svc = st.selectbox("Service", list(SERVICES.keys()), key="t_man_svc")
                    with c2: man_cos = st.selectbox("CoS", SERVICES[man_svc], key="t_man_cos")
                    with c3: man_vol = st.selectbox("Volume (GB)", CONSUMPTION_VOLUMES, index=0, key="t_man_vol")
                    c4, c5 = st.columns(2)
                    with c4: man_cgb = st.number_input("Cost per GB ($)", format="%.4f", value=0.0150, key="t_man_cgb")
                    with c5: man_mrc = st.number_input("MRC ($)", value=float(man_vol*man_cgb), key="t_man_mrc")
                    if self._themed_button("➕ Stage Token", theme="green", use_container_width=True):
                        st.session_state.staged_catalog["tokens"].append({"rate_id": st.session_state.active_rate_id, "service_type": f"{man_svc} - {man_cos}", "token_cost_per_gb": man_cgb, "included_gb_per_month": man_vol, "mrc_amount": man_mrc})
                        st.rerun()
    # =========================================================
    # --- STEPS 6 & 7: PROVIDERS & COMMIT ---
    # =========================================================
    def step_6_providers(self):
        st.header("Step 6: Partner Ecosystem")
        st.info("Live editing of Providers is omitted here. Only staging available.")

    def step_7_review_and_commit(self):
        st.header("Step 7: Final Review")
        st.markdown("All Live Database records are updated instantly when edited in Steps 1-5.")
        st.warning("Any remaining Staged items will be discarded if not committed.")

    def run(self):
        self._render_header()
        steps = {1: self.step_1_rate_card, 2: self.step_2_port_pricing, 3: self.step_3_access_pricing, 4: self.step_4_bandwidth_ladders, 5: self.step_5_usage_tokens, 6: self.step_6_providers, 7: self.step_7_review_and_commit}
        steps.get(self.current_step)()
        self._render_navigation()

def run_billing_dashboard():
    wizard = BillingCatalogWizard()
    
    # --- UPDATED TAB LAYOUT ---
    main_tab_builder, main_tab_explorer, tab_cap_builder, tab_cap_viewer = st.tabs([
        "🛠️ Catalog Builder & Editor", 
        "🗂️ Catalog Explorer (Summary)",
        "🏗️ Capabilities Builder",
        "👁️ Capabilities Viewer"
    ])
    
    with main_tab_builder:
        try: wizard.run()
        except Exception as e:
            st.error("Builder encountered an error.")
            st.exception(e)
            st.markdown('<div class="theme-amber" style="display:none;"></div>', unsafe_allow_html=True)
            if st.button("Reset Dashboard Session", key="reset_builder"):
                st.session_state.clear()
                st.rerun()
                
    with main_tab_explorer:
        try: run_catalog_explorer()
        except Exception as e:
            st.error("Explorer encountered an error.")
            st.exception(e)

    # --- INTEGRATED CAPABILITY TABS ---
    with tab_cap_builder:
        try: 
            run_capabilities_builder()
        except Exception as e:
            st.error("Capabilities Builder encountered an error.")
            st.exception(e)

    with tab_cap_viewer:
        try: 
            run_capabilities_viewer()
        except Exception as e:
            st.error("Capabilities Viewer encountered an error.")
            st.exception(e)

if __name__ == "__main__":
    run_billing_dashboard()