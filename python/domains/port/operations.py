"""
Business logic / operations layer for the Ports domain.
File: domains/ports/operations.py

Handles port inventory, bulk provisioning logic, and device-port associations.
"""

import logging
import uuid
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session

# Phase 1: Local proxy imports
from .models import Port, VDevicePorts
from .schemas import PortIn

# Phase 1: Proxy import for the Device model to support cross-domain JOINs
from scripts.api_model import Device 

logger = logging.getLogger(__name__)

# =========================================================
# READ OPERATIONS
# =========================================================

def get_ports(db: Session) -> List[Port]:
    """
    Fetches all raw ports from the base physical inventory table.
    """
    return db.query(Port).all()


def get_port_by_id(db: Session, port_id: UUID) -> Optional[VDevicePorts]:
    """
    Retrieve a single port with device enrichment via the VDevicePorts view.
    """
    return db.query(VDevicePorts).filter(VDevicePorts.port_id == port_id).first()


def get_ports_by_device_id(db: Session, device_id: UUID) -> List[Port]:
    """
    Fetch all physical ports belonging to a specific device UUID.
    """
    return db.query(Port).filter(Port.device_id == device_id).all()


def get_ports_by_device_name(db: Session, device_name: str) -> List[Port]:
    """
    Fetch all physical ports by executing a JOIN on the Device's human-readable name.
    """
    return (
        db.query(Port)
        .join(Device, Port.device_id == Device.device_id)
        .filter(Device.device_name == device_name)
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


def get_ports_by_customer_id(db: Session, customer_id: UUID) -> List[VDevicePorts]:
    """
    Fetch all port records from the v_device_ports view assigned to a specific customer.
    """
    return db.query(VDevicePorts).filter(VDevicePorts.customer_id == customer_id).all()


# =========================================================
# WRITE / PROVISIONING OPERATIONS
# =========================================================

def create_port_for_device(db: Session, device_id: UUID, data: PortIn) -> Optional[Port]:
    """
    Creates a single port for a validated device.
    """
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return None

        # Exclude unset values to let DB defaults apply where necessary
        port_data = data.model_dump(exclude_unset=True)
        port_data["port_id"] = uuid.uuid4()
        port_data["device_id"] = device.device_id

        new_port = Port(**port_data)
        db.add(new_port)
        db.commit()
        db.refresh(new_port)
        return new_port
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating port for device {device_id}: {e}")
        raise e


def create_ports_bulk_logic(db: Session, device_id: UUID, port_list: list[dict]) -> List[Port]:
    """
    Takes a list of dictionaries and creates multiple ports in the BASE TABLE.
    Used for rapid router template deployment in Streamlit.
    """
    created_ports = []
    try:
        for port_data in port_list:
            new_port = Port()
            new_port.port_id = uuid.uuid4()
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


# =========================================================
# UPDATE OPERATIONS
# =========================================================

def update_port_by_id(db: Session, port_id: UUID, updates: dict) -> Optional[Port]:
    """
    Finds a port in the BASE TABLE and applies dynamic updates.
    """
    port = db.query(Port).filter(Port.port_id == port_id).first()
    if not port:
        return None

    try:
        for key, value in updates.items():
            if hasattr(port, key):
                setattr(port, key, value)

        db.commit()
        db.refresh(port)
        return port
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating port {port_id}: {e}")
        raise e


def update_port_by_device_and_name(db: Session, device_id: UUID, port_name: str, updates: dict) -> Optional[Port]:
    """
    Updates all values of a specific port located by its device ID and exact port name.
    """
    port = db.query(Port).filter(Port.device_id == device_id, Port.port_name == port_name).first()
    if not port:
        return None

    try:
        for key, value in updates.items():
            if hasattr(port, key):
                setattr(port, key, value)

        db.commit()
        db.refresh(port)
        return port
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating port {port_name} on device {device_id}: {e}")
        raise e


# =========================================================
# DELETE OPERATIONS
# =========================================================

def delete_port_by_device_and_port_id(db: Session, device_id: UUID, port_id: UUID) -> bool:
    """
    Delete a specific port record after verifying its parent device matches.
    """
    try:
        port = db.query(Port).filter(Port.device_id == device_id, Port.port_id == port_id).first()
        if not port:
            return False

        db.delete(port)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting port {port_id}: {e}")
        raise e