# File: src/utils/ui_telemetry.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

def generate_performance_data(selection_type, alias, duration_days):
    """
    Generates realistic, mock time-series data for Performance metrics based on 
    the selected duration and component type.
    """
    now = datetime.now()
    
    # Determine interval based on duration to keep data points manageable
    if duration_days <= 2:
        interval_mins = 5
    elif duration_days <= 7:
        interval_mins = 30
    elif duration_days <= 30:
        interval_mins = 120
    else:
        interval_mins = 1440 # Daily for a year

    num_points = max(10, int((duration_days * 24 * 60) / interval_mins))
    timestamps = [now - timedelta(minutes=interval_mins * i) for i in range(num_points)]
    timestamps.reverse()

    df = pd.DataFrame({"timestamp": timestamps})

    # Add shared metrics (Traffic)
    base_traffic = np.random.normal(loc=500, scale=50, size=num_points)
    
    # Inject a realistic "spike" in the middle
    spike_start = int(num_points * 0.4)
    spike_end = int(num_points * 0.45)
    if spike_start < spike_end:
        base_traffic[spike_start:spike_end] += 300

    df["Traffic In (Mbps)"] = np.clip(base_traffic, 0, 1000)
    df["Traffic Out (Mbps)"] = np.clip(base_traffic * 0.8, 0, 1000)

    if selection_type == "Fabric Port":
        # Port-specific metrics
        # Simulate Status (mostly 1 for UP, occasional 0 for DOWN)
        status = np.random.choice([1, 1, 1, 1, 1, 0], size=num_points, p=[0.8, 0.1, 0.05, 0.03, 0.01, 0.01])
        df["Status"] = status
        
        # Simulate errors/drops (mostly 0, occasional spikes)
        df["Drops Out"] = np.random.poisson(lam=2, size=num_points) * np.random.choice([0, 1], size=num_points, p=[0.9, 0.1])
        df["Errors"] = np.random.poisson(lam=0.5, size=num_points) * np.random.choice([0, 1], size=num_points, p=[0.95, 0.05])

    elif selection_type == "Fabric Interface":
        # Interface-specific metrics (QoS Queues)
        total = df["Traffic Out (Mbps)"]
        
        # Allocate traffic across QoS queues (must sum to roughly 1.0)
        df["BE"] = total * np.random.uniform(0.3, 0.4, size=num_points)
        df["BE+"] = total * np.random.uniform(0.2, 0.3, size=num_points)
        df["Enhanced"] = total * np.random.uniform(0.1, 0.2, size=num_points)
        df["Enhanced+"] = total * np.random.uniform(0.05, 0.1, size=num_points)
        df["Priority"] = total * np.random.uniform(0.05, 0.1, size=num_points)
        df["Priority+"] = total * np.random.uniform(0.01, 0.05, size=num_points)

    return df.set_index("timestamp")
