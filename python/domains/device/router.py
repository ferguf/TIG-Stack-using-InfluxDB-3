import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List 
from sqlalchemy.orm import Session

# Centralized core DB
from core.database import get_db
from domains.location.models import LocationInfo
# Native relative imports from the domain slice
from . import operations
from .schemas import (
    DeviceDetailsOut, DeviceIn, DeviceOut, DeviceUpdate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])

# =========================================================
# DEVICES
# =========================================================

@router.get("/", response_model=List[DeviceOut])
def get_devices(db: Session = Depends(get_db)):
    try:
        devices = operations.get_devices(db)
        if not devices:
            raise HTTPException(status_code=404, detail="No devices found")
        return [DeviceOut.model_validate(d) for d in devices]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error retrieving devices")

@router.get("/name/{device_name}", response_model=DeviceOut)
def get_device_by_name(device_name: str, db: Session = Depends(get_db)):
    device = operations.get_device_by_name(db, device_name)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut.model_validate(device)

@router.get("/{device_id}", response_model=DeviceOut)
def get_device_by_id(device_id: str, db: Session = Depends(get_db)):
    device = operations.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut.model_validate(device)

@router.get("/location/{location_code}", response_model=List[DeviceOut])
def get_devices_by_location(location_code: str, db: Session = Depends(get_db)):
    try:
        devices = operations.get_devices_by_location(db, location_code)
        if not devices:
            raise HTTPException(status_code=404, detail=f"No devices found for location: {location_code}")
        return [DeviceOut.model_validate(d) for d in devices]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/network/{network}", response_model=List[DeviceDetailsOut])
def get_devices_by_network(network: str, db: Session = Depends(get_db)):
    try:
        devices = operations.get_devices_by_network(db, network)
        if not devices:
            raise HTTPException(status_code=404, detail=f"No devices found for network: {network}")
        return devices
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=DeviceOut, summary="Create a new device")
def post_device(data: DeviceIn, db: Session = Depends(get_db)):
    new_device = operations.post_device(db, data.model_dump(exclude_unset=True))
    return DeviceOut.model_validate(new_device)

@router.put("/{device_id}", response_model=DeviceOut)
def update_device(device_id: str, update: DeviceUpdate, db: Session = Depends(get_db)):
    try:
        updated_device = operations.put_device(db, device_id, update.model_dump(exclude_unset=True))
        if not updated_device:
            raise HTTPException(status_code=404, detail="Device not found or update failed")
        return DeviceOut.model_validate(updated_device)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}", response_model=dict)
def delete_device(device_id: str, db: Session = Depends(get_db)):
    try:
        success = operations.delete_device_by_id(db, device_id)
        if not success:
            raise HTTPException(status_code=404, detail="Device deletion failed")
        return {"message": f"Device {device_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))