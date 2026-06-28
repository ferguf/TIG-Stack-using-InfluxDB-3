
"""
Business logic / operations layer for the Location domain.
File: app/python/domains/location/operations.py
"""

from sqlalchemy.orm import Session
from uuid import UUID

# ---------------------------------------------------------
# PHASE 1 MIGRATION PROXY
# Safely importing from existing legacy files during migration
# to prevent SQLAlchemy duplicate table definition errors.
# ---------------------------------------------------------
from scripts.api_model import LocationInfo, DeviceLocation, NetworkSummary


# =========================================================
# CORE LOCATION CRUD OPERATIONS
# =========================================================

def get_all_locations(db: Session) -> list[LocationInfo]:
    """
    Retrieves all physical location records from the database.
    """
    return db.query(LocationInfo).all()


def get_locations_by_network(db: Session, network_name: str) -> list[NetworkSummary]:
    """
    Retrieves a summary of locations associated with a specific network.
    """
    return db.query(NetworkSummary).filter(NetworkSummary.network == network_name).all()


def get_location_by_clli(db: Session, location_code: str) -> LocationInfo:
    """
    Retrieves a single location by its physical CLLI code.
    """
    return db.query(LocationInfo).filter(LocationInfo.location_code == location_code).first()


def get_location_by_shortname(db: Session, short_name: str) -> LocationInfo:
    """
    Retrieves a single location by its short name identifier.
    """
    return db.query(LocationInfo).filter(LocationInfo.short_name == short_name).first()


def get_location_by_id(db: Session, location_id: UUID) -> LocationInfo:
    """
    Retrieves a single location by its UUID.
    """
    return db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()


def create_location_record(db: Session, location_data: dict) -> LocationInfo:
    """
    Creates a new physical location record.
    """
    new_location = LocationInfo(**location_data)
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location


def update_location_record(db: Session, location_id: UUID, update_data: dict) -> LocationInfo:
    """
    Updates an existing physical location record.
    """
    loc = db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()
    if loc:
        for field, value in update_data.items():
            setattr(loc, field, value)
        db.commit()
        db.refresh(loc)
    return loc


def delete_location_record(db: Session, location_id: UUID) -> bool:
    """
    Deletes a physical location record. Returns True if successful.
    """
    loc = db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()
    if loc:
        db.delete(loc)
        db.commit()
        return True
    return False


# =========================================================
# DEVICE LOCATION CRUD OPERATIONS
# =========================================================

def get_device_location_by_id(db: Session, device_id: UUID) -> DeviceLocation:
    """
    Retrieves the location mapping for a specific device UUID.
    """
    return db.query(DeviceLocation).filter(DeviceLocation.device_id == device_id).first()


def create_device_location_record(db: Session, location_data: dict) -> DeviceLocation:
    """
    Creates a new mapping linking a device to a physical location.
    """
    new_device_loc = DeviceLocation(**location_data)
    db.add(new_device_loc)
    db.commit()
    db.refresh(new_device_loc)
    return new_device_loc


def update_device_location_record(db: Session, device_id: UUID, update_data: dict) -> DeviceLocation:
    """
    Updates an existing mapping linking a device to a physical location.
    """
    loc = db.query(DeviceLocation).filter(DeviceLocation.device_id == device_id).first()
    if loc:
        for field, value in update_data.items():
            setattr(loc, field, value)
        db.commit()
        db.refresh(loc)
    return loc


def delete_device_location_record(db: Session, device_id: UUID) -> bool:
    """
    Deletes a device-to-location mapping. Returns True if successful.
    """
    loc = db.query(DeviceLocation).filter(DeviceLocation.device_id == device_id).first()
    if loc:
        db.delete(loc)
        db.commit()
        return True
    return False