from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.database import get_db
from . import operations
from .schemas import (
    LocationIn, LocationOut, LocationUpdate, 
    NetworkLocationOut, DeviceLocationOut, DeviceLocationIn
)

router = APIRouter(prefix="/locations", tags=["Location Domain"])

# ---------------------------------------------------------
# CORE LOCATION CRUD
# ---------------------------------------------------------
@router.post("/", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationIn, db: Session = Depends(get_db)):
    return operations.create_location(db, payload)

@router.get("/", response_model=List[LocationOut])
def list_locations(db: Session = Depends(get_db)):
    return operations.get_all_locations(db)

@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: UUID, db: Session = Depends(get_db)):
    loc = operations.get_location_by_id(db, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

# ---------------------------------------------------------
# NETWORK-SCOPED LOOKUPS (Missing in your screenshot)
# ---------------------------------------------------------
@router.get("/by-network/{network_name}", response_model=List[NetworkLocationOut])
def get_locations_by_network(network_name: str, db: Session = Depends(get_db)):
    locations = operations.get_locations_by_network(db, network_name)
    if not locations:
        raise HTTPException(status_code=404, detail=f"No locations found for network: {network_name}")
    return locations

# ---------------------------------------------------------
# DEVICE-SPECIFIC LOOKUPS (Missing in your screenshot)
# ---------------------------------------------------------
@router.get("/device/{device_id}", response_model=DeviceLocationOut)
def get_device_location(device_id: UUID, db: Session = Depends(get_db)):
    loc = operations.get_device_location(db, device_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Device location not found")
    return loc

@router.post("/device", response_model=DeviceLocationOut, status_code=status.HTTP_201_CREATED)
def create_device_location(payload: DeviceLocationIn, db: Session = Depends(get_db)):
    return operations.create_device_location(db, payload)