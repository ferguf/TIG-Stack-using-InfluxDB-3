"""
api_operation.py
High-level database interaction methods (CRUD + reporting) using SQLAlchemy.
"""
from ipaddress import IPv6Interface
from sqlalchemy.orm import Session
import os
import csv
from typing import Optional, List, Tuple
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from scripts.api_schema import FabricConnectionIn, FabricConnectionOut, FabricConnectionUpdate, ROPChannelMemberIn, ROPChannelMemberUpdate, VNetworkLinksDetailOut
from scripts.api_schema import CustomerOut, FabricServiceIn,FabricServiceOut, DeviceIn, CustomerIn, DeviceUpdate, FabricServiceUpdate, DeleteResponse
from scripts.api_schema import InterfaceIn, InterfaceUpdate, LRICCostModelIn, LRICCostModelUpdate, NetworkLinkIn, NetworkLinkUpdate, PortOut, PortIn 
from scripts.api_schema import PatchPanelIn,PatchPanelOut,DeviceOut, HardwareDocumentIn, HardwareDocumentUpdate, HardwareSpecsIn, HardwareSpecsUpdate, IPv4InterfaceIn, IPv6InterfaceIn
from scripts.api_schema import LocationIn,LocationOut,LocationUpdate,CrossConnectIn, CrossConnectUpdate, DeviceLocationIn, DeviceLocationUpdate
import uuid as uuid
from uuid import UUID
from scripts.api_session import get_db_session
from scripts.api_model import  GalileoNodes, PatchPanel,VNetworkLinksDetail,VNetworkLinksLAG,VDevicePorts,CrossConnect, Customer, CustomerSummaryView, DeviceLocation, FabricService, Device, HardwareDocument, HardwareSpecs, IPv4Interface, Interface, LRICCostModel, LocationInfo, NetworkLink, Port, FabricConnection, ROPChannelMember
import logging
from fastapi import APIRouter, Depends, HTTPException


TEMPLATE_DIR = "templates/roles"  # folder where CSVs live

# ----------------------------------------------------------------------
# CRU Customer Methods 
# ----------------------------------------------------------------------

def get_customers() -> List[Customer]:
    with get_db_session() as db:
        return db.query(Customer).all()

def get_customer(customer_id: str) -> Customer:
    """
    Return a single Customer object by customer_id.
    """
    with get_db_session() as db:
        return db.query(Customer).filter(Customer.customer_id == customer_id).first()

def post_customer(customer_name: str, account_id: str) -> Optional[Customer]:
    try:
        with get_db_session() as db:
            new_customer = Customer(customer_name=customer_name, account_id=account_id)
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)
            return new_customer
    except Exception as e:
        print(f"Error creating customer: {e}")
        return None

def put_customer(customer_id: str, customer_name: str, account_id: str) -> Optional[Customer]:
    with get_db_session() as db:
        customer = db.get(Customer, customer_id)
        if not customer:
            return None
        customer.customer_name = customer_name
        customer.account_id = account_id
        db.commit()
        db.refresh(customer)
        return customer

def delete_customer(customer_id: str) -> bool:
    with get_db_session() as db:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return False
        db.delete(customer)
        db.commit()
        return True



# CREATE customer

    try:
        with get_db_session() as db:
            new_customer = Customer(**customer_data)
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)
            return CustomerOut.from_orm(new_customer)
    except Exception as e:
        print(f"Error creating customer: {e}")
        return None

# READ all customers

    try:
        with get_db_session() as db:
            customers = db.query(Customer).all()
            return [CustomerOut.from_orm(c) for c in customers]
    except Exception as e:
        print(f"Error retrieving customers: {e}")
        return []

# READ customer by ID

    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            return CustomerOut.from_orm(customer) if customer else None
    except Exception as e:
        print(f"Error retrieving customer {customer_id}: {e}")
        return None

# UPDATE customer

    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return None
            for key, value in update_data.items():
                setattr(customer, key, value)
            db.commit()
            db.refresh(customer)
            return CustomerOut.from_orm(customer)
    except Exception as e:
        print(f"Error updating customer {customer_id}: {e}")
        return None

# DELETE customer

    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return False
            db.delete(customer)
            db.commit()
            return True
    except Exception as e:
        print(f"Error deleting customer {customer_id}: {e}")
        return False

