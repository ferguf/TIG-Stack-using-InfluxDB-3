import streamlit as st
import pandas as pd
import uuid
from streamlit_extras.stylable_container import stylable_container

# ==========================================
# 1. THE UI MASTER CLASS (Omni-Compatible)
# ==========================================

class UI:
    @staticmethod
    def button(label, color="blue", key=None, use_container_width=False, **kwargs):
        """
        Standardized NDT Button.
        Maintains internal padding and min-width while supporting custom colors.
        """
        color_map = {
            "green": "#28a745",
            "red": "#dc3545",
            "orange": "#fd7e14",
            "amber": "#ffbf00",
            "blue": "#007bff",
            "gray": "#6c757d"
        }
        hex_color = color_map.get(color, "#6c757d")
        
        # Scale to text logic + min-width 200px
        width_css = "100%" if use_container_width else "auto"
        min_width_css = "0px" if use_container_width else "200px"

        with stylable_container(
            key=f"container_{key}",
            css_styles=f"""
                button {{
                    background-color: {hex_color} !important;
                    color: white !important;
                    border-radius: 4px;
                    min-width: {min_width_css} !important;
                    width: {width_css} !important;
                    padding: 0 20px !important;
                    white-space: nowrap !important;
                    height: 34px !important;
                    border: none !important;
                    font-weight: 500 !important;
                }}
                button:hover {{ filter: brightness(92%); border: none !important; }}
            """,
        ):
            return st.button(label, key=key, **kwargs)

    @staticmethod
    def render_selectable_table(df, key_prefix, id_column_to_hide=None, id_columns_to_hide=None, id_to_hide=None):
        """
        Renders an NDT-styled table with row selection.
        PROTECTION: Accepts all historical variants of 'hide' arguments to prevent NameErrors.
        """
        if df is None or df.empty:
            st.info("No data available.")
            return None

        display_df = df.copy()
        if "Select" not in display_df.columns:
            display_df.insert(0, "Select", False)

        # Content Hash to prevent state loss on refresh
        data_hash = hash(pd.util.hash_pandas_object(df).sum())
        
        column_config = {
            "Select": st.column_config.CheckboxColumn("Select", help="Select a row", default=False)
        }

        # --- Interop: Consolidate all 'hide' argument variants ---
        hide_candidates = [id_column_to_hide, id_columns_to_hide, id_to_hide]
        to_hide = []
        for candidate in hide_candidates:
            if candidate:
                if isinstance(candidate, list): to_hide.extend(candidate)
                else: to_hide.append(candidate)

        for col in to_hide:
            if col in display_df.columns:
                column_config[col] = None
        # ---------------------------------------------------------

        edited_df = st.data_editor(
            display_df,
            key=f"{key_prefix}_{data_hash}_editor",
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            disabled=[c for c in display_df.columns if c != "Select"]
        )

        selected_rows = edited_df[edited_df["Select"] == True]
        if not selected_rows.empty:
            record = selected_rows.drop(columns=["Select"]).iloc[-1].to_dict()
            # Standard NDT state synchronization
            if "customer_name" in record:
                st.session_state["last_selected_name"] = record.get("customer_name")
            return record
        
        st.session_state["last_selected_name"] = None
        return None

    @staticmethod
    def render_service_context(fs_record, fc_record=None):
        """Standardized NDT context header."""
        if not fs_record:
            st.warning("⚠️ **Service Context Unavailable**")
            return False

        st.markdown("""
            <style>
                .context-box {
                    background-color: #f8fafc; padding: 12px; border-radius: 8px;
                    border: 1px solid #e2e8f0; margin-bottom: 1rem;
                }
                .context-label { color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; }
            </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown(f"### 🔗 Service: **{fs_record.get('service_name', 'N/A')}**")
            st.markdown('<div class="context-box">', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown('<p class="context-label">Type</p>', unsafe_allow_html=True)
                st.markdown(f"**{fs_record.get('service_type', 'N/A')}**")
            with c2:
                st.markdown('<p class="context-label">RT</p>', unsafe_allow_html=True)
                st.code(fs_record.get("route_target", "N/A"), language="text")
            with c3:
                st.markdown('<p class="context-label">Conn</p>', unsafe_allow_html=True)
                st.markdown(f"**{fc_record.get('connection_name', 'None')}**" if fc_record else "—")
            with c4:
                st.markdown('<p class="context-label">Fabric</p>', unsafe_allow_html=True)
                st.markdown("🟢 **Active**" if fs_record and fc_record else "🟡 **Draft**")
            st.markdown('</div>', unsafe_allow_html=True)
        return True

# ==========================================
# 2. STANDALONE HELPERS
# ==========================================

def display_topology_data(nodes, orbits, links, key_prefix="debug"):
    if st.toggle(f"🛠️ Debug: {key_prefix}", value=False, key=f"t_{key_prefix}"):
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1: st.json(orbits)
        with c2: st.json(nodes)
        with c3: st.json(links)

def render_metrics(metrics: dict):
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)

def render_table(df: pd.DataFrame, title: str):
    st.subheader(title)
    st.dataframe(df, use_container_width=True, hide_index=True)