def render_telemetry_tab(t_perf, svc_detail: dict):
    """
    Renders the Performance & Utilization tab.
    Includes an interactive UI for users to customize chart color schemes dynamically.
    Component options are context-aware based on the Service Type.
    """
    import streamlit as st
    import plotly.express as px

    with t_perf:
        st.subheader("📊 Performance & Utilization")

        # --- 0. DYNAMIC COMPONENT LOGIC ---
        svc_type = str(svc_detail.get("service_type", "")).upper().replace("_", "-")
        
        component_options = ["Fabric Port"]
        
        if svc_type in ["IPVPN", "MCGW", "IOD"]:
            component_options.append("Fabric Interface")
            
        if svc_type in ["EPL", "EVPL", "EVP-LAN", "EP-LAN", "EP-LAM"]:
            component_options.append("Fabric Connection")
            
        if svc_type in ["IPVPN", "MCGW"]:
            component_options.append("Cloud Connection")

        # --- 1. Control Panel ---
        with st.container(border=True):
            col_type, col_alias, col_time = st.columns([1, 2, 2])
            
            with col_type:
                view_type = st.radio("Component Type", component_options)
            
            with col_alias:
                # 🟢 FIX: Handle nested cloud_interconnects payload
                if view_type == "Fabric Port":
                    options = [p.get("port_name", "Unknown") for p in svc_detail.get("fabric_ports", [])]
                    if not options: options = ["No Ports Available"]
                    
                elif view_type == "Fabric Interface":
                    options = [i.get("interface_name", "Unknown") for i in svc_detail.get("fabric_interfaces", [])]
                    if not options: options = ["No Interfaces Available"]
                    
                elif view_type == "Fabric Connection":
                    options = [c.get("connection_name", "Unknown") for c in svc_detail.get("fabric_connections", [])]
                    if not options: options = ["No Connections Available"]
                    
                elif view_type == "Cloud Connection":
                    options = []
                    # Loop through the nested partner structures
                    for interconnect in svc_detail.get("cloud_interconnects", []):
                        for conn in interconnect.get("connections", []):
                            options.append(conn.get("connection_name", "Unknown Cloud Connection"))
                    
                    if not options: options = ["No Cloud Connections Available"]
                    
                selected_alias = st.selectbox(f"Select {view_type}", options)
            
            with col_time:
                time_map = {"1 Day": 1, "2 Days": 2, "1 Week": 7, "1 Month": 30, "1 Year": 365}
                selected_time = st.radio("Timeframe", list(time_map.keys()), horizontal=True)

        # --- 2. Color Customization UI ---
        with st.expander("🎨 Customize Graph Colors"):
            if view_type == "Fabric Port":
                st.markdown("##### Bandwidth & Errors")
                c1, c2, c3, c4 = st.columns(4)
                color_in = c1.color_picker("Traffic In", "#26A11B")
                color_out = c2.color_picker("Traffic Out", "#CA5D1E")
                color_drops = c3.color_picker("Drops Out", "#FF0000")
                color_errs = c4.color_picker("Errors", "#FF007B")
                
                st.markdown("##### Link Status")
                c5, c6 = st.columns(2)
                color_status_up = c5.color_picker("Status UP", "#28A745")
                color_status_down = c6.color_picker("Status DOWN", "#DC3545")
            
            else:
                # Interfaces and Connections share the same basic Traffic In/Out colors
                c1, c2, c3 = st.columns([1, 1, 2])
                color_in = c1.color_picker("Traffic In", "#1FB442")
                color_out = c2.color_picker("Traffic Out", "#00CED1")
                
                if view_type == "Fabric Interface":
                    qos_theme = c3.selectbox("QoS Color Theme", ["Prism", "Pastel", "Vivid", "Safe", "Darkmint"])

        # Guardrail: Check if a valid option was selected
        if not selected_alias or "No " in str(selected_alias):
            st.warning(f"No {view_type}s found in the manifest to display telemetry.")
        else:
            # --- 3. Fetch Data ---
            days = time_map[selected_time]
            
            df_perf = generate_performance_data(view_type, selected_alias, days)
            df_plot = df_perf.reset_index()
            
            shared_margins = dict(l=50, r=20, t=40, b=10)
            shared_legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)

            # --- 4. View Logic: Fabric Port ---
            if view_type == "Fabric Port":
                st.markdown(f"#### Port Telemetry: `{selected_alias}`")
                
                st.markdown("##### Link Status")
                df_plot['Status_Label'] = df_plot['Status'].map({1: 'UP', 0: 'DOWN'})
                df_plot['Ribbon_Height'] = 1 
                
                fig_status = px.bar(
                    df_plot, x='timestamp', y='Ribbon_Height', color='Status_Label',
                    color_discrete_map={'UP': color_status_up, 'DOWN': color_status_down},
                    hover_data={'timestamp': '|%Y-%m-%d %H:%M', 'Ribbon_Height': False, 'Status_Label': True}
                )
                fig_status.update_layout(
                    bargap=0, height=50, showlegend=False,
                    yaxis=dict(visible=False, fixedrange=True), 
                    xaxis=dict(title="", visible=False), 
                    margin=dict(l=50, r=20, t=10, b=0) 
                )
                st.plotly_chart(fig_status, use_container_width=True)
                
                st.markdown("##### Bandwidth Utilization (Mbps)")
                fig_bw = px.area(
                    df_plot, x='timestamp', y=["Traffic In (Mbps)", "Traffic Out (Mbps)"],
                    color_discrete_sequence=[color_in, color_out] 
                )
                fig_bw.update_layout(
                    height=250, xaxis_title="", yaxis_title="Mbps",
                    legend=shared_legend, legend_title_text="", 
                    margin=shared_margins, hovermode="x unified" 
                )
                st.plotly_chart(fig_bw, use_container_width=True)
                
                st.markdown("##### Drops & Errors")
                fig_err = px.line(
                    df_plot, x='timestamp', y=["Drops Out", "Errors"],
                    color_discrete_map={"Drops Out": color_drops, "Errors": color_errs} 
                )
                fig_err.update_layout(
                    height=200, xaxis_title="", yaxis_title="Count",
                    legend=shared_legend, legend_title_text="", 
                    margin=shared_margins, hovermode="x unified"
                )
                st.plotly_chart(fig_err, use_container_width=True)

            # --- 5. View Logic: Logical & Virtual Connections ---
            elif view_type in ["Fabric Interface", "Fabric Connection", "Cloud Connection"]:
                st.markdown(f"#### {view_type} Telemetry: `{selected_alias}`")
                
                st.markdown("##### Bandwidth Utilization (Mbps)")
                fig_bw_virt = px.area(
                    df_plot, x='timestamp', y=["Traffic In (Mbps)", "Traffic Out (Mbps)"],
                    color_discrete_sequence=[color_in, color_out]
                )
                fig_bw_virt.update_layout(
                    height=250, xaxis_title="", yaxis_title="Mbps",
                    legend=shared_legend, legend_title_text="", 
                    margin=shared_margins, hovermode="x unified"
                )
                st.plotly_chart(fig_bw_virt, use_container_width=True)
                
                # Only Interfaces get the QoS breakdown chart
                if view_type == "Fabric Interface":
                    st.markdown("##### QoS Class Utilization")
                    
                    theme_mapping = {
                        "Prism": px.colors.qualitative.Prism, "Pastel": px.colors.qualitative.Pastel,
                        "Vivid": px.colors.qualitative.Vivid, "Safe": px.colors.qualitative.Safe,
                        "Darkmint": px.colors.sequential.Darkmint 
                    }
                    selected_qos_sequence = theme_mapping.get(qos_theme, px.colors.qualitative.Prism)

                    qos_cols = ["BE", "BE+", "Enhanced", "Enhanced+", "Priority", "Priority+"]
                    valid_qos_cols = [c for c in qos_cols if c in df_plot.columns]
                    
                    if valid_qos_cols:
                        fig_qos = px.bar(
                            df_plot, x='timestamp', y=valid_qos_cols,
                            color_discrete_sequence=selected_qos_sequence 
                        )
                        fig_qos.update_layout(
                            barmode='stack', height=300, xaxis_title="", yaxis_title="Mbps",
                            legend=shared_legend, legend_title_text="", 
                            margin=shared_margins, hovermode="x unified"
                        )
                        st.plotly_chart(fig_qos, use_container_width=True)
                    else:
                        st.info("No QoS telemetry data available for this interface.")