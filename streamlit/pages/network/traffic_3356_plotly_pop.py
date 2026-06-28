import plotly.graph_objects as go
import numpy as np
import pandas as pd
import streamlit as st

# --- NDT CORE IMPORTS ---
from pages.network import net_3356_data as data_ctrl

def apply_dashboard_theme(fig, height=450, hide_axes=True):
    """Standardizes Plotly charts to the NDT Dark Mode theme."""
    fig.update_layout(
        template="plotly_dark", height=height,
        margin=dict(t=50, b=20, l=20, r=20),
        font=dict(size=12, color="#E0E0E0"),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    if hide_axes:
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    return fig

    # =============================================================================
    # REUSABLE CHART TEMPLATES
    # =============================================================================

def render_top_20_map(state: dict):
    """
    NDT Geospatial Component: Visualizes Top 20 routers on a global map.
    Rank Tiers:
    - 1-5:  Green  | 10px
    - 6-10: Blue   | 8px
    - 11-15: Orange | 6px
    - 16-20: Yellow | 4px
    """
    
    # --- 1. DATA EXTRACTION ---
    df_top = state.get("df_routers", pd.DataFrame())
    if df_top.empty:
        df_top = st.session_state.get("topo_df_routers", pd.DataFrame())

    if df_top.empty:
        st.warning("📡 No leaderboard data available to render the map.")
        return

    # --- 2. DATA PREPARATION ---
    df_map = df_top.head(20).reset_index(drop=True)
    df_map['latitude'] = pd.to_numeric(df_map['latitude'], errors='coerce')
    df_map['longitude'] = pd.to_numeric(df_map['longitude'], errors='coerce')
    
    # Filter out nodes missing coordinates
    df_map = df_map.dropna(subset=['latitude', 'longitude'])

    if df_map.empty:
        st.info("📍 Topology nodes detected but lack geographic coordinates for mapping.")
        return

    # --- 3. RANK-BASED LOGIC (Static Colors & Sizes) ---
    def get_rank_attributes(idx):
        """Returns (color, size) based on rank index."""
        if idx < 5:  
            return '#66BB6A', 24  # Rank 1-5: Green, 10px
        if idx < 10: 
            return '#29B6F6', 18   # Rank 6-10: Blue, 8px
        if idx < 15: 
            return '#FFA726', 12   # Rank 11-15: Orange, 6px
        return '#FFEE58', 10       # Rank 16-20: Yellow, 4px

    # Apply attributes to dataframe
    attributes = [get_rank_attributes(i) for i in range(len(df_map))]
    df_map['marker_color'] = [a[0] for a in attributes]
    df_map['marker_size'] = [a[1] for a in attributes]

    # --- 4. MAP RENDERING ---
    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        lat=df_map['latitude'],
        lon=df_map['longitude'],
        mode='markers+text',
        marker=go.scattermapbox.Marker(
            size=df_map['marker_size'],
            color=df_map['marker_color'],
            opacity=0.9
        ),
        text=df_map['city'].str.upper(),
        textposition="top right",
        textfont=dict(size=9, color="white"),
        hovertemplate=(
            "<b>Rank %{customdata[0]}</b><br>" +
            "Router: %{customdata[1]}<br>" +
            "City: %{text}<br>" +
            "Global Share: %{customdata[2]:.4f}%" +
            "<extra></extra>"
        ),
        customdata=list(zip(
            df_map.index + 1, 
            df_map['router'].str.upper(), 
            df_map['pct_router_egress_of_global']
        ))
    ))

    # Darkmode Layout configuration
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=go.layout.mapbox.Center(lat=35, lon=-25), 
            zoom=1.5,
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, height=600)
def create_sankey_chart(df_flows, center_node, height=600):
    """
    Generates a Sankey diagram mapping flow directionality.
    Egress flows (Center -> Peer) are Green.
    Ingress flows (Peer -> Center) are Red.
    Includes dynamic scaling to prevent Plotly layout collapse.
    """
    import plotly.graph_objects as go
    
    center_node = str(center_node).upper()

    # 1. Map unique nodes to indices
    unique_nodes = list(set(df_flows['src_pop'].str.upper()).union(set(df_flows['dst_pop'].str.upper())))
    if center_node in unique_nodes:
        unique_nodes.remove(center_node)
    
    all_nodes = [center_node] + unique_nodes
    node_map = {node: i for i, node in enumerate(all_nodes)}
    
    # --- FIX: Dynamic Height Calculation ---
    # Ensures we have at least 22 pixels of vertical space per node to prevent squishing
    dynamic_height = max(height, len(all_nodes) * 22)

    # 2. Prep lists and directional colors
    sources = []
    targets = []
    flow_values = []
    link_colors = []
    
    for _, row in df_flows.iterrows():
        src = row['src_pop'].upper()
        dst = row['dst_pop'].upper()
        val = row['total_bytes']
        
        sources.append(node_map[src])
        targets.append(node_map[dst])
        flow_values.append(val)
        
        # Color Logic: Green for Egress, Red for Ingress
        if src == center_node:
            link_colors.append("rgba(40, 167, 69, 0.4)")  # Green (Egress)
        else:
            link_colors.append("rgba(220, 53, 69, 0.4)")  # Red (Ingress)
    
    # 3. Build Hover labels
    # Using format_bytes dynamically if available in the module scope
    try:
        from pages.network import net_3356_data as data_ctrl
        format_func = data_ctrl.format_bytes
    except ImportError:
        format_func = lambda x: f"{x} B"

    link_hover = [
        f"<b>{src.upper()} ➔ {dst.upper()}</b><br>Volume: {format_func(val)}" 
        for src, dst, val in zip(df_flows['src_pop'], df_flows['dst_pop'], flow_values)
    ]

    # 4. Create Figure
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap', # --- FIX: Forces columns to align cleanly ---
        node=dict(
            pad=10, # --- FIX: Reduced padding to fit more nodes vertically ---
            thickness=15, 
            line=dict(color="rgba(255, 255, 255, 0.2)", width=1), 
            label=all_nodes, 
            color="#00d1ff" # Cyan for nodes to pop against red/green links
        ),
        link=dict(
            source=sources, 
            target=targets, 
            value=flow_values, 
            color=link_colors, 
            customdata=link_hover, 
            hovertemplate="%{customdata}<extra></extra>"
        )
    )])
    
    # 5. Theme and Layout
    # Assuming apply_dashboard_theme exists in this file
    if 'apply_dashboard_theme' in globals():
        fig = apply_dashboard_theme(fig, height=dynamic_height, hide_axes=True)
    else:
        # Fallback if the theme function isn't found
        fig.update_layout(height=dynamic_height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    fig.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        font=dict(size=12, color="#E0E0E0")
    )
    
    return fig