def get_customer_summaries() -> List[CustomerSummaryView]:
    """
    Fetches the aggregated summary data for all customers from the 
    v_customer_summary view.
    """
    with get_db_session() as db:
        return db.query(CustomerSummaryView).all()

# ----------------------------------------------------------------------
# CRUD Fabric services Methods 
# ----------------------------------------------------------------------    
 
def get_fabric_services(db: Session):
    return db.query(FabricService).all()   
    
def post_fabric_service(db: Session, data: FabricServiceIn):
    # Debug: check what FastAPI/Pydantic gave you
    print("DEBUG incoming service_type:", data.service_type)

    new_service = FabricService(
        service_id=uuid.uuid4(),
        customer_id=data.customer_id,
        service_name=data.service_name,
        service_alias=data.service_alias,
        service_type=data.service_type,   # <-- must be mapped
        service_description=data.service_description,
        route_target=data.route_target,
        health_status=data.health_status
    )

    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service

def update_fabric_service(db: Session, service_id: UUID, data: FabricServiceUpdate):
    service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="FabricService not found")

    # Apply updates only for provided fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service

def get_fabric_services_by_service(db: Session, service_id: str) -> List[FabricService]:
    """
    Retrieve all FabricService objects for a given customer.
    - customer_id: UUID string of the customer
    - returns: List of FabricService objects (empty list if none found)
    """
    return db.query(FabricService).filter(FabricService.service_id == service_id).all()

def get_fabric_services_by_customer(db: Session, customer_id: str) -> List[FabricService]:
    """
    Retrieve all FabricService objects for a given customer.
    - customer_id: UUID string of the customer
    - returns: List of FabricService objects (empty list if none found)
    """
    return db.query(FabricService).filter(FabricService.customer_id == customer_id).all()


# DELETE service
def delete_fabric_service(db: Session, service_id: UUID) -> bool:
    service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
    if not service:
        return False

    db.delete(service)
    db.commit()
    return True


# ----------------------------------------------------------------------
# CRUD Device Methods 
# ---------------------------------------------------------------------- 

def get_devices() -> List[DeviceOut]:
    try:
        with get_db_session() as db:
            devices = db.query(Device).all()
            return [DeviceOut.from_orm(d) for d in devices]
    except Exception as e:
        print(f"Error retrieving devices: {e}")
        return []

