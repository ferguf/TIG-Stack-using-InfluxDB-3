"""File Name: 'python/customer_cli.py' and version '1.0.25' date: 'November 30, 2025' (Refactor: Integrated core setup from cli_base.py. Features: Port Provisioning and Release options [8] and [9] are the latest inventory features.) """
import sys
import uuid
import datetime
# Import SQLAlchemy types needed for queries (like not_) but exclude Engine/Session setup
from sqlalchemy.sql.expression import not_

# --- IMPORT BASE CONFIGURATION AND SESSION FACTORY ---
# Import SessionLocal (the DB session factory), SERVICE_TYPES, and the new validation utility
from cli_base import SessionLocal, SERVICE_TYPES, validation_service_type

# Import models needed for querying
from network_inventory_models import (
    Customer, 
    FabricService, 
    Port, 
    Device, 
    # Base is no longer needed here as it is imported and bound in cli_base.py
)

# NOTE: The old SERVICE_TYPES definition and the entire 'SQLAlchemy Engine and Session Setup'
# block have been removed, as that functionality is now provided by cli_base.py.

# --- CLI Helpers ---

def get_session_or_fail():
    """Helper to retrieve a session by calling the imported SessionLocal factory."""
    session = None
    try:
        # Calling SessionLocal() attempts to connect via the engine bound in cli_base.py
        session = SessionLocal()
        return session
    except Exception as e:
        # This catch is usually for initialization/connection failure
        # SessionLocal will raise a RuntimeError if the engine failed to initialize in cli_base.py
        print(f"\n❌ DATABASE CONNECTION ERROR: Could not establish a session.")
        print("Please ensure your database is running and configured correctly. Run option [4] to initialize schema.")
        print("Details: Check your database configuration and status.")
        return None

# --- CLI Functions ---

def create_new_customer():
    """CLI handler for [1] Customer: Create New"""
    session = get_session_or_fail()
    if not session: return

    name = input("Enter Customer Name: ")
    account_id = input("Enter unique Account ID (e.g., CUST001): ")
    
    try:
        new_customer = Customer(
            customer_name=name,
            account_id=account_id
        )
        session.add(new_customer)
        session.commit()
        print(f"\n✅ Customer '{name}' created successfully with ID: {account_id}")
    except Exception as e:
        session.rollback()
        if "unique constraint" in str(e):
            print(f"\n❌ FAILED to create customer. Account ID '{account_id}' already exists.")
        else:
            print(f"\n❌ FAILED to create customer. Error: {e}")
    finally:
        if session:
            session.close() 

def list_all_customers():
    """CLI handler for [2] Customer: List All (with Service Count)"""
    session = get_session_or_fail()
    if not session: return
    
    try:
        customers = session.query(Customer).all()
        
        if not customers:
            print("\nℹ️ No customers found. Run option 13 to seed initial data.")
            return

        print("\n--- ALL CUSTOMERS ---")
        # Column headers
        print(f"{'Account ID':<15} | {'Customer Name':<30} | {'Services':<10}")
        print("-" * 55)
        
        for cust in customers:
            service_count = session.query(FabricService).filter(FabricService.customer_id == cust.customer_id).count()
            print(f"{cust.account_id:<15} | {cust.customer_name:<30} | {service_count:<10}")
        print("---------------------\n")
        
    except Exception as e:
        print(f"\n❌ FAILED to list customers. Error: {e}")
    finally:
        if session:
            session.close()

