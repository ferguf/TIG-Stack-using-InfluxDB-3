""" File Name: 'db_operations.py' date: '2025-12-01 11:07 MST' (Core Database Operations and Data Retrieval - Finalized Imports and Views) """
# db_operations.py
"""
Contains all high-level database interaction methods (CRUD) using SQLAlchemy,
including reporting functions that utilize the ViewFabricConnection ORM model.
These methods abstract the session handling from the application handlers.
"""
from typing import Optional, List, Tuple
import uuid
from sqlalchemy import func, or_ # func and or_ can be imported here
from sqlalchemy.orm import Session # Correct import for Session
from sqlalchemy.exc import IntegrityError
from scripts.cli_base import get_db, Engine
# Note: Importing models from the latest db_setup.py
from python.scripts.api_model import (
    Customer, 
    FabricService, 
    Port, 
    FabricConnection, 
    Device, 
    ViewFabricConnection,
    create_database_tables # Imported for utility if needed
)


# ======================================================================
# --- CUSTOMER CRUD OPERATIONS ---
# ======================================================================

def create_customer(name: str, account_id: str) -> Optional[Customer]:
    """Creates a new Customer entry in the database."""
    try:
        db = next(get_db())
        # Check if account_id already exists to enforce uniqueness
        if db.query(Customer).filter(func.lower(Customer.account_id) == func.lower(account_id)).first():
            print(f"Error: Customer with Account ID '{account_id}' already exists.")
            return None
            
        new_customer = Customer(
            customer_name=name,
            account_id=account_id
        )
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        return new_customer
    except IntegrityError as e:
        db.rollback()
        print(f"Database error during customer creation (IntegrityError): {e}")
        return None
    except Exception as e:
        print(f"Error creating customer: {e}")
        return None

def get_all_customers() -> List[Tuple[str, str, uuid.UUID, int]]:
    """
    Retrieves all Customer records along with a count of their associated Fabric Services.
    Returns a list of tuples: (account_id, customer_name, customer_id, service_count).
    """
    try:
        db = next(get_db())
        
        # Subquery to count services per customer
        service_count_subquery = db.query(
            FabricService.customer_id,
            func.count(FabricService.service_id).label('service_count')
        ).group_by(FabricService.customer_id).subquery()
        
        # Main query: Select specific attributes needed for display, plus the service count
        results = db.query(
            Customer.account_id,
            Customer.customer_name,
            Customer.customer_id,
            service_count_subquery.c.service_count
        ).outerjoin(
            service_count_subquery,
            Customer.customer_id == service_count_subquery.c.customer_id
        ).order_by(Customer.customer_name).all()
        
        # Process results: convert None count (from OUTER JOIN where count is 0) to 0
        processed_results = [
            (account_id, customer_name, customer_id, count if count is not None else 0)
            for account_id, customer_name, customer_id, count in results
        ]
        
        return processed_results
    except Exception as e:
        print(f"Error retrieving customers with service count: {e}")
        return []

def delete_customer_by_id(customer_id: uuid.UUID) -> bool:
    """Deletes a Customer by ID. Requires cascade delete to be handled or services deleted first."""
    try:
        db = next(get_db())
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        
        if customer:
            # Prevent deletion if services still exist (unless services were deleted by fs_handlers)
            service_count = db.query(FabricService).filter(FabricService.customer_id == customer_id).count()
            if service_count > 0:
                print(f"Error: Customer has {service_count} associated services. Delete services first.")
                return False

            db.delete(customer)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error deleting customer {customer_id}: {e}")
        return False


# ======================================================================
# --- FABRIC SERVICE CRUD OPERATIONS ---
# ======================================================================

