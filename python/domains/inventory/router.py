import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import ValidationError

# Centralized core DB
from core.database import get_db

# Native relative imports within the domain slice
from . import operations
from . import schemas as s

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory Domain"])

# ============================================================
#  DEBUG ENDPOINTS
# ============================================================

@router.get("/debug/raw")
def debug_raw(db: Session = Depends(get_db)):
    sql = text("SELECT * FROM v_network_summary_master_v2 ORDER BY id")
    rows = db.execute(sql).fetchall()
    return [dict(r._mapping) for r in rows]

# ============================================================
#  GROUPED MASTER SUMMARY ENDPOINTS
# ============================================================

@router.get("/network/summary/grouped", response_model=s.SummaryGroupedResponse)
def get_network_summary_grouped(db: Session = Depends(get_db)):
    try:
        return operations.get_network_summary_grouped(db)
    except Exception as e:
        logger.error(f"Error fetching grouped summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch grouped summary")


@router.get("/network/summary/grouped/v2", response_model=s.SummaryGroupedResponseV2)
def get_network_summary_grouped_v2(db: Session = Depends(get_db)):
    try:
        return operations.get_network_summary_grouped_v2(db)
    except Exception as e:
        logger.error(f"Error fetching grouped v2 summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch grouped v2 summary")

# ============================================================
#  GRANULAR SUMMARY ENDPOINTS
# ============================================================

@router.get("/summary/devices", response_model=List[s.SummaryDevices])
def read_summary_devices(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_devices(db)
    except Exception as e:
        logger.error(f"Error fetching device summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch device summary")


@router.get("/summary/ports", response_model=List[s.SummaryPorts])
def read_summary_ports(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_ports(db)
    except Exception as e:
        logger.error(f"Error fetching port summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch port summary")


@router.get("/summary/ports/health", response_model=List[s.SummaryPortHealth])
def read_summary_port_health(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_port_health(db)
    except Exception as e:
        logger.error(f"Error fetching port health summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch port health summary")


@router.get("/summary/links", response_model=List[s.SummaryLinks])
def read_summary_links(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_links(db)
    except Exception as e:
        logger.error(f"Error fetching link summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch link summary")


@router.get("/summary/links/location", response_model=List[s.SummaryLinksByLocation])
def read_summary_links_by_location(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_links_by_location(db)
    except Exception as e:
        logger.error(f"Error fetching link-by-location summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch link-by-location summary")


@router.get("/summary/customers", response_model=List[s.SummaryCustomers])
def read_summary_customers(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_customers(db)
    except Exception as e:
        logger.error(f"Error fetching customer summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer summary")


@router.get("/summary/customers/services", response_model=List[s.SummaryCustomerServices])
def read_summary_customer_services(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_customer_services(db)
    except Exception as e:
        logger.error(f"Error fetching customer service summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer service summary")


@router.get("/summary/services", response_model=List[s.SummaryServices])
def read_summary_services(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_services(db)
    except Exception as e:
        logger.error(f"Error fetching service summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service summary")


@router.get("/summary/connections", response_model=List[s.SummaryConnections])
def read_summary_connections(db: Session = Depends(get_db)):
    try:
        return operations.get_summary_connections(db)
    except Exception as e:
        logger.error(f"Error fetching connection summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch connection summary")

# ============================================================
#  MASTER DASHBOARD ENDPOINT
# ============================================================

@router.get("/networkLinks/dashboard/master/{network_name}", response_model=List[s.VNetworkDashboardOut])
def read_master_dashboard(
    network_name: str, 
    pop: Optional[str] = Query(None, description="Filter by specific POP (e.g., NYC6)"),
    link_type: Optional[str] = Query(None, description="Filter by link type (e.g., Inter-Pop)"),
    db: Session = Depends(get_db)
):
    safe_network_name = network_name.upper()
    
    dashboard_data = operations.get_master_network_dashboard(
        db=db, 
        network=safe_network_name, 
        pop=pop, 
        link_type=link_type
    )
    
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="No data found matching those filters")
        
    try:
        validated_data = [s.VNetworkDashboardOut.model_validate(row) for row in dashboard_data]
        return validated_data
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error on Master Dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
#  PHYSICAL ASSET TRACKING ENDPOINTS
# ============================================================

@router.get("/assets", response_model=List[s.InventoryAssetResponse])
def api_get_all_assets(db: Session = Depends(get_db)):
    """Fetch the complete hardware inventory catalog."""
    return operations.get_all_assets(db)

@router.get("/assets/{asset_id}", response_model=s.InventoryAssetResponse)
def api_get_asset(asset_id: UUID, db: Session = Depends(get_db)):
    """Fetch a specific asset by its exact UUID."""
    asset = operations.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset

@router.get("/assets/lumen/{lumen_id}", response_model=s.InventoryAssetResponse)
def api_get_asset_by_lumen_id(lumen_id: str, db: Session = Depends(get_db)):
    """Look up an asset using the corporate Lumen ID tag."""
    asset = operations.get_asset_by_lumen_id(db, lumen_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset

@router.post("/assets", response_model=s.InventoryAssetResponse, status_code=status.HTTP_201_CREATED)
def api_create_asset(asset_in: s.InventoryAssetCreate, db: Session = Depends(get_db)):
    """Onboard a new physical hardware asset into the digital twin."""
    try:
        return operations.create_asset(db, asset_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/assets/{asset_id}", response_model=s.InventoryAssetResponse)
def api_update_asset(asset_id: UUID, asset_in: s.InventoryAssetUpdate, db: Session = Depends(get_db)):
    """Modify the physical or financial attributes of an existing asset."""
    try:
        updated_asset = operations.update_asset(db, asset_id, asset_in)
        if not updated_asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        return updated_asset
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_asset(asset_id: UUID, db: Session = Depends(get_db)):
    """Purge an asset entirely from the system."""
    success = operations.delete_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return None