def view_customer_details():
    """CLI handler for [3] Customer: View Details by Account ID"""
    session = get_session_or_fail()
    if not session: return
    
    account_id = input("Enter the Account ID of the customer to view: ").strip()
    
    try:
        customer = session.query(Customer).filter(Customer.account_id == account_id).one_or_none()

        if customer is None:
            print(f"\n❌ Customer with Account ID '{account_id}' not found.")
            return

        # 1. Display Customer Details
        print("\n--- CUSTOMER DETAILS ---")
        print(f"ID:       {customer.account_id}")
        print(f"Name:         {customer.customer_name}")
        print(f"Database UUID: {customer.customer_id}")
        print("------------------------")

        # 2. Display Associated Fabric Services
        services = session.query(FabricService).filter(FabricService.customer_id == customer.customer_id).all()
        
        if services:
            print(f"--- ASSOCIATED SERVICES ({len(services)}) ---")
            for service in services:
                # Safely handle nullable route_target
                rt_display = service.route_target if service.route_target is not None else "N/A"
                print(f"  Service Name:   {service.service_name}")
                print(f"  Alias:          {service.service_alias}")
                print(f"  Type:           {service.service_type}")
                print(f"  RT:             {rt_display}")
                description = getattr(service, 'service_description', None)
                description_display = ((description[:40] + '...') if description and len(description) > 40 else description) if description else 'N/A'
                print(f"  Description:    {description_display}")
                print("  ---")
        else:
            print("--- ASSOCIATED SERVICES (0) ---")
            print("  This customer has no active fabric services.")
        
        print("--------------------------------\n")

    except Exception as e:
        print(f"\n❌ FAILED to retrieve customer details. Error: {e}")
    finally:
        if session:
            session.close()

def create_new_fabric_service():
    """
    CLI handler for [4] Service: Create New Fabric Service.
    Includes interactive selection for Customer Account ID and Service Type.
    """
    session = get_session_or_fail()
    if not session: return

    print("\n--- Create New Fabric Service ---")
    
    # 1. Interactive Customer Selection
    customers = session.query(Customer).all()
    if not customers:
        print("\n❌ No customers found. Please create a customer first (Option 1 or 13).")
        session.close()
        return

    print("\nAvailable Customers:")
    for cust in customers:
        print(f" - [{cust.account_id}] {cust.customer_name}")
    print("--------------------")

    account_id = input("Enter Customer Account ID (to link service): ").strip()
    
    customer = session.query(Customer).filter(Customer.account_id == account_id).one_or_none()
    
    if customer is None:
        print(f"\n❌ Customer with Account ID '{account_id}' not found.")
        session.close()
        return

    # 2. Get Service Name and Alias
    service_name = input("Enter Service Name (e.g., VPN-01): ").strip()
    service_alias = input("Enter Service Alias: ").strip()

    # 3. Interactive Service Type Selection
    # Use the utility function for service type validation and selection
    selected_service_type = validation_service_type(SERVICE_TYPES)
    
    if selected_service_type is None:
        # Validation utility handles prompting/errors and returns None on cancellation or major failure.
        session.close()
        return
        
    print(f"Selected Service Type: {selected_service_type}")

    # 4. Get Description
    service_description = input("Enter Service Description: ").strip()
    
    try:
        # Check if service name already exists (Unique constraint check)
        existing_service = session.query(FabricService).filter(FabricService.service_name == service_name).one_or_none()
        if existing_service:
            print(f"\n❌ FAILED to create service. Service Name '{service_name}' already exists.")
            session.close()
            return
            
        # Create the new service instance
        new_service = FabricService(
            customer_id=customer.customer_id,
            service_name=service_name,
            service_alias=service_alias,
            service_type=selected_service_type, # Use the selected type
            service_description=service_description,
            # route_target is set to None, relying on DB defaults/triggers if available
        )
        
        session.add(new_service)
        session.commit()
        
        # After commit, the service_id (UUID) should be populated
        print(f"\n✅ Fabric Service '{service_name}' created successfully.")
        print(f"  Linked to Customer: {customer.customer_name} ({account_id})")
        print(f"  Service Type: {selected_service_type}")
        print(f"  Service UUID: {new_service.service_id}")
        
    except Exception as e:
        session.rollback()
        error_msg = str(e)
        if "foreign key constraint" in error_msg:
             print("\n❌ FAILED to create service. Check foreign key constraints.")
        elif "unique constraint" in error_msg and "fabric_service_service_name_key" in error_msg:
             print(f"\n❌ FAILED to create service. Service Name '{service_name}' already exists.")
        else:
             print(f"\n❌ FAILED to create fabric service. Error: {e}")
    finally:
        session.close()

