import argparse
import sys
import uuid
import random
from typing import List, Dict, Any, Tuple

# --- MOCK PLACEHOLDERS for database utility functions ---
# These mocks emulate the database connection and utility functions 
# (get_db_connection, handle_db_error, get_next_lag_index, etc.) 
# from the script provided by the user.

DEVICE_DB = {
    "VAR2.DEN1": 101,
    "CORE-RTR-A": 102
}
PORT_DATA = [
    {
        "id": 200, "port_name": "Eth1/1", "port_speed": "100G", 
        "service_status": "In-Service", "fabric_port_type": "P2P",
        "port_tagging": "Untagged", "health": 98, "lag_name": "N/A", 
        "port_description": "Link to Core A"
    },
    {
        "id": 201, "port_name": "Eth1/2", "port_speed": "10G", 
        "service_status": "Out-of-Service", "fabric_port_type": "Access",
        "port_tagging": "Tagged", "health": 75, "lag_name": "LAG100", 
        "port_description": "Customer XYZ Access"
    },
    {
        "id": 202, "port_name": "Eth1/3", "port_speed": "40G", 
        "service_status": "In-Service", "fabric_port_type": "Trunk",
        "port_tagging": "Tagged", "health": 99, "lag_name": "LAG100", 
        "port_description": "Inter-switch link member"
    }
]

def mock_get_db_connection():
    """Simulates establishing a connection."""
    print("MOCK: Database connection established.")
    return True # Mock connection object

def mock_handle_db_error(message, conn):
    """Simulates handling a database error."""
    print(f"❌ MOCK DB ERROR: {message}")

def mock_handle_connection_close(conn):
    """Simulates closing a database connection."""
    if conn:
        print("MOCK: Database connection closed.")

def mock_get_next_lag_index(cur, device_id):
    """Simulates finding the next available LAG index."""
    # Mocking to always suggest ae50
    return 50

def mock_add_lag_interface(router_name: str, lag_name: str) -> int:
    """Simulates creating a new LAG interface and returns its new ID."""
    new_lag_id = random.randint(300, 400)
    print(f"✅ MOCK SUCCESS: LAG interface '{lag_name}' created (ID: {new_lag_id}).")
    return new_lag_id

def mock_assign_ports_to_lag(lag_id: int, lag_name: str, device_id: int):
    """Simulates the interactive process of assigning ports to the new LAG."""
    print("\n--- Port Assignment ---")
    
    # 1. Show available ports (MOCK)
    available_ports = [p for p in PORT_DATA if p['lag_name'] == 'N/A']
    if not available_ports:
        print("MOCK: No unassigned ports available for this device.")
        return

    port_map = {}
    print("\nAvailable ports to assign:")
    for i, port in enumerate(available_ports, 1):
        port_map[i] = port
        print(f"  [{i}] {port['port_name']} ({port['port_speed']} / {port['port_description']})")

    try:
        selection = input("\nEnter port numbers to assign (e.g., '1,3,4') or press Enter to skip: ").strip()
        if not selection:
            print("MOCK: Port assignment skipped.")
            return

        selected_indices = [int(i.strip()) for i in selection.split(',') if i.strip().isdigit()]
        
        assigned_names = []
        for index in selected_indices:
            if index in port_map:
                assigned_names.append(port_map[index]['port_name'])
        
        if assigned_names:
            print(f"✅ MOCK SUCCESS: Ports {', '.join(assigned_names)} assigned to {lag_name} (ID: {lag_id}).")
        else:
            print("MOCK: No valid ports selected for assignment.")
            
    except ValueError:
        print("❌ Invalid input format for port selection.")
    except Exception as e:
        print(f"An unexpected error occurred during port assignment mock: {e}")

def mock_delete_port(port_id: int, port_name: str):
    """Simulates deleting a port using its ID and name."""
    print(f"✅ MOCK SUCCESS: Deleting Port ID {port_id} ('{port_name}')... Completed.")
    # In a real scenario, the PORT_DATA list would be updated here.

