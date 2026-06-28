import sys
from pathlib import Path

# 1. Force Python to recognize the /app root directory
sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
import pandas as pd

# --- NDT CORE IMPORTS ---
from src.utils.api_network import fetch_topology_links

# --- GALILEO SDK IMPORTS ---
from src.galileo.galileo_topology import (
    adapt_api_to_galileo,
    render_global_backbone_map,
    render_orbital_pop_map,
    extract_pop_from_hostname
)
from src.galileo.galileo_taxonomy import (
    NETWORK_CONSTRUCTS,
    extract_role
)

# ==========================================
# 1. API INGESTION & SANITIZATION
# ==========================================

@st.cache_data(ttl=300)
def get_cached_topology_links(network: str, pop_filter=None):
    if pop_filter is None or pop_filter == "-- Global Backbone --":
        raw_data = fetch_topology_links(network, pop=None, link_type="Inter-Pop")
    else:
        raw_data = fetch_topology_links(network, pop=pop_filter, link_type=None)
    
    if not raw_data:
        return []
        
    df = pd.DataFrame(raw_data)
    if not df.empty:
        df['a_loc_clean'] = df['a_device_location'].astype(str).str.strip().str.upper()
        df['b_loc_clean'] = df['b_device_location'].astype(str).str.strip().str.upper()

        intra_mask = df['a_loc_clean'] == df['b_loc_clean']
        df.loc[intra_mask, 'link_type'] = 'Intra-Pop'
        df.loc[~intra_mask, 'link_type'] = 'Inter-Pop'

        df = df.drop(columns=['a_loc_clean', 'b_loc_clean'])
        
    return df.to_dict('records')

@st.cache_data(ttl=300)
def get_cached_pop_full_topology(network: str, pop: str):
    raw_data = fetch_topology_links(network, pop=pop, link_type=None)
    return pd.DataFrame(raw_data) if raw_data else pd.DataFrame()

@st.cache_data(ttl=3600)
def get_cached_pop_list(network: str = "AS3549"):
    from src.utils.api_network import fetch_locations_by_network
    
    raw_locations = fetch_locations_by_network(network)
    
    if raw_locations:
        pops = []
        for loc in raw_locations:
            short_name = str(loc.get("short_name", "")).upper()
            if short_name:
                city = str(loc.get("city", "")).title()
                state = str(loc.get("state", "")).title()
                country = str(loc.get("country", "")).upper()
                
                location_context = f"{city}"
                if state: location_context += f", {state}"
                if country: location_context += f" ({country})"
                
                display_label = f"{short_name} | {location_context}" if location_context.strip() else short_name

                pops.append({
                    "short_name": short_name,
                    "location_code": loc.get("location_code", "UNKNOWN"),
                    "location_name": loc.get("location_name", "Unknown"),
                    "city": city,
                    "state": state,
                    "country": country,
                    "display_label": display_label
                })
        return sorted(pops, key=lambda x: x["short_name"])
        
    fallback_pops = ["ASH1", "CHI2", "DFW1", "LAX1", "NYC6"]
    return [{"short_name": p, "display_label": p} for p in fallback_pops]

# ==========================================
# 2. LOCAL DATA PREPARATION HELPERS
# ==========================================

def _prepare_regional_dataframe(df_raw):
    df_clean = df_raw.copy()
    
    # Delegate parsing completely to the universal taxonomy tools
    df_clean['a_role_clean'] = df_clean['a_device_name'].apply(extract_role)
    df_clean['b_role_clean'] = df_clean['b_device_name'].apply(extract_role)
    
    df_clean['a_pop_clean'] = df_clean['a_device_name'].apply(extract_pop_from_hostname)
    df_clean['b_pop_clean'] = df_clean['b_device_name'].apply(extract_pop_from_hostname)
    
    df_clean['is_intra'] = df_clean['a_pop_clean'] == df_clean['b_pop_clean']
    
    return df_clean

