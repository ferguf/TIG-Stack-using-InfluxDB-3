import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional 
from scripts.api_schema import PortOut,PortUpdate,PortIn,DevicePortOut
import sys, os
logger = logging.getLogger(__name__)


# Ensure scripts directory is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "..", "..", "scripts")
sys.path.append(SCRIPTS_DIR)

import uuid as uuid
from uuid import UUID
from scripts.api_session import get_db
from scripts.api_model import Port
import scripts.api_operation as api_operation

router = APIRouter(prefix="/ports", tags=["ports"])

# -----------------------------

# -----------------------------

@router.get(
    "/",
    response_model=List[PortOut],
    summary="Get all ports"
)
def get_ports(db: Session = Depends(get_db)):
    """
    Retrieve all ports in the system.
    - returns: Array of port objects
    """
    ports = api_operation.get_ports(db)
    return [PortOut.model_validate(p) for p in ports]

@router.post(
    "/{device_id}",
    response_model=PortOut,
    summary="Create a new port for a device"
)
def create_port(
    device_id: UUID,
    new_port: PortIn,   # Pydantic schema with all fields of Port
    db: Session = Depends(get_db)
):
    """
    Create a new port attached to a given device.
    - **device_name**: Path parameter for the device
    - **new_port**: Body payload with values for the new port
    - **returns**: Newly created port object
    """
    port = api_operation.create_port_for_device(db, device_id, new_port)
    if not port:
        raise HTTPException(status_code=404, detail="Device not found")

    return PortOut.model_validate(port)

@router.post("/bulk/{device_id}", response_model=list[PortOut])
def bulk_create_ports(
    device_id: str,
    payload: list[dict], # Streamlit sends a list of dictionaries
    db: Session = Depends(get_db)
):
    """
    Router to handle the ingestion of the 12 port rows.
    """
    ports = api_operation.create_ports_bulk_logic(db, device_id, payload)
    if not ports:
        raise HTTPException(status_code=400, detail="Bulk ingestion failed")
    
    return ports


@router.get("/port/{port_id}", response_model=List[DevicePortOut])
def get_port_by_port_id(port_id: UUID, db: Session = Depends(get_db)):
    """
    Return a port associated with a given port_id.
    """
    # This returns a single VDevicePorts object, not a list
    port = api_operation.get_port_by_id(db, str(port_id))
    
    if not port:
        # Return empty list if no port found to satisfy the List response model
        return []

    # Wrap the single object in a list so the list comprehension (or validation) works
    return [DevicePortOut.model_validate(port)]

@router.get("/device/{device_id}", response_model=List[PortOut], summary="Get ports for a specific device")
def get_ports_for_device(device_id: str, db: Session = Depends(get_db)):
    ports = api_operation.get_ports_by_device_id(db, device_id)
    return [PortOut.model_validate(p) for p in ports]

@router.get("/name/{device_name}", response_model=List[PortOut], summary="Get ports for a specific device")
def get_ports_for_device_by_name(device_name: str, db: Session = Depends(get_db)):
    ports = api_operation.get_ports_by_device_name(db, device_name)
    return [PortOut.model_validate(p) for p in ports]

@router.get(
    "/device/{device_name}/port/{port_name:path}",
    response_model=PortOut,
    summary="Get a specific port on a device by device name and port name"
)
def get_port_by_device_and_port_name(
    device_name: str,
    port_name: str,
    db: Session = Depends(get_db)
):
    port = api_operation.get_port_by_device_and_port_name(db, device_name, port_name)

    if port is None:
        raise HTTPException(
            status_code=404,
            detail=f"Port '{port_name}' not found on device '{device_name}'"
        )

    return PortOut.model_validate(port)


@router.get("/customer/{customer_id}", response_model=List[DevicePortOut])
def get_ports_by_customer_id_api(customer_id: UUID, db: Session = Depends(get_db)):
    """
    Return all ports associated with a given customer_id.
    """
    ports = api_operation.get_ports_by_customer_id(db, customer_id)
    # Convert ORM rows to Pydantic models explicitly, as in your style
    return [DevicePortOut.model_validate(p) for p in ports]


@router.put("/id/{port_id}", response_model=PortOut)
def update_port_by_id(
    port_id: UUID,
    port_update: PortUpdate,
    db: Session = Depends(get_db)
):
    # Convert Pydantic model to dict, excluding fields the user didn't send
    update_data = port_update.model_dump(exclude_unset=True)
    
    # Pass everything to the operation function
    port = api_operation.update_port_by_id(db, str(port_id), update_data)
    
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")

    return port # PortOut will handle the validation automatically


@router.put(
    "/{device_id}/{port_id}",
    response_model=PortOut,
    summary="Update a port by device and port name"
)
def update_port(
    device_id: UUID,
    port_name: str,
    updates: PortUpdate,   # Pydantic schema with all fields of Port
    db: Session = Depends(get_db)
):
    """
    Update all values of a port by device name and port name.
    - **device_name**: Path parameter for the device
    - **port_name**: Path parameter for the port
    - **updates**: Body payload with new values for the port
    - **returns**: Updated port object
    """
    port = api_operation.update_port_by_device_and_name(
        db, device_id, port_name, updates.dict(exclude_unset=True)
    )
    if not port:
        raise HTTPException(status_code=404, detail="Device or port not found")

    return PortOut.model_validate(port)


@router.delete(
    "/{device_id}/{port_id:path}",
    summary="Delete a port by device and port name"
)
def delete_port(
    device_id: str,
    port_id: str,
    db: Session = Depends(get_db)):
    """
    Delete a port by device name and port name.
    - **device_name**: Path parameter for the device
    - **port_name**: Path parameter for the port
    - **returns**: Success message if deleted
    """
    deleted = api_operation.delete_port_by_device_and_port_id(db, device_id, port_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Device or port not found")

    return {"detail": f"Port '{port_id}' on device '{device_id}' deleted successfully"}

# -----------------------------