def post_device(db: Session, data: DeviceIn):
    payload = data.model_dump(exclude_unset=True)

    new_device = Device(
        device_id=uuid.uuid4(),
        **payload
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

def get_device_by_id(device_id: str) -> Optional[DeviceOut]:
    try:
        with get_db_session() as db:
            device = db.query(Device).filter(Device.device_name == device_id).first()
            return DeviceOut.from_orm(device) if device else None
    except Exception as e:
        print(f"Error retrieving device {device_id}: {e}")
        return None

def get_devices_by_location(location_code: str) -> List[DeviceOut]:
    """
    Database operation to fetch devices filtered by lowercase location code.
    """
    try:
        # Normalize input to lowercase
        clean_code = str(location_code).strip().upper()
        
        with get_db_session() as db:
            # Filter by the 'location' column
            devices = db.query(Device).filter(Device.location == clean_code).all()
            
            # Map SQLAlchemy models to Pydantic objects
            return [DeviceOut.from_orm(d) for d in devices]
    except Exception as e:
        print(f"Error retrieving devices for location {location_code}: {e}")
        return []


def put_device(device_id: str, update_data: dict) -> Optional[DeviceOut]:
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
        print(f"Error updating device {device_id}: {e}")
        return None

def delete_device_by_id(device_id: str) -> bool:
    try:
        with get_db_session() as db:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return False
            db.delete(device)
            db.commit()
            return True
    except Exception as e:
        print(f"Error deleting device {device_id}: {e}")
        return False

# ----------------------------------------------------------------------
# CRUD Ports
# ---------------------------------------------------------------------- 
def get_galileo_nodes(db: Session):
    """
    Fetches the Harry Beck grid-snapped city hubs and their 
    internal unique devices from the Postgres view.
    """
    return db.query(GalileoNodes).all()

def get_galileo_links(db: Session):
    """
    Fetches the inter-city connectivity fabric with 
    snapped A and B coordinates for topological rendering.
    """
    return db.query(GalileoLinks).all()

def get_ports(db: Session):
    return db.query(Port).all()

def get_ports_by_port_id(db: Session, port_id: str):
    return db.query(VDevicePorts).filter(VDevicePorts.port_id == port_id).first()
    
def get_port_by_id(db: Session, port_id: str) -> Optional[VDevicePorts]:
    """
    Retrieve a single Port object by its UUID.
    - port_id: UUID string of the port
    - returns: Port object or None if not found
    """
    return db.query(VDevicePorts).filter(VDevicePorts.port_id == port_id).first()

def get_ports_by_device_name(db: Session, device_name: str):
    return (
        db.query(Port)
        .join(Device, Port.device_id == Device.device_id)
        .filter(Device.device_name == device_name)
        .all()
    )

    
def get_ports_by_device_id(db: Session, device_id: str):
    return (
        db.query(Port)
        .join(Device, Port.device_id == Device.device_id)
        .filter(Device.device_id == device_id)
        .all()
    )

def get_ports_by_customer_id(db: Session, customer_id: UUID) -> List["VDevicePorts"]:
    """
    Fetch all records from the v_device_ports view that match a specific customer_id.
    Returns a list of VDevicePorts ORM objects.
    """
    return (
        db.query(VDevicePorts)
        .filter(VDevicePorts.customer_id == customer_id)
        .all()
    )

def get_port_by_device_and_port_name(db: Session, device_name: str, port_name: str):
    return (
        db.query(Port)
        .join(Device, Port.device_id == Device.device_id)
        .filter(Device.device_name == device_name)
        .filter(Port.port_name == port_name)
        .first()
    )


def create_ports_bulk_logic(
    db: Session,
    device_id: str,
    port_list: list[dict]
) -> list[Port]:
    """
    Takes a list of dictionaries and creates multiple ports in the BASE TABLE.
    """
    created_ports = []

    try:
        for port_data in port_list:
            # Step 1: Initialize new model instance
            new_port = Port()
            
            # Step 2: Set basic identifiers
            new_port.port_id = str(uuid.uuid4())
            new_port.device_id = device_id

            # Step 3: Apply updates from the CSV/Dictionary (Mirroring your update style)
            for key, value in port_data.items():
                if hasattr(new_port, key):
                    setattr(new_port, key, value)
            
            db.add(new_port)
            created_ports.append(new_port)

        # Step 4: Save the batch
        db.commit()
        
        # Refresh to get IDs/defaults back from DB
        for p in created_ports:
            db.refresh(p)
            
        return created_ports

    except Exception as e:
        db.rollback()
        raise e

def create_port_for_device(db: Session, device_id: UUID, data: PortIn):
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

def update_port_by_device_and_name(
    db: Session,
    device_id: UUID,
    port_name: str,
    updates: dict
):
    """
    Update all values of a Port object based on router (device) name and port name.
    - device_name: the parent device's name
    - port_name: the current port name
    - updates: dict of new values for the Port model
    """
    # Find the device
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return None

    # Find the port belonging to that device
    port = (
        db.query(Port)
        .filter(Port.device_id == device.device_id, Port.port_name == port_name)
        .first()
    )
    if not port:
        return None

    # Apply all updates dynamically
    for key, value in updates.items():
        if hasattr(port, key) and value is not None:
            setattr(port, key, value)

    db.add(port)
    db.commit()
    db.refresh(port)
    return port

def update_port_by_id(
    db: Session,
    port_id: str,
    updates: dict
) -> Optional[Port]:
    """
    Finds a port in the BASE TABLE and applies updates.
    """
    # Step 1: Query the TABLE (Ensure 'Port' is the SQLAlchemy Table model)
    port = db.query(Port).filter(Port.port_id == port_id).first()
    
    if not port:
        return None

    # Step 2: Apply updates
    for key, value in updates.items():
        # Only set if the attribute exists on the model
        if hasattr(port, key):
            setattr(port, key, value)

    # Step 3: Save
    try:
        db.commit()
        db.refresh(port)
        return port
    except Exception as e:
        db.rollback()
        raise e
 
def delete_port_by_device_and_port_id(db: Session, device_id: str, port_id: str) -> bool:
    """
    Delete a port based on device name and port name.
    Returns True if deleted, False if not found.
    """
    # Find the device
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return False

    # Find the port belonging to that device
    port = (
        db.query(Port)
        .filter(Port.device_id == device.device_id, Port.port_id == port_id)
        .first()
    )
    if not port:
        return False

    # Delete the port
    db.delete(port)
    db.commit()
    return True

# ----------------------------------------------------------------------
# CRUD Fabic Connections
# ---------------------------------------------------------------------- 
# READ get Fabric Connections
def get_fabric_connections(db: Session):
    return db.query(FabricConnection).all()

def get_fabric_connections_by_service_id(service_id: str, db: Session):
    """
    Retrieve all FabricConnection objects for a given service_id.
    - service_id: UUID string of the Fabric Service
    - returns: List of FabricConnection objects (empty list if none found)
    """
    return db.query(FabricConnection).filter(FabricConnection.service_id == service_id).all()

def post_fabric_connection(db: Session, data: FabricConnectionIn):
    # Debug: check what FastAPI/Pydantic gave you
    print("DEBUG incoming service_id:", data.service_id)
    print("DEBUG incoming connection_name:", data.connection_name)
    print("DEBUG incoming vrf_name:", data.vrf_name)
    print("DEBUG incoming service_bw:", data.service_bw)
    print("DEBUG incoming health_status:", data.health_status)

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
        connection_status = data.connection_status,
        health_status=data.health_status
    )

    # Debug: check what you’re about to insert
    print("DEBUG ORM connection_name:", new_connection.connection_name)
    print("DEBUG ORM vrf_name:", new_connection.vrf_name)
    print("DEBUG ORM service_bw:", new_connection.service_bw)
    print("DEBUG ORM health_status:", new_connection.health_status)

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