def _render_regional_filter_ui(all_roles: list, target_network: str = "AS3549"):
    # Dynamically pull the construct mapping from the taxonomy
    network_constructs = NETWORK_CONSTRUCTS.get(target_network, {})
    local_constructs = {k: list(v) for k, v in network_constructs.items()}
    
    known_roles = set()
    for key, roles in local_constructs.items():
        if key != "Other":
            for item in roles:
                if isinstance(item, tuple):
                    known_roles.update(item)
                else:
                    known_roles.add(item)
    
    local_constructs["Other"] = [r for r in all_roles if r not in known_roles]

    active_constructs = []
    for construct, mapped_items in local_constructs.items():
        is_active = False
        for item in mapped_items:
            if isinstance(item, tuple):
                if item[0] in all_roles and item[1] in all_roles:
                    is_active = True
                    break
            elif item in all_roles:
                is_active = True
                break
        if is_active: active_constructs.append(construct)
    
    if not active_constructs: active_constructs = ["Other"]
    
    st.write(f"##### 🎛️ {target_network} Architecture Layers")
    
    selected_construct = st.radio(
        "Select Network Construct:",
        options=active_constructs,
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.write("") 

    col_mode, col_iso = st.columns(2)
    with col_mode:
        match_mode = st.radio(
            "Layer Match Mode:",
            options=["Adjacency (OR)", "Strict (AND)"],
            horizontal=True
        )
    with col_iso:
        isolate_local = st.toggle(
            "Isolate Local Devices",
            value=False,
            help="Hides external Inter-PoP backbone links."
        )
        
    st.divider()
    selected_roles = local_constructs.get(selected_construct, [])
        
    return selected_construct, selected_roles, match_mode, isolate_local

def _apply_regional_filters(df_clean, selected_construct: str, selected_roles: list, match_mode: str, isolate_local: bool):
    import pandas as pd
    
    df_filtered = df_clean.copy()

    if isolate_local:
        df_filtered = df_filtered[df_filtered['is_intra'] == True]

    if selected_roles:
        strict_pairs = [r for r in selected_roles if isinstance(r, tuple)]
        wildcard_roles = [r for r in selected_roles if isinstance(r, str)]
        
        mask_overall = pd.Series(False, index=df_filtered.index)
        
        for role_1, role_2 in strict_pairs:
            pair_mask = (
                ((df_filtered['a_role_clean'] == role_1) & (df_filtered['b_role_clean'] == role_2)) |
                ((df_filtered['a_role_clean'] == role_2) & (df_filtered['b_role_clean'] == role_1))
            )
            mask_overall = mask_overall | pair_mask

        if wildcard_roles:
            mask_a = df_filtered['a_role_clean'].isin(wildcard_roles)
            mask_b = df_filtered['b_role_clean'].isin(wildcard_roles)
            
            if "Strict" in match_mode:
                wildcard_mask = mask_a & mask_b
            else:
                wildcard_mask = mask_a | mask_b
                
            mask_overall = mask_overall | wildcard_mask

        df_filtered = df_filtered[mask_overall]
    else:
        df_filtered = pd.DataFrame()
        
    return df_filtered

def render_regional_pop_tab(selected_loc: str, network: str):
    if 'FabricStateManager' not in st.session_state:
        st.session_state['FabricStateManager'] = {}
        
    st.session_state['FabricStateManager']['current_pop'] = selected_loc
    
    if selected_loc == "-- Global Backbone --":
        st.warning("Global Backbone selected in Regional View. Please switch to the Global Backbone tab.")
        return

    with st.spinner(f"Loading cached fabric for {selected_loc}..."):
        df_pop_raw = get_cached_pop_full_topology(network, selected_loc)
    
    if df_pop_raw.empty:
        st.info(f"No local connections found for {selected_loc}.")
        return
        
    df_prepared = _prepare_regional_dataframe(df_pop_raw)
    all_roles = sorted(list(set(df_prepared['a_role_clean'].tolist() + df_prepared['b_role_clean'].tolist())))
    
    selected_construct, selected_roles, match_mode, isolate_local = _render_regional_filter_ui(all_roles, target_network=network)
    
    df_filtered = _apply_regional_filters(df_prepared, selected_construct, selected_roles, match_mode, isolate_local)
        
    if df_filtered.empty:
        st.warning("⚠️ No connections match the current architecture configuration.")
        return

    if selected_construct == "Backbone":
        active_engine = "Backbone Layout"
    else:
        active_engine = "Edge Layout"

    st.caption(f"Engine Template: **{active_engine}** | Links Ingested: {len(df_filtered)} / {len(df_pop_raw)}")

    with st.spinner(f"Mapping local fabric for {selected_loc}..."):
        galileo_nodes, galileo_links = adapt_api_to_galileo(df_filtered, mode="orbital")
        
        nodes_payload = galileo_nodes
        if isinstance(galileo_nodes, list):
            nodes_payload = {n.get('id', n.get('name', str(i))): n for i, n in enumerate(galileo_nodes)}

        clean_mode = match_mode.split(" ")[0]

        render_orbital_pop_map(
            nodes_payload=nodes_payload,
            links_payload=galileo_links,
            selected_template=active_engine, 
            title=f"Orbital PoP: {selected_loc} | Layer: {selected_construct} ({clean_mode}) | Engine: {active_engine} | Links: {len(df_filtered)}"
        )

def render_global_backbone_tab(df_backbone, network: str):
    st.markdown("#### Geographic Core Transport")

    if df_backbone.empty:
        st.info("🗺️ No Inter-Pop backbone links available.")
        return

    st.write("##### 🎛️ Network Layer Filter")
    
    if network == "AS3356":
        tier_options = [
            "Full Backbone", 
            "Tier 1 Core (EBR ↔ EBR)", 
            "Tier 3+ (EBR to Non-EBR)"
        ]
    else: 
        tier_options = [
            "Full Backbone", 
            "Tier 1 (SDR ↔ SDR)", 
            "Tier 2 (SCR)", 
            "Tier 3 (CR)", 
            "Tier 5 (Edge / Non-Core)"
        ]
    
    selected_tier = st.radio(
        "Select Layer:", 
        options=tier_options, 
        index=0, 
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.divider()

    # Apply global taxonomy extraction for safe evaluation
    df_backbone['a_role_safe'] = df_backbone['a_device_name'].apply(extract_role)
    df_backbone['b_role_safe'] = df_backbone['b_device_name'].apply(extract_role)
    
    if network == "AS3356":
        if selected_tier == "Tier 1 Core (EBR ↔ EBR)":
            df_backbone = df_backbone[
                (df_backbone['a_role_safe'] == 'EBR') & (df_backbone['b_role_safe'] == 'EBR')
            ]
        elif selected_tier == "Tier 3+ (EBR to Non-EBR)":
            core_roles = ['EBR', 'SRR', 'RR', 'ERR']
            df_backbone = df_backbone[
                (~df_backbone['a_role_safe'].isin(core_roles)) | (~df_backbone['b_role_safe'].isin(core_roles))
            ]
            
    else: 
        if selected_tier == "Tier 1 (SDR ↔ SDR)":
            df_backbone = df_backbone[
                (df_backbone['a_role_safe'] == 'SDR') & (df_backbone['b_role_safe'] == 'SDR')
            ]
        elif selected_tier == "Tier 2 (SCR)":
            df_backbone = df_backbone[
                (df_backbone['a_role_safe'] == 'SCR') | (df_backbone['b_role_safe'] == 'SCR')
            ]
        elif selected_tier == "Tier 3 (CR)":
            df_backbone = df_backbone[
                (df_backbone['a_role_safe'] == 'CR') | (df_backbone['b_role_safe'] == 'CR')
            ]
        elif selected_tier == "Tier 5 (Edge / Non-Core)":
            core_roles = ['SDR', 'SCR', 'CR']
            df_backbone = df_backbone[
                (~df_backbone['a_role_safe'].isin(core_roles)) | (~df_backbone['b_role_safe'].isin(core_roles))
            ]
        
    df_backbone = df_backbone.drop(columns=['a_role_safe', 'b_role_safe'], errors='ignore')

    if df_backbone.empty:
        st.warning(f"⚠️ No links match the **{selected_tier}** filter.")
    else:
        galileo_nodes, galileo_links = adapt_api_to_galileo(df_backbone)
        render_global_backbone_map(
            nodes=galileo_nodes, 
            links=galileo_links, 
            title=f"{network} Geographic Core Transport: {selected_tier}"
        )      

def render_data_inspector_tab(df_links, selected_loc: str, network: str):
    st.markdown("#### 🔬 NDT Data Inspector")
    st.caption(f"Tabular dataset review for the Global Backbone and **{selected_loc}**.")

    with st.spinner("Preparing datasets for tabular view..."):
        raw_backbone = get_cached_topology_links(network)
        df_backbone = pd.DataFrame(raw_backbone)
        
        global_nodes, global_links = adapt_api_to_galileo(df_backbone, mode="backbone")
        df_global_nodes = pd.DataFrame(global_nodes)
        df_global_links = pd.DataFrame(global_links)

        if not df_links.empty:
            pop_nodes, pop_links = adapt_api_to_galileo(df_links, mode="orbital")
            df_pop_nodes = pd.DataFrame(pop_nodes)
            df_pop_links = pd.DataFrame(pop_links)
        else:
            df_pop_nodes, df_pop_links = pd.DataFrame(), pd.DataFrame()

    tab_global_nodes, tab_global_links, tab_pop_nodes, tab_pop_links = st.tabs([
        "Global Nodes Dataset", 
        "Global Links Dataset",
        "Pop Nodes Dataset", 
        "Pop Links Dataset"
    ])

    with tab_global_nodes:
        if not df_global_nodes.empty:
            st.dataframe(df_global_nodes, use_container_width=True, hide_index=True)
        else:
            st.info("No global nodes parsed from the backbone payload.")
            
    with tab_global_links:
        if not df_global_links.empty:
            st.dataframe(df_global_links, use_container_width=True, hide_index=True)
        else:
            st.info("No global links parsed from the backbone payload.")

    with tab_pop_nodes:
        if not df_pop_nodes.empty:
            cols = ['id', 'device_role', 'label_header', 'colors']
            existing_cols = [c for c in cols if c in df_pop_nodes.columns] + [c for c in df_pop_nodes.columns if c not in cols]
            st.dataframe(df_pop_nodes[existing_cols], use_container_width=True, hide_index=True)
        else:
            st.info(f"No local nodes parsed for {selected_loc}.")
            
    with tab_pop_links:
        if not df_pop_links.empty:
            st.dataframe(df_pop_links, use_container_width=True, hide_index=True)
        else:
            st.info(f"No local links parsed for {selected_loc}.")

# ==========================================
# 4. MAIN TOPOLOGY ORCHESTRATOR
# ==========================================
def render_topology_view(network: str):
    st.markdown(f"### 🪐 {network} Galileo Universe")
    
    with st.spinner("Discovering Network PoPs..."):
        pop_data_list = get_cached_pop_list(network)
        
    col1, col2 = st.columns(2)
    
    with col1:
        city_search = st.text_input("🔍 City Search (e.g., Denver, LAX)", value="")
        
    with col2:
        if city_search:
            filtered_pops = [
                p for p in pop_data_list 
                if city_search.lower() in str(p.get("display_label", "")).lower() 
                or city_search.lower() in str(p.get("short_name", "")).lower()
            ]
        else:
            filtered_pops = pop_data_list

        if not filtered_pops:
            st.warning(f"No facilities found matching '{city_search}'.")
            selected_pop = None
        else:
            selected_pop_obj = st.selectbox(
                "📍 Select Facility for Orbital View", 
                options=filtered_pops,
                format_func=lambda x: x.get("display_label", x.get("short_name", "Unknown"))
            )
            selected_pop = selected_pop_obj.get("short_name") if selected_pop_obj else None

    with st.spinner("Hydrating NDT Backbone..."):
        raw_backbone_list = get_cached_topology_links(network)
        df_backbone = pd.DataFrame(raw_backbone_list)

    tab_backbone, tab_pop, tab_inspector = st.tabs(["🌍 Global Backbone", "🏢 Regional PoP", "🔬 Data Inspector"])

    with tab_backbone:
        render_global_backbone_tab(df_backbone, network)

    with tab_pop:
        if selected_pop:
            render_regional_pop_tab(selected_pop, network)
        else:
            st.info("Please select a valid facility to view the Regional PoP architecture.")

    with tab_inspector:
        if selected_pop:
            df_pop_full = get_cached_pop_full_topology(network, selected_pop)
            render_data_inspector_tab(df_pop_full, selected_pop, network)
        else:
            st.info("Please select a valid facility to inspect data.")