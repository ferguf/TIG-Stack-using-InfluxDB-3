"""
Business logic / operations layer for the Devices domain.
Refactored to focus strictly on Device inventory operations.
File: app/python/domains/devices/operations.py
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

# Local proxy import restricted to core Device model
from .models import Device

logger = logging.getLogger(__name__)

# =========================================================
# DEVICE INVENTORY OPERATIONS
# =========================================================

def get_devices(db: Session) -> List[Device]:
    """Retrieves all device inventory records."""
    return db.query(Device).all()

def get_device_by_name(db: Session, device_name: str) -> Optional[Device]:
    """Retrieves a device by its unique name."""
    return db.query(Device).filter(Device.device_name == device_name).first()

def get_device_by_id(db: Session, device_id: str) -> Optional[Device]:
    """Retrieves a device by its unique ID."""
    return db.query(Device).filter(Device.device_id == device_id).first()

def get_devices_by_location(db: Session, location_code: str) -> List[Device]:
    """Retrieves devices filtered by a physical location code."""
    clean_code = str(location_code).strip().upper()
    return db.query(Device).filter(Device.location == clean_code).all()

def get_devices_by_network(db: Session, network: str) -> List[dict]:
    """Retrieves devices from the aggregated v_device_details view."""
    network = network.strip().upper()
    rows = db.execute(
        text("SELECT * FROM v_device_details WHERE network = :network"),
        {"network": network}
    ).fetchall()
    return [dict(r._mapping) for r in rows]

def post_device(db: Session, payload: dict) -> Device:
    """Creates a new device inventory record."""
    new_device = Device(**payload)
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

def put_device(db: Session, device_id: str, update_data: dict) -> Optional[Device]:
    """Updates an existing device inventory record."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return None
    for key, value in update_data.items():
        setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device

def delete_device_by_id(db: Session, device_id: str) -> bool:
    """Deletes a device inventory record by ID."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return False
    db.delete(device)
    db.commit()
    return True