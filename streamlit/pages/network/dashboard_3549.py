import streamlit as st
import pandas as pd
import plotly.express as px

def render_3549_dashboard(dashboard_data: list):
    """TAB 1: Visual Analytics & Overview (Powered by God Mode API)"""
    
    if not dashboard_data:
        st.warning("No telemetry data available from the API.")
        return

    # --- 1. Flatten Data & Calculate Classifications ---
    total_devices = sum((pop.get('total_devices') or 0) for pop in dashboard_data)
    unique_locations = len(dashboard_data)
    
    total_backbone_gbps = 0.0
    
    # Capacity Tracking (Gbps tracked internally, converted to Tbps for UI)
    t1_backbone_gbps = 0.0
    t2_backbone_gbps = 0.0
    t3_backbone_gbps = 0.0
    edge_capacity_gbps = 0.0

    # Structures for the POP type visualizations
    loc_type_data = []

    # POP Classification Counters
    tier1_pops = 0
    tier2_pops = 0
    dce_pops = 0
    non_digital_pops = 0
    other_digital_pops = 0 

    # --- NEW: Core vs Edge Role Dictionaries ---
    # Tracking exact counts for individual roles instead of just a global total
    core_roles_set = {"SDR", "SCR", "CR", "VRR", "VR", "RR"}
    core_role_counts = {}
    edge_role_counts = {}

    for pop in dashboard_data:
        loc = pop.get('pop_location') or 'Unknown'
        pop_device_count = pop.get('total_devices') or 0
        roles = pop.get('role_distribution') or []
        
        # Create a clean set of roles for this specific POP (ignoring empty counts)
        roles_in_pop = {r.get('role') for r in roles if r.get('count', 0) > 0}
        
        # --- POP CLASSIFICATION LOGIC ---
        if 'VAR' not in roles_in_pop:
            pop_type = 'Non-Digital'
            non_digital_pops += 1
        elif 'SDR' in roles_in_pop:
            pop_type = 'Tier 1 Digital'
            tier1_pops += 1
        elif 'SCR' in roles_in_pop:
            pop_type = 'Tier 2 Digital'
            tier2_pops += 1
        elif 'ES' in roles_in_pop and len(roles_in_pop - {'VAR', 'ES'}) == 0:
            pop_type = 'DCE'
            dce_pops += 1
        else:
            pop_type = 'Other Digital'
            other_digital_pops += 1
            
        # Store for visualizations
        loc_type_data.append({
            'Location': loc,
            'POP Type': pop_type,
            'Total Devices': pop_device_count
        })

        # --- CORE VS EDGE AGGREGATION ---
        for r in roles:
            r_name = str(r.get('role', '')).upper().strip()
            r_count = r.get('count', 0)
            
            if not r_name:
                continue
                
            if r_name in core_roles_set:
                core_role_counts[r_name] = core_role_counts.get(r_name, 0) + r_count
            else:
                edge_role_counts[r_name] = edge_role_counts.get(r_name, 0) + r_count
            
        # --- CAPACITY PARSING & CUSTOM RULES ---
        links = pop.get('link_distribution') or []
        for link_obj in links:
            cap = link_obj.get('total_capacity_gbps') or 0.0
            l_type = link_obj.get('link_type', '')
            
            # Custom Rule 4: Pop sum Edge capacity (Intra-Pop)
            if l_type == 'Intra-Pop':
                edge_capacity_gbps += cap
                
            # Backbone Math (Inter-Pop)
            elif l_type == 'Inter-Pop':
                total_backbone_gbps += cap

                # Evaluate backbone tier based on the POP's highest-tier core routing role
                if 'SDR' in roles_in_pop:
                    t1_backbone_gbps += cap
                elif 'SCR' in roles_in_pop:
                    t2_backbone_gbps += cap
                elif 'CR' in roles_in_pop:
                    t3_backbone_gbps += cap

    # Convert tracked Gbps metrics into Tbps
    t1_backbone_tbps = t1_backbone_gbps / 1000.0
    t2_backbone_tbps = t2_backbone_gbps / 1000.0
    t3_backbone_tbps = t3_backbone_gbps / 1000.0
    edge_capacity_tbps = edge_capacity_gbps / 1000.0

    # --- 2. CSS Injector for Metric Cards ---
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
        /* Metric Colors */
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

    # --- 3. Render Top Metrics (Custom HTML) ---
    st.markdown("##### 📊 Network Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card border-blue"><div class="metric-title">Total Devices</div><div class="metric-value">{total_devices:,}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card border-purple"><div class="metric-title">Active POPs</div><div class="metric-value">{unique_locations:,}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card border-teal"><div class="metric-title">Total Backbone</div><div class="metric-value">{total_backbone_gbps:,.0f} <span style="font-size: 1rem;">Gbps</span></div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card border-orange"><div class="metric-title">Tier 1 Footprint</div><div class="metric-value">{tier1_pops:,} <span style="font-size: 1rem;">POPs</span></div></div>', unsafe_allow_html=True)
    
    # --- 4. Render POP Classifications (Custom HTML) ---
    st.markdown("##### 🏢 POP Classifications")
    c5, c6, c7, c8 = st.columns(4)
    c5.markdown(f'<div class="metric-card border-pink"><div class="metric-title">Tier 1 Digital (VAR + SDR)</div><div class="metric-value">{tier1_pops:,}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-card border-yellow"><div class="metric-title">Tier 2 Digital (VAR + SCR)</div><div class="metric-value">{tier2_pops:,}</div></div>', unsafe_allow_html=True)
    c7.markdown(f'<div class="metric-card border-green"><div class="metric-title">DCE (VAR + ES Only)</div><div class="metric-value">{dce_pops:,}</div></div>', unsafe_allow_html=True)
    c8.markdown(f'<div class="metric-card border-red"><div class="metric-title">Non-Digital (No VAR)</div><div class="metric-value">{non_digital_pops:,}</div></div>', unsafe_allow_html=True)

    # --- 5. Render Network Capacity Rules (Tbps) ---
    st.markdown("##### ⚡ Network Capacity Metrics")
    c9, c10, c11, c12 = st.columns(4)
    c9.markdown(f'<div class="metric-card border-blue"><div class="metric-title">Tier 1 Backbone</div><div class="metric-value">{t1_backbone_tbps:,.1f} <span style="font-size: 1rem;">Tbps</span></div></div>', unsafe_allow_html=True)
    c10.markdown(f'<div class="metric-card border-purple"><div class="metric-title">Tier 2 Backbone</div><div class="metric-value">{t2_backbone_tbps:,.1f} <span style="font-size: 1rem;">Tbps</span></div></div>', unsafe_allow_html=True)
    c11.markdown(f'<div class="metric-card border-teal"><div class="metric-title">Tier 3 Backbone</div><div class="metric-value">{t3_backbone_tbps:,.1f} <span style="font-size: 1rem;">Tbps</span></div></div>', unsafe_allow_html=True)
    c12.markdown(f'<div class="metric-card border-orange"><div class="metric-title">Edge Capacity</div><div class="metric-value">{edge_capacity_tbps:,.1f} <span style="font-size: 1rem;">Tbps</span></div></div>', unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    
    # --- 6. Render Visualizations (3 Columns) ---
    c13, c14, c15 = st.columns(3)
    
    with c13:
        st.markdown("**1. POP Classification**")
        with st.container(border=True):
            df_loc_type = pd.DataFrame(loc_type_data)
            if not df_loc_type.empty:
                type_counts = df_loc_type['POP Type'].value_counts().reset_index()
                type_counts.columns = ['POP Type', 'Location Count']
                
                fig1 = px.pie(
                    type_counts, 
                    names='POP Type', 
                    values='Location Count', 
                    hole=0.4, 
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