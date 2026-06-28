""" File Name: 'fs_cli.py' date: '2025-11-30 23:55 MST' (Added Fabric Connection assignment handlers) """
# fs_cli.py
"""
The Command Line Interface for the Network Inventory Database Management system.
"""
import sys
import uuid
from typing import Optional, List, Tuple
from datetime import datetime

# Import database setup functions (for option 1) and CRUD operations
from cli_base import Engine
import db_operations as db
from python.scripts.api_model import create_database_tables, Device # Need Device for create

# --- Helper Functions ---

def print_header(title: str):
    """Prints a styled header for CLI screens."""
    print("-" * 50)
    print(f"{title}")
    print("-" * 50)

def get_input(prompt: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    """Helper function for consistent user input with optional requirement enforcement."""
    full_prompt = f"{prompt}{f' [{default}]' if default is not None else ''}: "
    while True:
        value = input(full_prompt).strip()
        if value:
            return value
        elif not required:
            return default
        else:
            print("This field is required. Please enter a value.")

def display_table(headers: list, data: list):
    """Dynamically formats and prints data in a table structure."""
    if not data:
        print("\nNo records found in the database.")
        return

    # Determine maximum width for each column
    # Ensure headers list and the number of elements in data rows match for accurate width calculation
    data_width = len(data[0]) if data else 0
    num_cols = min(len(headers), data_width)

    col_widths = [len(header) for header in headers[:num_cols]]
    
    for row in data:
        for i in range(num_cols):
            item = row[i]
            # Ensure UUIDs are strings for length calculation
            col_widths[i] = max(col_widths[i], len(str(item)))

    # Print Header
    header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(num_cols))
    print("\n" + header_line)
    print("-" * len(header_line))

    # Print Data Rows
    for row in data:
        row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(num_cols))
        print(row_line)
    print("-" * len(header_line))

# --- Database Setup Handler ---

def handle_setup_db():
    """Handles option 1: Setup Database Tables."""
    try:
        create_database_tables(Engine)
    except Exception as e:
        print(f"Failed to set up database: {e}")

# --- Customer Handlers ---

def handle_create_customer():
    """Handles option 2: Create New Customer."""
    print_header("Create New Customer")
    name = get_input("Customer Name")
    account_id = get_input("Account ID")

    customer = db.create_customer(name, account_id)
    if customer:
        print(f"\nSUCCESS: Customer '{customer.customer_name}' created with ID: {customer.customer_id}")
    else:
        print("\nFAILED: Customer creation failed (check logs for details).")

def handle_view_all_customers():
    """Handles option 3: View All Customers."""
    print_header("All Customers")
    customers_data = db.get_all_customers()
    
    # Define the headers based on the query results
    headers = ["Account ID", "Customer Name", "Customer UUID (first 8 chars)", "Services Count"]
    
    # Process the tuple results for display
    display_data = []
    for account_id, name, customer_id, service_count in customers_data:
        display_data.append([
            account_id,
            name,
            str(customer_id)[:8],  # Safely convert UUID to string and slice
            service_count
        ])

    display_table(headers, display_data)

def handle_search_customers():
    """Handles option 4: Search Customers (currently not implemented)."""
    print_header("Search Customers")
    print("This function is not yet implemented.")

# --- Device Handlers ---

def handle_create_device():
    """Handles option 5: Create New Device."""
    print_header("Create New Device")
    
    # Mandatory fields based on db_setup.py
    device_name = get_input("Device Name (e.g., PE-RTR-NYC-01)")
    location = get_input("Location")
    device_role = get_input("Device Role (e.g., PE, Core, Access)")
    device_vendor = get_input("Device Vendor (e.g., Cisco, Juniper)")
    
    # Optional fields (Placeholder for full implementation in db_operations.py)
    # Note: Full create_device logic needs to be implemented in db_operations.py
    print("\n[NOTE: Full Device creation logic is a placeholder until implemented in db_operations.py]")
    
    # Example placeholder return:
    print(f"\nPLACEHOLDER: Device '{device_name}' would be created.")

