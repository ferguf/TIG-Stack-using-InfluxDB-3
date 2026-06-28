"""
operations/device.py
Domain-specific logic for Router/Device inventory and Hardware specifications.
Handles physical asset management, rack locations, and hardware metadata.
"""

import logging
import uuid
from uuid import UUID
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from scripts.api_session import get_db_session
from scripts.api_model import Device, HardwareSpecs, HardwareDocument, DeviceLocation, LocationInfo
from scripts.api_schema import DeviceDetailsOut, DeviceIn, DeviceOut, HardwareSpecsIn, HardwareSpecsUpdate, HardwareDocumentIn, HardwareDocumentUpdate, LocationIn, LocationUpdate

logger = logging.getLogger(__name__)

# --- Device / Router Management ---

def get_devices() -> List[DeviceOut]:
    """
    Retrieves all devices from the inventory, mapped to Pydantic schemas.
    """
    try:
        with get_db_session() as db:
            devices = db.query(Device).all()
            return [DeviceOut.from_orm(d) for d in devices]
    except Exception as e:
        logger.error(f"Error retrieving devices: {e}")
        return []

def get_device_by_id(device_id: str) -> Optional[DeviceOut]:
    """
    Retrieves a single device by its name/ID string.
    """
    try:
        with get_db_session() as db:
            device = db.query(Device).filter(Device.device_name == device_id).first()
            return DeviceOut.from_orm(device) if device else None
    except Exception as e:
        logger.error(f"Error retrieving device {device_id}: {e}")
        return None

def get_devices_by_location(location_code: str) -> List[DeviceOut]:
    """
    Fetches devices filtered by uppercase location code (e.g., NYC1).
    """
    try:
        clean_code = str(location_code).strip().upper()
        with get_db_session() as db:
            devices = db.query(Device).filter(Device.location == clean_code).all()
            return [DeviceOut.from_orm(d) for d in devices]
    except Exception as e:
        logger.error(f"Error retrieving devices for location {location_code}: {e}")
        return []

def get_devices_by_network(network: str) -> List[DeviceDetailsOut]:
    """
    Retrieves devices filtered by network.
    """
    try:
        with get_db_session() as db:
            rows = db.execute(
                text("""
                    SELECT * 
                    FROM v_device_details
                    WHERE network = :network
                """),
                {"network": network}
            ).fetchall()

            return [DeviceDetailsOut(**dict(r._mapping)) for r in rows]

    except Exception as e:
        logger.error(f"Error retrieving devices by network: {e}")
        return []


def post_device(db: Session, data: DeviceIn) -> Device:
    """
    Creates a new device record with a fresh UUID.
    """
    payload = data.model_dump(exclude_unset=True)
    new_device = Device(
        device_id=uuid.uuid4(),
        **payload
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

def put_device(device_id: str, update_data: dict) -> Optional[DeviceOut]:
    """
    Updates an existing device via dictionary payload.
    """
    try:
        with get_db_session() as db:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return None
            for key, value in update_data.items():
                setattr(device, key, value)
            db.commit()
            db.refresh(device)
            return DeviceOut.from_orm(device)
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        return None

def delete_device_by_id(device_id: str) -> bool:
    """
    Removes a device from the database by UUID.
    """
    try:
        with get_db_session() as db:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return False
            db.delete(device)
            db.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        return False

# --- Hardware Specifications & Documentation ---

def get_hardware_specs(db: Session) -> List[HardwareSpecs]:
    """Retrieves all hardware models and specs."""
    return db.query(HardwareSpecs).all()

def get_hardware_spec_by_id(db: Session, hardware_id: UUID) -> Optional[HardwareSpecs]:
    """Retrieves specific hardware metadata by ID."""
    return db.query(HardwareSpecs).filter(HardwareSpecs.hardware_id == hardware_id).first()

def post_hardware_spec(db: Session, data: HardwareSpecsIn) -> HardwareSpecs:
    """Creates a new hardware specification entry."""
    new_spec = HardwareSpecs(**data.model_dump())
    db.add(new_spec)
    db.commit()
    db.refresh(new_spec)
    return new_spec

def get_hardware_documents(db: Session) -> List[HardwareDocument]:
    """Retrieves all associated hardware documentation."""
    return db.query(HardwareDocument).all()

def post_hardware_document(db: Session, data: HardwareDocumentIn) -> HardwareDocument:
    """Associates a new document with hardware."""
    new_doc = HardwareDocument(**data.model_dump())
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc

# --- Location & Rack Management ---

def get_location_by_id(db: Session, location_id: UUID) -> Optional[LocationInfo]:
    """Fetches high-level site info (NYC1, SFO1)."""
    return db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()

def post_location(db: Session, data: LocationIn) -> LocationInfo:
    """Creates a new physical site location."""
    new_location = LocationInfo(**data.model_dump())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location

def get_device_location_by_id(db: Session, device_id: UUID) -> Optional[DeviceLocation]:
    """Retrieves specific rack/aisle data for a device."""
    return db.query(DeviceLocation).filter(DeviceLocation.device_id == device_id).first()

def create_device_location(db: Session, data: DeviceLocation) -> DeviceLocation:
    """Pins a device to a specific rack position."""
    db.add(data)
    db.commit()
    db.refresh(data)
    return data