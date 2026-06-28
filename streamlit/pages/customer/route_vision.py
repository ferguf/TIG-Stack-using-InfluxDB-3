import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from src.utils.api_route_vision import (
    get_route_vision_by_service, 
    process_routing_dataframe,
    provision_test_data
)
from src.utils.file_utils import MessageHandler
from src.ui_components import UI

# --- UTILITIES ---

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

# --- RENDERERS ---

import streamlit as st
import pandas as pd
import uuid

def show_route_vision(service_id: str):
    """
    Entry point for Tier 7: Route Vision.
    Features a 2-tab layout for technical RIB and customer-facing view.
    """
    from src.state_managers import FabricStateManager
    
    manager = FabricStateManager()
    fs_record = manager.get_active_record("fs")
    
    if not UI.render_service_context(fs_record):
        return

    service_type = fs_record.get("service_type", "").upper()

    # --- ACTION BAR ---
    st.divider()
    header_col, action_col = st.columns([3, 1])
    
    with header_col:
        st.markdown(f"#### 🛰️ Route Management")
        st.caption(f"Context: {service_type} Interface")

    with action_col:
        eligible_types = ["IPVPN", "MCGW"]
        is_eligible = any(t in service_type for t in eligible_types)
        
        if is_eligible:
            # Fixed with strict namespace _rv_hdr
            if UI.button("Create Routes", color="green", key=f"btn_create_{service_id}_rv_hdr"):
                with st.spinner("Injecting 60 test routes..."):
                    if provision_test_data(service_id):
                        st.toast("Routes Provisioned!", icon="🚀")
                        st.rerun()
        else:
            # Fixed dynamic key for disabled state
            st.button("Create Routes", disabled=True, key=f"btn_disabled_{service_id}_rv_hdr", use_container_width=True)
            st.caption("⚠️ Only for L3 Services")

    # 2. Fetch and Process Data
    raw_data = get_route_vision_by_service(service_id)
    df = process_routing_dataframe(raw_data)

    if df.empty:
        st.info("No routing data found. Use the 'Create Routes' button to initialize the RIB.")
        return

    # 3. Render Analytics (Metrics & Plots)
    render_vision_summary(df)
    st.divider()
    render_vision_details(df, service_id)

    # 4. TABBED VIEW - Explicitly defined
    st.markdown("### 📊 Routing Tables")
    tab1, tab2 = st.tabs(["📜 Fabric RIB", "👤 Customer View"])

    with tab1:
        st.markdown("#### Full Routing Information Base (RIB)")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("#### Customer Service View")
        view_df = df.copy()
        
        cust_mapping = {
            "ip_prefix": "Prefix",
            "ip_next_hop": "Nexthop",
            "route_type": "Type",
            "route_status": "Status",
            "bgp_asn": "Customer ASN",
            "bgp_community": "BGP Communities"
        }
        
        # Format Timestamps
        for time_col in ['created_at', 'updated_at']:
            if time_col in view_df.columns:
                view_df[time_col] = pd.to_datetime(view_df[time_col], utc=True)
                view_df[time_col] = view_df[time_col].apply(format_time_ago)

        # Filtering and renaming
        columns_to_display = [c for c in cust_mapping.keys() if c in view_df.columns]
        if 'created_at' in view_df.columns: columns_to_display.append('created_at')
        if 'updated_at' in view_df.columns: columns_to_display.append('updated_at')

        final_display = view_df[columns_to_display].rename(columns=cust_mapping)
        final_display = final_display.rename(columns={
            "created_at": "Created",
            "updated_at": "Last Updated"
        })

        st.dataframe(final_display, use_container_width=True, hide_index=True)