def list_all_services():
    """
    CLI handler for [5] Service: List All Services.
    Retrieves all fabric services and their associated customer details.
    """
    session = get_session_or_fail()
    if not session: return

    try:
        # Query FabricService and join with Customer to get related data efficiently
        services_data = session.query(
            FabricService,
            Customer.customer_name,
            Customer.account_id
        ).join(Customer, FabricService.customer_id == Customer.customer_id).all()

        if not services_data:
            print("\nℹ️ No fabric services found.")
            return

        print(f"\n--- ALL FABRIC SERVICES ({len(services_data)}) ---")
        
        # Column headers
        print(f"{'Service Name':<15} | {'Type':<10} | {'Customer Name':<25} | {'Account ID':<10} | {'Route Target':<15}")
        print("-" * 80)

        for service, customer_name, account_id in services_data:
            # Check if route_target is None and provide a default string ("N/A")
            rt_display = service.route_target if service.route_target is not None else "N/A"
            
            print(f"{service.service_name:<15} | {service.service_type:<10} | {customer_name:<25} | {account_id:<10} | {rt_display:<15}")

        print("--------------------------------------------------------------------------------\n")
        
    except Exception as e:
        print(f"\n❌ FAILED to list services. Error: {e}")
    finally:
        if session:
            session.close()

def list_all_assigned_ports():
    """
    CLI handler for [6] Inventory: List ALL Assigned Ports.
    """
    session = get_session_or_fail()
    if not session: return

    # 1. Get user input for device filtering
    device_name_filter = input(
        "Enter Device Name to filter (leave blank for all devices): "
    ).strip()

    print("\n--- Listing Assigned Ports ---")

    try:
        assigned_statuses = ['Assigned', 'Active']
        
        # Explicitly select only the attributes needed for display and known to exist
        query = (
            session.query(
                Port.port_name,
                Port.port_service_status,
                Port.port_type,
                Port.port_description,
                Device.device_name,
                FabricService.service_name
            ) 
            # Join Port (device_id) to Device (device_id)
            .join(Device, Port.device_id == Device.device_id)
            # Join Port (service_id) to FabricService (service_id). 
            .join(FabricService, Port.service_id == FabricService.service_id) 
            
            # --- APPLY ASSIGNED PORT RULES ---
            .filter(Port.port_type == 'Fabric Port')
            .filter(Port.port_service_status.in_(assigned_statuses))
        )

        # 2. Apply device filter if provided
        if device_name_filter:
            query = query.filter(Device.device_name.ilike(f'%{device_name_filter}%'))
            print(f"Filter applied: Device Name containing '{device_name_filter}'")

        # Execute the query, returning tuples of selected attributes
        results = query.all()

        if not results:
            print("\nℹ️ No assigned ports found matching the criteria.")
            return

        print(f"--- ASSIGNED PORTS ({len(results)}) ---")
        
        # Column headers
        print(f"{'Device Name':<15} | {'Port Name':<10} | {'Status':<15} | {'Port Type':<10} | {'Service Name':<15} | {'Description':<25}")
        print("-" * 95)

        # Unpack the tuple of attributes from the explicit query result
        for port_name, port_status, port_type, port_description, device_name, service_name in results:
            
            # Truncate description for clean display
            link_description = port_description if port_description else "No Port Description"
            description_display = (link_description[:22] + '...') if len(link_description) > 25 else link_description
            
            print(f"{device_name:<15} | {port_name:<10} | {port_status:<15} | {port_type:<10} | {service_name:<15} | {description_display:<25}")

        print("-----------------------------------------------------------------------------------------------\n")
        
    except Exception as e:
        print(f"\n❌ FAILED to list assigned ports. Error: {e}")
    finally:
        if session:
            session.close()