def mock_show_ports_and_get_ids(device_name: str) -> Tuple[Dict[int, Dict[str, Any]], int]:
    """
    Combines reading ports with formatting and returning a dictionary map 
    required for interactive deletion/assignment.
    """
    device_id = DEVICE_DB.get(device_name)
    if device_id is None:
        print(f"❌ Error: Device '{device_name}' not found in mock database.")
        return {}, 0
        
    ports_data = PORT_DATA # Use the mock data
    
    # Define column widths for alignment
    COLUMNS = [
        ("#", 3), ("PORT NAME", 10), ("SPEED", 8), ("TYPE", 8), 
        ("TAG", 6), ("LAG", 6), ("STATUS", 16), ("HEALTH", 6), 
        ("DESCRIPTION", 30)
    ]
    
    # Header Row
    header = "".join(f"{col[0]:<{col[1]}} | " for col in COLUMNS)
    print("\n" + "=" * len(header))
    print(f"PORTS TABLE for Device: {device_name} ({len(ports_data)} Records) (Device ID: {device_id})")
    print("=" * len(header))
    print(header)
    print("=" * len(header))

    port_map = {}
    for i, port in enumerate(ports_data, 1):
        port_map[i] = {"id": port['id'], "name": port['port_name'], "lag": port['lag_name']}
        row = (
            f"[{i:<2}] | "
            f"{port.get('port_name', 'N/A'):<{COLUMNS[1][1]}} | "
            f"{port.get('port_speed', 'N/A'):<{COLUMNS[2][1]}} | "
            f"{port.get('fabric_port_type', 'N/A'):<{COLUMNS[3][1]}} | "
            f"{port.get('port_tagging', 'N/A'):<{COLUMNS[4][1]}} | "
            f"{port.get('lag_name', 'N/A'):<{COLUMNS[5][1]}} | "
            f"{port.get('service_status', 'N/A'):<{COLUMNS[6][1]}} | "
            f"{port.get('health', 'N/A'):<{COLUMNS[7][1]}} | "
            f"{port.get('port_description', 'N/A')[:COLUMNS[8][1]]:<{COLUMNS[8][1]}}"
        )
        print(row)
    
    print("=" * len(header))
    return port_map, device_id

# Map mock functions to original names for handlers
create_port = lambda *args, **kwargs: print(f"✅ MOCK SUCCESS: Created new Port {kwargs.get('port_name', 'N/A')}")
update_port = lambda *args, **kwargs: print(f"✅ MOCK SUCCESS: Updated Port {kwargs.get('original_port_name', 'N/A')}")
delete_port_direct = lambda device, name: print(f"✅ MOCK SUCCESS: Deleted Port '{name}' from device '{device}' (Non-Interactive)")

# --- CLI Command Handlers ---

def handle_port_create(args):
    """Handles the 'pc' subcommand for creating a Port (Non-Interactive)."""
    print(f"Attempting to create Port '{args.name}' on Device '{args.device}'...")
    create_port(
        device_name=args.device, port_name=args.name, port_speed=args.speed, 
        fabric_port_type=args.type, port_tagging=args.tagging, service_status=args.status,
        lag_name=args.lag, customer_alias=args.alias, mac_address=args.mac,
        port_optic=args.optic, health=args.health, port_description=args.desc
    )

def handle_port_read(args):
    """Handles the 'pr' subcommand for reading Ports (Non-Interactive Display)."""
    mock_show_ports_and_get_ids(args.device)

def handle_port_update(args):
    """Handles the 'pu' subcommand for updating a Port (Non-Interactive)."""
    print(f"Attempting to update Port '{args.name}' on Device '{args.device}'...")
    update_port(
        device_name=args.device, original_port_name=args.name, new_port_name=args.new_name,
        new_lag_name=args.lag, new_speed=args.speed, new_type=args.type,
        new_tagging=args.tagging, new_svc_status=args.status, new_health=args.health,
        new_description=args.desc
    )

def handle_port_delete(args):
    """Handles the 'pd' subcommand for deleting a Port (Non-Interactive by Name)."""
    print(f"Attempting to delete Port '{args.name}' from Device '{args.device}'...")
    delete_port_direct(args.device, args.name)

# --- NEW INTERACTIVE HANDLERS ---

def handle_port_lag_add(args):
    """Handles the 'pla' subcommand for creating a LAG and assigning ports (Interactive)."""
    router_name = args.device
    conn = None
    device_id = None
    suggestion = "ae0"
    
    try:
        # 1. Get Device ID and LAG suggestion
        conn = mock_get_db_connection()
        device_id = DEVICE_DB.get(router_name)
        
        if device_id:
            suggested_index = mock_get_next_lag_index(None, device_id)
            suggestion = f"ae{suggested_index}"
        else:
            print(f"❌ Error: Device '{router_name}' not found.")
            return

    except Exception as error:
        mock_handle_db_error(f"during LAG setup: {error}", conn)
        return
    finally:
        mock_handle_connection_close(conn)

    # 2. Prompt for LAG name and execute workflow
    lag_name_input = input(f"Enter unique LAG interface name (e.g., {suggestion}): ").strip()
    
    if lag_name_input:
        new_lag_id = mock_add_lag_interface(router_name, lag_name_input)
        
        if new_lag_id and device_id:
            # This mock function handles the interactive port assignment
            mock_assign_ports_to_lag(new_lag_id, lag_name_input, device_id)
            mock_show_ports_and_get_ids(router_name) # Show final state
    else:
        print("Operation cancelled: Interface name cannot be empty.")

