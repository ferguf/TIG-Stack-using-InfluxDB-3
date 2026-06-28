import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

@st.cache_data
def load_network_config() -> dict:
    """Loads the universal network taxonomy from the JSON configuration file."""
    config_path = os.path.join(os.path.dirname(__file__), "network_inventory.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load network_inventory.json: {e}")
        return {}

def render_network_dashboard(dashboard_data: list, target_asn: str):
    """TAB 1: Visual Analytics & Overview (Universal Engine Powered by JSON Taxonomy)"""
    
    if not dashboard_data:
        st.warning(f"No telemetry data available from the API for {target_asn}.")
        return

    # --- 1. Load Dynamic Configurations ---
    global_config = load_network_config()
    net_config = global_config.get(target_asn, {})
    
    tier_config = net_config.get("tiers", {})
    color_map = net_config.get("colors", {})

    # Fallback if the network isn't defined in the JSON yet
    if not tier_config:
        tier_config = {
            "Tier 1 Core": ["EBR", "SDR", "SCR", "CR", "CORE", "PCOR"], 
            "Tier 2 Edge": ["EAR", "EDGE", "VAR", "ES", "AGG"]
        }

    tier_names = list(tier_config.keys())
    
    # --- 2. Initialize Dynamic Trackers ---
    total_devices = sum((pop.get('total_devices') or 0) for pop in dashboard_data)
    unique_locations = len(dashboard_data)
    total_backbone_gbps = 0.0

    # Dynamically track POP classifications based on the JSON keys
    pop_tier_counts = {t: 0 for t in tier_names}
    pop_tier_counts["Mixed / Other"] = 0

    # Dynamically track Capacities based on the JSON keys
    cap_tier_gbps = {t: 0.0 for t in tier_names}
    cap_tier_gbps["Edge / Intra-Pop"] = 0.0

    loc_type_data = []
    core_role_counts = {}
    edge_role_counts = {}

    # Identify "Core" tiers heuristically (assume the top half of the defined tiers are core/backbone)
    core_tiers = tier_names[:max(1, len(tier_names)//2)]

    # --- 3. Process Telemetry Payload ---
    for pop in dashboard_data:
        loc = pop.get('pop_location') or 'Unknown'
        pop_device_count = pop.get('total_devices') or 0
        roles = pop.get('role_distribution') or []
        
        # Clean set of active roles in this POP
        roles_in_pop = {r.get('role') for r in roles if r.get('count', 0) > 0}
        
        # --- DYNAMIC POP CLASSIFICATION ---
        pop_type = "Mixed / Other"
        # Iterate through the JSON tiers (Order matters: Tier 1 matches before Tier 3)
        for t_name, t_roles in tier_config.items():
            if any(r in roles_in_pop for r in t_roles):
                pop_type = t_name
                break 
        
        pop_tier_counts[pop_type] += 1
        
        loc_type_data.append({
            'Location': loc,
            'POP Type': pop_type,
            'Total Devices': pop_device_count
        })

        # --- DYNAMIC CORE VS EDGE ROLE SORTING ---
        for r in roles:
            r_name = str(r.get('role', '')).upper().strip()
            r_count = r.get('count', 0)
            if not r_name: continue

            # Determine if this role belongs to a "Core" tier
            is_core = any(r_name in tier_config[t] for t in core_tiers)
            
            # Fallback heuristic for unknown roles
            if not is_core and any(x in r_name for x in ["CR", "SDR", "EBR", "COR"]):
                is_core = True
            
            if is_core:
                core_role_counts[r_name] = core_role_counts.get(r_name, 0) + r_count
            else:
                edge_role_counts[r_name] = edge_role_counts.get(r_name, 0) + r_count
            
        # --- DYNAMIC CAPACITY ROUTING ---
        links = pop.get('link_distribution') or []
        for link_obj in links:
            cap = link_obj.get('total_capacity_gbps') or 0.0
            l_type = link_obj.get('link_type', '')
            
            if l_type == 'Intra-Pop':
                cap_tier_gbps["Edge / Intra-Pop"] += cap
            elif l_type == 'Inter-Pop':
                total_backbone_gbps += cap
                # Assign the backbone capacity to the highest routing tier found in the POP
                if pop_type in cap_tier_gbps:
                    cap_tier_gbps[pop_type] += cap
                else:
                    cap_tier_gbps[tier_names[0]] += cap

    # Convert all capacities to Tbps for clean UI
    cap_tier_tbps = {k: v / 1000.0 for k, v in cap_tier_gbps.items()}

    # --- 4. CSS Injector for Metric Cards ---
    st.markdown("""
        <style>
        .metric-card {
            background-color: #1e1e2f; 
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 16px;
            border-left: 4px solid transparent;
        }
        .metric-title {
            color: #a0a0b0;
            font-size: 0.85rem;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-value {
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: bold;
        }
        .border-blue { border-left-color: #3b82f6; }
        .border-purple { border-left-color: #8b5cf6; }
        .border-teal { border-left-color: #14b8a6; }
        .border-orange { border-left-color: #f97316; }
        .border-pink { border-left-color: #ec4899; }
        .border-yellow { border-left-color: #eab308; }
        .border-green { border-left-color: #22c55e; }
        .border-red { border-left-color: #ef4444; }
        </style>
    """, unsafe_allow_html=True)

    # --- 5. Render Top Metrics ---
    st.markdown("##### 📊 Network Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card border-blue"><div class="metric-title">Total Devices</div><div class="metric-value">{total_devices:,}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card border-purple"><div class="metric-title">Active POPs</div><div class="metric-value">{unique_locations:,}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card border-teal"><div class="metric-title">Total Backbone</div><div class="metric-value">{total_backbone_gbps:,.0f} <span style="font-size: 1rem;">Gbps</span></div></div>', unsafe_allow_html=True)
    
    primary_tier = tier_names[0] if tier_names else "Core"
    c4.markdown(f'<div class="metric-card border-orange"><div class="metric-title">{primary_tier} Footprint</div><div class="metric-value">{pop_tier_counts.get(primary_tier, 0):,} <span style="font-size: 1rem;">POPs</span></div></div>', unsafe_allow_html=True)
    
    # --- 6. Render Dynamic POP Classifications ---
    st.markdown("##### 🏢 POP Classifications")
    pop_cols = st.columns(4)
    border_colors = ["border-pink", "border-yellow", "border-green", "border-red", "border-blue"]
    
    # Render up to 4 classification boxes dynamically
    render_idx = 0
    for t_name, count in pop_tier_counts.items():
        if render_idx >= 4: break
        with pop_cols[render_idx]:
            color_class = border_colors[render_idx % len(border_colors)]
            st.markdown(f'<div class="metric-card {color_class}"><div class="metric-title">{t_name}</div><div class="metric-value">{count:,}</div></div>', unsafe_allow_html=True)
        render_idx += 1

    # --- 7. Render Dynamic Network Capacity ---
    st.markdown("##### ⚡ Network Capacity Metrics")
    cap_cols = st.columns(4)
    
    render_idx = 0
    # Prioritize rendering the edge, then fill in backbone tiers
    with cap_cols[3]:
        st.markdown(f'<div class="metric-card border-orange"><div class="metric-title">Edge Capacity</div><div class="metric-value">{cap_tier_tbps.get("Edge / Intra-Pop", 0):,.1f} <span style="font-size: 1rem;">Tbps</span></div></div>', unsafe_allow_html=True)
    
    for t_name, tbps in cap_tier_tbps.items():
        if t_name == "Edge / Intra-Pop" or render_idx >= 3: continue
        with cap_cols[render_idx]:
            color_class = border_colors[render_idx % len(border_colors)]
            st.markdown(f'<div class="metric-card {color_class}"><div class="metric-title">{t_name} Backbone</div><div class="metric-value">{tbps:,.1f} <span style="font-size: 1rem;">Tbps</span></div></div>', unsafe_allow_html=True)
        render_idx += 1

    st.write("<br>", unsafe_allow_html=True)
    
    # --- 8. Render Visualizations ---
    c13, c14, c15 = st.columns(3)
    
    with c13:
        st.markdown("**1. POP Classification**")
        with st.container(border=True):
            df_loc_type = pd.DataFrame(loc_type_data)
            if not df_loc_type.empty:
                type_counts = df_loc_type['POP Type'].value_counts().reset_index()
                type_counts.columns = ['POP Type', 'Location Count']
                
                # Apply JSON color mappings dynamically to the Pie Chart
                fig1 = px.pie(
                    type_counts, 
                    names='POP Type', 
                    values='Location Count', 
                    hole=0.4, 
                    color='POP Type',
                    color_discrete_map=color_map,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig1.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20), height=350,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No classification data available.")

    with c14:
        st.markdown("**2. Core Role Distribution**")
        with st.container(border=True):
            if core_role_counts:
                df_core = pd.DataFrame(list(core_role_counts.items()), columns=['Role', 'Count'])
                fig2 = px.pie(
                    df_core, 
                    names='Role', 
                    values='Count', 
                    hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                fig2.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20), height=350,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No Core device data available.")

    with c15:
        st.markdown("**3. Edge Role Distribution**")
        with st.container(border=True):
            if edge_role_counts:
                df_edge = pd.DataFrame(list(edge_role_counts.items()), columns=['Role', 'Count'])
                fig3 = px.pie(
                    df_edge, 
                    names='Role', 
                    values='Count', 
                    hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig3.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20), height=350,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("No Edge device data available.")