def handle_view_all_devices():
    """Handles option 6: View All Devices."""
    print_header("All Devices")
    devices = db.get_all_devices()

    headers = ["Device Name", "Location", "Role", "Vendor", "ID (first 8 chars)"]
    display_data = []
    
    for d in devices:
        display_data.append([
            d.device_name,
            d.location,
            d.device_role,
            d.device_vendor,
            str(d.device_id)[:8]
        ])
    
    display_table(headers, display_data)


# --- Port Handlers ---

def handle_create_port():
    """Handles option 8: Create New Port (currently not implemented)."""
    print_header("Create New Port")
    print("This function is not yet implemented.")

def handle_view_all_ports_detailed():
    """Handles option 9: View All Ports (Detailed)."""
    print_header("All Ports (Detailed)")
    # Returns (device_name, port_name, port_speed, port_service_status, port_type, service_id)
    ports_data = db.get_all_ports_with_device_details()
    
    # We only want to display the first 5 columns for brevity, excluding the UUID
    display_data = [row[:5] for row in ports_data]
    headers = ["Device Name", "Port Name", "Speed", "Status", "Type"]
    
    display_table(headers, display_data)


# --- Fabric Service Handlers ---

def handle_create_fabric_service():
    """Handles option 10: Create New Fabric Service (currently not implemented)."""
    print_header("Create New Fabric Service")
    print("This function is not yet implemented.")

def handle_view_all_fabric_services():
    """Handles option 11: View All Fabric Services."""
    print_header("All Fabric Services")
    
    # Returns (customer_name, service_name, service_alias, service_type, health_status, service_id, port_count)
    services_data_full = db.get_all_fabric_services()
    
    # NEW: Select Customer Name (0), Service Type (3), Health Status (4), and Port Count (6)
    display_data = []
    for row in services_data_full:
        # Check if the row has enough elements (7 elements expected now)
        if len(row) >= 7:
            display_data.append([
                row[0], # Customer Name
                row[3], # Service Type
                row[4], # Health Status
                row[6]  # Assigned Ports Count
            ])
        else:
            pass
            
    # NEW headers: Removed Service Name and Alias, added Assigned Ports
    headers = ["Customer Name", "Service Type", "Health Status", "Assigned Ports"]
    display_table(headers, display_data)


# --- Port Assignment Handlers ---

