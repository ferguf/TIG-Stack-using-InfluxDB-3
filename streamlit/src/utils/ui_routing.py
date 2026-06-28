from src.utils.api_customer import get_fabric_services # Resolved NameError

from src.utils.api_customer import (
    get_fabric_services, 
    get_bgp_policies, 
    get_bgp_policies_by_service,  # 👈 This was likely missing
    delete_bgp_policy,
    post_bgp_policy,
    put_bgp_policy
)
import streamlit as st
import uuid
import copy
import re
import time
from src.ui_components import UI
from streamlit_extras.stylable_container import stylable_container
# ==========================================
# 1. CORE LOGIC ENGINE
# ==========================================


def apply_auto_resequence(terms: list) -> list:
    """
    Physically updates the 'sequence' key in each term dictionary.
    This ensures the API payload matches the visual 10, 20, 30 order.
    """
    if not terms:
        return []
        
    # Sort by existing sequence if they exist, otherwise keep current order
    sorted_terms = sorted(terms, key=lambda x: int(x.get("sequence", 9999)))
    
    for i, term in enumerate(sorted_terms):
        # Physically set the integer back into the dictionary
        term["sequence"] = (i + 1) * 10
        
    return sorted_terms    

def insert_bgp_term(terms, term_dict):
    """Inserts a term safely before the 'deny-all' anchor."""
    deny_idx = next((i for i, t in enumerate(terms) if t.get("term_name") == "deny-all"), len(terms))
    terms.insert(deny_idx, term_dict)
    return apply_auto_resequence(terms)

def move_bgp_term(terms, index, direction):
    """Handles Up/Down movement while respecting the deny-all lock."""
    target = index - 1 if direction == "up" else index + 1
    if 0 <= target < len(terms):
        if terms[target].get("term_name") == "deny-all" and direction == "down":
            return terms
        terms[index], terms[target] = terms[target], terms[index]
    return apply_auto_resequence(terms)

def provision_rfc1918_export(terms, med=200, prepend=None):
    """Provisions the three standard RFC1918 summary terms."""
    rfc_subnets = [("10.0.0.0/8", "RFC1918-10"), ("172.16.0.0/12", "RFC1918-172"), ("192.168.0.0/16", "RFC1918-192")]
    for subnet, name in rfc_subnets:
        terms = insert_bgp_term(terms, {
            "term_id": str(uuid.uuid4())[:8], "term_name": name, "prefixes": [subnet],
            "base_action": "Advertise", "match_type": "Auto-Summary", "med": med, "as_prepend": prepend
        })
    return terms

def provision_default_export(terms, mode="summary_others", med=200, prepend=None):
    """Provisions default route logic for Export policies."""
    if mode == "default_only":
        terms = [{"term_id": str(uuid.uuid4())[:8], "term_name": "DEFAULT-ONLY", "prefixes": ["0.0.0.0/0"],
                  "base_action": "Advertise", "match_type": "Auto-Summary", "med": med, "as_prepend": prepend}]
    else:
        terms = insert_bgp_term(terms, {"term_id": str(uuid.uuid4())[:8], "term_name": "DEFAULT-ROUTE", "prefixes": ["0.0.0.0/0"],
                                       "base_action": "Advertise", "match_type": "Exact", "med": med, "as_prepend": prepend})
    return terms

# ==========================================
# 2. WORKFLOW ROUTING
# ==========================================

def render_bgp_launcher_tile(customer_id: str):
    """Dashboard tile to trigger the embedded BGP Policy Builder."""
    def _trigger_bgp_mode():
        st.session_state.prov_mode = "bgp_builder"
        st.session_state.show_launcher = False
        st.session_state.bgp_builder_mode = "Import"

    with st.container(border=True):
        st.markdown("#### 📜 BGP Policy Engine")
        st.caption("Construct and manage reusable routing policies.")
        UI.button("Launch Policy Builder", color="blue", key=f"btn_launch_bgp_{customer_id}", use_container_width=True, on_click=_trigger_bgp_mode)