def create_fabric_service(
    customer_id: uuid.UUID,
    service_name: str,
    service_alias: str,
    service_type: str,
    service_description: Optional[str] = None,
    route_target: Optional[str] = None,
    health_status: int = 4
) -> Optional[FabricService]:
    """Creates a new Fabric Service entry."""
    try:
        db = next(get_db())
        
        # Check if service_name already exists to enforce uniqueness
        if db.query(FabricService).filter(func.lower(FabricService.service_name) == func.lower(service_name)).first():
            print(f"Error: Fabric Service with name '{service_name}' already exists.")
            return None

        new_service = FabricService(
            customer_id=customer_id,
            service_name=service_name,
            service_alias=service_alias,
            service_type=service_type,
            service_description=service_description,
            route_target=route_target,
            health_status=health_status
        )
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        return new_service
    except IntegrityError as e:
        db.rollback()
        print(f"Database error during service creation (IntegrityError): {e}")
        return None
    except Exception as e:
        print(f"Error creating fabric service: {e}")
        return None


def get_all_fabric_services() -> List[Tuple[str, str, str, str, Optional[int], uuid.UUID, int]]:
    """
    Retrieves all Fabric Services, including the associated customer name, service ID, and count of assigned Ports.
    Returns a list of tuples: 
    (customer_name, service_name, service_alias, service_type, health_status, service_id, port_count)
    """
    try:
        db = next(get_db())
        
        # Subquery to count ports associated with each Fabric Service
        port_count_subquery = db.query(
            Port.service_id,
            func.count(Port.port_id).label('port_count')
        ).filter(
            Port.service_id.is_not(None) # Only count assigned ports
        ).group_by(Port.service_id).subquery()

        # Main query
        results = db.query(
            Customer.customer_name,
            FabricService.service_name,
            FabricService.service_alias,
            FabricService.service_type,
            FabricService.health_status,
            FabricService.service_id,
            port_count_subquery.c.port_count # New field
        ).join(Customer).outerjoin(
            port_count_subquery,
            FabricService.service_id == port_count_subquery.c.service_id
        ).order_by(FabricService.service_name).all()
        
        # Process results: convert None count (from OUTER JOIN) to 0
        processed_results = [
            (c_name, s_name, s_alias, s_type, h_status, s_id, count if count is not None else 0)
            for c_name, s_name, s_alias, s_type, h_status, s_id, count in results
        ]
        
        return processed_results
    except Exception as e:
        print(f"Error retrieving all fabric services: {e}")
        return []

def get_fabric_services_by_type(service_type: str) -> List[Tuple[str, str, str, Optional[int], uuid.UUID, int]]:
    """
    Retrieves Fabric Services filtered by type, along with customer name and port count.
    Returns: (customer_name, service_name, service_alias, health_status, service_id, port_count)
    """
    try:
        db = next(get_db())
        
        # Subquery to count ports associated with each Fabric Service
        port_count_subquery = db.query(
            Port.service_id,
            func.count(Port.port_id).label('port_count')
        ).filter(
            Port.service_id.is_not(None)
        ).group_by(Port.service_id).subquery()

        results = db.query(
            Customer.customer_name,
            FabricService.service_name,
            FabricService.service_alias,
            FabricService.health_status,
            FabricService.service_id,
            port_count_subquery.c.port_count
        ).join(Customer).outerjoin(
            port_count_subquery,
            FabricService.service_id == port_count_subquery.c.service_id
        ).filter(
            FabricService.service_type == service_type
        ).order_by(FabricService.service_name).all()
        
        # Process results: convert None count (from OUTER JOIN) to 0
        processed_results = [
            (c_name, s_name, s_alias, h_status, s_id, count if count is not None else 0)
            for c_name, s_name, s_alias, h_status, s_id, count in results
        ]
        
        return processed_results
    except Exception as e:
        print(f"Error retrieving fabric services by type: {e}")
        return []

def get_ports_by_service_id(service_id: uuid.UUID) -> List[Tuple[uuid.UUID, str, str, str, str]]:
    """
    Retrieves all ports assigned to a specific Fabric Service.
    Returns: (port_id, device_name, port_name, port_service_status, port_type)
    """
    try:
        db = next(get_db())

        results = db.query(
            Port.port_id,
            Device.device_name,
            Port.port_name,
            Port.port_service_status,
            Port.port_type
        ).join(Device).filter(
            Port.service_id == service_id
        ).order_by(Device.device_name, Port.port_name).all()
        
        return results
    except Exception as e:
        print(f"Error retrieving ports for service {service_id}: {e}")
        return []