def _create_ip_configs(db: Session, interface_id: UUID, ipv4_data: List[IPv4InterfaceIn], ipv6_data: List[IPv6InterfaceIn]):
    # Create IPv4 records
    for ip4_data in ipv4_data:
        new_ip4 = IPv4Interface(interface_id=interface_id, **ip4_data.model_dump())
        db.add(new_ip4)

    # Create IPv6 records
    for ip6_data in ipv6_data:
        new_ip6 = IPv6Interface(interface_id=interface_id, **ip6_data.model_dump())
        db.add(new_ip6)
    
    db.flush() # Ensure children are created before parent is committed


# --- Interface CRUD Operations ---

def get_interfaces(db: Session) -> List[Interface]:
    return db.query(Interface).all()

def get_interface_by_id(db: Session, interface_id: UUID) -> Optional[Interface]:
    return db.query(Interface).filter(Interface.interface_id == interface_id).first()

def post_interface(db: Session, data: InterfaceIn) -> Interface:
    # Separate nested IP data from core interface data
    ip4_data = data.ipv4_configs
    ip6_data = data.ipv6_configs
    core_data = data.model_dump(exclude={'ipv4_configs', 'ipv6_configs'})

    new_interface = Interface(**core_data)
    
    try:
        db.add(new_interface)
        db.flush() # Flush to get the new interface_id
        
        _create_ip_configs(db, new_interface.interface_id, ip4_data, ip6_data)
        
        db.commit()
        db.refresh(new_interface)
        return new_interface
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error: Duplicate unique constraint or invalid FK. {e}")
    except Exception as e:
        db.rollback()
        raise e

def put_interface(db: Session, interface_id: UUID, update_data: InterfaceUpdate) -> Optional[Interface]:
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        # 1. Update core interface fields
        if update_dict:
            db.query(Interface).filter(Interface.interface_id == interface_id).update(update_dict)

        # Note: Nested IP updates (PUT/DELETE) require more complex logic
        # (e.g., finding the specific IP record and updating it, or replacing the whole list).
        # We will keep this simple and rely on direct access for IP updates for now.
        
        db.commit()
        return get_interface_by_id(db, interface_id)
        
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_interface_by_id(db: Session, interface_id: UUID) -> bool:
    try:
        # Cascading deletes will handle ipv4/ipv6 records automatically
        result = db.query(Interface).filter(Interface.interface_id == interface_id).delete()
        db.commit()
        return result > 0
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Cannot delete interface {interface_id} due to existing dependencies (RESTRICTed FK). {e}")
    except Exception as e:
        db.rollback()
        raise e

# --- PatchPanel CRUD Operations ---
def get_patch_panel(db: Session, port_id: UUID): # Renamed to port_id for consistency
    return db.query(PatchPanel).filter(
        PatchPanel.port_id == port_id
    ).first()