def create_split_axis_bar(df_flows, center_node, height=500):
    """
    Renders a Split-Axis/Butterfly Bar Chart for NDT.
    Legend order: Ingress (Left/Green) then Egress (Right/Red).
    """
    # 1. Prep Data
    unique_nodes = list(set(df_flows['src_pop'].str.upper()).union(set(df_flows['dst_pop'].str.upper())))
    if center_node in unique_nodes: 
        unique_nodes.remove(center_node)
        
    egress_df = df_flows[df_flows['src_pop'].str.upper() == center_node]
    ingress_df = df_flows[df_flows['dst_pop'].str.upper() == center_node]
    
    peer_stats = []
    for peer in unique_nodes:
        eg_vol = egress_df[egress_df['dst_pop'].str.upper() == peer]['total_bytes'].sum() if not egress_df.empty else 0
        in_vol = ingress_df[ingress_df['src_pop'].str.upper() == peer]['total_bytes'].sum() if not ingress_df.empty else 0
        peer_stats.append({'peer': peer, 'egress': eg_vol, 'ingress': in_vol, 'total': eg_vol + in_vol})
    
    df_peers = pd.DataFrame(peer_stats).sort_values('total', ascending=True)

    # 2. Build Figure
    fig = go.Figure()

    # --- INGRESS FIRST (Aligns to the left in the legend) ---
    fig.add_trace(go.Bar(
        y=df_peers['peer'], 
        x=-df_peers['ingress'],
        name='Ingress (Inbound)', 
        orientation='h',
        marker_color='rgba(102, 187, 106, 0.85)', # NDT Green
        hovertext=[f"IN: {data_ctrl.format_bytes(v)}" for v in df_peers['ingress']],
        hoverinfo="text+y"
    ))

    # --- EGRESS SECOND (Aligns to the right in the legend) ---
    fig.add_trace(go.Bar(
        y=df_peers['peer'], 
        x=df_peers['egress'],
        name='Egress (Outbound)', 
        orientation='h',
        marker_color='rgba(239, 83, 80, 0.85)', # NDT Red
        hovertext=[f"OUT: {data_ctrl.format_bytes(v)}" for v in df_peers['egress']],
        hoverinfo="text+y"
    ))

    # 3. Symmetry & Formatting
    abs_max = max(df_peers['egress'].max(), df_peers['ingress'].max()) if not df_peers.empty else 1
    x_limit = abs_max * 1.1

    tick_vals = np.linspace(-x_limit, x_limit, 5)
    tick_text = [data_ctrl.format_bytes(abs(v)) for v in tick_vals]

    fig.update_layout(
        barmode='relative',
        bargap=0.1,
        xaxis=dict(
            tickmode='array', 
            tickvals=tick_vals, 
            ticktext=tick_text,
            zeroline=True, 
            zerolinewidth=2, 
            zerolinecolor='white',
            gridcolor='rgba(255,255,255,0.1)',
            title="Traffic Volume"
        ),
        yaxis=dict(showgrid=False, title=""),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.05, 
            xanchor="center", 
            x=0.5,
            font=dict(size=12)
        )
    )

    return apply_dashboard_theme(fig, height=height, hide_axes=False)