def list_all_unassigned_ports():
    """
    CLI handler for [7] Inventory: List ALL Unassigned Ports (Available Ports).
    """
    session = get_session_or_fail()
    if not session: return

    # 1. Get user input for device filtering
    device_name_filter = input(
        "Enter Device Name to filter (leave blank for all devices): "
    ).strip()

    print("\n--- Listing Available Ports ---")

    try:
        # Define the set of valid statuses for an available port
        available_statuses = ['Available', 'Ready for use']
        
        # Explicitly select only the attributes needed for display and known to exist
        query = (
            session.query(
                Port.port_id, # Include port_id for potential downstream use (like option 10)
                Port.port_name,
                Port.port_service_status,
                Port.port_type,
                Port.port_description,
                Device.device_name
            )
            # Explicitly join Port (device_id) to Device (device_id)
            .join(Device, Port.device_id == Device.device_id)
            # Filter 1: Status is IN the available_statuses list
            .filter(Port.port_service_status.in_(available_statuses))
            # Filter 2: Port Type is 'Physical'
            .filter(Port.port_type == 'Physical')
        )

        # 2. Apply device filter if provided
        if device_name_filter:
            query = query.filter(Device.device_name.ilike(f'%{device_name_filter}%'))
            print(f"Filter applied: Device Name containing '{device_name_filter}'")

        # Execute the query, returning tuples of selected attributes
        # Store results as a list of dictionaries for easier lookup later
        results = [
            {
                "port_id": str(r[0]),
                "port_name": r[1],
                "port_service_status": r[2],
                "port_type": r[3],
                "port_description": r[4],
                "device_name": r[5]
            }
            for r in query.all()
        ]

        if not results:
            print("\nℹ️ No available ports found matching the criteria.")
            return

        print(f"--- AVAILABLE PORTS ({len(results)}) ---")
        
        # Column headers
        # NOTE: We use index (IDX) here to make selection easier for the user
        print(f"{'IDX':<5} | {'Device Name':<15} | {'Port Name':<10} | {'Status':<15} | {'Port Type':<10} | {'Description':<25}")
        print("-" * 85)

        # Display results with index
        for i, port in enumerate(results):
            port_description = port['port_description'] if port['port_description'] else "No Port Description"
            description_display = (port_description[:22] + '...') if len(port_description) > 25 else port_description
            
            print(
                f"{i:<5} | {port['device_name']:<15} | {port['port_name']:<10} | "
                f"{port['port_service_status']:<15} | {port['port_type']:<10} | "
                f"{description_display:<25}"
            )
        
        print("----------------------------------------------------------------------------------\n")
        
    except Exception as e:
        print(f"\n❌ FAILED to list available ports. Error: {e}")
    finally:
        if session:
            session.close()