def handle_port_delete_interactive(args):
    """Handles the 'pdl' subcommand for deleting a Port (Interactive by Index)."""
    router_name = args.device
    port_map, device_id = mock_show_ports_and_get_ids(router_name)
    
    if port_map:
        try:
            key_input = input("\nEnter the '#' (index) of the port to delete: ").strip()
            key_index = int(key_input)
            
            if key_index in port_map:
                port_info_to_delete = port_map[key_index]
                port_id_to_delete = port_info_to_delete['id']
                port_name_to_delete = port_info_to_delete['name']
                
                confirm = input(f"Are you sure you want to DELETE port '{port_name_to_delete}'? (yes/no): ").lower()
                if confirm == 'yes':
                    # Calls the mock delete function
                    mock_delete_port(port_id_to_delete, port_name_to_delete)
                    mock_show_ports_and_get_ids(router_name) # Show updated list
                else:
                    print("Deletion cancelled by user.")
            else:
                print(f"❌ Invalid index key: {key_index}. Please enter a number from the list.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except Exception as e:
            print(f"An error occurred during deletion setup: {e}")


# --- Main CLI Setup ---

def main():
    parser = argparse.ArgumentParser(
        description="Dedicated CLI for Network Port Management (CRUD and Interactive LAG/Delete).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # --- PORT MANAGEMENT COMMANDS (pr, pc, pu, pd) ---
    
    # pc - Create Port
    parser_pc = subparsers.add_parser('pc', help='Create a new physical port (Non-Interactive).')
    parser_pc.add_argument('device', type=str, help='Device name the port belongs to.')
    parser_pc.add_argument('name', type=str, help='Port name (e.g., Eth1/1).')
    parser_pc.add_argument('speed', type=str, help='Port speed (e.g., 10G, 40G).')
    parser_pc.add_argument('type', type=str, help='Fabric port type (e.g., Access, Trunk, P2P).')
    parser_pc.add_argument('tagging', type=str, help='Port tagging (e.g., Tagged, Untagged).')
    parser_pc.add_argument('status', type=str, help='Service status (e.g., In-Service, Out-of-Service).')
    parser_pc.add_argument('-l', '--lag', type=str, default=None, help='LAG name if port is a member.')
    parser_pc.add_argument('-a', '--alias', type=str, default=None, help='Customer alias.')
    parser_pc.add_argument('-m', '--mac', type=str, default=None, help='MAC address.')
    parser_pc.add_argument('-o', '--optic', type=str, default=None, help='Optic type/model.')
    parser_pc.add_argument('-hl', '--health', type=int, default=None, help='Health score (0-100).')
    parser_pc.add_argument('-d', '--desc', type=str, default=None, help='Port description.')
    parser_pc.set_defaults(func=handle_port_create)

    # pr - Read/List Ports (Uses the mock_show_ports_and_get_ids formatting)
    parser_pr = subparsers.add_parser('pr', help='Read/List ports for a specific device (Detailed Interrogation).')
    parser_pr.add_argument('device', type=str, help='Device name to query.')
    parser_pr.set_defaults(func=handle_port_read)

    # pu - Update Port
    parser_pu = subparsers.add_parser('pu', help='Update an existing port (Non-Interactive).')
    parser_pu.add_argument('device', type=str, help='Device name the port belongs to.')
    parser_pu.add_argument('name', type=str, help='Original port name to update.')
    parser_pu.add_argument('-nn', '--new-name', type=str, default=None, help='New port name.')
    parser_pu.add_argument('-l', '--lag', type=str, default=None, help='New LAG name (or None to unlink).')
    parser_pu.add_argument('-s', '--speed', type=str, default=None, help='New port speed.')
    parser_pu.add_argument('-t', '--type', type=str, default=None, help='New fabric port type.')
    parser_pu.add_argument('-tg', '--tagging', type=str, default=None, help='New port tagging.')
    parser_pu.add_argument('-st', '--status', type=str, default=None, help='New service status.')
    parser_pu.add_argument('-hl', '--health', type=int, default=None, help='New health score (0-100).')
    parser_pu.add_argument('-d', '--desc', type=str, default=None, help='New port description.')
    parser_pu.set_defaults(func=handle_port_update)

    # pd - Delete Port (Non-Interactive by Name)
    parser_pd = subparsers.add_parser('pd', help='Delete a port by name (Non-Interactive).')
    parser_pd.add_argument('device', type=str, help='Device name the port belongs to.')
    parser_pd.add_argument('name', type=str, help='Port name to delete.')
    parser_pd.set_defaults(func=handle_port_delete)

    # --- NEW INTERACTIVE LAG COMMAND ---
    parser_pla = subparsers.add_parser('pla', help='[Interactive] Create a new LAG and assign ports to it.')
    parser_pla.add_argument('device', type=str, help='Device name to perform LAG creation on (e.g., VAR2.DEN1).')
    parser_pla.set_defaults(func=handle_port_lag_add)

    # --- NEW INTERACTIVE DELETE COMMAND ---
    parser_pdl = subparsers.add_parser('pdl', help='[Interactive] Show list and delete port by index.')
    parser_pdl.add_argument('device', type=str, help='Device name to perform interactive deletion on.')
    parser_pdl.set_defaults(func=handle_port_delete_interactive)


    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()