def render_vision_summary(df: pd.DataFrame):
    """
    ROW 1: Route Vision Summary (Integrated 1:7 Metrics)
    Includes the compact 50px BGP Session Status Ribbon chart.
    """
    import streamlit as st
    import plotly.express as px
    import pandas as pd

    # 1. Column Identification
    type_col = 'route_type' if 'route_type' in df.columns else 'Type'
    prefix_col = next((c for c in ['ip_prefix', 'Prefix', 'prefix'] if c in df.columns), None)
    nh_col = 'ip_next_hop' if 'ip_next_hop' in df.columns else 'Next Hop'

    # 2. Protocol & Addressing Logic
    type_series = df[type_col].str.upper() if type_col in df.columns else pd.Series()
    counts = type_series.value_counts().to_dict()

    ipv4_count, ipv6_count = 0, 0
    if prefix_col:
        prefix_series = df[prefix_col].astype(str)
        ipv4_count = prefix_series.str.contains(r'\.', regex=True, na=False).sum()
        ipv6_count = prefix_series.str.contains(r':', regex=True, na=False).sum()

    # 3. Topology Metrics Logic
    unique_sites = df[nh_col].nunique() if nh_col in df.columns else 0

    bgp_neighbors = 0
    if nh_col in df.columns and type_col in df.columns:
        bgp_neighbors = df[df[type_col].str.upper() == "BGP"][nh_col].nunique()

    # --- UI RENDER ---
    with st.container(border=True):
        st.subheader("📡 Protocol & Addressing")
        p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
        p1.metric("Sites", int(unique_sites), help="Distinct Next-Hops (All Types)")
        p2.metric("BGP Neighbors", int(bgp_neighbors), help="Distinct Next-Hops (BGP Only)")        
        p3.metric("IPv4", int(ipv4_count))
        p4.metric("IPv6", int(ipv6_count))
        p5.metric("BGP Routes", int(counts.get("BGP", 0)))
        p6.metric("Static", int(counts.get("STATIC", 0)))
        p7.metric("Direct", int(counts.get("DIRECT", 0)))

        # --- BGP Session Status Ribbon ---
        st.divider()
        st.markdown("##### BGP Session Status")
        
        # Identify necessary columns for the timeline
        ts_col = 'updated_at' if 'updated_at' in df.columns else ('created_at' if 'created_at' in df.columns else None)
        status_col = 'route_status' if 'route_status' in df.columns else ('Status' if 'Status' in df.columns else None)

        if ts_col and status_col:
            # Filter specifically for BGP records
            df_bgp = df[df[type_col].astype(str).str.upper() == "BGP"].copy()

            if not df_bgp.empty:
                # Normalize timestamps and status logic safely
                df_bgp['timestamp'] = pd.to_datetime(df_bgp[ts_col], utc=True)
                
                # Normalizes 1/0, "Active"/"Down", "Up"/"Down" all into strict 'UP' or 'DOWN'
                df_bgp['Status_Label'] = df_bgp[status_col].astype(str).str.upper().apply(
                    lambda x: 'UP' if x in ['1', '1.0', 'ACTIVE', 'UP', 'TRUE'] else 'DOWN'
                )
                df_bgp['Ribbon_Height'] = 1 
                
                fig_status = px.bar(
                    df_bgp, x='timestamp', y='Ribbon_Height', color='Status_Label',
                    color_discrete_map={'UP': '#28a745', 'DOWN': '#dc3545'},
                    hover_data={
                        'timestamp': '|%Y-%m-%d %H:%M', 
                        'Ribbon_Height': False, 
                        'Status_Label': True,
                        prefix_col: True if prefix_col else False
                    }
                )
                fig_status.update_layout(
                    bargap=0, 
                    height=50, 
                    showlegend=False,
                    yaxis=dict(visible=False, fixedrange=True), 
                    xaxis=dict(title="", visible=False), 
                    margin=dict(l=10, r=10, t=10, b=0) 
                )
                
                import uuid
                run_id = uuid.uuid4().hex[:6]
                st.plotly_chart(fig_status, use_container_width=True, key=f"bgp_status_ribbon_{run_id}")
            else:
                st.info("No active BGP routes available to generate session timeline.")
        else:
            st.caption("⚠️ Missing `updated_at` or `route_status` columns in the RIB payload.")
            
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

def get_stub_route_vision_data(service_id: str) -> list:
    """
    Generates mock routing data to stub the Route Vision API.
    Includes historical BGP session state changes to populate the timeline ribbon.
    """
    import uuid
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    data = []

    # 1. Generate Historical BGP Session States (For the Ribbon Chart)
    # We create 24 hours of state changes to simulate a session over time
    for i in range(24, -1, -1):
        record_time = now - timedelta(hours=i)
        
        # Simulate a network flap: Session goes DOWN 14 hours ago, recovers 12 hours ago
        is_up = 0 if i in [14, 13] else 1 
        
        data.append({
            "route_id": str(uuid.uuid4()),
            "service_id": service_id,
            "route_type": "BGP",
            "ip_prefix": "0.0.0.0/0",
            "ip_next_hop": "172.16.254.1",
            "route_status": is_up,
            "bgp_asn": 64512,
            "bgp_community": "64512:100",
            "created_at": (now - timedelta(days=30)).isoformat() + "Z",
            "updated_at": record_time.isoformat() + "Z"
        })

    # 2. Add Current BGP Routes (Learned via the active session)
    bgp_prefixes = ["10.50.0.0/24", "10.51.0.0/24", "10.52.0.0/24", "2001:db8:1::/64"]
    for pref in bgp_prefixes:
        data.append({
            "route_id": str(uuid.uuid4()),
            "service_id": service_id,
            "route_type": "BGP",
            "ip_prefix": pref,
            "ip_next_hop": "172.16.254.1",
            "route_status": 1,
            "bgp_asn": 64512,
            "bgp_community": "64512:100",
            "created_at": (now - timedelta(hours=5)).isoformat() + "Z",
            "updated_at": now.isoformat() + "Z"
        })

    # 3. Generate Static & Direct Routes
    static_prefixes = ["10.10.0.0/16", "10.20.0.0/16", "192.168.100.0/24"]
    for pref in static_prefixes:
        data.append({
            "route_id": str(uuid.uuid4()),
            "service_id": service_id,
            "route_type": "STATIC",
            "ip_prefix": pref,
            "ip_next_hop": "10.0.0.1",
            "route_status": 1,
            "bgp_asn": None,
            "bgp_community": None,
            "created_at": (now - timedelta(days=10)).isoformat() + "Z",
            "updated_at": (now - timedelta(days=1)).isoformat() + "Z"
        })
        
    data.append({
        "route_id": str(uuid.uuid4()),
        "service_id": service_id,
        "route_type": "DIRECT",
        "ip_prefix": "8.56.0.0/30",
        "ip_next_hop": "0.0.0.0",
        "route_status": 1,
        "bgp_asn": None,
        "bgp_community": None,
        "created_at": (now - timedelta(days=30)).isoformat() + "Z",
        "updated_at": (now - timedelta(days=30)).isoformat() + "Z"
    })

    return data