def create_radial_topology(df_flows, center_node, height=500):
    """
    Generates a Hub & Spoke star topology.
    Legend is restricted to primary directional colors: Red (Ingress) and Green (Egress).
    """
    unique_nodes = list(set(df_flows['src_pop'].str.upper()).union(set(df_flows['dst_pop'].str.upper())))
    if center_node in unique_nodes: unique_nodes.remove(center_node)
    
    all_nodes = [center_node] + unique_nodes
    node_map = {node: i for i, node in enumerate(all_nodes)}
    
    fig = go.Figure()
    angles = np.linspace(0, 2 * np.pi, len(unique_nodes), endpoint=False)
    x_coords = [0] + [np.cos(a) for a in angles]
    y_coords = [0] + [np.sin(a) for a in angles]
    
    # --- Data Calculations ---
    node_volumes = [0] * len(all_nodes)
    flow_values = []
    for i, row in df_flows.iterrows():
        s_idx, t_idx = node_map[row['src_pop'].upper()], node_map[row['dst_pop'].upper()]
        val = row['total_bytes']
        node_volumes[s_idx] += val
        node_volumes[t_idx] += val
        flow_values.append(val)
    
    v_max = max(node_volumes) if node_volumes else 1
    display_sizes = [max(15, (v / v_max) * 50) for v in node_volumes]
    max_flow = max(flow_values) if flow_values else 1

    # --- 1. Primary Legend Proxies ---
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color="rgba(40, 167, 69, 0.8)", width=6),
        name="Egress (Outbound)", showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color="rgba(220, 53, 69, 0.8)", width=6),
        name="Ingress (Inbound)", showlegend=True
    ))

    # --- 2. Draw Edges ---
    for i, row in df_flows.iterrows():
        s_idx, t_idx = node_map[row['src_pop'].upper()], node_map[row['dst_pop'].upper()]
        val = row['total_bytes']
        
        is_egress = row['src_pop'].upper() == center_node
        edge_color = "rgba(40, 167, 69, 0.6)" if is_egress else "rgba(220, 53, 69, 0.6)"
        legend_group = "Egress (Outbound)" if is_egress else "Ingress (Inbound)"
            
        # Line Weighting: Base 2x multiplier
        weighted_width = max(2.0, (val / max_flow) * 12) 
        
        fig.add_trace(go.Scatter(
            x=[x_coords[s_idx], x_coords[t_idx]], 
            y=[y_coords[s_idx], y_coords[t_idx]],
            mode='lines', 
            line=dict(width=weighted_width, color=edge_color), 
            legendgroup=legend_group,
            showlegend=False, 
            hoverinfo='text',
            hovertext=f"{row['src_pop'].upper()} ➔ {row['dst_pop'].upper()}<br>Vol: {data_ctrl.format_bytes(val)}"
        ))
    
    # --- 3. Add Nodes (No Legend) ---
    fig.add_trace(go.Scatter(
        x=x_coords, y=y_coords, mode='markers+text',
        text=all_nodes, textposition="top center",
        marker=dict(size=display_sizes, color="#00d1ff", line=dict(width=1.5, color="white")),
        showlegend=False
    ))
    
    # --- 4. Layout ---
    fig = apply_dashboard_theme(fig, height=height, hide_axes=True)
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color="#E0E0E0")
        )
    )
    fig.update_xaxes(range=[-1.5, 1.5]).update_yaxes(range=[-1.5, 1.5], scaleanchor="x", scaleratio=1)
    
    return fig