def handle_assign_port_to_service():
    """
    Workflow to assign an eligible port to an existing fabric service.
    """
    print_header("Assign Port to Fabric Service")
    
    # 1. Select Fabric Service
    # Returns (customer_name, service_name, service_alias, service_type, health_status, service_id, port_count)
    services_data = db.get_all_fabric_services() 
    if not services_data:
        print("No Fabric Services found. Please create one first. Aborting.")
        return

    print("\n--- 1. Select Fabric Service to Assign Port to ---")
    
    # Prepare data for display: (Index, Service Name, Customer Name, Type, Service UUID)
    display_services = []
    # We use index 1 (service_name) and 2 (customer_name) for display selection
    for i, (c_name, s_name, s_alias, s_type, s_health, s_uuid, p_count) in enumerate(services_data, 1):
        display_services.append((s_uuid, s_name, c_name, s_type))
    
    service_headers = ["#", "Service Name", "Customer Name", "Type"]
    service_table_data = [[i, data[1], data[2], data[3]] for i, data in enumerate(display_services, 1)]
    display_table(service_headers, service_table_data)


    try:
        service_choice = get_input("Enter the number of the Service")
        choice_index = int(service_choice) - 1
        
        if not (0 <= choice_index < len(display_services)):
            print("Invalid service number selected. Aborting.")
            return

        selected_service_id = display_services[choice_index][0]
        selected_service_name = display_services[choice_index][1]
        print(f"\nSelected Service: {selected_service_name} (ID: {str(selected_service_id)[:8]}...)")
    except (ValueError, EOFError):
        print("\nInvalid input or input cancelled. Aborting.")
        return

    # 2. Select Eligible Port
    
    # Returns (port_id, device_name, port_name, port_service_status, port_type)
    eligible_ports = db.get_eligible_ports() 
    if not eligible_ports:
        print("\nNo eligible ports found for assignment (Must be unassigned, 'Available'/'Ready for use', and 'Physical'/'UNI'). Aborting.")
        return

    print("\n--- 2. Select Eligible Port to Assign ---")

    # Prepare data for display: (Index, Device Name, Port Name, Status, Type, Port UUID)
    display_ports = []
    for i, (p_uuid, d_name, p_name, p_status, p_type) in enumerate(eligible_ports, 1):
        display_ports.append((p_uuid, d_name, p_name, p_status, p_type))

    port_headers = ["#", "Device Name", "Port Name", "Status", "Type"]
    port_table_data = [[i, data[1], data[2], data[3], data[4]] for i, data in enumerate(display_ports, 1)]
    display_table(port_headers, port_table_data)

    try:
        port_choice = get_input("Enter the number of the Port to assign")
        choice_index = int(port_choice) - 1
        
        if not (0 <= choice_index < len(display_ports)):
            print("Invalid port number selected. Aborting.")
            return

        selected_port_id = display_ports[choice_index][0]
        selected_device_name = display_ports[choice_index][1]
        selected_port_name = display_ports[choice_index][2]
        print(f"Selected Port: {selected_device_name} / {selected_port_name} (ID: {str(selected_port_id)[:8]}...)")
    except (ValueError, EOFError):
        print("\nInvalid input or input cancelled. Aborting.")
        return

    # 3. Perform Assignment
    
    if db.assign_port_to_service(selected_port_id, selected_service_id):
        print(f"\nSUCCESS: Port {selected_port_name} on {selected_device_name} is now a 'Fabric Port' and 'Configured' for service {selected_service_name}.")
    else:
        print("\nFAILURE: Port assignment failed. Check DB logs for details.")


def handle_unassign_port_from_service():
    """
    Workflow to unassign a port from a fabric service and reset its status/type.
    """
    print_header("Unassign Port from Fabric Service")

    # Returns (port_id, device_name, port_name, service_name, service_alias)
    assigned_ports = db.get_assigned_ports() 
    if not assigned_ports:
        print("No ports are currently assigned to any Fabric Service. Aborting.")
        return

    print("\n--- 1. Select Assigned Port to Unassign ---")
    
    # Prepare data for display: (Index, Device Name, Port Name, Service Name, Service Alias, Port UUID)
    display_ports = []
    for i, (p_uuid, d_name, p_name, s_name, s_alias) in enumerate(assigned_ports, 1):
        display_ports.append((p_uuid, d_name, p_name, s_name, s_alias)) 

    port_headers = ["#", "Device Name", "Port Name", "Assigned Service (Alias)"]
    port_table_data = [[i, data[1], data[2], f"{data[3]} ({data[4]})"] for i, data in enumerate(display_ports, 1)]
    display_table(port_headers, port_table_data)

    try:
        port_choice = get_input("Enter the number of the Port to unassign")
        choice_index = int(port_choice) - 1
        
        if not (0 <= choice_index < len(display_ports)):
            print("Invalid port number selected. Aborting.")
            return

        selected_port_id = display_ports[choice_index][0]
        selected_device_name = display_ports[choice_index][1]
        selected_port_name = display_ports[choice_index][2]
        print(f"Selected Port: {selected_device_name} / {selected_port_name} (ID: {str(selected_port_id)[:8]}...)")
    except (ValueError, EOFError):
        print("\nInvalid input or input cancelled. Aborting.")
        return

    # 2. Perform Unassignment
    if db.unassign_port_from_service(selected_port_id):
        print(f"\nSUCCESS: Port {selected_port_name} on {selected_device_name} is unassigned.")
        print("Status reset to 'Ready for use' and Type reset to 'Physical'.")
    else:
        print("\nFAILURE: Port unassignment failed. Check DB logs for details.")


