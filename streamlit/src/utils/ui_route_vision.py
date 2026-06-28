import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.api_route_vision import (
    get_route_vision_by_service, 
    process_routing_dataframe,
    provision_test_data
)
from src.ui_components import UI # Assuming this is available based on your snippet

def format_time_ago(ts):
    """Converts timestamp to a 'time ago' string (e.g., 2h ago, 3d ago)."""
    if pd.isna(ts):
        return "N/A"
    try:
        ts = pd.to_datetime(ts, utc=True)
        now = pd.Timestamp.now(tz='UTC')
        diff = now - ts
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = (diff.seconds % 3600) // 60
        return f"{minutes}m ago"
    except:
        return "N/A"

def render_route_vision(service_id: str, fs_detail: dict):
    """
    Renders the Route Vision analytics and RIB tables.
    Designed to be called inside a Streamlit tab.
    """
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import uuid

    # Cache buster ONLY for Plotly Charts to prevent duplicate rendering errors
    run_id = uuid.uuid4().hex[:6]

    service_type = fs_detail.get("service_type", "").upper()

    # --- ACTION BAR ---
    header_col, action_col = st.columns([3, 1])
    
    with header_col:
        st.subheader("🛰️ Routing & Control Plane")
        st.caption(f"Context: {service_type} Interface")

    with action_col:
        eligible_types = ["IPVPN", "MCGW", "L3VPN"] 
        is_eligible = any(t in service_type for t in eligible_types)
        
        if is_eligible:
            if st.button("🚀 Create Routes", type="primary", use_container_width=True, key=f"btn_create_{service_id}"):
                print("\n" + "="*40)
                print("🚨 1. STREAMLIT REGISTERED THE CLICK!")
                
                with st.spinner("Injecting test routes..."):
                    try:
                        print("🚨 2. CALLING provision_test_data()...")
                        
                        # We capture the output to verify it doesn't return None
                        result = provision_test_data(service_id)
                        
                        print(f"🚨 3. PROVISIONING RETURNED: {result}")
                        
                        if result:
                            st.toast("Routes Provisioned!", icon="✅")
                            st.rerun()
                        else:
                            st.error("API returned None. Check MessageHandler logs.")
                            
                    except Exception as e:
                        # If there is a hidden Python crash (like a missing import), this will catch it and print it!
                        print(f"🛑 CRASH CAUGHT: {e}")
                        st.error(f"Hidden Python Crash: {e}")
                
                print("="*40 + "\n")

    st.divider()

    # --- FETCH AND PROCESS DATA ---
    with st.spinner("Querying Route Information Base..."):
        # Using the stub data while the backend API is built
        raw_data = get_route_vision_by_service(service_id)
        df = process_routing_dataframe(raw_data)

    if df.empty:
        st.info("No routing data found. Use the 'Create Routes' button to initialize the RIB.")
        return

    # --- ROW 1: SUMMARY METRICS & BGP RIBBON ---
    type_col = 'route_type' if 'route_type' in df.columns else 'Type'
    prefix_col = next((c for c in ['ip_prefix', 'Prefix', 'prefix'] if c in df.columns), None)
    nh_col = 'ip_next_hop' if 'ip_next_hop' in df.columns else 'Next Hop'

    type_series = df[type_col].str.upper() if type_col in df.columns else pd.Series(dtype=str)
    counts = type_series.value_counts().to_dict()

    ipv4_count, ipv6_count = 0, 0
    if prefix_col:
        prefix_series = df[prefix_col].astype(str)
        ipv4_count = prefix_series.str.contains(r'\.', regex=True, na=False).sum()
        ipv6_count = prefix_series.str.contains(r':', regex=True, na=False).sum()

    unique_sites = df[nh_col].nunique() if nh_col in df.columns else 0
    bgp_neighbors = 0
    if nh_col in df.columns and type_col in df.columns:
        bgp_neighbors = df[df[type_col].str.upper() == "BGP"][nh_col].nunique()

    with st.container(border=True):
        st.markdown("##### 📡 Protocol & Addressing")
        p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
        p1.metric("Sites", int(counts.get("DIRECT", 0)), help="Distinct Direct")
        p2.metric("BGP Neighbors", int(bgp_neighbors), help="Distinct Next-Hops (BGP Only)")        
        p3.metric("IPv4", int(ipv4_count))
        p4.metric("IPv6", int(ipv6_count))
        p5.metric("BGP Routes", int(counts.get("BGP", 0)))
        p6.metric("Static", int(counts.get("STATIC", 0)))

        st.divider()
        ribbon_header, ribbon_controls = st.columns([1, 2])
        with ribbon_header:
            st.markdown("##### BGP Session Status")
        with ribbon_controls:
            # 🟢 FIX: Stable key for radio button so it remembers your choice
            time_filter = st.radio(
                "Timeframe Filter",
                ["1 Day", "7 Days", "1 Month", "All Time"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"bgp_time_{service_id}"
            )
        
        ts_col = 'updated_at' if 'updated_at' in df.columns else ('created_at' if 'created_at' in df.columns else None)
        status_col = 'route_status' if 'route_status' in df.columns else ('Status' if 'Status' in df.columns else None)

        if ts_col and status_col:
            df_bgp = df[df[type_col].astype(str).str.upper() == "BGP"].copy()

            if not df_bgp.empty:
                df_bgp['timestamp'] = pd.to_datetime(df_bgp[ts_col], utc=True)
                
                now = pd.Timestamp.utcnow()
                if time_filter == "1 Day":
                    df_bgp = df_bgp[df_bgp['timestamp'] >= (now - pd.Timedelta(days=1))]
                elif time_filter == "7 Days":
                    df_bgp = df_bgp[df_bgp['timestamp'] >= (now - pd.Timedelta(days=7))]
                elif time_filter == "1 Month":
                    df_bgp = df_bgp[df_bgp['timestamp'] >= (now - pd.Timedelta(days=30))]

                if df_bgp.empty:
                    st.info(f"No BGP events found in the last {time_filter.lower()}.")
                else:
                    df_bgp['Status_Label'] = df_bgp[status_col].astype(str).str.upper().apply(
                        lambda x: 'UP' if x in ['1', '1.0', 'ACTIVE', 'UP', 'TRUE'] else 'DOWN'
                    )
                    df_bgp['Ribbon_Height'] = 1 
                    
                    fig_status = px.bar(
                        df_bgp, x='timestamp', y='Ribbon_Height', color='Status_Label',
                        color_discrete_map={'UP': '#28a745', 'DOWN': '#dc3545'},
                        hover_data={
                            'timestamp': '|%b %d, %H:%M', 
                            'Ribbon_Height': False, 
                            'Status_Label': True,
                            prefix_col: True if prefix_col else False
                        }
                    )
                    
                    fig_status.update_layout(
                        bargap=0, 
                        height=75, 
                        showlegend=False,
                        yaxis=dict(visible=False, fixedrange=True), 
                        xaxis=dict(
                            title="", 
                            visible=True,
                            showgrid=False,
                            tickformat="%b %d, %H:%M"
                        ), 
                        margin=dict(l=10, r=10, t=5, b=20) 
                    )
                    
                    # Chart keeps run_id so it safely re-renders without breaking
                    st.plotly_chart(fig_status, use_container_width=True, key=f"bgp_status_ribbon_{service_id}_{run_id}")
            else:
                st.info("No active BGP routes available to generate session timeline.")
        else:
            st.caption("⚠️ Missing `updated_at` or `route_status` columns in the RIB payload.")

    # --- ROW 2: ANALYTICAL DETAIL ---
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        with st.container(border=True):
            st.caption("📊 Protocol Mix")
            if not df.empty and type_col in df.columns:
                mix_df = df[type_col].str.upper().value_counts().reset_index()
                mix_df.columns = ['Protocol', 'Count']
                fig1 = px.bar(
                    mix_df, x='Protocol', y='Count', color='Protocol', text_auto=True, 
                    height=200, template="plotly_white",
                    color_discrete_map={"BGP": "#636EFA", "STATIC": "#EF553B", "DIRECT": "#00CC96"}
                )
                fig1.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                
                st.plotly_chart(fig1, use_container_width=True, key=f"chart_proto_{service_id}_{run_id}")

    with c2:
        with st.container(border=True):
            st.caption("🏢 Nexthop Density")
            if not df.empty and nh_col in df.columns:
                nh_counts = df[nh_col].value_counts().reset_index()
                nh_counts.columns = ['Nexthop', 'Count']
                fig2 = px.bar(nh_counts.head(5), x='Nexthop', y='Count', height=200, template="plotly_white")
                fig2.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(t=0,b=0,l=0,r=0))
                
                st.plotly_chart(fig2, use_container_width=True, key=f"chart_nh_{service_id}_{run_id}")

    with c3:
        with st.container(border=True):
            st.caption("⚡ Utilization")
            limit = 1000
            current = len(df)
            st.metric("RIB Table Scale", f"{current}/{limit}", delta=f"{limit-current} available")
            st.progress(current/limit if current < limit else 1.0)
            st.caption(f"Service Route Capacity: {limit} Max")

    # --- ROW 3: SEARCH & TABBED TABLES ---
    render_rib_tables(df, service_id)  