def create_single_donut(df_flows, center_node, direction='egress', height=500):
    """
    Generates a single donut chart for either Egress or Ingress share.
    
    Parameters:
    - df_flows: DataFrame containing flow telemetry.
    - center_node: The target PoP (Point of Presence) to filter on.
    - direction: 'egress' (default) or 'ingress' to determine the traffic perspective.
    - height: Figure height in pixels.
    """
    import plotly.graph_objects as go
    
    # 1. Prep Data and define dynamic variables based on direction
    if direction.lower() == 'egress':
        target_df = df_flows[df_flows['src_pop'].str.upper() == center_node.upper()].copy()
        labels_col = 'dst_pop'
        title_text = "Egress Share"
        center_text = "OUT"
    elif direction.lower() == 'ingress':
        target_df = df_flows[df_flows['dst_pop'].str.upper() == center_node.upper()].copy()
        labels_col = 'src_pop'
        title_text = "Ingress Share"
        center_text = "IN"
    else:
        raise ValueError("The 'direction' parameter must be either 'egress' or 'ingress'.")

    # Sort for consistent color mapping
    target_df = target_df.sort_values('total_bytes', ascending=False)

    # 2. Create Figure
    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=target_df[labels_col].str.upper(),
        values=target_df['total_bytes'],
        name=title_text,
        hole=.4,
        textinfo='label+percent',
        hovertext=[data_ctrl.format_bytes(v) for v in target_df['total_bytes']],
        hoverinfo="text+label"
    ))

    # 3. Update Layout
    fig.update_layout(
        title_text=title_text,
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
        annotations=[
            # Places the dynamic text exactly in the center of the single donut
            dict(text=center_text, x=0.5, y=0.5, font_size=16, showarrow=False) 
        ]
    )

    # Returning via your custom NDT dashboard theme applier
    return apply_dashboard_theme(fig, height=height, hide_axes=True)

