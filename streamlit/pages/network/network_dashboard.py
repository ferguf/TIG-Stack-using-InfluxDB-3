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
    
    # New structures for the POP type visualizations
    loc_type_data = []

    # New POP Classification Counters
    tier1_pops = 0
    tier2_pops = 0
    dce_pops = 0
    non_digital_pops = 0
    other_digital_pops = 0 # Safety catch-all for unexpected VAR combinations

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
            # Catches edge cases (e.g., VAR + EVCR but no SDR/SCR/ES)
            pop_type = 'Other Digital'
            other_digital_pops += 1
            
        # Store for visualizations
        loc_type_data.append({
            'Location': loc,
            'POP Type': pop_type,
            'Total Devices': pop_device_count
        })
            
        # Parse Link Capacity safely (Inter-Pop only for backbone math)
        links = pop.get('link_distribution') or []
        for link_obj in links:
            if link_obj.get('link_type') == 'Inter-Pop':
                total_backbone_gbps += (link_obj.get('total_capacity_gbps') or 0.0)

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
        /* Top Row Colors */
        .border-blue { border-left-color: #3b82f6; }
        .border-purple { border-left-color: #8b5cf6; }
        .border-teal { border-left-color: #14b8a6; }
        .border-orange { border-left-color: #f97316; }
        
        /* POP Classification Colors */
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

    st.write("<br>", unsafe_allow_html=True)
    
    # --- 5. Render POP Type Visualizations ---
    c1, c2 = st.columns(2)
    
    # Convert our visualization tracking list to a DataFrame
    df_loc_type = pd.DataFrame(loc_type_data)
    
    with c1:
        st.markdown("**1. POP Classification Distribution**")
        with st.container(border=True):
            if not df_loc_type.empty:
                # Group by POP Type to get the raw counts for the Pie Chart
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
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No classification data available.")

    with c2:
        st.markdown("**2. Hardware Density by POP Type**")
        with st.container(border=True):
            if not df_loc_type.empty:
                # Sort descending by device count so the largest Tier 1s sit on the left
                df_loc_type = df_loc_type.sort_values(by='Total Devices', ascending=False)
                sorted_locations = df_loc_type['Location'].tolist()
                
                fig2 = px.bar(
                    df_loc_type, 
                    x='Location', 
                    y='Total Devices', 
                    color='POP Type', 
                    text_auto=True, 
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    category_orders={"Location": sorted_locations}
                )
                
                show_x_labels = len(sorted_locations) <= 15
                fig2.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20), height=350, xaxis_title="Location",
                    xaxis=dict(showticklabels=show_x_labels),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No location density data available.")