def provision_port_to_service():
    """
    CLI handler for [8] Inventory: Provision Port to Service.
    1. Select Customer
    2. Select Fabric Service
    3. Select Unassigned Port
    4. Update Port to link to Service
    """
    session = get_session_or_fail()
    if not session: return

    try:
        print("\n--- Port Provisioning Wizard (Step 1 of 3: Select Customer) ---")
        
        # --- STEP 1: SELECT CUSTOMER ---
        account_id = input("Enter Customer Account ID (e.g., CUST001): ").strip()
        customer = session.query(Customer).filter(Customer.account_id == account_id).one_or_none()

        if customer is None:
            print(f"\n❌ Error: Customer with Account ID '{account_id}' not found.")
            return

        # --- STEP 2: SELECT FABRIC SERVICE ---
        print(f"\n--- Port Provisioning Wizard (Step 2 of 3: Select Service for {customer.customer_name}) ---")
        services = session.query(FabricService).filter(FabricService.customer_id == customer.customer_id).all()
        
        if not services:
            print(f"\n❌ Error: Customer '{customer.customer_name}' has no fabric services. Please create one (Option 4).")
            return

        print("Available Services for Provisioning:")
        service_map = {}
        # Display services and map names for selection
        for i, service in enumerate(services):
            print(f"  [{i+1}] {service.service_name} (Type: {service.service_type})")
            service_map[i+1] = service

        service_choice = input(f"Enter number [1-{len(services)}] of the Service to provision the port to: ").strip()
        
        try:
            service_choice_int = int(service_choice)
            selected_service = service_map.get(service_choice_int)
        except ValueError:
            selected_service = None
            
        if selected_service is None:
            print(f"\n❌ Invalid service selection: '{service_choice}'. Operation cancelled.")
            return

        print(f"✅ Selected Service: {selected_service.service_name}")
        
        # --- STEP 3: SELECT UNASSIGNED PORT ---
        print("\n--- Port Provisioning Wizard (Step 3 of 3: Select Available Port) ---")
        
        available_statuses = ['Available', 'Ready for use']
        # Query for unassigned ports
        available_ports_query = (
            session.query(
                Port.port_id,
                Port.port_name,
                Device.device_name
            )
            .join(Device, Port.device_id == Device.device_id)
            .filter(Port.port_service_status.in_(available_statuses))
            .filter(Port.port_type == 'Physical')
            .all() # Execute the query
        )
        
        if not available_ports_query:
            print("\n❌ Error: No Physical ports are currently 'Available' or 'Ready for use'. Cannot provision.")
            return

        # Prepare a list of dictionaries for display and lookup
        available_ports = [
            {
                "port_id": str(r[0]), 
                "port_name": r[1], 
                "device_name": r[2]
            } 
            for r in available_ports_query
        ]
        
        print(f"Available Ports for Provisioning ({len(available_ports)} found):")
        
        for i, port in enumerate(available_ports):
             print(f"  [{i+1}] Device: {port['device_name']}, Port: {port['port_name']}")

        port_choice = input(f"Enter number [1-{len(available_ports)}] of the Port to provision: ").strip()
        
        try:
            port_choice_int = int(port_choice) - 1
            selected_port_data = available_ports[port_choice_int] if 0 <= port_choice_int < len(available_ports) else None
        except (ValueError, IndexError):
            selected_port_data = None

        if selected_port_data is None:
            print(f"\n❌ Invalid port selection: '{port_choice}'. Operation cancelled.")
            return
            
        # Retrieve the actual Port ORM object
        selected_port_obj = session.query(Port).filter(Port.port_id == uuid.UUID(selected_port_data['port_id'])).one()

        print(f"✅ Selected Port: {selected_port_data['device_name']} / {selected_port_data['port_name']}")

        # --- STEP 4: PERFORM UPDATE AND COMMIT ---
        
        print("\n--- Applying Provisioning Changes... ---")
        
        # Update the Port object
        selected_port_obj.service_id = selected_service.service_id
        selected_port_obj.port_service_status = 'Assigned' # Move from Available/Ready to Assigned
        selected_port_obj.port_type = 'Fabric Port' # Change type to reflect its new service role
        selected_port_obj.updated_at = datetime.datetime.now() # Update timestamp

        session.commit()
        
        print("\n=======================================================")
        print(f"✅ SUCCESS: Port Provisioned!")
        print(f"  Port: {selected_port_data['device_name']}/{selected_port_data['port_name']}")
        print(f"  Status: Assigned")
        print(f"  Linked Service: {selected_service.service_name} ({customer.account_id})")
        print("=======================================================\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ FAILED to provision port. An unexpected error occurred: {e}")
    finally:
        if session:
            session.close()