# --- Fabric Connection Handlers (NEW) ---

def handle_assign_eline_epl():
    """Specific handler for creating an E-Line EPL Fabric Connection (2 ports required)."""
    print_header("Assign E-Line EPL Fabric Connection (2 Ports)")
    service_type = "E-Line"
    
    # 1. Select Service of Type E-Line
    # Returns: (customer_name, service_name, service_alias, health_status, service_id, port_count)
    services_data = db.get_fabric_services_by_type(service_type)

    if not services_data:
        print(f"No Fabric Services of type '{service_type}' found. Aborting.")
        return

    print(f"\n--- 1. Select '{service_type}' Service ---")
    
    display_services = []
    for i, (c_name, s_name, s_alias, h_status, s_uuid, p_count) in enumerate(services_data, 1):
        # Only allow selection if the service has at least 2 ports assigned (EPL requirement)
        if p_count < 2:
            s_name = f"{s_name} (Needs {2-p_count} more ports)"
        display_services.append((s_uuid, s_name, c_name, p_count))
    
    service_headers = ["#", "Service Name", "Customer Name", "Ports Assigned"]
    service_table_data = [[i, data[1], data[2], data[3]] for i, data in enumerate(display_services, 1)]
    display_table(service_headers, service_table_data)

    try:
        service_choice = get_input("Enter the number of the Service")
        choice_index = int(service_choice) - 1
        
        if not (0 <= choice_index < len(display_services)):
            print("Invalid service number selected. Aborting.")
            return
        
        selected_service_id = display_services[choice_index][0]
        selected_service_name = display_services[choice_index][1]
        port_count = display_services[choice_index][3]

        if port_count < 2:
            print(f"Error: E-Line EPL requires 2 assigned ports. Selected service only has {port_count}. Aborting.")
            return
            
        print(f"\nSelected Service: {selected_service_name} (ID: {str(selected_service_id)[:8]}...)")
    except (ValueError, EOFError):
        print("\nInvalid input or input cancelled. Aborting.")
        return

    # 2. Select the two Ports assigned to this Service
    
    # Returns (port_id, device_name, port_name, port_service_status, port_type)
    assigned_ports = db.get_ports_by_service_id(selected_service_id)

    print(f"\n--- 2. Select 2 Ports from '{selected_service_name}' ---")
    
    display_ports = []
    for i, (p_uuid, d_name, p_name, p_status, p_type) in enumerate(assigned_ports, 1):
        display_ports.append((p_uuid, d_name, p_name))

    port_headers = ["#", "Device Name", "Port Name"]
    port_table_data = [[i, data[1], data[2]] for i, data in enumerate(display_ports, 1)]
    display_table(port_headers, port_table_data)

    try:
        port_a_choice = get_input("Enter number for Port A (First endpoint)")
        port_b_choice = get_input("Enter number for Port B (Second endpoint)")

        port_a_index = int(port_a_choice) - 1
        port_b_index = int(port_b_choice) - 1
        
        if not (0 <= port_a_index < len(display_ports) and 0 <= port_b_index < len(display_ports)):
            print("Invalid port number(s) selected. Aborting.")
            return
        
        if port_a_index == port_b_index:
            print("Error: Port A and Port B must be different ports. Aborting.")
            return
            
        port_a_id = display_ports[port_a_index][0]
        port_b_id = display_ports[port_b_index][0]
        
        port_a_name = f"{display_ports[port_a_index][1]}/{display_ports[port_a_index][2]}"
        port_b_name = f"{display_ports[port_b_index][1]}/{display_ports[port_b_index][2]}"

        print(f"Connection will be created between Port A: {port_a_name} and Port B: {port_b_name}.")
    except (ValueError, EOFError):
        print("\nInvalid input or input cancelled. Aborting.")
        return

    # 3. Create the E-Line EPL Connection
    
    connection = db.create_epl_connection(selected_service_id, port_a_id, port_b_id)
    
    if connection:
        print(f"\nSUCCESS: E-Line EPL Connection '{connection.connection_name}' created!")
        print(f"Connection ID: {str(connection.connection_id)[:8]}... Status: {connection.connection_status}")
    else:
        print("\nFAILURE: E-Line EPL Connection creation failed. Check DB logs.")