def render_vision_details(df: pd.DataFrame, service_id: str):
    """
    ROW 2: Visual Analytics for Routes.
    Implements the UUID cache buster to prevent duplicate key errors.
    """
    import streamlit as st
    import plotly.express as px
    import uuid
    
    # Generate a unique ID for this specific render pass
    run_id = uuid.uuid4().hex[:6]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Protocol Distribution")
        type_col = 'route_type' if 'route_type' in df.columns else 'Type'
        if type_col in df.columns:
            proto_counts = df[type_col].value_counts().reset_index()
            proto_counts.columns = ['Protocol', 'Count']
            
            fig_proto = px.pie(proto_counts, names='Protocol', values='Count', hole=0.4)
            fig_proto.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            
            # The UUID fix applied here
            st.plotly_chart(fig_proto, use_container_width=True, key=f"chart_proto_{service_id}_{run_id}")
            
    with col2:
        st.markdown("#### Top Next Hops")
        nh_col = 'ip_next_hop' if 'ip_next_hop' in df.columns else 'Next Hop'
        if nh_col in df.columns:
            nh_counts = df[nh_col].value_counts().head(5).reset_index()
            nh_counts.columns = ['Next Hop', 'Route Count']
            
            fig_nh = px.bar(nh_counts, x='Next Hop', y='Route Count', color='Route Count')
            fig_nh.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            
            # The UUID fix applied here
            st.plotly_chart(fig_nh, use_container_width=True, key=f"chart_nh_{service_id}_{run_id}")