def release_port_from_service():
    """
    CLI handler for [9] Inventory: Release Port from Service.
    1. Select Customer
    2. Select Fabric Service
    3. Select Assigned Port
    4. Update Port to release it back to 'Ready for use'
    """
    session = get_session_or_fail()
    if not session: return

    try:
        print("\n--- Port Release Wizard (Step 1 of 3: Select Customer) ---")
        
        # --- STEP 1: SELECT CUSTOMER ---
        # Reuse list_all_customers output format for convenience
        # NOTE: This calls a function that opens and closes its own session.
        # It's less efficient but maintains modularity for the CLI display.
        list_all_customers() 
        account_id = input("Enter Customer Account ID (e.g., CUST001): ").strip()
        customer = session.query(Customer).filter(Customer.account_id == account_id).one_or_none()

        if customer is None:
            print(f"\n❌ Error: Customer with Account ID '{account_id}' not found. Operation cancelled.")
            return

        # --- STEP 2: SELECT FABRIC SERVICE ---
        print(f"\n--- Port Release Wizard (Step 2 of 3: Select Service for {customer.customer_name}) ---")
        services = session.query(FabricService).filter(FabricService.customer_id == customer.customer_id).all()
        
        if not services:
            print(f"\n❌ Error: Customer '{customer.customer_name}' has no fabric services. Operation cancelled.")
            return

        print("Available Services to Release Ports From:")
        service_map = {}
        # Display services and map names for selection
        for i, service in enumerate(services):
            port_count = session.query(Port).filter(Port.service_id == service.service_id).count()
            print(f"  [{i+1}] {service.service_name} (Type: {service.service_type}, Assigned Ports: {port_count})")
            service_map[i+1] = service

        service_choice = input(f"Enter number [1-{len(services)}] of the Service to release a port from: ").strip()
        
        try:
            service_choice_int = int(service_choice)
            selected_service = service_map.get(service_choice_int)
        except ValueError:
            selected_service = None
            
        if selected_service is None:
            print(f"\n❌ Invalid service selection: '{service_choice}'. Operation cancelled.")
            return

        print(f"✅ Selected Service: {selected_service.service_name}")
        
        # --- STEP 3: SELECT ASSIGNED PORT ---
        print("\n--- Port Release Wizard (Step 3 of 3: Select Assigned Port) ---")
        
        assigned_statuses = ['Assigned', 'Active']
        # Query for ports currently assigned to the selected service
        assigned_ports_query = (
            session.query(
                Port.port_id,
                Port.port_name,
                Device.device_name
            )
            .join(Device, Port.device_id == Device.device_id)
            .filter(Port.service_id == selected_service.service_id)
            .filter(Port.port_service_status.in_(assigned_statuses))
            .all() # Execute the query
        )
        
        if not assigned_ports_query:
            print(f"\n❌ Error: No ports are currently assigned to service '{selected_service.service_name}'. Operation cancelled.")
            return

        # Prepare a list of dictionaries for display and lookup
        assigned_ports = [
            {
                "port_id": str(r[0]), 
                "port_name": r[1], 
                "device_name": r[2]
            } 
            for r in assigned_ports_query
        ]
        
        print(f"Assigned Ports to Release ({len(assigned_ports)} found):")
        
        for i, port in enumerate(assigned_ports):
             print(f"  [{i+1}] Device: {port['device_name']}, Port: {port['port_name']}")

        port_choice = input(f"Enter number [1-{len(assigned_ports)}] of the Port to release: ").strip()
        
        try:
            port_choice_int = int(port_choice) - 1
            selected_port_data = assigned_ports[port_choice_int] if 0 <= port_choice_int < len(assigned_ports) else None
        except (ValueError, IndexError):
            selected_port_data = None

        if selected_port_data is None:
            print(f"\n❌ Invalid port selection: '{port_choice}'. Operation cancelled.")
            return
            
        # Retrieve the actual Port ORM object
        selected_port_obj = session.query(Port).filter(Port.port_id == uuid.UUID(selected_port_data['port_id'])).one()

        print(f"✅ Selected Port for Release: {selected_port_data['device_name']} / {selected_port_data['port_name']}")

        # --- STEP 4: PERFORM UPDATE AND COMMIT ---
        
        print("\n--- Applying Release Changes... ---")
        
        # Update the Port object to release it
        selected_port_obj.service_id = None # Remove service link
        selected_port_obj.port_service_status = 'Ready for use' # Set status to available
        selected_port_obj.port_type = 'Physical' # Change type back to Physical/unassigned
        selected_port_obj.updated_at = datetime.datetime.now() # Update timestamp

        session.commit()
        
        print("\n=======================================================")
        print(f"✅ SUCCESS: Port Released!")
        print(f"  Port: {selected_port_data['device_name']}/{selected_port_data['port_name']}")
        print(f"  New Status: Ready for use")
        print(f"  Released from Service: {selected_service.service_name}")
        print("=======================================================\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ FAILED to release port. An unexpected error occurred: {e}")
    finally:
        if session:
            session.close()

# Removed the commented out Fabric Connection related functions (Options [10] and [11]).