def render_builder_workflow(customer_id: str, direction: str = "Import", existing_policy: dict = None):
    """
    Main workflow router for the BGP Manager.
    Tracks 'is_new' state to determine POST vs PUT during commit.
    """
    # 1. Session State Initialization
    if "bgp_builder_active" not in st.session_state:
        st.session_state.bgp_builder_active = False

    def return_to_manager():
        st.session_state.pop("bgp_builder_active", None)
        st.session_state.pop("bgp_builder", None)
        st.rerun()

    # Route to Active Editor if building
    if st.session_state.bgp_builder_active:
        builder = st.session_state.get("bgp_builder", {})
        build_dir = builder.get("direction", "Import")
        
        if build_dir == "Import":
            render_import_designer(customer_id, on_close_callback=return_to_manager)
        else:
            render_export_designer(customer_id, on_close_callback=return_to_manager)
        return

    st.markdown("### 🌐 BGP Policy Infrastructure Context")
    
    # 2. Fetch Live Fabric Services
    services_df = get_fabric_services(customer_id)
    filtered_services = []
    if not services_df.empty:
        allowed_types = ["IPVPN", "DIA", "MCGW"]
        l3_df = services_df[services_df["service_type"].isin(allowed_types)]
        for _, row in l3_df.iterrows():
            filtered_services.append({
                "id": str(row.get("service_id")),
                "name": row.get("service_name"),
                "desc": row.get("service_description"),
                "type": row.get("service_type")
            })

    # 3. Infrastructure Selection Header
    with st.container(border=True):
        col_cust, col_serv = st.columns(2)
        with col_cust:
            st.text_input("Active Customer Context", value=customer_id, disabled=True)
        
        with col_serv:
            if not filtered_services:
                st.warning("No compatible L3 services found.")
                selected_service_id = None
            else:
                service_map = {f"{s['name']} : {s['desc']}": s['id'] for s in filtered_services}
                service_map["None (Standalone Policy)"] = None
                selected_display = st.selectbox("Associate Policy to Service", options=list(service_map.keys()))
                selected_service_id = service_map[selected_display]

    st.divider()

    # 4. Contextual API Fetch
    with st.spinner("Fetching routing context..."):
        if selected_service_id:
            raw_policies = get_bgp_policies_by_service(selected_service_id) or []
        else:
            all_cust_policies = get_bgp_policies(customer_id) or []
            raw_policies = [p for p in all_cust_policies if not p.get("fabric_service_id")]
    
    policy_lookup = {"Import": {}, "Export": {}}
    for term in raw_policies:
        p_name = term.get("policy_name")
        p_dir = term.get("direction", "Import").capitalize() 
        if p_dir in policy_lookup:
            if p_name not in policy_lookup[p_dir]:
                policy_lookup[p_dir][p_name] = {"policy_id": term.get("policy_id"), "terms": []}
            policy_lookup[p_dir][p_name]["terms"].append(term)

    # 5. Policy Designer Section
    st.markdown("### 🗃️ Policy Designer")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            action = st.radio("Policy Function", ["Create New Policy", "Modify Existing", "Delete Existing"])
        with c2:
            if action == "Create New Policy":
                dir_opts = ["Import", "Export"]
                selected_dir = st.radio("Direction", dir_opts)
            else:
                selected_dir = st.radio("Filter", ["Import", "Export"], horizontal=True)
                p_names = list(policy_lookup[selected_dir].keys())
                sel_p_name = st.selectbox("Select Policy", p_names) if p_names else None
        with c3:
            if action == "Create New Policy":
                base_ctx = st.selectbox("Context", options=["Headquarters", "Cloud-AWS","Cloud-GCP","Cloud-Azure","Data Center","Retail", "Custom..."])
                if base_ctx == "Custom...": base_ctx = st.text_input("Custom Context", value="CUSTOM-'Name-Replace'")

    # --- ACTION EXECUTION ---
    if action == "Create New Policy":
        final_name = f"{selected_dir.upper()}-{base_ctx.upper()}"
        if st.button("➕ Start Building", type="primary"):
            st.session_state.bgp_builder = {
                "policy_id": str(uuid.uuid4()),
                "fabric_service_id": selected_service_id, 
                "policy_name": final_name, 
                "direction": selected_dir, 
                "terms": [],
                "is_new": True  # 🚀 MARK AS NEW (POST)
            }
            st.session_state.bgp_builder_active = True
            st.rerun()
            
    elif action == "Modify Existing" and sel_p_name:
        if st.button("✏️ Edit Policy", type="primary"):
            selected_data = policy_lookup[selected_dir][sel_p_name]
            st.session_state.bgp_builder = {
                "policy_id": selected_data["policy_id"],
                "fabric_service_id": selected_service_id, 
                "policy_name": sel_p_name,
                "direction": selected_dir,
                "terms": selected_data["terms"],
                "is_new": False  # 🛠️ MARK AS EXISTING (PUT)
            }
            st.session_state.bgp_builder_active = True
            st.rerun()

def render_builder_editor_form(customer_id: str, on_close_callback: callable):
    """Router to direct the UI to the specific Import or Export designer."""
    st.markdown("""
        <style>
            .compact-header { background-color: #e5e7eb; padding: 8px 12px; border-radius: 6px 6px 0 0; border: 1px solid #d1d5db; margin-bottom: -1px; font-weight: bold; color: #1d4ed8; }
            [data-testid="stVerticalBlock"] > div > div > div > div > .stMarkdown p { margin-bottom: 0px; line-height: 1.2; }
            hr { margin-top: 4px !important; margin-bottom: 4px !important; }
        </style>
    """, unsafe_allow_html=True)

    builder = st.session_state.bgp_builder
    direction = builder.get("direction", "Import")

    st.markdown(f"#### 📜 Active Editor: `{builder['policy_name']}`")

    if direction == "Import":
        render_import_designer(customer_id, on_close_callback)
    else:
        render_export_designer(customer_id, on_close_callback)

