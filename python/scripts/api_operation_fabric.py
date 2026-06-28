"""
operations/fabric.py
Domain-specific logic for Fabric Services and logical Fabric Connections.
Handles customer service provisioning, bandwidth allocation, and VRF logical links.
"""

import logging
import uuid
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from scripts.api_model import FabricService, FabricConnection, FabricServiceDetail
from scripts.api_schema import FabricServiceIn, FabricServiceUpdate, FabricConnectionIn, FabricConnectionUpdate

logger = logging.getLogger(__name__)

# --- Fabric Service Management ---

def get_fabric_service_detail(db: Session, service_id: UUID):
    return (
        db.query(FabricServiceDetail)
        .filter(FabricServiceDetail.service_id == service_id)
        .first()
    )

def get_fabric_services(db: Session) -> List[FabricService]:
    """
    Retrieves all defined network services (e.g., L3VPN, E-Line).
    """
    return db.query(FabricService).all()

def get_fabric_services_by_service(db: Session, service_id: str) -> List[FabricService]:
    """
    Retrieve specific FabricService objects by service_id.
    """
    return db.query(FabricService).filter(FabricService.service_id == service_id).all()

def get_fabric_services_by_customer(db: Session, customer_id: str) -> List[FabricService]:
    """
    Retrieve all FabricService objects associated with a specific customer UUID.
    """
    return db.query(FabricService).filter(FabricService.customer_id == customer_id).all()

def post_fabric_service(db: Session, data: FabricServiceIn) -> FabricService:
    """
    Provisions a new high-level Fabric Service for a customer.
    """
    new_service = FabricService(
        service_id=uuid.uuid4(),
        customer_id=data.customer_id,
        service_name=data.service_name,
        service_alias=data.service_alias,
        service_type=data.service_type,
        service_description=data.service_description,
        route_target=data.route_target,
        health_status=data.health_status
    )

    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service

def update_fabric_service(db: Session, service_id: UUID, data: FabricServiceUpdate) -> FabricService:
    """
    Updates Fabric Service metadata or health status.
    """
    service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="FabricService not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service

def delete_fabric_service(db: Session, service_id: UUID) -> bool:
    """
    Removes a Fabric Service. Note: Cascading constraints should handle connections.
    """
    service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
    if not service:
        return False

    db.delete(service)
    db.commit()
    return True

# --- Fabric Connection Management ---

def get_fabric_connections(db: Session) -> List[FabricConnection]:
    """
    Returns all logical connections (VCs/Circuits) across the fabric.
    """
    return db.query(FabricConnection).all()

def get_fabric_connections_by_service_id(db: Session, service_id: str) -> List[FabricConnection]:
    """
    Returns all logical connections belonging to a specific parent service.
    """
    return db.query(FabricConnection).filter(FabricConnection.service_id == service_id).all()

def post_fabric_connection(db: Session, data: FabricConnectionIn) -> FabricConnection:
    """
    Creates a logical connection between two endpoints (A and B) within a service.
    Handles VRF assignment, VLAN tagging, and bandwidth parameters.
    """
    new_connection = FabricConnection(
        connection_id=uuid.uuid4(),
        service_id=data.service_id,
        connection_name=data.connection_name,
        connector_a_id=data.connector_a_id,
        connector_b_id=data.connector_b_id,
        connector_a_table=data.connector_a_table,
        connector_b_table=data.connector_b_table,
        vrf_name=data.vrf_name,
        service_bw=data.service_bw,
        s_vlan=data.s_vlan,
        c_vlan_list=data.c_vlan_list,
        connection_status=data.connection_status,
        health_status=data.health_status
    )

    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)
    return new_connection

def update_fabric_connection(db: Session, connection_id: UUID, data: FabricConnectionUpdate):
    # Fetch existing connection
    connection = db.query(FabricConnection).filter(FabricConnection.connection_id == connection_id).first()
    if not connection:
        raise ValueError(f"FabricConnection {connection_id} not found")

    # Debug: show incoming update data
    print("DEBUG update data:", data.dict(exclude_unset=True))

    # Apply updates only for provided fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(connection, field, value)

    # Debug: show ORM after update
    print("DEBUG ORM connection after update:", connection.__dict__)

    db.commit()
    db.refresh(connection)
    return connection

def delete_fabric_connection(db: Session, connection_id: UUID) -> bool:
    connection = db.query(FabricConnection).filter(FabricConnection.connection_id == connection_id).first()
    if not connection:
        return False

    # Debug: show what will be deleted
    print("DEBUG deleting FabricConnection:", connection.connection_id, connection.connection_name)

    db.delete(connection)
    db.commit()
    return True