def get_patch_panels_for_device(db: Session, device_id: UUID):
    """
    Fetches all ports associated with a specific device.
    """
    return db.query(PatchPanel).filter(
        PatchPanel.device_id == device_id
    ).all() # .all() returns a list, which prevents 404/500 errors if empty

def get_patch_panel_port(db: Session, device_id: UUID, port_id: UUID):
    return db.query(PatchPanel).filter(
        PatchPanel.device_id == device_id,
        PatchPanel.port_id == port_id
    ).first()

def get_patch_panel_port_by_port_name(db: Session, device_name: str, port_name: str):
    return (
        db.query(PatchPanel)
        .join(Device, PatchPanel.device_id == Device.device_id)
        .filter(Device.device_name == device_name)
        .filter(PatchPanel.port_name == port_name)
        .first()
    )

def get_patch_panel_ports_by_device_name(db: Session, device_name: str):
    return (
        db.query(PatchPanel)
        .join(Device, PatchPanel.device_id == Device.device_id)
        .filter(Device.device_name == device_name)
        .all()
    )

def create_patch_panel(db: Session, panel_data: PatchPanelIn):
    # Convert Pydantic model to a dictionary
    data_dict = panel_data.model_dump()
    
    # Generate the UUID in Python to ensure it's never NULL
    if not data_dict.get("port_id"):
        data_dict["port_id"] = uuid.uuid4()
        
    # Create the SQLAlchemy model instance
    new_panel = PatchPanel(**data_dict)
    
    db.add(new_panel)
    db.commit()   # Finalize the transaction
    db.refresh(new_panel) # Reload the object (picks up created_at/updated_at)
    return new_panel
    truncate    

def patch_patch_panel(db: Session, port_id: UUID, panel_data: PatchPanelIn):
    panel = db.query(PatchPanel).filter(
        PatchPanel.port_id == port_id
    ).first()

    if panel is None:
        return None

    # --- THE FIX ---
    # model_dump(exclude_unset=True) ensures ONLY the fields sent 
    # in the JSON request are included in the dictionary.
    update_data = panel_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(panel, key, value)

    db.commit() 
    db.refresh(panel)
    return panel

def delete_patch_panel(db: Session, port_id: UUID):
    deleted = db.query(PatchPanel).filter(
        PatchPanel.port_id == port_id
    ).delete(synchronize_session=False)

    db.commit()
    return deleted

# --- PatchPanel CRUD Operations ---


def get_cross_connects(db: Session) -> List[CrossConnect]:
    return db.query(CrossConnect).all()

def get_cross_connect_by_id(db: Session, connect_id: UUID) -> Optional[CrossConnect]:
    return db.query(CrossConnect).filter(CrossConnect.connect_id == connect_id).first()

def post_cross_connect(db: Session, data: CrossConnectIn) -> CrossConnect:
    new_connect = CrossConnect(**data.model_dump())
    
    try:
        db.add(new_connect)
        db.commit()
        db.refresh(new_connect)
        return new_connect
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error: Duplicate circuit ID or invalid ports specified. {e}")
    except Exception as e:
        db.rollback()
        raise e

def put_cross_connect(db: Session, connect_id: UUID, update_data: CrossConnectUpdate) -> Optional[CrossConnect]:
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        db.query(CrossConnect).filter(CrossConnect.connect_id == connect_id).update(update_dict)
        db.commit()
        return get_cross_connect_by_id(db, connect_id)
        
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_cross_connect_by_id(db: Session, connect_id: UUID) -> bool:
    try:
        result = db.query(CrossConnect).filter(CrossConnect.connect_id == connect_id).delete()
        db.commit()
        return result > 0
    except Exception as e:
        db.rollback()
        raise e
    
def get_hardware_specs(db: Session) -> List[HardwareSpecs]:
    return db.query(HardwareSpecs).all()

def get_hardware_spec_by_id(db: Session, hardware_id: UUID) -> Optional[HardwareSpecs]:
    return db.query(HardwareSpecs).filter(HardwareSpecs.hardware_id == hardware_id).first()

def post_hardware_spec(db: Session, data: HardwareSpecsIn) -> HardwareSpecs:
    new_spec = HardwareSpecs(**data.model_dump())
    
    try:
        db.add(new_spec)
        db.commit()
        db.refresh(new_spec)
        return new_spec
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error: Check unique constraints or invalid Foreign Keys. {e}")
    except Exception as e:
        db.rollback()
        raise e