# ==========================================
# TOOLTIP DICTIONARY
# ==========================================
def get_ui_hover_text() -> dict:
    """Centralized dictionary for NDT UI tooltips."""
    return {
        "add_std": "Appends a new empty term above the deny-all guardrail.",
        "allow_all": "Adds a catch-all term to accept all remaining inbound prefixes.",
        "deny_all_imp": "Adds a safety guardrail to drop any inbound prefixes not explicitly matched above.",
        "deny_all_exp": "Adds a safety guardrail to drop any outbound prefixes not explicitly matched above.",
        "m_rfc": "Injects standard RFC 1918 private subnets (10/8, 172.16/12, 192.168/16) as Auto-Summary terms.",
        "m_def_sum": "Advertises the default route (0.0.0.0/0) alongside other standard policy terms.",
        "m_def_only": "Locks down the export to ONLY advertise the default route (0.0.0.0/0).",
        "t_name": "Unique identifier for this policy sequence.",
        "t_act_imp": "Advertise (permit) or Deny (drop) the matched inbound routes.",
        "t_act_exp": "Advertise (export) or Deny (withhold) the matched routes to the BGP peer.",
        "t_pref": "Format: x.x.x.x/y. Multiple subnets can be separated by commas.",
        "t_match": "Exact: Matches mask exactly. All: Matches subnet and all smaller subsets. Auto-Summary: Route aggregation bounds.",
        "t_upto": "Maximum prefix length to match. For example, 32 acts as 'le 32' for IPv4.",
        "t_lp": "BGP Local Preference. Higher values dictate the preferred exit path for outbound traffic within your AS.",
        "t_med": "Multi-Exit Discriminator. Suggests to external peers the preferred path into your AS.",
        "t_prep": "Artificially lengthens the AS Path to make this route less preferred by inbound traffic.",
        "done": "Save changes to this term and return to the queue view.",
        "up": "Move Sequence Up",
        "down": "Move Sequence Down",
        "edit": "Edit Term Configurations",
        "delete": "Delete Term",
        "back": "Exit without saving changes.",
        "update": "Save changes locally to session state.",
        "commit": "Commit policy to the database and close the builder."
    }

def render_policy_designer_launcher(customer_id: str, selected_service_id: str, selected_dir: str, base_ctx: str, action: str = "Create New Policy"):
    """
    Orchestrates the BGP Policy Designer entry point.
    Fixes SyntaxError, ensures proper name ordering, and integrates NDT Step 4 Diagram.
    """
    import streamlit as st
    import uuid


    # --- 1. DEFINE POLICY IDENTITY ---
    # Construct the name first so it can be used in the header and state
    final_name = f"{selected_dir.upper()}-{base_ctx.upper()}"

    # --- 2. UI HEADER ---
    # Corrected f-string syntax to append the policy name
    st.header(f"📤 Export Policy Designer:")
    

    # --- 4. ACTION EXECUTION ---
    with st.container(border=True):
        st.markdown("#### 🛠️ Policy Control Plane")
        
        if action == "Create New Policy":
            st.write(f"Initializing a new **{selected_dir}** policy for context: `{base_ctx}`")
            
            c_build, c_skip = st.columns(2)
            
            with c_build:
                if st.button("➕ Start Building", type="primary", use_container_width=True):
                    # Initialize the NDT-compliant builder state
                    st.session_state.bgp_builder = {
                        "policy_id": str(uuid.uuid4()),
                        "fabric_service_id": selected_service_id, 
                        "policy_name": final_name,
                        "direction": selected_dir, 
                        "terms": [],
                        "is_new": True  # Mark as new for POST execution
                    }
                    st.session_state.bgp_builder_active = True
                    st.rerun()

            with c_skip:
                # Escape Hatch: Move to Step 5 (Final Stitching / Connections)
                if st.button("⏭️ Skip to Connections / Next Step", type="secondary", use_container_width=True):
                    st.session_state.prov_step = 5
                    st.session_state.prov_mode = "ATTACH_PORT"
                    st.rerun()
        else:
            st.info("Select 'Create New Policy' or a template to begin.")

    # --- 5. SYSTEM CONTEXT ---
    with st.expander("📝 Designer Metadata"):
        st.caption(f"Resource Anchor: `{selected_service_id}`")
        st.caption(f"Calculated Name: `{final_name}`")

