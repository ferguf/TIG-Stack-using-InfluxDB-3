import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys, os

from scripts.api_schema import (
    LocationIn, LocationOut, LocationUpdate,
    NetworkLocationOut,
    PortOut, PortUpdate, PortIn,
    DeviceLocationIn, DeviceLocationOut
)

logger = logging.getLogger(__name__)

# Ensure scripts directory is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "..", "..", "scripts")
sys.path.append(SCRIPTS_DIR)

from uuid import UUID
from scripts.api_session import get_db
from scripts.api_model import LocationInfo, DeviceLocation, NetworkSummary
import scripts.api_operation as api_operation


router = APIRouter(prefix="/locations", tags=["locations"])

# ---------------------------------------------------------
# CREATE
# ---------------------------------------------------------
@router.post("/", response_model=LocationOut)
def create_location(location: LocationIn, db: Session = Depends(get_db)):
    new_location = LocationInfo(**location.model_dump())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location

# ---------------------------------------------------------
# READ (all)
# ---------------------------------------------------------
@router.get("/", response_model=List[LocationOut])
def list_locations(db: Session = Depends(get_db)):
    return db.query(LocationInfo).all()

# ---------------------------------------------------------
# READ: Locations by Network  (STATIC ROUTE - MUST COME FIRST)
# ---------------------------------------------------------
@router.get("/by-network/{network_name}", response_model=List[NetworkLocationOut])
def get_locations_by_network(network_name: str, db: Session = Depends(get_db)):
    rows = (
        db.query(NetworkSummary)
        .filter(NetworkSummary.network == network_name)
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No locations found for this network")

    return rows

# ---------------------------------------------------------
# READ: By CLLI
# ---------------------------------------------------------
@router.get("/clli/{location_code}", response_model=LocationOut)
def get_location_by_clli(location_code: str, db: Session = Depends(get_db)):
    loc = (
        db.query(LocationInfo)
        .filter(LocationInfo.location_code == location_code)
        .first()
    )
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

# ---------------------------------------------------------
# READ: By Short Name
# ---------------------------------------------------------
@router.get("/shortName/{short_name}", response_model=LocationOut)
def get_location_by_shortname(short_name: str, db: Session = Depends(get_db)):
    loc = (
        db.query(LocationInfo)
        .filter(LocationInfo.short_name == short_name)
        .first()
    )
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

# ---------------------------------------------------------
# READ (single) — MUST BE UUID CONSTRAINED
# ---------------------------------------------------------
@router.get("/{location_id:uuid}", response_model=LocationOut)
def get_location(location_id: UUID, db: Session = Depends(get_db)):
    loc = db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

# ---------------------------------------------------------
# UPDATE
# ---------------------------------------------------------
@router.put("/{location_id:uuid}", response_model=LocationOut)
def update_location(location_id: UUID, update: LocationUpdate, db: Session = Depends(get_db)):
    loc = db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(loc, field, value)

    db.commit()
    db.refresh(loc)
    return loc

# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------
@router.delete("/{location_id:uuid}")
def delete_location(location_id: UUID, db: Session = Depends(get_db)):
    loc = db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    db.delete(loc)
    db.commit()
    return {"detail": "Location deleted"}

# ---------------------------------------------------------
# DEVICE LOCATION CRUD
# ---------------------------------------------------------
@router.get("/device/{device_id:uuid}", response_model=DeviceLocationOut)
def get_device_location(device_id: UUID, db: Session = Depends(get_db)):
    loc = (
        db.query(DeviceLocation)
        .filter(DeviceLocation.device_id == device_id)
        .first()
    )
    if not loc:
        raise HTTPException(status_code=404, detail="Device location not found")
    return loc

@router.post("/device", response_model=DeviceLocationOut)
def create_device_location(device_loc: DeviceLocationIn, db: Session = Depends(get_db)):
    new_device_loc = DeviceLocation(**device_loc.model_dump())
    db.add(new_device_loc)
    db.commit()
    db.refresh(new_device_loc)
    return new_device_loc

@router.put("/device/{device_id:uuid}", response_model=DeviceLocationOut)
def update_device_location(device_id: UUID, device_loc: DeviceLocationIn, db: Session = Depends(get_db)):
    loc = (
        db.query(DeviceLocation)
        .filter(DeviceLocation.device_id == device_id)
        .first()
    )
    if not loc:
        raise HTTPException(status_code=404, detail="Device location not found")

    for field, value in device_loc.model_dump().items():
        setattr(loc, field, value)

    db.commit()
    db.refresh(loc)
    return loc

@router.delete("/device/{device_id:uuid}")
def delete_device_location(device_id: UUID, db: Session = Depends(get_db)):
    loc = (
        db.query(DeviceLocation)
        .filter(DeviceLocation.device_id == device_id)
        .first()
    )
    if not loc:
        raise HTTPException(status_code=404, detail="Device location not found")

    db.delete(loc)
    db.commit()
    return {"detail": "Device location deleted successfully"}