def put_hardware_spec(db: Session, hardware_id: UUID, update_data: HardwareSpecsUpdate) -> Optional[HardwareSpecs]:
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        db.query(HardwareSpecs).filter(HardwareSpecs.hardware_id == hardware_id).update(update_dict)
        db.commit()
        return get_hardware_spec_by_id(db, hardware_id)
        
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_hardware_spec_by_id(db: Session, hardware_id: UUID) -> bool:
    try:
        # Check if any devices or documents reference this spec
        # (This relies on the FOREIGN KEY constraint to raise an IntegrityError if referenced)
        result = db.query(HardwareSpecs).filter(HardwareSpecs.hardware_id == hardware_id).delete()
        db.commit()
        return result > 0
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Cannot delete hardware spec {hardware_id}. It is currently referenced by Devices, Documents, or Material Qualifications.")
    except Exception as e:
        db.rollback()
        raise e
    
def get_hardware_documents(db: Session) -> List[HardwareDocument]:
    return db.query(HardwareDocument).all()

def get_hardware_document_by_id(db: Session, document_id: UUID) -> Optional[HardwareDocument]:
    return db.query(HardwareDocument).filter(HardwareDocument.document_id == document_id).first()

def get_hardware_documents_by_spec(db: Session, hardware_id: UUID) -> List[HardwareDocument]:
    return db.query(HardwareDocument).filter(HardwareDocument.hardware_id == hardware_id).all()

def post_hardware_document(db: Session, data: HardwareDocumentIn) -> HardwareDocument:
    new_doc = HardwareDocument(**data.model_dump())
    
    try:
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        return new_doc
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error: Invalid hardware_id (spec not found). {e}")
    except Exception as e:
        db.rollback()
        raise e

def put_hardware_document(db: Session, document_id: UUID, update_data: HardwareDocumentUpdate) -> Optional[HardwareDocument]:
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        db.query(HardwareDocument).filter(HardwareDocument.document_id == document_id).update(update_dict)
        db.commit()
        return get_hardware_document_by_id(db, document_id)
        
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_hardware_document_by_id(db: Session, document_id: UUID) -> bool:
    try:
        result = db.query(HardwareDocument).filter(HardwareDocument.document_id == document_id).delete()
        db.commit()
        return result > 0
    except Exception as e:
        db.rollback()
        raise e

def get_lric_models(db: Session) -> List[LRICCostModel]:
    return db.query(LRICCostModel).all()

def get_lric_model_by_id(db: Session, cost_model_id: UUID) -> Optional[LRICCostModel]:
    return db.query(LRICCostModel).filter(LRICCostModel.cost_model_id == cost_model_id).first()

def post_lric_model(db: Session, data: LRICCostModelIn) -> LRICCostModel:
    new_model = LRICCostModel(**data.model_dump())
    
    try:
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return new_model
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error: Check constraints or invalid Foreign Keys. {e}")
    except Exception as e:
        db.rollback()
        raise e

def put_lric_model(db: Session, cost_model_id: UUID, update_data: LRICCostModelUpdate) -> Optional[LRICCostModel]:
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        db.query(LRICCostModel).filter(LRICCostModel.cost_model_id == cost_model_id).update(update_dict)
        db.commit()
        return get_lric_model_by_id(db, cost_model_id)
        
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_lric_model_by_id(db: Session, cost_model_id: UUID) -> bool:
    try:
        # Deletion will fail if any devices or other tables reference this cost_model_id
        result = db.query(LRICCostModel).filter(LRICCostModel.cost_model_id == cost_model_id).delete()
        db.commit()
        return result > 0
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Cannot delete LRIC cost model {cost_model_id}. It is currently referenced by other objects (e.g., Devices).")
    except Exception as e:
        db.rollback()
        raise e

def get_device_location_by_id(db: Session, device_id: UUID) -> Optional[DeviceLocation]:
    """Retrieves the location record for a specific device."""
    return db.query(DeviceLocation).filter(DeviceLocation.device_id == device_id).first()


def post_device_location(db: Session, data: DeviceLocationIn) -> DeviceLocation:
    """Creates a new device location record."""
    new_location = DeviceLocation(**data.model_dump())
    
    try:
        db.add(new_location)
        db.commit()
        db.refresh(new_location)
        return new_location
    except IntegrityError as e:
        db.rollback()
        # This will catch if the device_id already has a location record or if the device_id is invalid
        raise ValueError(f"Integrity Error: The device_id is invalid or already has a location record. {e}")
    except Exception as e:
        db.rollback()
        raise e