def get_fabric_service_by_id(service_id: uuid.UUID) -> Optional[FabricService]:
    """Retrieves a single Fabric Service by its ID."""
    try:
        db = next(get_db())
        service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
        return service
    except Exception as e:
        print(f"Error retrieving service {service_id}: {e}")
        return None

# ======================================================================
# --- FABRIC CONNECTION CRUD OPERATIONS (NEW) ---
# ======================================================================

def create_epl_connection(service_id: uuid.UUID, port_a_id: uuid.UUID, port_b_id: uuid.UUID) -> Optional[FabricConnection]:
    """
    Creates a point-to-point E-Line EPL Fabric Connection.
    Assumes ports are already assigned to the service.
    """
    try:
        db = next(get_db())

        # 1. Verification (Ensure the ports are assigned to this service)
        port_a_check = db.query(Port).filter(Port.port_id == port_a_id, Port.service_id == service_id).first()
        port_b_check = db.query(Port).filter(Port.port_id == port_b_id, Port.service_id == service_id).first()
        
        if not port_a_check or not port_b_check:
            print("Error: Ports must be assigned to the selected Fabric Service before connection creation.")
            return None

        # 2. Connection Creation
        # Note: interface_id is required but its source is undefined, using uuid.uuid4() placeholder.
        new_connection = FabricConnection(
            service_id=service_id,
            connection_name="E-line EPL",
            connection_status="Configured",
            port_a_id=port_a_id,
            port_b_id=port_b_id,
            interface_id=uuid.uuid4() 
        )
        
        db.add(new_connection)
        
        # 3. Update Ports' status to reflect the new connection
        port_a_check.port_service_status = "In Use (EPL)"
        port_b_check.port_service_status = "In Use (EPL)"

        db.commit()
        db.refresh(new_connection)
        return new_connection
    except IntegrityError as e:
        db.rollback()
        print(f"Database integrity error: A required field is missing or a foreign key failed. {e}")
        return None
    except Exception as e:
        db.rollback()
        print(f"Error creating E-line EPL connection: {e}")
        return None


# ======================================================================
# --- DEVICE & PORT CRUD OPERATIONS ---
# ======================================================================

def get_all_devices() -> List[Device]:
    """Retrieves all Device records."""
    try:
        db = next(get_db())
        return db.query(Device).all()
    except Exception as e:
        print(f"Error retrieving all devices: {e}")
        return []

def get_all_ports_with_device_details() -> List[Tuple[str, str, str, str, str, Optional[uuid.UUID]]]:
    """
    Retrieves all Port records, including the associated Device Name, and service_id.
    Returns a list of tuples: 
    (device_name, port_name, port_speed, port_service_status, port_type, service_id)
    """
    try:
        db = next(get_db())
        
        # Explicitly query for the fields needed for display, plus service_id for status check
        results = db.query(
            Device.device_name,
            Port.port_name,
            Port.port_speed,
            Port.port_service_status,
            Port.port_type,
            Port.service_id # NEW: Include service_id
        ).join(Device, Port.device_id == Device.device_id).all()
        
        return results
    except Exception as e:
        print(f"Error retrieving all ports with device details: {e}")
        return []


def get_eligible_ports() -> List[Tuple[uuid.UUID, str, str, str, str]]:
    """
    Retrieves ports eligible for assignment: 
    - port_service_status IN ('Available', 'Ready for use') 
    - port_type IN ('Physical', 'UNI')
    - service_id IS NULL (unassigned)
    Returns: (port_id, device_name, port_name, port_service_status, port_type)
    """
    try:
        db = next(get_db())
        
        eligible_status = ['Available', 'Ready for use']
        eligible_type = ['Physical', 'UNI']

        results = db.query(
            Port.port_id,
            Device.device_name,
            Port.port_name,
            Port.port_service_status,
            Port.port_type
        ).join(Device).filter(
            Port.port_service_status.in_(eligible_status),
            Port.port_type.in_(eligible_type),
            Port.service_id.is_(None)
        ).order_by(Device.device_name, Port.port_name).all()
        
        return results
    except Exception as e:
        print(f"Error retrieving eligible ports: {e}")
        return []


