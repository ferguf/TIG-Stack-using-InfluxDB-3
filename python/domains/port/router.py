import logging
from uuid import UUID
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Centralized core DB
from core.database import get_db

# Native relative imports from the domain slice
from . import operations
from .schemas import PortIn, PortOut, PortUpdate, DevicePortOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ports", tags=["Ports Domain"])

# =========================================================
# GET / READ ROUTES
# =========================================================

@router.get("/", response_model=List[PortOut], summary="Get all physical ports")
def get_ports(db: Session = Depends(get_db)):
    """Retrieve all ports in the system."""
    ports = operations.get_ports(db)
    return [PortOut.model_validate(p) for p in ports]


@router.get("/port/{port_id}", response_model=List[DevicePortOut])
def get_port_by_port_id(port_id: UUID, db: Session = Depends(get_db)):
    """
    Return a port associated with a given port_id.
    Wrapped in a list to satisfy legacy frontend UI requirements.
    """
    port = operations.get_port_by_id(db, port_id)
    if not port:
        return []
    return [DevicePortOut.model_validate(port)]


@router.get("/device/{device_id}", response_model=List[PortOut], summary="Get ports for a specific device UUID")
def get_ports_for_device(device_id: UUID, db: Session = Depends(get_db)):
    ports = operations.get_ports_by_device_id(db, device_id)
    return [PortOut.model_validate(p) for p in ports]


@router.get("/name/{device_name}", response_model=List[PortOut], summary="Get ports for a specific device name")
def get_ports_for_device_by_name(device_name: str, db: Session = Depends(get_db)):
    ports = operations.get_ports_by_device_name(db, device_name)
    return [PortOut.model_validate(p) for p in ports]


@router.get(
    "/device/{device_name}/port/{port_name:path}",
    response_model=PortOut,
    summary="Get a specific port by device name and exact port name"
)
def get_port_by_device_and_port_name(device_name: str, port_name: str, db: Session = Depends(get_db)):
    port = operations.get_port_by_device_and_port_name(db, device_name, port_name)
    if port is None:
        raise HTTPException(
            status_code=404,
            detail=f"Port '{port_name}' not found on device '{device_name}'"
        )
    return PortOut.model_validate(port)


@router.get("/customer/{customer_id}", response_model=List[DevicePortOut])
def get_ports_by_customer_id_api(customer_id: UUID, db: Session = Depends(get_db)):
    """Return all enriched ports (v_device_ports) associated with a given customer_id."""
    ports = operations.get_ports_by_customer_id(db, customer_id)
    return [DevicePortOut.model_validate(p) for p in ports]


# =========================================================
# POST / CREATE ROUTES
# =========================================================

@router.post("/{device_id}", response_model=PortOut, summary="Create a new port for a device")
def create_port(device_id: UUID, new_port: PortIn, db: Session = Depends(get_db)):
    """Create a new port attached to a given device UUID."""
    port = operations.create_port_for_device(db, device_id, new_port)
    if not port:
        raise HTTPException(status_code=404, detail="Parent Device not found")
    return PortOut.model_validate(port)


@router.post("/bulk/{device_id}", response_model=List[PortOut])
def bulk_create_ports(device_id: UUID, payload: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """
    Handle the rapid ingestion of multiple port rows.
    Heavily utilized by the Streamlit template provisioning wizard.
    """
    try:
        ports = operations.create_ports_bulk_logic(db, device_id, payload)
        if not ports:
            raise HTTPException(status_code=400, detail="Bulk ingestion failed to return data")
        return [PortOut.model_validate(p) for p in ports]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# PUT / UPDATE ROUTES
# =========================================================

@router.put("/id/{port_id}", response_model=PortOut)
def update_port_by_id(port_id: UUID, port_update: PortUpdate, db: Session = Depends(get_db)):
    """Update a port using its unique UUID."""
    update_data = port_update.model_dump(exclude_unset=True)
    port = operations.update_port_by_id(db, port_id, update_data)
    
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")
    return PortOut.model_validate(port)


@router.put(
    "/{device_id}/name/{port_name:path}",
    response_model=PortOut,
    summary="Update a port by device UUID and exact port name"
)
def update_port_by_name(device_id: UUID, port_name: str, updates: PortUpdate, db: Session = Depends(get_db)):
    """Update a specific port located by its device ID and exact port name."""
    port = operations.update_port_by_device_and_name(
        db, device_id, port_name, updates.model_dump(exclude_unset=True)
    )
    if not port:
        raise HTTPException(status_code=404, detail="Device or port not found")
    return PortOut.model_validate(port)


# =========================================================
# DELETE ROUTES
# =========================================================

@router.delete("/{device_id}/{port_id:path}", summary="Delete a port by device and port ID")
def delete_port(device_id: UUID, port_id: UUID, db: Session = Depends(get_db)):
    """Delete a port, strictly verifying its parent device UUID."""
    deleted = operations.delete_port_by_device_and_port_id(db, device_id, port_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Device or port not found")
    return {"detail": f"Port '{port_id}' on device '{device_id}' deleted successfully"}