def put_device_location(db: Session, device_id: UUID, update_data: DeviceLocationUpdate) -> Optional[DeviceLocation]:
    """Updates an existing device location record."""
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        # Update device location fields
        result = db.query(DeviceLocation).filter(DeviceLocation.device_id == device_id).update(update_dict)
        db.commit()
        
        if result == 0:
            return None # Location record not found
            
        return get_device_location_by_id(db, device_id)
        
    except exec.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_device_location_by_id(db: Session, device_id: UUID) -> bool:
    """Deletes a device location record."""
    try:
        result = db.query(DeviceLocation).filter(DeviceLocation.device_id == device_id).delete()
        db.commit()
        return result > 0
    except Exception as e:
        db.rollback()
        raise e
 

# --- Network_links CRUD Operations ---    
def get_network_links(db: Session) -> List[NetworkLink]:
    return db.query(NetworkLink).all()

def get_network_links_lag(db: Session) -> List[VNetworkLinksLAG]:
    return db.query(VNetworkLinksLAG).all()

def get_network_link_by_id(db: Session, link_id: UUID) -> Optional[NetworkLink]:
    return db.query(NetworkLink).filter(NetworkLink.link_id == link_id).first()

def get_network_links_lag_by_device(db: Session, device_id: UUID) -> List[VNetworkLinksLAG]:
    return (
        db.query(VNetworkLinksLAG)
        .filter(VNetworkLinksLAG.device_id == device_id)
        .all()
    )

def get_network_links_detail(db: Session) -> List[VNetworkLinksDetail]:
    return (
        db.query(VNetworkLinksDetail)
        .all()
    )

def get_network_links_detail_by_type(db: Session, link_type: str) -> List[VNetworkLinksDetail]:
    return (
        db.query(VNetworkLinksDetail)
        .filter(VNetworkLinksDetail.link_type == link_type)
        .all()
    )
    
def get_network_links_detail_by_device(db: Session, device_id: UUID) -> List[VNetworkLinksDetail]:
    return (
        db.query(VNetworkLinksDetail)
        .filter(
            (VNetworkLinksDetail.a_device_id == device_id) |
            (VNetworkLinksDetail.b_device_id == device_id)
        )
        .all()
    )

def get_network_links_detail_by_location(db: Session, location: str) -> List[VNetworkLinksDetail]:
    return (
        db.query(VNetworkLinksDetail)
        .filter(
            (VNetworkLinksDetail.a_device_location == location) |
            (VNetworkLinksDetail.b_device_location == location)
        )
        .all()
    )
    
def get_network_links_by_type(db: Session, link_type: str) -> List[NetworkLink]:
    return (
        db.query(NetworkLink)
        .filter(NetworkLink.link_type == link_type)
        .all()
    )

def post_network_link(db: Session, link_data: NetworkLinkIn) -> NetworkLink:
    try:
        create_dict = link_data.model_dump()
        new_link = NetworkLink(**create_dict)

        db.add(new_link)
        db.commit()
        db.refresh(new_link)

        return new_link

    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during insert: {e}")

    except Exception as e:
        db.rollback()
        raise e

def put_network_link(db: Session, link_id: UUID, update_data: NetworkLinkUpdate) -> Optional[NetworkLink]:
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        result = db.query(NetworkLink).filter(NetworkLink.link_id == link_id).update(update_dict)
        db.commit()
        
        if result == 0:
            return None
            
        return get_network_link_by_id(db, link_id)
        
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_network_link_by_id(db: Session, link_id: UUID) -> bool:
    try:
        result = db.query(NetworkLink).filter(NetworkLink.link_id == link_id).delete()
        db.commit()
        return result > 0
    except Exception as e:
        db.rollback()
        raise e

def get_rop_channel_members(db: Session) -> List[ROPChannelMember]:
    return db.query(ROPChannelMember).all()

def get_rop_channel_member_by_id(db: Session, rop_member_id: UUID) -> Optional[ROPChannelMember]:
    return db.query(ROPChannelMember).filter(ROPChannelMember.rop_member_id == rop_member_id).first()