def handle_assign_fabric_connection():
    """Handles option 14: Assign a Fabric Connection (Service Type Menu)."""
    print_header("Assign Fabric Connection - Select Service Type")
    
    service_type_map = {
        '1': ("E-Line EPL", handle_assign_eline_epl),
        '2': ("E-Line EVPL", lambda: print("Handler for E-line EVPL not yet implemented.")),
        '3': ("E-LAN EVPLAN", lambda: print("Handler for E-LAN EVPLAN not yet implemented.")),
        '4': ("IPVPN", lambda: print("Handler for IPVPN not yet implemented.")),
        '5': ("MCGW", lambda: print("Handler for MCGW not yet implemented.")),
        '6': ("DIA", lambda: print("Handler for DIA not yet implemented.")),
        '7': ("IOD", lambda: print("Handler for IOD not yet implemented.")),
    }

    print("1. E-Line EPL (Point-to-Point)")
    print("2. E-Line EVPL")
    print("3. E-LAN EVPLAN")
    print("4. IPVPN")
    print("5. MCGW")
    print("6. DIA")
    print("7. IOD")
    print("0. Back to Main Menu")
    print("-" * 50)
    
    choice = input("Enter connection type (1-7, 0 to cancel): ").strip()
    
    if choice == '0':
        return
    elif choice in service_type_map:
        service_type_map[choice][1]() # Execute the handler function
    else:
        print("Invalid choice. Returning to connection menu.")


# --- Main CLI Loop ---

def main_menu():
    """Displays the main menu and handles user input."""
    options = {
        '1': handle_setup_db,
        '2': handle_create_customer,
        '3': handle_view_all_customers,
        '4': handle_search_customers,
        '5': handle_create_device,
        '6': handle_view_all_devices,
        '8': handle_create_port,
        '9': handle_view_all_ports_detailed,
        '10': handle_create_fabric_service,
        '11': handle_view_all_fabric_services,
        '12': handle_assign_port_to_service, 
        '13': handle_unassign_port_from_service,
        '14': handle_assign_fabric_connection, # NEW OPTION
    }

    while True:
        try:
            print("\n" * 2)
            print("=" * 40)
            print("  Network Inventory Database Management CLI")
            print("=" * 40)
            print("1. Setup Database Tables (Run First!)")
            print("\n--- Customer Management ---")
            print("2. Create New Customer")
            print("3. View All Customers")
            print("4. Search Customers by Name/Account ID")
            print("\n--- Device Management ---")
            print("5. Create New Device")
            print("6. View All Devices")
            print("7. Search Devices by Name/Location (Not Implemented)")
            print("\n--- Port Management ---")
            print("8. Create New Port (Not Implemented)")
            print("9. View All Ports (Detailed)")
            print("\n--- Fabric Service Management ---")
            print("10. Create New Fabric Service (Not Implemented)")
            print("11. View All Fabric Services")
            print("\n--- Assignment Management (Port to Service) ---")
            print("12. Assign Port to Fabric Service")
            print("13. Unassign Port from Fabric Service")
            print("\n--- Connection Management (Service to Ports) ---")
            print("14. Assign Fabric Connection (Service Type Menu)")
            print("0. Exit")
            print("=" * 40)
            
            choice = input("Enter your choice (0-14): ").strip()

            if choice == '0':
                print("Exiting CLI. Goodbye!")
                sys.exit(0)
            elif choice in options:
                options[choice]()
            else:
                print("Invalid choice. Please enter a number between 0 and 14.")

        except Exception as e:
            print(f"\nAn unexpected error occurred in the main loop: {e}")

if __name__ == '__main__':
    main_menu()