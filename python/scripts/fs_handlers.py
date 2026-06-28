""" File Name: 'fs_handlers.py' date: '2025-11-30 20:38 MST' (Update: Display Customer List with Service Count and without IDs) """
# fs_handlers.py
"""
Contains all the application logic, input handling, and database operations
for the Fabric Service Manager CLI.
"""
import uuid
from typing import Optional, List, Tuple

# Assuming db_operations.py is in the same directory
try:
    import db_operations as dbo # Reusing methods from db_operations
    # Importing models for type hinting and context
    from python.scripts.api_model import Customer, Port, FabricService 
except ImportError:
    print("Error: Could not import database modules.")
    # In a real app, this would be a critical failure, but we allow import error handling in fs_cli.py

# ======================================================================
# --- HELPER FUNCTIONS ---
# ======================================================================

def safe_uuid(s: str) -> Optional[uuid.UUID]:
    """Tries to convert a string to a UUID, returning None on failure."""
    try:
        return uuid.UUID(s)
    except (ValueError, AttributeError):
        return None

def display_customers_and_select() -> Optional[Customer]:
    """
    Displays all customers with their service count (new format) and prompts 
    the user to select one.
    """
    # Now returns List[Tuple[Customer object, service_count]]
    customer_data_list: List[Tuple[Customer, int]] = dbo.get_all_customers() 
    customers: List[Customer] = [data[0] for data in customer_data_list] # Extract Customer objects
    
    if not customers:
        print("\nNo customers found.")
        return None
    
    print("\n--- Available Customers ---")
    
    # Store selected customer objects for index mapping
    display_customers = [] 
    
    for i, (c, count) in enumerate(customer_data_list, 1):
        # New Display Format: Name (Account ID) | Services: [Count]
        print(f"{i}. {c.customer_name} (Account: {c.account_id}) | Services: {count}")
        display_customers.append(c)

    print("-" * 60)

    while True:
        try:
            selection = input("Enter the number of the Customer (or '0' to cancel): ").strip()
            if selection == '0':
                return None
            
            idx = int(selection) - 1
            if 0 <= idx < len(display_customers):
                return display_customers[idx]
            else:
                print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def display_services_and_select(customer_id: uuid.UUID) -> Optional[FabricService]:
    """
    Displays services associated with a customer and prompts the user to select one.
    This assumes a dbo.get_fabric_services_by_customer_id method exists.
    """
    # Assuming dbo.get_fabric_services_by_customer_id method exists
    services = dbo.get_fabric_services_by_customer_id(customer_id)
    if not services:
        print("\nNo fabric services found for this customer.")
        return None
    
    print("\n--- Available Fabric Services ---")
    for i, s in enumerate(services, 1):
        short_id = str(s.service_id)[:8]
        print(f"{i}. {s.service_name} ({s.service_alias}) [ID: {short_id}...] | Type: {s.service_type}")
    print("-" * 60)

    while True:
        try:
            selection = input("Enter the number of the Service (or '0' to cancel): ").strip()
            if selection == '0':
                return None
            
            idx = int(selection) - 1
            if 0 <= idx < len(services):
                return services[idx]
            else:
                print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
# ======================================================================
# --- MENU HANDLERS: CUSTOMER CRUD (Option 1, 2, 7) ---
# ======================================================================

def handle_create_customer():
    """Handles creating a new customer via user input."""
    print("\n--- Create New Customer ---")
    name = input("Enter Customer Name: ").strip()
    account_id = input("Enter Account ID (e.g., ACC-001): ").strip()

    if not name or not account_id:
        print("Customer Name and Account ID cannot be empty.")
        return

    # Reuses dbo.create_customer
    customer = dbo.create_customer(name, account_id)
    if customer:
        print(f"\nSUCCESS: Customer '{customer.customer_name}' created with ID {customer.customer_id}.")
    else:
        print("\nFAILURE: Failed to create customer. (Check if Account ID already exists).")

def handle_view_all_customers():
    """Handles viewing all customers, now including service count."""
    # Now returns List[Tuple[Customer object, service_count]]
    customer_data_list: List[Tuple[Customer, int]] = dbo.get_all_customers() 

    print("\n" + "="*85)
    print("                 CURRENT CUSTOMER DATABASE")
    print("="*85)
    if not customer_data_list:
        print("No customers found.")
        return

    # Column formatting for clean output, including Service Count
    print(f"{'ID':<38} | {'Name':<25} | {'Account ID':<10} | {'Services':<10}")
    print("-" * 85)
    for c, count in customer_data_list:
        print(f"{str(c.customer_id):<38} | {c.customer_name:<25} | {c.account_id:<10} | {count:<10}")
    print("="*85)


def handle_delete_customer():
    """
    Handles deleting a customer, prompting to delete all associated fabric services first.
    Uses the display_customers_and_select helper which shows service counts.
    """
    print("\n--- Delete Customer ---")
    
    # Step 1: Select Customer
    customer = display_customers_and_select()
    if not customer:
        print("Deletion cancelled.")
        return

    customer_id = customer.customer_id
    customer_name = customer.customer_name
    
    # We must re-check the count here as we need the raw count for the prompt
    associated_services = dbo.get_fabric_services_by_customer_id(customer_id)
    service_count = len(associated_services)

    print(f"\nCustomer '{customer_name}' has {service_count} associated Fabric Service(s).")
    
    # Step 2: Prompt to delete associated services
    if service_count > 0:
        confirmation = input(f"Do you want to DELETE all {service_count} associated services before deleting the customer? (y/N): ").strip().lower()
        
        if confirmation == 'y':
            # Assuming dbo.delete_services_by_customer_id exists
            deleted_count = dbo.delete_services_by_customer_id(customer_id)
            print(f"INFO: Successfully deleted {deleted_count} Fabric Service(s) associated with {customer_name}.")
        else:
            print("Deletion cancelled. Cannot delete customer if associated services exist.")
            return

    # Step 3: Final confirmation and Customer deletion
    final_confirmation = input(f"Are you absolutely sure you want to DELETE Customer '{customer_name}'? (Y/n): ").strip().lower()

    if final_confirmation == 'y':
        # Assuming dbo.delete_customer_by_id exists
        success = dbo.delete_customer_by_id(customer_id)
        if success:
            print(f"\nSUCCESS: Customer '{customer_name}' deleted.")
        else:
            print(f"\nFAILURE: Could not delete customer '{customer_name}'. It may no longer exist.")
    else:
        print("Customer deletion cancelled.")