def get_channels_by_rop_link(db: Session, rop_link_id: UUID) -> List[ROPChannelMember]:
    """Retrieves all channel members for a specific ROP link."""
    return db.query(ROPChannelMember).filter(ROPChannelMember.rop_link_id == rop_link_id).all()

def post_rop_channel_member(db: Session, data: ROPChannelMemberIn) -> ROPChannelMember:
    new_member = ROPChannelMember(**data.model_dump())
    
    try:
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        return new_member
    except exc.IntegrityError as e:
        db.rollback()
        # This primarily catches the uq_rop_link_channel constraint violation
        raise ValueError(f"Integrity Error: Channel ID {data.channel_id} already exists within ROP Link {data.rop_link_id} or invalid Foreign Key used. {e}")
    except Exception as e:
        db.rollback()
        raise e

def put_rop_channel_member(db: Session, rop_member_id: UUID, update_data: ROPChannelMemberUpdate) -> Optional[ROPChannelMember]:
    update_dict = update_data.model_dump(exclude_unset=True)
    
    try:
        result = db.query(ROPChannelMember).filter(ROPChannelMember.rop_member_id == rop_member_id).update(update_dict)
        db.commit()
        
        if result == 0:
            return None
            
        return get_rop_channel_member_by_id(db, rop_member_id)
        
    except exc.IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error during update: Channel ID conflict within ROP link. {e}")
    except Exception as e:
        db.rollback()
        raise e

def delete_rop_channel_member_by_id(db: Session, rop_member_id: UUID) -> bool:
    try:
        result = db.query(ROPChannelMember).filter(ROPChannelMember.rop_member_id == rop_member_id).delete()
        db.commit()
        return result > 0
    except Exception as e:
        db.rollback()
        raise e

# GET all locations

def get_location_by_id(db: Session, location_id: UUID) -> Optional[LocationInfo]:
    return db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()

# POST (create) new location
def post_location(db: Session, data: LocationIn) -> LocationInfo:
    new_location = LocationInfo(**data.model_dump())
    try:
        db.add(new_location)
        db.commit()
        db.refresh(new_location)
        return new_location
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error: Check constraints or invalid Foreign Keys. {e}")
    except Exception as e:
        db.rollback()
        raise e

# PUT (update) existing location
def put_location(db: Session, location_id: UUID, update_data: LocationUpdate) -> Optional[LocationInfo]:
    location = db.query(LocationInfo).filter(LocationInfo.location_id == location_id).first()
    if not location:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(location, field, value)

    try:
        db.commit()
        db.refresh(location)
        return location
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Integrity Error: Check constraints or invalid Foreign Keys. {e}")
    except Exception as e:
        db.rollback()
        raise e

# GET device locations information

def get_device_location_by_id(db: Session, device_id: UUID) -> Optional[DeviceLocation]:
    return (
        db.query(DeviceLocation)
        .filter(DeviceLocation.device_id == device_id)
        .first()
    )

def create_device_location(db: Session, data: DeviceLocationIn) -> DeviceLocation:
    new_loc = DeviceLocation(
        device_id=data.device_id,
        clli=data.clli,
        location=data.location,
        floor_number=data.floor_number,
        rack_identifier=data.rack_identifier,
        aisle_identifier=data.aisle_identifier,
        rack_start_ru=data.rack_start_ru,
        ru_height=data.ru_height,
    )

    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc

def update_device_location(
    db: Session, device_id: UUID, data: DeviceLocationIn
) -> Optional[DeviceLocation]:

    loc = (
        db.query(DeviceLocation)
        .filter(DeviceLocation.device_id == device_id)
        .first()
    )

    if not loc:
        return None

    # Update fields only if provided
    loc.clli = data.clli if data.clli is not None else loc.clli
    loc.location = data.location if data.location is not None else loc.location
    loc.floor_number = data.floor_number if data.floor_number is not None else loc.floor_number
    loc.rack_identifier = data.rack_identifier if data.rack_identifier is not None else loc.rack_identifier
    loc.aisle_identifier = data.aisle_identifier if data.aisle_identifier is not None else loc.aisle_identifier
    loc.rack_start_ru = data.rack_start_ru if data.rack_start_ru is not None else loc.rack_start_ru
    loc.ru_height = data.ru_height if data.ru_height is not None else loc.ru_height

    db.commit()
    db.refresh(loc)
    return loc
