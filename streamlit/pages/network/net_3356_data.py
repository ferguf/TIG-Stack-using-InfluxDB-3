import streamlit as st
import pandas as pd
import numpy as np
import math
import logging

# --- NDT CORE IMPORTS ---
from src.utils.api_network import get_global_traffic_summary, get_regional_detail_summary, get_pop_to_pop_summary, get_router_summary,get_pop_summary,get_router_detail

logger = logging.getLogger(__name__)

# =============================================================================
# MATH & FORMATTING HELPERS
# =============================================================================

def format_bytes(size_in_bytes):
    """Converts raw byte counts into human-readable formats (TB, PB, EB, ZB)."""
    if not size_in_bytes or size_in_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_in_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_in_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_bezier_curve(p0, p2, p1=(0, 0), num_points=30):
    """Generates Radial Chord ribbons pulling towards the center (0,0)."""
    t = np.linspace(0, 1, num_points)
    x = (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
    y = (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
    return x, y

# =============================================================================
# DATA FETCHERS & NORMALIZERS (STATIC CACHE)
# =============================================================================

@st.cache_data(show_spinner=False)
def global_traffic_summary():
    """
    Fetches and normalizes the Global Macro Telemetry.
    Returns a dictionary containing the raw payload, global metrics, and regional DataFrame.
    """
    try:
        raw_payload = get_global_traffic_summary()
    except Exception as e:
        logger.error(f"Macro fetch failed: {e}")
        return {"error": str(e)}

    if raw_payload and isinstance(raw_payload, dict) and "global" in raw_payload and "regions" in raw_payload:
        return {
            "raw": raw_payload,
            "global_metrics": raw_payload["global"],
            "df_regions": pd.DataFrame(raw_payload["regions"])
        }
    return {"error": "Invalid API payload structure."}


@st.cache_data(show_spinner=False)
def fetch_micro_state(granularity, duration):
    """
    Fetches and normalizes Inter-Pop FEC Telemetry.
    """
    raw_traffic = [
        {"fec_id": "012d5e1d", "bucket_start": "2026-05-04T00:00:00Z", "granularity": "day", "device_a_name": "EAR3.SFO1", "device_b_name": "EAR3.NYC1", "fec_label": "EAR3.SFO1 ↔ EAR3.NYC1", "avg_mbps": 122, "min_mbps": 97.01, "max_mbps": 146.99, "p95_mbps": 146.65, "total_mbps": 11712},
        {"fec_id": "0af9779b", "bucket_start": "2026-05-04T00:00:00Z", "granularity": "day", "device_a_name": "EAR1.SFO1", "device_b_name": "EAR1.WDC1", "fec_label": "EAR1.SFO1 ↔ EAR1.WDC1", "avg_mbps": 95, "min_mbps": 52.02, "max_mbps": 137.98, "p95_mbps": 137.42, "total_mbps": 9120},
        {"fec_id": "mock-333", "bucket_start": "2026-05-04T00:00:00Z", "granularity": "day", "device_a_name": "EAR1.WDC1", "device_b_name": "EAR3.NYC1", "fec_label": "EAR1.WDC1 ↔ EAR3.NYC1", "avg_mbps": 210, "min_mbps": 150.00, "max_mbps": 300.00, "p95_mbps": 280.00, "total_mbps": 25000}
    ]

    if not raw_traffic:
        return {"error": "No inter-pop telemetry returned."}

    if isinstance(raw_traffic, dict):
        if "data" in raw_traffic: raw_traffic = raw_traffic["data"]
        elif "results" in raw_traffic: raw_traffic = raw_traffic["results"]
        else: raw_traffic = [raw_traffic]

    df_traffic = pd.DataFrame(raw_traffic)
    if 'device_a_name' not in df_traffic.columns or 'device_b_name' not in df_traffic.columns:
        return {"error": "Telemetry payload missing required routing nodes."}

    return {"df_traffic": df_traffic, "raw": raw_traffic}


@st.cache_data(show_spinner=False)
def regional_detail_summary(report_date="2026-04-23", pop_limit=50, router_limit=50):
    """
    Fetches and normalizes deep regional topology data.
    Flattens the nested Region -> Provider -> PoP JSON into a DataFrame-friendly format.
    """
    try:
        raw_payload = get_regional_detail_summary(report_date, pop_limit, router_limit)
    except Exception as e:
        logger.error(f"Regional detail fetch failed: {e}")
        raw_payload = {}

    if not raw_payload or "regions" not in raw_payload:
        return {"error": "Invalid regional API payload structure or no data returned."}

    flattened_pops = []
    for region_data in raw_payload.get("regions", []):
        region_name = region_data.get("region", "Unknown")
        for provider_data in region_data.get("providers", []):
            provider_name = provider_data.get("provider", provider_data.get("provider_name", "Primary")) 
            for pop_data in provider_data.get("pops", []):
                flattened_pops.append({
                    "region": region_name,
                    "provider": provider_name,
                    "pop_id": pop_data.get("pop"),
                    "city": pop_data.get("city", ""),
                    "state": pop_data.get("state", ""),
                    "country": pop_data.get("country", ""),
                    "router_count": pop_data.get("router_count", 0),
                    "routers": pop_data.get("routers", []) 
                })

    return {
        "raw": raw_payload,
        "df_pops": pd.DataFrame(flattened_pops)
    }


@st.cache_data(show_spinner=False)
def pop_to_pop_telemetry(source_pop: str, limit: int = 25):
    """
    Fetches and normalizes bi-directional flow telemetry for a specific PoP.
    """
    try:
        raw_payload = get_pop_to_pop_summary(source_pop, limit)
    except Exception as e:
        logger.error(f"PoP-to-PoP fetch failed: {e}")
        raw_payload = []

    # --- FALLBACK MOCK DATA (Matches the new bi-directional schema) ---
    if not raw_payload:
        raw_payload = [
            {"rank": 1, "src_pop": source_pop, "dst_pop": "slc1", "total_bytes": 29506319545470910, "inter_bytes": 29506319545470910, "src_region": "North America", "dst_region": "North America"},
            {"rank": 2, "src_pop": "dal1", "dst_pop": source_pop, "total_bytes": 15713834164019952, "inter_bytes": 15713834157036272, "src_region": "North America", "dst_region": "North America"},
            {"rank": 3, "src_pop": "dal2", "dst_pop": source_pop, "total_bytes": 10267757266112794, "inter_bytes": 10267757266112794, "src_region": "North America", "dst_region": "North America"}
        ]
    
    if isinstance(raw_payload, dict):
        if "data" in raw_payload: raw_payload = raw_payload["data"]
        elif "results" in raw_payload: raw_payload = raw_payload["results"]
        else: raw_payload = [raw_payload]

    df_flows = pd.DataFrame(raw_payload)

    return {
        "df_flows": df_flows,
        "raw": raw_payload
    }
    
def get_pop_site_summary(pop_id: str):
    """
    NDT Controller: Fetches the aggregate site summary and router list for a PoP.
    Connects to the /traffic/pops/{pop_id}/summary endpoint.
    """
    # 1. Fetch raw JSON from the API layer (assumes direct import)
    # Ensure 'from src.api_customer import get_pop_summary' is at top of file
    raw_data = get_pop_summary(pop_id=pop_id)
    
    # 2. Safety check for empty or failed API responses
    if not raw_data:
        logger.error(f"NDT Data Controller - No summary returned for PoP: {pop_id}")
        return {
            "success": False, 
            "error": f"No data found for {pop_id}",
            "raw": {}
        }
    
    # 3. Standardize the data object for the UI
    # We extract common metrics here so the UI doesn't have to parse JSON logic
    return {
        "success": True,
        "total_egress": raw_data.get("pop_egress_total_bytes", 0),
        "total_ingress": raw_data.get("pop_ingress_total_bytes", 0),
        "router_count": len(raw_data.get("routers", [])),
        "global_share": raw_data.get("pct_pop_egress_of_global", 0),
        "raw": raw_data  # Pass through the full JSON for the Chassis Inventory table
    }


def router_detail_summary(router_id: str, report_date: str = "2026-04-21", limit: int = 25):
    """
    NDT Controller: Fetches detailed router-to-router ingress/egress flows.
    Safely renamed to prevent naming collisions with the imported API function.
    """
    # Calls the get_router_detail imported from src.utils.api_network
    raw_data = get_router_detail(
        router_id=router_id, 
        report_date=report_date, 
        egress_limit=limit, 
        ingress_limit=limit
    )
    
    if not raw_data:
        return {
            "success": False, 
            "error": f"No flow data returned for {router_id}",
            "raw": {}
        }
    
    return {
        "success": True,
        "raw": raw_data
    }
def router_traffic_leaderboard(limit=20, sort="egress_total"):
    """
    NDT Controller: Wraps the API call and prepares a DataFrame for Streamlit.
    """
    # 1. Call the API layer
    raw_json = get_router_summary(limit=limit, sort=sort)
    
    # 2. Return consistent state object
    if raw_json:
        return {
            "df_routers": pd.DataFrame(raw_json),
            "raw": raw_json
        }
    
    return {
        "df_routers": pd.DataFrame(),
        "error": "No data returned from NDT API"
    }