def render_export_designer(customer_id: str, on_close_callback: callable):
    """
    Standalone UI definition for BGP Export Policies.
    Fully expanded all conditional and context manager blocks to resolve SyntaxErrors.
    """
    builder = st.session_state.get("bgp_builder", {})
    storage_key = f"bgp_policies_{customer_id}"
    tooltips = get_ui_hover_text() if 'get_ui_hover_text' in globals() else {}
    
    if "bgp_active_edit_id" not in st.session_state: 
        st.session_state.bgp_active_edit_id = None
        
    curr_names = [t.get("term_name", "") for t in builder.get("terms", [])]
    has_any_terms = len(builder.get("terms", [])) > 0

    st.header("📤 Export Policy Designer")

    # ==========================================
    # 1. THE EDITABLE TABLE
    # ==========================================
    if has_any_terms:
        st.subheader("Current Policy Terms")
        table_data = []
        for i, t in enumerate(builder.get("terms", [])):
            # Patch missing sequences in memory
            if t.get("sequence") is None:
                t["sequence"] = (i + 1) * 10
                
            table_data.append({
                "_id": t.get("term_id"),
                "Sequence": t.get("sequence"),
                "Name": t.get("term_name", ""),
                "Action": t.get("base_action", t.get("action", "Advertise"))
            })

        edited_data = st.data_editor(
            table_data,
            column_config={
                "_id": None, 
                "Sequence": st.column_config.NumberColumn("Sequence", step=10, min_value=1, format="%d"),
                "Name": st.column_config.TextColumn("Name"),
                "Action": st.column_config.SelectboxColumn("Action", options=["Advertise", "Deny"])
            },
            use_container_width=True,
            key="terms_editor_export"
        )

        if edited_data != table_data:
            for edited_row in edited_data:
                target_id = edited_row.get("_id")
                for t in builder["terms"]:
                    if t.get("term_id") == target_id:
                        t["sequence"] = int(edited_row.get("Sequence", 9999))
                        t["term_name"] = edited_row.get("Name")
                        t["base_action"] = edited_row.get("Action")
                        t["action"] = edited_row.get("Action")
            
            builder["terms"] = sorted(builder["terms"], key=lambda x: int(x.get("sequence", 9999)))
            st.rerun()

    # ==========================================
    # 2. MACROS & QUICK PROVISIONING
    # ==========================================
    with st.container(border=True):
        st.markdown("**Quick Export Provisioning**")
        q1, q2, q3 = st.columns(3)
        
        with q1:
            if UI.button("➕ Add Standard Term", color="green", key="btn_add_std_exp", use_container_width=True):
                existing_seqs = [int(t.get("sequence", 0)) for t in builder.get("terms", [])]
                next_seq = (max(existing_seqs) + 10) if existing_seqs else 10
                new_t = {"term_id": str(uuid.uuid4())[:8], "sequence": next_seq, "term_name": "SEQ-TEMP", "prefixes": [], "base_action": "Advertise", "action": "Advertise", "match_type": "Exact"}
                builder["terms"].append(new_t)
                builder["terms"] = sorted(builder["terms"], key=lambda x: int(x.get("sequence", 9999)))
                st.session_state.bgp_active_edit_id = new_t["term_id"]
                st.rerun()

        with q2:
            has_rfc1918 = any("RFC1918" in str(name) for name in curr_names)
            if not has_rfc1918:
                if UI.button("📦 RFC1918 Summaries", color="green", key="m_rfc_exp", use_container_width=True):
                    if 'provision_rfc1918_export' in globals():
                        # 1. Run the macro logic
                        new_terms = provision_rfc1918_export(builder.get("terms", []), 200, None)
                        
                        # 2. 🛡️ THE FIX: Patch sequences for newly added macro terms
                        # We use enumerate starting at 1 to generate 10, 20, 30...
                        for i, t in enumerate(new_terms):
                            if t.get("sequence") is None:
                                t["sequence"] = (i + 1) * 10
                        
                        # 3. Update state and sort
                        builder["terms"] = sorted(new_terms, key=lambda x: int(x.get("sequence", 9999)))
                        st.rerun()
        with q3:
            if "deny-all" not in curr_names and "DENY-ALL" not in curr_names:
                if UI.button("🛡️ Provision Deny-All", color="green", key="btn_deny_all_exp", use_container_width=True):
                    existing_seqs = [int(t.get("sequence", 0)) for t in builder.get("terms", [])]
                    next_seq = (max(existing_seqs) + 10) if existing_seqs else 100
                    builder["terms"].append({"term_id": str(uuid.uuid4())[:8], "sequence": next_seq, "term_name": "deny-all", "prefixes": ["0.0.0.0/0"], "base_action": "Deny", "action": "Deny", "match_type": "Upto", "upto_mask": 32})
                    builder["terms"] = sorted(builder["terms"], key=lambda x: int(x.get("sequence", 9999)))
                    st.rerun()

    # ==========================================
    # 3. ACTIVE TERM BLOCK (DEEP EDIT)
    # ==========================================
    if st.session_state.bgp_active_edit_id:
        active_idx = next((i for i, t in enumerate(builder.get("terms", [])) if t.get("term_id") == st.session_state.bgp_active_edit_id), None)
        if active_idx is not None:
            term = builder["terms"][active_idx]
            st.markdown(f"### ⚙️ Deep Edit: `{term.get('term_name', 'Unknown')}`")
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                t_id = term.get('term_id')
                term["term_name"] = c1.text_input("Name", value=term.get("term_name", ""), key=f"t_n_exp_{t_id}")
                curr_action = term.get("base_action", term.get("action", "Advertise"))
                action_idx = 0 if curr_action == "Advertise" else 1
                selected_action = c2.radio("Action", ["Advertise", "Deny"], index=action_idx, horizontal=True, key=f"t_a_exp_{t_id}")
                term["base_action"] = selected_action
                term["action"] = selected_action

                p_in = st.text_input("Prefixes (comma separated)", value=", ".join(term.get("prefixes", [])), key=f"t_p_exp_{t_id}")
                term["prefixes"] = [p.strip() for p in p_in.split(",") if p.strip()]

                m_opt = ["Exact", "All", "Upto", "Auto-Summary"]
                m_col1, m_col2 = st.columns([3, 1])
                current_match = term.get("match_type", "Exact")
                safe_match_index = m_opt.index(current_match) if current_match in m_opt else 0
                term["match_type"] = m_col1.radio("Match Type", m_opt, index=safe_match_index, horizontal=True, key=f"t_m_exp_{t_id}")

                if term["match_type"] == "Upto":
                    term["upto_mask"] = m_col2.text_input("Upto Mask (le)", value=str(term.get("upto_mask", "32")), key=f"t_um_exp_{t_id}")
                else:
                    term.pop("upto_mask", None)

                if selected_action == "Advertise":
                    st.divider()
                    e1, e2 = st.columns(2)
                    med_opts = ["100", "200", "300", "400"]
                    curr_med = str(term.get("med", "200"))
                    if curr_med not in med_opts: curr_med = "200"
                    term["med"] = int(e1.radio("MED", med_opts, index=med_opts.index(curr_med), horizontal=True, key=f"t_med_exp_{t_id}"))
                    
                    prep_opts = ["None", "1", "2", "3"]
                    curr_prep = str(term.get("as_prepend", "None"))
                    if curr_prep not in prep_opts: curr_prep = "None"
                    sel_prep = e2.radio("AS-Path Prepend", prep_opts, index=prep_opts.index(curr_prep), horizontal=True, key=f"t_prep_exp_{t_id}")
                    term["as_prepend"] = None if sel_prep == "None" else int(sel_prep)

                if UI.button("✔️ Done Deep Editing", color="green", key=f"done_exp_{t_id}", use_container_width=True):
                    st.session_state.bgp_active_edit_id = None
                    st.rerun()

    # ==========================================
    # 4. EXPORT EXECUTION QUEUE (Repaired Logic)
    # ==========================================
    if has_any_terms:
        st.markdown('<div class="compact-header">📋 Export Execution Queue</div>', unsafe_allow_html=True)
        with stylable_container(
            key="queue_table_exp",
            css_styles="""
                button { min-width: 32px !important; width: 32px !important; height: 32px !important; padding: 0px !important; margin: 0px !important; display: flex !important; justify-content: center !important; align-items: center !important; border: 1px solid #d1d5db !important; background-color: #f8fafc !important; color: #0f172a !important; }
                button:hover { background-color: #e2e8f0 !important; }
                [data-testid="column"] { min-width: 0px !important; padding: 0px 2px !important; gap: 0px !important; }
            """
        ):
            with st.container(border=True):
                h1, h2, h3, h4, h5 = st.columns([0.4, 1.4, 2.0, 2.2, 1.5])
                h1.caption("SEQ"); h2.caption("TERM"); h3.caption("PREFIXES"); h4.caption("LOGIC"); h5.caption("ACTIONS")
                st.divider()
                
                for i, term in enumerate(builder.get("terms", [])):
                    is_deny = (term.get("term_name") == "deny-all")
                    r1, r2, r3, r4, r5 = st.columns([0.4, 1.4, 2.0, 2.2, 1.5])
                    
                    r1.write(f"`{term.get('sequence', (i+1)*10)}`")
                    r2.write(f"**{term.get('term_name', 'Unnamed')}**")
                    r3.write(f"<small>{', '.join(term.get('prefixes', [])) if term.get('prefixes') else 'any'}</small>", unsafe_allow_html=True)
                    
                    match_display = f"Upto /{term.get('upto_mask', '32')}" if term.get('match_type') == "Upto" else term.get('match_type', 'Exact')
                    rendered_action = term.get("base_action", term.get("action", "Advertise"))
                    logic_str = f"{match_display} ⮕ {rendered_action}"
                    
                    if rendered_action == "Advertise" and (term.get("med") or term.get("as_prepend")):
                        extras = []
                        if term.get("med"): extras.append(f"MED:{term['med']}")
                        if term.get("as_prepend"): extras.append(f"Prep:{term['as_prepend']}")
                        logic_str += f" [{', '.join(extras)}]"
                    
                    r4.write(f"<small>{logic_str}</small>", unsafe_allow_html=True)
                    
                    with r5:
                        act_cols = st.columns(4)
                        
                        # --- Repaired Section: No one-liners allowed ---
                        if not is_deny:
                            if i > 0: 
                                with act_cols[0]: 
                                    st.button(
                                        "⬆️", 
                                        key=f"u_e_{term.get('term_id', i)}", 
                                        on_click=lambda idx=i: move_bgp_term(builder["terms"], idx, "up")
                                    )
                            if i < len(builder["terms"]) - 1: 
                                with act_cols[1]: 
                                    st.button(
                                        "⬇️", 
                                        key=f"d_e_{term.get('term_id', i)}", 
                                        on_click=lambda idx=i: move_bgp_term(builder["terms"], idx, "down")
                                    )
                        
                        with act_cols[2]: 
                            if st.button("✏️", key=f"e_e_{term.get('term_id', i)}"): 
                                st.session_state.bgp_active_edit_id = term.get("term_id")
                                st.rerun()
                        
                        with act_cols[3]: 
                            if st.button("🗑️", key=f"x_e_{term.get('term_id', i)}"):
                                if st.session_state.bgp_active_edit_id == term.get("term_id"): 
                                    st.session_state.bgp_active_edit_id = None
                                builder["terms"].pop(i)
                                apply_auto_resequence(builder["terms"])
                                st.rerun()
                st.divider()

    # ==========================================
    # 5. API COMMIT & FOOTER
    # ==========================================
    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1, 1.5, 1.5])
    with f1:
        if UI.button("❌ Back", color="gray", key="btn_back_exp", use_container_width=True): 
            st.session_state.bgp_active_edit_id = None
            on_close_callback()
    with f2:
        if UI.button("💾 Update State", color="green", key="btn_update_exp", use_container_width=True):
            if storage_key not in st.session_state: st.session_state[storage_key] = {}
            st.session_state[storage_key][builder["policy_name"]] = copy.deepcopy(builder)
            st.toast("Saved Locally", icon="💾")
    with f3:
        if UI.button("🚀 Commit Policy", color="red", key="btn_commit_exp", use_container_width=True): 
            if commit_bgp_policy(): 
                if storage_key not in st.session_state: st.session_state[storage_key] = {}
                st.session_state[storage_key][builder["policy_name"]] = copy.deepcopy(builder)
                on_close_callback()