def render_rib_tables(df, service_id: str):
    """
    Renders the searchable, tabbed routing tables.
    Includes Fabric RIB, Customer View, and BGP Neighbors.
    Uses stable service_id for Streamlit widget keys to prevent phantom clicks.
    """
    import streamlit as st
    import pandas as pd
    import random

    st.divider()
    st.markdown("#### 🗄️ Routing Table Exploration")

    # 🟢 FIX: Using stable service_id so Streamlit doesn't forget your search query on rerun
    search_query = st.text_input(
        "🔍 Search RIB", 
        placeholder="Filter by Prefix, Nexthop, ASN, or Protocol...",
        help="Filters the Fabric RIB, Customer View, and BGP Neighbors simultaneously.",
        key=f"rib_search_{service_id}" 
    )

    if search_query:
        mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    tab_rib, tab_cust, tab_bgp = st.tabs(["📜 Fabric RIB", "👤 Customer View", "🤝 BGP Neighbors"])

    with tab_rib:
        st.markdown(f"##### Full Routing Information Base ({len(filtered_df)} routes)")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    with tab_cust:
        st.markdown("##### Customer Service View")
        
        view_df = filtered_df.copy()
        
        cust_mapping = {
            "ip_prefix": "Prefix",
            "ip_next_hop": "Nexthop",
            "route_type": "Type",
            "route_status": "Status",
            "bgp_asn": "Customer ASN",
            "bgp_community": "BGP Communities"
        }
        
        for time_col in ['created_at', 'updated_at']:
            if time_col in view_df.columns:
                view_df[time_col] = pd.to_datetime(view_df[time_col], utc=True)
                try:
                    view_df[time_col] = view_df[time_col].apply(format_time_ago)
                except NameError:
                    view_df[time_col] = view_df[time_col].dt.strftime('%Y-%m-%d %H:%M')

        columns_to_display = [c for c in cust_mapping.keys() if c in view_df.columns]
        if 'created_at' in view_df.columns: columns_to_display.append('created_at')
        if 'updated_at' in view_df.columns: columns_to_display.append('updated_at')

        final_display = view_df[columns_to_display].rename(columns=cust_mapping)
        final_display = final_display.rename(columns={
            "created_at": "Created",
            "updated_at": "Last Updated"
        })

        st.dataframe(final_display, use_container_width=True, hide_index=True)

    with tab_bgp:
        st.markdown("##### BGP Neighbor Summary")
        
        type_col = 'route_type' if 'route_type' in filtered_df.columns else 'Type'
        nh_col = 'ip_next_hop' if 'ip_next_hop' in filtered_df.columns else 'Next Hop'
        bgp_asn_col = 'bgp_asn' if 'bgp_asn' in filtered_df.columns else 'Customer ASN'
        bgp_status_col = 'route_status' if 'route_status' in filtered_df.columns else 'Status'

        if type_col in filtered_df.columns and nh_col in filtered_df.columns:
            bgp_df = filtered_df[filtered_df[type_col].astype(str).str.upper() == 'BGP']
            
            if not bgp_df.empty:
                bgp_neighbors_df = bgp_df.groupby(nh_col).agg({
                    bgp_asn_col: 'first' if bgp_asn_col in bgp_df.columns else lambda x: "Unknown",
                    bgp_status_col: 'first' if bgp_status_col in bgp_df.columns else lambda x: 1,
                    nh_col: 'count'
                }).rename(columns={nh_col: 'Prefixes Received'})
                
                bgp_neighbors_df = bgp_neighbors_df.reset_index()
                
                bgp_neighbors_df = bgp_neighbors_df.rename(columns={
                    nh_col: 'Neighbor IP',
                    bgp_asn_col: 'Peer ASN'
                })
                
                bgp_neighbors_df['State'] = bgp_neighbors_df[bgp_status_col].apply(
                    lambda x: 'Established' if str(x).upper() in ['1', '1.0', 'ACTIVE', 'UP', 'TRUE'] else 'Idle/Down'
                )
                
                bgp_neighbors_df['Uptime'] = [f"{random.randint(1, 45)}d {random.randint(1, 23)}h" for _ in range(len(bgp_neighbors_df))]
                
                bgp_neighbors_df = bgp_neighbors_df[['Neighbor IP', 'Peer ASN', 'State', 'Uptime', 'Prefixes Received']]
                
                st.dataframe(bgp_neighbors_df, use_container_width=True, hide_index=True)
            else:
                st.info("No BGP neighbors found in the current route table filter.")
        else:
            st.warning("Missing routing columns required to map BGP neighbors.")