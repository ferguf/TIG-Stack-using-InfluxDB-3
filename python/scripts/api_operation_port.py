"""
api_operations_port.py
Domain-specific logic for Physical Ports and Patch Panels.
Handles port inventory, bulk provisioning logic, and physical cross-connect infrastructure.
"""

import logging
import uuid
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from scripts.api_model import Port, VDevicePorts, PatchPanel, Device, CrossConnect
from scripts.api_schema import PortIn, PatchPanelIn, CrossConnectIn, CrossConnectUpdate

logger = logging.getLogger(__name__)

# --- Physical Port Management ---

def get_ports(db: Session) -> List[Port]:
    """
    Fetches all raw ports from the base physical inventory table.
    """
    return db.query(Port).all()

def get_port_by_id(db: Session, port_id: str) -> Optional[VDevicePorts]:
    """
    Retrieve a single port with device enrichment via the VDevicePorts view.
    """
    return db.query(VDevicePorts).filter(VDevicePorts.port_id == port_id).first()

def get_ports_by_device_id(db: Session, device_id: str) -> List[Port]:
    """
    Fetch all physical ports belonging to a specific device UUID.
    """
    return (
        db.query(Port)
        .filter(Port.device_id == device_id)
        .all()
    )

def get_ports_by_device_name(db: Session, device_name: str):
    return (
        db.query(Port)
        .join(Device, Port.device_id == Device.device_id)
        .filter(Device.device_name == device_name)
        .all()
    )

def get_ports_by_customer_id(db: Session, customer_id: UUID) -> List[VDevicePorts]:
    """
    Fetch all port records from the v_device_ports view assigned to a specific customer.
    """
    return (
        db.query(VDevicePorts)
        .filter(VDevicePorts.customer_id == customer_id)
        .all()
    )

def get_port_by_device_and_port_name(db: Session, device_name: str, port_name: str) -> Optional[Port]:
    """
    Finds a specific port using the human-readable device name and port identifier.
    """
    return (
        db.query(Port)
        .join(Device, Port.device_id == Device.device_id)
        .filter(Device.device_name == device_name)
        .filter(Port.port_name == port_name)
        .first()
    )

# --- Bulk & Creation Logic ---

def create_ports_bulk_logic(db: Session, device_id: str, port_list: list[dict]) -> List[Port]:
    """
    Takes a list of dictionaries and creates multiple ports in the BASE TABLE.
    Used for rapid router template deployment.
    """
    created_ports = []
    try:
        for port_data in port_list:
            new_port = Port()
            new_port.port_id = str(uuid.uuid4())
            new_port.device_id = device_id

            for key, value in port_data.items():
                if hasattr(new_port, key):
                    setattr(new_port, key, value)
            
            db.add(new_port)
            created_ports.append(new_port)

        db.commit()
        for p in created_ports:
            db.refresh(p)
        return created_ports
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk port creation failed for device {device_id}: {e}")
        raise e

def create_port_for_device(db: Session, device_id: UUID, data: PortIn) -> Optional[Port]:
    """
    Creates a single port for a validated device.
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return None

    port_data = data.dict(exclude_unset=True)
    port_data["port_id"] = uuid.uuid4()
    port_data["device_id"] = device.device_id

    new_port = Port(**port_data)
    db.add(new_port)
    db.commit()
    db.refresh(new_port)
    return new_port

# --- Port Updates & Deletions ---

def update_port_by_id(db: Session, port_id: str, updates: dict) -> Optional[Port]:
    """
    Finds a port in the BASE TABLE and applies dynamic updates.
    """
    port = db.query(Port).filter(Port.port_id == port_id).first()
    if not port:
        return None

    for key, value in updates.items():
        if hasattr(port, key):
            setattr(port, key, value)

    try:
        db.commit()
        db.refresh(port)
        return port
    except Exception as e:
        db.rollback()
        raise e

def delete_port_by_device_and_port_id(db: Session, device_id: str, port_id: str) -> bool:
    """
    Delete a specific port record after verifying its parent device.
    """
    port = (
        db.query(Port)
        .filter(Port.device_id == device_id, Port.port_id == port_id)
        .first()
    )
    if not port:
        return False

    db.delete(port)
    db.commit()
    return True

# --- Patch Panel & Cross-Connects ---

def get_patch_panels_for_device(db: Session, device_id: UUID) -> List[PatchPanel]:
    """
    Returns all patch panel terminations associated with a specific router.
    """
    return db.query(PatchPanel).filter(PatchPanel.device_id == device_id).all()

def create_patch_panel(db: Session, panel_data: PatchPanelIn) -> PatchPanel:
    """
    Creates a new physical patch panel port entry.
    """
    data_dict = panel_data.model_dump()
    if not data_dict.get("port_id"):
        data_dict["port_id"] = uuid.uuid4()
        
    new_panel = PatchPanel(**data_dict)
    db.add(new_panel)
    db.commit()
    db.refresh(new_panel)
    return new_panel

def delete_patch_panel(db: Session, port_id: UUID) -> int:
    """
    Deletes a patch panel entry by its port UUID.
    """
    deleted = db.query(PatchPanel).filter(PatchPanel.port_id == port_id).delete()
    db.commit()
    return deleted

def get_cross_connects(db: Session) -> List[CrossConnect]:
    """
    Retrieves all physical cross-connect records.
    """
    return db.query(CrossConnect).all()

def post_cross_connect(db: Session, data: CrossConnectIn) -> CrossConnect:
    """
    Records a new physical cross-connect (e.g., fiber jumper between two panels).
    """
    new_connect = CrossConnect(**data.model_dump())
    db.add(new_connect)
    db.commit()
    db.refresh(new_connect)
    return new_connect