def get_assigned_ports() -> List[Tuple[uuid.UUID, str, str, str, str]]:
    """
    Retrieves ports currently assigned to a service.
    Returns: (port_id, device_name, port_name, service_name, service_alias)
    """
    try:
        db = next(get_db())

        results = db.query(
            Port.port_id,
            Device.device_name,
            Port.port_name,
            FabricService.service_name,
            FabricService.service_alias
        ).join(Device).join(FabricService, Port.service_id == FabricService.service_id).filter(
            Port.service_id.is_not(None)
        ).order_by(Device.device_name, Port.port_name).all()
        
        return results
    except Exception as e:
        print(f"Error retrieving assigned ports: {e}")
        return []


def assign_port_to_service(port_id: uuid.UUID, service_id: uuid.UUID) -> bool:
    """
    Assigns a port to a fabric service and updates its status and type.
    """
    try:
        db = next(get_db())
        port = db.query(Port).filter(Port.port_id == port_id).first()
        service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
        
        if not port:
            print(f"Error: Port with ID {port_id} not found.")
            return False
        if not service:
            print(f"Error: Fabric Service with ID {service_id} not found.")
            return False
        if port.service_id is not None:
            print(f"Error: Port {port.port_name} is already assigned to a service.")
            return False

        # Apply assignment rules
        port.service_id = service_id
        port.port_service_status = 'Configured'
        port.port_type = 'Fabric Port'
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error assigning port {port_id} to service {service_id}: {e}")
        return False


def unassign_port_from_service(port_id: uuid.UUID) -> bool:
    """
    Removes a port assignment and resets its status and type to ready for use.
    """
    try:
        db = next(get_db())
        port = db.query(Port).filter(Port.port_id == port_id).first()
        
        if not port:
            print(f"Error: Port with ID {port_id} not found.")
            return False
        if port.service_id is None:
            print(f"Error: Port {port.port_name} is not currently assigned to a service.")
            return False

        # Apply unassignment rules
        port.service_id = None
        port.port_service_status = 'Ready for use'
        port.port_type = 'Physical'
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error unassigning port {port_id}: {e}")
        return False

# ======================================================================
# --- View Fabric Connections ---
# ======================================================================

def view_fabric_Connection_counts(db: Session):
    """
    Generates a report that counts distinct connections and ports per service.
    
    Returns: List of query results (customer_name, service_name, connection_count, port_count)
    """
    
    # --- Report: Count connections and ports per service ---
    
    # We use the ViewFabricConnection class, group by customer and service name, 
    # and count distinct connection and port IDs.
    count_query = (
        db.query(
            ViewFabricConnection.customer_name,
            ViewFabricConnection.service_name,
            func.count(func.distinct(ViewFabricConnection.connection_id)).label('connection_count'),
            func.count(func.distinct(ViewFabricConnection.port_id)).label('port_count')
        )
        .group_by(ViewFabricConnection.customer_name, ViewFabricConnection.service_name)
        .order_by(ViewFabricConnection.customer_name, ViewFabricConnection.service_name)
        .all()
    )
    return count_query


def view_fabric_Connection_ports(db: Session):
    """
    Generates a detailed list of all connection endpoints represented in the view.
    
    Returns: List of query results (all detailed port columns)
    """

    # --- Report: List all ports and their details ---

    # This query directly selects the required columns from the ViewFabricConnection
    # and orders them by customer name.
    detail_query = (
        db.query(
            ViewFabricConnection.customer_name,
            ViewFabricConnection.service_name,
            ViewFabricConnection.device_name,
            ViewFabricConnection.port_name,
            ViewFabricConnection.connection_name,
            ViewFabricConnection.connection_status
        )
        .order_by(ViewFabricConnection.customer_name)
        .all()
    )
    
    return detail_query