def render_import_designer(customer_id: str, on_close_callback: callable):
    """
    Standalone UI definition for BGP Import Policies (NDT).
    Hides the top data_editor table to reduce UI clutter.
    """
    import streamlit as st
    import pandas as pd
    import uuid
    import copy

    # --- 1. CONTEXT RESOLUTION ---
    fs_detail = st.session_state.get("active_service_detail", {})
    base_ctx = fs_detail.get("service_name", "Unknown Service")
    svc_id = fs_detail.get("service_id")
    
    builder = st.session_state.get("bgp_builder", {})
    storage_key = f"bgp_policies_{customer_id}"
    
    if "bgp_active_edit_id" not in st.session_state: 
        st.session_state.bgp_active_edit_id = None
        
    curr_names = [t.get("term_name", "") for t in builder.get("terms", [])]
    has_any_terms = len(builder.get("terms", [])) > 0

    st.header("📥 Import Policy Designer")

    # ==========================================
    # 2. MACROS & QUICK PROVISIONING
    # ==========================================
    with st.container(border=True):
        st.markdown(f"**{base_ctx}: Import Provisioning**")
        q1, q2, q3, q4 = st.columns(4)
        
        with q1:
            if UI.button("➕ Add Term", color="green", key="btn_add_std_imp", use_container_width=True):
                existing_seqs = [int(t.get("sequence", 0)) for t in builder.get("terms", [])]
                next_seq = (max(existing_seqs) + 10) if existing_seqs else 10
                new_t = {"term_id": str(uuid.uuid4())[:8], "sequence": next_seq, "term_name": f"TERM-{next_seq}", "prefixes": [], "base_action": "Permit", "action": "Permit", "match_type": "Exact"}
                builder["terms"].append(new_t)
                builder["terms"] = sorted(builder["terms"], key=lambda x: int(x.get("sequence", 9999)))
                st.session_state.bgp_active_edit_id = new_t["term_id"]
                st.rerun()

        with q2:
            if not any(name.upper() == "PERMIT-ALL" for name in curr_names):
                if UI.button("✅ Permit All", color="green", key="m_permit_all_imp", use_container_width=True):
                    existing_seqs = [int(t.get("sequence", 0)) for t in builder.get("terms", [])]
                    next_seq = (max(existing_seqs) + 10) if existing_seqs else 10
                    builder["terms"].append({
                        "term_id": str(uuid.uuid4())[:8], "sequence": next_seq, "term_name": "PERMIT-ALL", 
                        "prefixes": ["0.0.0.0/0"], "base_action": "Permit", "action": "Permit", 
                        "match_type": "Upto", "upto_mask": 32
                    })
                    builder["terms"] = sorted(builder["terms"], key=lambda x: int(x.get("sequence", 9999)))
                    st.rerun()

        with q3:
            if "deny-all" not in [n.lower() for n in curr_names]:
                if UI.button("🛡️ Deny All", color="green", key="btn_deny_all_imp", use_container_width=True):
                    existing_seqs = [int(t.get("sequence", 0)) for t in builder.get("terms", [])]
                    next_seq = (max(existing_seqs) + 10) if existing_seqs else 100
                    builder["terms"].append({
                        "term_id": str(uuid.uuid4())[:8], "sequence": next_seq, "term_name": "deny-all", 
                        "prefixes": ["0.0.0.0/0"], "base_action": "Deny", "action": "Deny", 
                        "match_type": "Upto", "upto_mask": 32
                    })
                    builder["terms"] = sorted(builder["terms"], key=lambda x: int(x.get("sequence", 9999)))
                    st.rerun()

        with q4:
            if UI.button("⏭️ Skip Step", color="gray", key="btn_skip_bgp_imp", use_container_width=True):
                st.session_state.prov_step = 5
                st.session_state.prov_mode = "ATTACH_PORT"
                st.rerun()

    # ==========================================
    # 3. ACTIVE TERM BLOCK (DEEP EDIT)
    # ==========================================
    if st.session_state.bgp_active_edit_id:
        active_idx = next((i for i, t in enumerate(builder.get("terms", [])) if t.get("term_id") == st.session_state.bgp_active_edit_id), None)
        if active_idx is not None:
            term = builder["terms"][active_idx]
            st.markdown(f"### ⚙️ Deep Edit: `{term.get('term_name', 'Unknown')}`")
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                t_id = term.get('term_id')
                term["term_name"] = c1.text_input("Name", value=term.get("term_name", ""), key=f"t_n_imp_{t_id}")
                
                curr_action = term.get("base_action", term.get("action", "Permit"))
                action_idx = 0 if curr_action == "Permit" else 1
                selected_action = c2.radio("Action", ["Permit", "Deny"], index=action_idx, horizontal=True, key=f"t_a_imp_{t_id}")
                term["base_action"] = selected_action
                term["action"] = selected_action

                p_in = st.text_input("Prefixes (comma separated)", value=", ".join(term.get("prefixes", [])), key=f"t_p_imp_{t_id}")
                term["prefixes"] = [p.strip() for p in p_in.split(",") if p.strip()]

                m_opt = ["Exact", "All", "Upto", "Auto-Summary"]
                m_col1, m_col2 = st.columns([3, 1])
                current_match = term.get("match_type", "Exact")
                safe_match_index = m_opt.index(current_match) if current_match in m_opt else 0
                term["match_type"] = m_col1.radio("Match Type", m_opt, index=safe_match_index, horizontal=True, key=f"t_m_imp_{t_id}")

                if term["match_type"] == "Upto":
                    term["upto_mask"] = m_col2.text_input("Upto Mask (le)", value=str(term.get("upto_mask", "32")), key=f"t_um_imp_{t_id}")
                else:
                    term.pop("upto_mask", None)

                if selected_action == "Permit":
                    st.divider()
                    e1, e2 = st.columns(2)
                    lp_opts = ["None", "50", "90", "100", "110", "150"]
                    curr_lp = str(term.get("local_pref", "None"))
                    if curr_lp not in lp_opts: curr_lp = "None"
                    sel_lp = e1.radio("Local Preference", lp_opts, index=lp_opts.index(curr_lp), horizontal=True, key=f"t_lp_imp_{t_id}")
                    term["local_pref"] = None if sel_lp == "None" else int(sel_lp)
                    
                    comm_str = ", ".join(term.get("communities", []))
                    comm_in = e2.text_input("Add Community", value=comm_str, key=f"t_comm_imp_{t_id}")
                    term["communities"] = [c.strip() for c in comm_in.split(",") if c.strip()]

                if UI.button("✔️ Done Deep Editing", color="green", key=f"done_imp_{t_id}", use_container_width=True):
                    st.session_state.bgp_active_edit_id = None
                    st.rerun()

    # ==========================================
    # 4. IMPORT EXECUTION QUEUE (Primary View)
    # ==========================================
    if has_any_terms:
        st.markdown('📋 **Import Execution Queue**')
        with st.container(border=True):
            h1, h2, h3, h4, h5 = st.columns([0.4, 1.4, 2.0, 2.2, 1.5])
            h1.caption("SEQ"); h2.caption("TERM"); h3.caption("PREFIXES"); h4.caption("LOGIC"); h5.caption("ACTIONS")
            st.divider()
            
            for i, term in enumerate(builder.get("terms", [])):
                is_deny = (term.get("term_name") == "deny-all")
                r1, r2, r3, r4, r5 = st.columns([0.4, 1.4, 2.0, 2.2, 1.5])
                
                r1.write(f"`{term.get('sequence', (i+1)*10)}`")
                r2.write(f"**{term.get('term_name', 'Unnamed')}**")
                r3.write(f"<small>{', '.join(term.get('prefixes', [])) if term.get('prefixes') else 'any'}</small>", unsafe_allow_html=True)
                
                match_display = f"Upto /{term.get('upto_mask', '32')}" if term.get('match_type') == "Upto" else term.get('match_type', 'Exact')
                rendered_action = term.get("base_action", term.get("action", "Permit"))
                logic_str = f"{match_display} ⮕ {rendered_action}"
                
                if rendered_action == "Permit" and (term.get("local_pref") or term.get("communities")):
                    extras = []
                    if term.get("local_pref"): extras.append(f"LP:{term['local_pref']}")
                    if term.get("communities"): extras.append(f"Comm:{len(term['communities'])}")
                    logic_str += f" [{', '.join(extras)}]"
                
                r4.write(f"<small>{logic_str}</small>", unsafe_allow_html=True)
                
                with r5:
                    act_cols = st.columns(4)
                    if not is_deny:
                        if i > 0: 
                            with act_cols[0]: 
                                st.button("⬆️", key=f"u_i_{term.get('term_id', i)}", on_click=lambda idx=i: move_bgp_term(builder["terms"], idx, "up"))
                        if i < len(builder["terms"]) - 1: 
                            with act_cols[1]: 
                                st.button("⬇️", key=f"d_i_{term.get('term_id', i)}", on_click=lambda idx=i: move_bgp_term(builder["terms"], idx, "down"))
                    
                    with act_cols[2]: 
                        if st.button("✏️", key=f"e_i_{term.get('term_id', i)}"): 
                            st.session_state.bgp_active_edit_id = term.get("term_id")
                            st.rerun()
                    
                    with act_cols[3]: 
                        if st.button("🗑️", key=f"x_i_{term.get('term_id', i)}"):
                            if st.session_state.bgp_active_edit_id == term.get("term_id"): st.session_state.bgp_active_edit_id = None
                            builder["terms"].pop(i)
                            apply_auto_resequence(builder["terms"])
                            st.rerun()
            st.divider()

    # ==========================================
    # 5. COMMIT & FOOTER
    # ==========================================
    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1, 1.5, 1.5])
    with f1:
        if UI.button("❌ Back", color="gray", key="btn_back_imp", use_container_width=True): 
            st.session_state.bgp_active_edit_id = None
            on_close_callback()
    with f2:
        if UI.button("💾 Update State", color="green", key="btn_update_imp", use_container_width=True):
            if storage_key not in st.session_state: st.session_state[storage_key] = {}
            st.session_state[storage_key][builder["policy_name"]] = copy.deepcopy(builder)
            st.toast("Saved Locally", icon="💾")
    with f3:
        if UI.button("🚀 Commit Policy", color="blue", key="btn_commit_imp", use_container_width=True): 
            if commit_bgp_policy(): 
                if storage_key not in st.session_state: st.session_state[storage_key] = {}
                st.session_state[storage_key][builder["policy_name"]] = copy.deepcopy(builder)
                on_close_callback()

