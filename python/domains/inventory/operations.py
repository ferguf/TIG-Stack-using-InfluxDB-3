"""
Business logic / operations layer for the Inventory domain.
File: domains/inventory/operations.py

Handles querying the pre-aggregated summary views for dashboards,
as well as standard CRUD operations for physical asset tracking.
"""

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError

# Local domain imports
from . import models as m
from . import schemas as s

logger = logging.getLogger(__name__)

# ============================================================
# MASTER SUMMARY OPERATIONS
# ============================================================

def get_network_summary_grouped(db: Session) -> s.SummaryGroupedResponse:
    rows = db.query(m.NetworkSummaryMaster).order_by(
        m.NetworkSummaryMaster.category,
        m.NetworkSummaryMaster.unique_id
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
                s.SummaryRow(
                    id=row.unique_id,
                    category=row.category,
                    dimension=row.dimension,
                    count_value=row.count_value
                )
            )

    return s.SummaryGroupedResponse(**grouped)


def get_network_summary_grouped_v2(db: Session) -> s.SummaryGroupedResponseV2:
    rows = db.query(m.NetworkSummaryMasterV2).order_by(
        m.NetworkSummaryMasterV2.category,
        m.NetworkSummaryMasterV2.unique_id
    ).all()

    grouped = {
        "devices": [],
        "device_health": [],
    }

    for row in rows:
        if row.category in grouped:
            grouped[row.category].append(
                s.SummaryRowV2(
                    id=row.unique_id,
                    category=row.category,
                    dimension=row.dimension,
                    count_value=row.count_value
                )
            )

    return s.SummaryGroupedResponseV2(**grouped)


# ============================================================
# GRANULAR SUMMARY OPERATIONS
# ============================================================

def get_summary_devices(db: Session) -> List[m.VSummaryDevices]:
    return db.query(m.VSummaryDevices).all()

def get_summary_ports(db: Session) -> List[m.VSummaryPorts]:
    return db.query(m.VSummaryPorts).all()

def get_summary_port_health(db: Session) -> List[m.VSummaryPortHealth]:
    return db.query(m.VSummaryPortHealth).all()

def get_summary_links(db: Session) -> List[m.VSummaryLinks]:
    return db.query(m.VSummaryLinks).all()

def get_summary_links_by_location(db: Session) -> List[m.VSummaryLinksByLocation]:
    return db.query(m.VSummaryLinksByLocation).all()

def get_summary_customers(db: Session) -> List[m.VSummaryCustomers]:
    return db.query(m.VSummaryCustomers).all()

def get_summary_customer_services(db: Session) -> List[m.VSummaryCustomerServices]:
    return db.query(m.VSummaryCustomerServices).all()

def get_summary_services(db: Session) -> List[m.VSummaryServices]:
    return db.query(m.VSummaryServices).all()

def get_summary_connections(db: Session) -> List[m.VSummaryConnections]:
    return db.query(m.VSummaryConnections).all()


# ============================================================
# MASTER DASHBOARD OPERATIONS
# ============================================================

def get_master_network_dashboard(
    db: Session, 
    network: str, 
    pop: Optional[str] = None, 
    link_type: Optional[str] = None
) -> List[dict]:
    """
    Retrieves the master network dashboard metrics directly from the v_network_dashboard view.
    Replaces the legacy `scripts.api_operation_network` function.
    """
    query = "SELECT * FROM v_network_dashboard WHERE network = :network"
    params = {"network": network}

    if pop:
        query += " AND pop_location = :pop"
        params["pop"] = pop
    
    sql = text(query)
    rows = db.execute(sql, params).fetchall()
    
    return [dict(r._mapping) for r in rows]


# ============================================================
# PHYSICAL ASSET TRACKING OPERATIONS (CRUD)
# ============================================================

def get_asset(db: Session, asset_id: UUID) -> Optional[m.InventoryAsset]:
    """Retrieve a single asset by its primary key."""
    return db.get(m.InventoryAsset, asset_id)

def get_asset_by_lumen_id(db: Session, lumen_id: str) -> Optional[m.InventoryAsset]:
    """Retrieve an asset by its internal corporate tracking tag."""
    query = select(m.InventoryAsset).where(m.InventoryAsset.lumen_id == lumen_id)
    result = db.execute(query)
    return result.scalar_one_or_none()

def get_all_assets(db: Session) -> List[m.InventoryAsset]:
    """Retrieve the entire inventory catalog."""
    query = select(m.InventoryAsset).order_by(m.InventoryAsset.vendor, m.InventoryAsset.vendor_id)
    result = db.execute(query)
    return result.scalars().all()

def create_asset(db: Session, obj_in: s.InventoryAssetCreate) -> m.InventoryAsset:
    """Create a new physical asset record."""
    db_obj = m.InventoryAsset(
        vendor=obj_in.vendor,
        vendor_id=obj_in.vendor_id,
        lumen_id=obj_in.lumen_id,
        description=obj_in.description,
        list_price=obj_in.list_price,
        discount=obj_in.discount,
        lumen_price=obj_in.lumen_price
    )
    db.add(db_obj)
    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError(f"An asset with Lumen ID '{obj_in.lumen_id}' already exists.")

def update_asset(db: Session, asset_id: UUID, obj_in: s.InventoryAssetUpdate) -> Optional[m.InventoryAsset]:
    """Update specific fields of an existing asset."""
    db_obj = db.get(m.InventoryAsset, asset_id)
    if not db_obj:
        return None
        
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError("The requested Lumen ID update conflicts with an existing asset.")

def delete_asset(db: Session, asset_id: UUID) -> bool:
    """Remove an asset from the inventory."""
    db_obj = db.get(m.InventoryAsset, asset_id)
    if not db_obj:
        return False
        
    db.delete(db_obj)
    db.commit()
    return True