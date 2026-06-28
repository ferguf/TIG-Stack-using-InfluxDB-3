"""File Name: 'network_service_logic.py' and version '1.1.5' date: 'November 30, 2025 11:50 AM MST' (Change: Fixed SQLAlchemy IntegrityError in setup_mock_data by adding an intermediate session.flush() to ensure port IDs are generated before being referenced by the Interface object.) """
import sys
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, Session 
from sqlalchemy.exc import SQLAlchemyError
from network_inventory_models import FabricService, Port, Interface, FabricConnection, Customer, Base

# --- Database Utility Functions ---

@contextmanager
def db_session_scope(engine):
    """
    Provide a transactional scope around a series of operations.
    If an exception occurs, the transaction is rolled back.
    """
    # Create a local session factory bound to the engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        print(f"\n[DB TRANSACTION ERROR] Rolling back changes: {e}", file=sys.stderr)
        session.rollback()
        raise # Re-raise the exception after rollback
    except Exception as e:
        print(f"\n[GENERIC ERROR] Rolling back changes: {e}", file=sys.stderr)
        session.rollback()
        raise
    finally:
        session.close()

def setup_mock_data(session: Session) -> dict:
    """
    Sets up the necessary pre-existing (mock) data in the database 
    required before running the configuration logic.
    """
    print("Setting up mock inventory data...")
    
    # 1. Create Customer
    customer = Customer(
        name="Global Telco Corp",
        account_id="ACC-1001"
    )

    # 2. Create Ports (pre-provisioned infrastructure)
    # Note: These ports are initially NNI (Network-to-Network Interface) in the mock data
    port_a = Port(
        port_name='ATL-SW-01/1/1', 
        device_id='SW-ATL-001', 
        port_service_status='Assigned',
        port_type='Fabric Port'
    )
    port_b = Port(
        port_name='DAL-SW-02/1/2', 
        device_id='SW-DAL-002', 
        port_service_status='Assigned',
        port_type='UNI'
    )
    
    # 3. Create Fabric Service (Linked to Customer)
    service = FabricService(
        customer=customer,
        service_name='EPL-Service-10G', 
        service_type='EPL'
    )

    # Add objects that generate IDs needed for the Interface object and flush them
    session.add_all([customer, port_a, port_b, service])
    session.flush() # Flush here to ensure port_a.port_id is populated

    # 4. Create Logical Interface (Tied to Port, acts as the logical config template)
    interface = Interface(
        port_id=port_a.port_id, # Linking the interface config to Port A's device (ID is now available)
        interface_name=f"{service.service_name}-INT-A", 
        is_active=True
    )

    # Add the final object and flush
    session.add(interface)
    session.flush() 

    return {
        'customer': customer,
        'service': service,
        'port1': port_a,
        'port2': port_b,
        'interface': interface,
    }

# --- Core Business Logic ---

def configure_eline_epl(session: Session, service: FabricService, port1: Port, port2: Port, service_bw_mbits: int, interface: Interface) -> FabricConnection:
    """
    Core function to provision an E-Line EPL service.
    
    This function interacts with the underlying PostgreSQL tables: `customer` (via service), 
    `fabric_service`, and `ports` by manipulating the SQLAlchemy ORM objects.
    
    1. Updates the status and type of the two endpoints (ports).
    2. Creates a new FabricConnection record linking all objects and storing bandwidth.
    """
    print(f"\n[LOGIC] Starting E-Line EPL configuration for Service '{service.service_name}' (Customer: {service.customer.name})...")
    
    # 1. Validation Checks
    if port1.port_service_status != 'Assigned' or port2.port_service_status != 'Assigned':
        raise ValueError("One or both ports are not available for allocation.")
        
    if service_bw_mbits > port1.max_capacity_mbits or service_bw_mbits > port2.max_capacity_mbits:
        raise ValueError("Requested bandwidth exceeds port capacity.")
        
    # Check if the interface configuration is already used by an existing connection
    # Note: The 'connections' relationship in Interface is a list.
    if interface.connections:
        raise ValueError(f"Interface '{interface.interface_name}' is already in use by a connection.")

    # 2. Update Port Status and Type (Business Rule Application - modifies the 'ports' table data)
    # For a newly provisioned E-Line to a customer, the NNI ports are repurposed as UNI (User-to-Network Interface)
    port1.port_service_status = 'Configured'
    port1.port_type = 'UNI'
    
    port2.port_service_status = 'Confgured'
    port2.port_type = 'UNI'
    
    session.add_all([port1, port2])
    print(f"[LOGIC] Updated Ports: {port1.port_name} and {port2.port_name} to status 'Confgiured' and type 'UNI' or 'Fabric Port' .")

    # 3. Create the Fabric Connection Record
    connection_name = f"FC-{service.service_name}-{service_bw_mbits}M"
    
    new_connection = FabricConnection(
        connection_name=connection_name,
        service_id=service.service_id, # References the 'fabric_service' table
        interface_id=interface.interface_id,
        connection_type='EPL',
        bandwidth_mbits=service_bw_mbits,
        port1_id=port1.port_id, # References the 'ports' table
        port2_id=port2.port_id  # References the 'ports' table
    )
    
    session.add(new_connection)
    session.flush() # Ensures the new_connection object has its ID for the return value
    print(f"[LOGIC] Created new FabricConnection: {new_connection.connection_name}")
    
    return new_connection
    
def decommission_eline_epl(session: Session, service_id: str) -> bool:
    """
    Decommissions an E-Line EPL service by:
    1. Finding the FabricConnection associated with the service_id.
    2. Resets the status and type of the two associated ports back to inventory defaults (affecting the `ports` table).
    3. Deletes the FabricConnection record.
    
    Returns True if successful, raises ValueError if connection is not found.
    """
    print(f"\n[LOGIC] Starting E-Line EPL decommission for Service ID: {service_id}...")

    # 1. Find the connection
    connection = session.query(FabricConnection).filter(FabricConnection.service_id == service_id).one_or_none()

    if not connection:
        raise ValueError(f"No active FabricConnection found for Service ID: {service_id}")

    connection_name = connection.connection_name
    port1_id = connection.port1_id
    port2_id = connection.port2_id

    # 2. Get Ports (for inventory reset)
    port1 = session.get(Port, port1_id)
    port2 = session.get(Port, port2_id)
    service = session.get(FabricService, service_id) # For logging
    
    # 3. Reset Port Status and Type (Inventory Restock)
    if port1:
        port1.port_service_status = 'Assigned'
        port1.port_type = 'Fabric Port' 
        session.add(port1)
        print(f"[LOGIC] Reset Port 1: {port1.port_name} to status 'Assigned' and type 'Fabric Port'.")
    
    if port2:
        port2.port_service_status = 'Assigned'
        port2.port_type = 'Fabric Port'
        session.add(port2)
        print(f"[LOGIC] Reset Port 2: {port2.port_name} to status 'Assigned' and type 'Fabric Port'.")

    # 4. Delete the Fabric Connection Record
    session.delete(connection)
    session.flush()

    print(f"[LOGIC] Successfully deleted FabricConnection: {connection_name}")
    print(f"[LOGIC] Decommission complete for service {service.service_name if service else 'ID ' + service_id}.")
    
    return True