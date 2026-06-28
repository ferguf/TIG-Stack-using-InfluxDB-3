import logging
from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.orm import Session
from typing import List, Optional
from scripts.api_operation_network import get_network_links_detail_by_network, get_master_network_dashboard
from scripts.api_session import get_db,Base
from scripts import api_operation  # (kept since you may use it elsewhere)

# ------------------------------------------------------------
# Router Setup
# ------------------------------------------------------------
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inventory", tags=["inventory"])

# ------------------------------------------------------------
# ORM Models
# ------------------------------------------------------------
from scripts.api_model import (
    NetworkSummaryMaster,
    NetworkSummaryMasterV2,
    VSummaryDevices,
    VSummaryPorts,
    VSummaryPortHealth,
    VSummaryLinks,
    VSummaryLinksByLocation,
    VSummaryCustomers,
    VSummaryCustomerServices,
    VSummaryServices,
    VSummaryConnections,
)

# ------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------
from scripts.api_schema import (
    SummaryGroupedResponse,
    SummaryGroupedResponseV2,
    SummaryDevices,
    SummaryPorts,
    SummaryPortHealth,
    SummaryLinks,
    SummaryLinksByLocation,
    SummaryCustomers,
    SummaryCustomerServices,
    SummaryRow,
    SummaryRowV2,
    SummaryServices,
    SummaryConnections,
    VNetworkDashboardOut,
)

# ============================================================
#  GROUPED MASTER SUMMARY ENDPOINT
# ============================================================

from sqlalchemy import text

@router.get("/debug/raw")
def debug_raw(db: Session = Depends(get_db)):
    sql = text("SELECT * FROM v_network_summary_master_v2 ORDER BY id")
    rows = db.execute(sql).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/debug/models")
def debug_models():
    return {"models": list(Base.metadata.tables.keys())}


@router.get("/network/summary/grouped", response_model=SummaryGroupedResponse)
def get_network_summary_grouped(db: Session = Depends(get_db)):
    rows = db.query(NetworkSummaryMaster).order_by(
        NetworkSummaryMaster.category,
        NetworkSummaryMaster.unique_id
    ).all()

    grouped = {
        "devices": [],
        "device_health": [],
        "device_lifecycle": [],
        "device_location": [],
        "device_vendor_model": [],
        "ports": [],
        "port_type": [],
        "port_speed": [],
        "port_optic": [],
        "port_health": [],
        "links_by_type": [],
        "links_by_location": [],
    }

    for row in rows:
        if row.category in grouped:
            grouped[row.category].append(
                SummaryRow(
                    id=row.unique_id,          # ← updated
                    category=row.category,
                    dimension=row.dimension,
                    count_value=row.count_value
                )
            )

    return grouped
@router.get("/network/summary/grouped/v2", response_model=SummaryGroupedResponseV2)

def get_network_summary_grouped_v2(db: Session = Depends(get_db)):
    rows = db.query(NetworkSummaryMasterV2).order_by(
        NetworkSummaryMasterV2.category,
        NetworkSummaryMasterV2.unique_id
    ).all()

    grouped = {
        "devices": [],
        "device_health": [],
    }

    for row in rows:
        grouped[row.category].append(
            SummaryRowV2(
                id=row.unique_id,
                category=row.category,
                dimension=row.dimension,
                count_value=row.count_value
            )
        )

    return grouped

# ============================================================
#  DEVICES SUMMARY
# ============================================================
@router.get("/summary/devices", response_model=List[SummaryDevices])
def read_summary_devices(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryDevices).all()
    except Exception as e:
        logger.error(f"Error fetching device summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch device summary")


# ============================================================
#  PORTS SUMMARY
# ============================================================
@router.get("/summary/ports", response_model=List[SummaryPorts])

def read_summary_ports(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryPorts).all()
    except Exception as e:
        logger.error(f"Error fetching port summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch port summary")


@router.get("/summary/ports/health", response_model=List[SummaryPortHealth])
def read_summary_port_health(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryPortHealth).all()
    except Exception as e:
        logger.error(f"Error fetching port health summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch port health summary")


# ============================================================
#  LINKS SUMMARY
# ============================================================
@router.get("/summary/links", response_model=List[SummaryLinks])
def read_summary_links(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryLinks).all()
    except Exception as e:
        logger.error(f"Error fetching link summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch link summary")


@router.get("/summary/links/location", response_model=List[SummaryLinksByLocation])
def read_summary_links_by_location(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryLinksByLocation).all()
    except Exception as e:
        logger.error(f"Error fetching link-by-location summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch link-by-location summary")


# ============================================================
#  CUSTOMERS SUMMARY
# ============================================================
@router.get("/summary/customers", response_model=List[SummaryCustomers])
def read_summary_customers(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryCustomers).all()
    except Exception as e:
        logger.error(f"Error fetching customer summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer summary")


@router.get("/summary/customers/services", response_model=List[SummaryCustomerServices])
def read_summary_customer_services(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryCustomerServices).all()
    except Exception as e:
        logger.error(f"Error fetching customer service summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer service summary")


# ============================================================
#  SERVICES SUMMARY
# ============================================================
@router.get("/summary/services", response_model=List[SummaryServices])
def read_summary_services(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryServices).all()
    except Exception as e:
        logger.error(f"Error fetching service summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service summary")


# ============================================================
#  CONNECTIONS SUMMARY
# ============================================================
@router.get("/summary/connections", response_model=List[SummaryConnections])
def read_summary_connections(db: Session = Depends(get_db)):
    try:
        return db.query(VSummaryConnections).all()
    except Exception as e:
        logger.error(f"Error fetching connection summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch connection summary")
   
# --- New Step 6 Master Dashboard Endpoint ---
from pydantic import ValidationError

@router.get("/networkLinks/dashboard/master/{network_name}", response_model=List[VNetworkDashboardOut])
def read_master_dashboard(
    network_name: str, 
    pop: Optional[str] = Query(None, description="Filter by specific POP (e.g., NYC6)"),
    link_type: Optional[str] = Query(None, description="Filter by link type (e.g., Inter-Pop)"),
    db: Session = Depends(get_db)
):
    safe_network_name = network_name.upper()
    
    # Pass the optional parameters down to your database logic
    dashboard_data = get_master_network_dashboard(
        db, 
        network=safe_network_name, 
        pop=pop, 
        link_type=link_type
    )
    
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="No data found matching those filters")
        
    # Manually attempt validation to catch and print the exact Pydantic error
    try:
        validated_data = [VNetworkDashboardOut.from_orm(row) for row in dashboard_data]
        return validated_data
    except ValidationError as e:
        print("------------- PYDANTIC VALIDATION ERROR -------------")
        print(e)
        print("---------------------------------------------------")
        raise HTTPException(status_code=500, detail=str(e))