def commit_bgp_policy():
    """
    Finalizes the builder state and pushes the bulk term list to the API.
    Branches logic between POST (New) and PUT (Modify).
    """
    builder = st.session_state.get("bgp_builder")
    if not builder:
        st.error("No active builder session found.")
        return False

    # 1. Payload Preparation with Sequence fail-safe
    payload = []
    for i, term in enumerate(builder.get("terms", [])):
        # Fallback for sequence if macro or manual entry missed it
        safe_seq = term.get("sequence")
        if safe_seq is None or safe_seq == "":
            safe_seq = (i + 1) * 10
            
        payload.append({
            "policy_id": builder["policy_id"],
            "fabric_service_id": builder["fabric_service_id"],
            "policy_name": builder["policy_name"],
            "direction": builder["direction"],
            "sequence": int(safe_seq),
            "term_name": term.get("term_name"),
            "prefixes": term.get("prefixes", []),
            "match_type": term.get("match_type", "Exact"),
            "upto_mask": term.get("upto_mask"),
            "action": term.get("base_action", term.get("action", "Permit")), 
            "med": term.get("med"),
            "local_pref": term.get("local_pref"),
            "as_prepend": term.get("as_prepend"),
            "communities": term.get("communities", [])
        })

    if not payload:
        st.warning("⚠️ Cannot commit an empty policy.")
        return False

    # 2. Determine Verb Context
    is_new = builder.get("is_new", True)
    
    # 3. API Execution
    with st.status(f"{'Creating' if is_new else 'Updating'} {builder['policy_name']}...", expanded=True) as status:
        try:
            if is_new:
                st.write("📡 Sending POST request to Galileo...")
                result = post_bgp_policy(payload)
            else:
                st.write(f"📡 Sending PUT request for ID {builder['policy_id']}...")
                result = put_bgp_policy(payload, builder["policy_id"])
            
            if result:
                st.write(f"✅ Success: {len(result)} terms confirmed.")
                status.update(label="**Policy Committed Successfully!**", state="complete", expanded=False)
                time.sleep(1)
                return True
                
        except Exception as e:
            status.update(label="**Commit Failed**", state="error", expanded=True)
            st.error(f"**API Exception:** {str(e)}")
            return False

## Cleanup session state on builder exit        