def create_dual_donuts(df_flows, center_node, height=500):
    """
    Generates two side-by-side donut charts for Egress and Ingress share.
    """
    from plotly.subplots import make_subplots
    
    # 1. Prep Data
    egress_df = df_flows[df_flows['src_pop'].str.upper() == center_node].copy()
    ingress_df = df_flows[df_flows['dst_pop'].str.upper() == center_node].copy()
    
    # Sort for consistent color mapping across both charts
    egress_df = egress_df.sort_values('total_bytes', ascending=False)
    ingress_df = ingress_df.sort_values('total_bytes', ascending=False)

    # 2. Create Subplots (1 row, 2 cols)
    fig = make_subplots(
        rows=1, cols=2, 
        specs=[[{'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=("Egress Share", "Ingress Share")
    )

    # Egress Donut (Left)
    fig.add_trace(go.Pie(
        labels=egress_df['dst_pop'].str.upper(),
        values=egress_df['total_bytes'],
        name="Egress",
        hole=.4,
        textinfo='label+percent',
        hovertext=[data_ctrl.format_bytes(v) for v in egress_df['total_bytes']],
        hoverinfo="text+label"
    ), 1, 1)

    # Ingress Donut (Right)
    fig.add_trace(go.Pie(
        labels=ingress_df['src_pop'].str.upper(),
        values=ingress_df['total_bytes'],
        name="Ingress",
        hole=.4,
        textinfo='label+percent',
        hovertext=[data_ctrl.format_bytes(v) for v in ingress_df['total_bytes']],
        hoverinfo="text+label"
    ), 1, 2)

    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
        annotations=[
            dict(text='OUT', x=0.20, y=0.5, font_size=12, showarrow=False),
            dict(text='IN', x=0.80, y=0.5, font_size=12, showarrow=False)
        ]
    )

    return apply_dashboard_theme(fig, height=height, hide_axes=True)

def create_dual_donuts_vertical(df_flows, center_node, height=700):
    """
    Generates two vertically stacked donut charts for Egress and Ingress share.
    Optimized for sidebars or narrow column layouts.
    """
    from plotly.subplots import make_subplots
    
    # 1. Prep Data
    egress_df = df_flows[df_flows['src_pop'].str.upper() == center_node].copy()
    ingress_df = df_flows[df_flows['dst_pop'].str.upper() == center_node].copy()
    
    # Sort for consistent color mapping
    egress_df = egress_df.sort_values('total_bytes', ascending=False)
    ingress_df = ingress_df.sort_values('total_bytes', ascending=False)

    # 2. Create Subplots (2 rows, 1 col)
    fig = make_subplots(
        rows=2, cols=1, 
        specs=[[{'type': 'domain'}], [{'type': 'domain'}]],
        subplot_titles=("Egress Share (Outbound)", "Ingress Share (Inbound)"),
        vertical_spacing=0.08
    )

    # Egress Donut (Top - Row 1)
    fig.add_trace(go.Pie(
        labels=egress_df['dst_pop'].str.upper(),
        values=egress_df['total_bytes'],
        name="Egress",
        hole=.45,
        textinfo='label+percent',
        hovertext=[data_ctrl.format_bytes(v) for v in egress_df['total_bytes']],
        hoverinfo="text+label"
    ), 1, 1)

    # Ingress Donut (Bottom - Row 2)
    fig.add_trace(go.Pie(
        labels=ingress_df['src_pop'].str.upper(),
        values=ingress_df['total_bytes'],
        name="Ingress",
        hole=.45,
        textinfo='label+percent',
        hovertext=[data_ctrl.format_bytes(v) for v in ingress_df['total_bytes']],
        hoverinfo="text+label"
    ), 2, 1)

    # 3. Layout Styling
    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        # Centering the IN/OUT text within the donut holes
        annotations=[
            dict(text='OUT', x=0.5, y=0.81, font_size=14, showarrow=False, font_color="#00d1ff"),
            dict(text='IN', x=0.5, y=0.19, font_size=14, showarrow=False, font_color="#ffc107")
        ]
    )

    # Note: We increase the default height since they are stacked
    return apply_dashboard_theme(fig, height=height, hide_axes=True)

def create_asymmetry_scatter(df_flows, center_node, height=500):
    """
    Replaces the Donut chart with an Asymmetry Matrix.
    X-axis: Egress Volume | Y-axis: Ingress Volume
    """
    unique_nodes = list(set(df_flows['src_pop'].str.upper()).union(set(df_flows['dst_pop'].str.upper())))
    if center_node in unique_nodes: unique_nodes.remove(center_node)
    
    peer_stats = []
    for peer in unique_nodes:
        egress = df_flows[(df_flows['src_pop'].str.upper() == center_node) & (df_flows['dst_pop'].str.upper() == peer)]['total_bytes'].sum()
        ingress = df_flows[(df_flows['dst_pop'].str.upper() == center_node) & (df_flows['src_pop'].str.upper() == peer)]['total_bytes'].sum()
        peer_stats.append({'peer': peer, 'egress': egress, 'ingress': ingress})
    
    df_asm = pd.DataFrame(peer_stats)
    
    fig = go.Figure()
    
    # 45-degree Symmetry Line
    max_val = max(df_asm['egress'].max(), df_asm['ingress'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode='lines',
        line=dict(color='rgba(255,255,255,0.2)', dash='dash'), name='Symmetry Line'
    ))

    fig.add_trace(go.Scatter(
        x=df_asm['egress'], y=df_asm['ingress'], mode='markers+text',
        text=df_asm['peer'], textposition="top center",
        marker=dict(size=12, color='#00d1ff', symbol='diamond'),
        hovertext=[f"Eg: {data_ctrl.format_bytes(e)}<br>In: {data_ctrl.format_bytes(i)}" 
                   for e, i in zip(df_asm['egress'], df_asm['ingress'])],
        hoverinfo="text+text", name="Peers"
    ))

    fig.update_layout(
        xaxis_title="Egress Volume", yaxis_title="Ingress Volume",
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', scaleanchor="x", scaleratio=1),
        showlegend=False
    )

    return apply_dashboard_theme(fig, height=height, hide_axes=False)

def create_internal_sankey(df, title, height=600):
    """
    Generates a Sankey diagram mapping Routers to Traffic Categories.
    Updated to force labels outside the nodes and set font color to black.
    """
    # Create unique list of all nodes
    all_nodes = list(pd.concat([df['src'], df['dst']]).unique())
    node_map = {name: i for i, name in enumerate(all_nodes)}

    fig = go.Figure(data=[go.Sankey(
        # --- FIX 1: Set exact font color and size ---
        textfont=dict(color="black", size=12),
        node=dict(
            pad=15, 
            thickness=20, 
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color="lightgray"
        ),
        link=dict(
            source=df['src'].map(node_map),
            target=df['dst'].map(node_map),
            value=df['val'],
            color=df['clr']
        )
    )])

    fig.update_layout(
        title_text=title, 
        height=height, 
        # --- FIX 2: Add left/right margins to give text room to sit OUTSIDE ---
        margin=dict(l=140, r=140, t=40, b=20)
    )
    
    return fig

def get_flow_ledger_config(df_flows):
    """
    Processes flow data for tabular display and returns the DataFrame 
    along with its Streamlit column configuration.
    """
    # 1. Create display copy and format bytes
    df_display = df_flows.copy()
    byte_cols = ['total_bytes', 'inter_bytes', 'intra_bytes', 'router_bytes']
    
    for col in byte_cols:
        if col in df_display:
            df_display[col] = df_display[col].apply(data_ctrl.format_bytes)
            
    # 2. Define standard UI configuration
    column_config = {
        "rank": st.column_config.NumberColumn("Rank", format="%d"),
        "src_pop": "Source PoP",
        "dst_pop": "Target PoP",
        "total_bytes": "Total Volume",
        "inter_bytes": "Backbone Vol (Inter)",
        "src_region": "Source Region",
        "dst_region": "Target Region"
    }
    
    # Select columns to display
    display_cols = ['rank', 'src_pop', 'dst_pop', 'total_bytes', 'inter_bytes', 'src_region', 'dst_region']
    
    return df_display[display_cols], column_config