# ======================================================================
# --- MENU HANDLERS: FABRIC SERVICE CRUD (Option 3, 4, 8) ---
# ======================================================================

def handle_create_fabric_service():
    """Handles creating a new Fabric Service."""
    print("\n--- Create New Fabric Service ---")

    # Step 1: Select Customer to associate the service with
    # Uses updated display_customers_and_select
    customer = display_customers_and_select()
    if not customer:
        print("Service creation cancelled. Customer selection is mandatory.")
        return

    # Step 2: Get Service details
    service_name = input("Enter Service Name (Unique ID, e.g., EPL-ACME-001): ").strip()
    service_alias = input("Enter Service Alias (Friendly Name, e.g., ACME-NYC-LA): ").strip()
    service_type = input("Enter Service Type (e.g., E-line, IPVPN, L3VPN): ").strip()
    description = input("Enter Service Description (Optional): ").strip() or None
    route_target = input("Enter Route Target (Optional, e.g., 65000:100): ").strip() or None

    if not all([service_name, service_alias, service_type]):
        print("Service Name, Alias, and Type cannot be empty. Creation cancelled.")
        return

    # Reuses dbo.create_fabric_service
    service = dbo.create_fabric_service(
        customer_id=customer.customer_id,
        service_name=service_name,
        service_alias=service_alias,
        service_type=service_type,
        service_description=description,
        route_target=route_target,
        health_status=4 # Default to Unknown
    )

    if service:
        print(f"\nSUCCESS: Service '{service.service_name}' created for customer {customer.customer_name} with ID {service.service_id}.")
    else:
        print("\nFAILURE: Failed to create fabric service. (Check if Service Name already exists).")


def handle_view_all_fabric_services():
    """Handles viewing all fabric services."""
    # Reuses dbo.get_all_fabric_services
    services: List[Tuple[str, str, str, str, Optional[int]]] = dbo.get_all_fabric_services()
    print("\n" + "="*80)
    print("                 CURRENT FABRIC SERVICES DATABASE")
    print("="*80)
    if not services:
        print("No fabric services found.")
        return

    HEALTH_MAP = {1: "Green", 2: "Amber", 3: "Red", 4: "Unknown"}

    # Column formatting for clean output
    print(f"{'Customer':<15} | {'Service Name':<20} | {'Alias':<20} | {'Type':<10} | {'Health':<10}")
    print("-" * 80)
    for cust_name, name, alias, svc_type, health_int in services:
        health_status = HEALTH_MAP.get(health_int, 'N/A')
        print(f"{cust_name:<15} | {name:<20} | {alias:<20} | {svc_type:<10} | {health_status:<10}")
    print("="*80)


def handle_delete_fabric_service():
    """
    Handles deleting a specific fabric service after selecting the parent customer.
    Assumes dbo.delete_fabric_service_by_id exists.
    """
    print("\n--- Delete Fabric Service ---")
    
    # Step 1: Select Customer (Uses updated display_customers_and_select)
    customer = display_customers_and_select()
    if not customer:
        print("Deletion cancelled.")
        return
    
    # Step 2: Select Fabric Service associated with the customer
    service = display_services_and_select(customer.customer_id)
    if not service:
        print("Deletion cancelled. No service selected.")
        return

    service_id = service.service_id
    service_name = service.service_name
    
    # Step 3: Final confirmation and Service deletion
    confirmation = input(f"Are you sure you want to DELETE Fabric Service '{service_name}' for customer '{customer.customer_name}'? (y/N): ").strip().lower()

    if confirmation == 'y':
        # Assuming dbo.delete_fabric_service_by_id exists
        success = dbo.delete_fabric_service_by_id(service_id)
        if success:
            print(f"\nSUCCESS: Fabric Service '{service_name}' deleted.")
        else:
            print(f"\nFAILURE: Could not delete service '{service_name}'. It may no longer exist.")
    else:
        print("Fabric Service deletion cancelled.")


# ======================================================================
# --- MENU HANDLERS: ASSIGNMENT (Option 5 & 6) ---
# ======================================================================
# NOTE: These remain placeholders until the database model for assignments
# is reintroduced in db_setup.py and db_operations.py.

def handle_assign_port_to_service_placeholder():
    """Placeholder for Port-to-Service assignment logic."""
    print("\n---------------------------------------------------------")
    print("   Assignment Logic Required: Port to Fabric Service")
    print("---------------------------------------------------------")
    print("The database structure for linking Ports and Fabric Services")
    print("needs to be defined before implementing the assignment logic here.")
    print("---------------------------------------------------------")

def handle_view_assignments_placeholder():
    """Placeholder for viewing assignments logic."""
    print("\n---------------------------------------------------------")
    print("   View Assignment Logic Required")
    print("---------------------------------------------------------")
    print("Cannot view assignments until the assignment feature (Option 5) ")
    print("is fully implemented with its database backend.")
    print("---------------------------------------------------------")