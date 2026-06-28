"""File Name: 'cli.py' and version '1.0.9' date: 'November 28, 2025 11:55 AM MST' (Fixed get_device_id import and usage) """
import argparse
import sys
from typing import Dict, Any, Tuple, Optional, List
from psycopg2 import Error

# Import helpers from provided files
from python.db_config import get_db_connection, handle_db_error, handle_connection_close
from utils import get_next_lag_index
from db_operations import (
    get_all_devices, create_device, update_device, delete_device, # Device CRUD
    show_ports_and_get_ids, create_port, delete_port, # Port CRUD
    get_device_ids, add_lag_interface, get_ports_for_lag_assignment, # FIX: get_device_id -> get_device_ids
    update_port_lag_assignment # LAG Ops
)
from bulk_load_devices import bulk_load_devices_main # Import the bulk load entry point (THIS FILE IS NOW CREATED)

# --- Interactive Selectors ---

def select_device_interactive(prompt: str) -> Optional[str]:
    """
    Displays all devices and prompts the user to select one by index.
    Returns the selected device name or None if cancelled/invalid.
    """
    # get_all_devices is now defined in db_operations.py and accepts silent=False
    device_map = get_all_devices(silent=False) 
    
    if not device_map:
        return None
        
    print(f"\n--- {prompt} ---")
    try:
        key_input = input("Enter the '#' (index) of the target device, or 'q' to cancel: ").strip()
        if key_input.lower() == 'q' or not key_input:
            print("Operation cancelled.")
            return None
            
        key_index = int(key_input)
        
        if key_index in device_map:
            return device_map[key_index]['name']
        else:
            print(f"❌ Invalid index key: {key_index}. Please enter a number from the list.")
            return None
    except ValueError:
        print("❌ Invalid input. Please enter a number or 'q'.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- Device CRUD Handlers ---

def handle_device_list(args):
    """Handles 'dls' subcommand (Read)"""
    get_all_devices()

def handle_device_create(args):
    """Handles 'dc' subcommand (Create)"""
    print(f"Attempting to create Device '{args.name}'...")
    create_device(
        device_name=args.name, gw_shortname=args.shortname, device_role=args.role, 
        device_type=args.type, availability_zone=args.az, lifecycle_status=args.lcs, 
        device_status=args.status, device_model=args.model, device_vendor=args.vendor, 
        health=args.health
    )

def handle_device_update(args):
    """Handles 'du' subcommand (Update)"""
    # Exclude command-specific arguments from the update payload
    updates = {
        k: v for k, v in vars(args).items() 
        if k not in ['name', 'func', 'command'] and v is not None
    }
    
    # Map CLI arguments to database column names (optional, ensures clean dictionary keys)
    column_mapping = {
        'new_name': 'device_name', 'shortname': 'gw_shortname', 'role': 'device_role',
        'type': 'device_type', 'az': 'availability_zone', 'lcs': 'lifecycle_status',
        'status': 'device_status', 'model': 'device_model', 'vendor': 'device_vendor',
        'health': 'health'
    }
    
    db_updates = {column_mapping.get(k, k): v for k, v in updates.items()}
    
    print(f"Attempting to update Device '{args.name}'...")
    update_device(args.name, db_updates)


def handle_device_delete(args):
    """Handles 'dd' subcommand (Delete)"""
    if not args.name:
        # Interactive selection if name is missing
        device_name = select_device_interactive("Select Device to DELETE")
        if not device_name:
            return
    else:
        device_name = args.name
        
    confirm = input(f"WARNING: Are you sure you want to DELETE device '{device_name}' and ALL associated ports? (type device name to confirm): ").strip()
    
    if confirm == device_name:
        delete_device(device_name)
    else:
        print("Deletion cancelled or confirmation failed.")

def handle_device_bulk_load(args):
    """Handles the 'dbulk' subcommand (Bulk Load)"""
    # args.path is the file path provided by the user
    bulk_load_devices_main(args.path)

# --- Port CRUD & LAG Handlers ---

def handle_port_list(args):
    """Handles 'pls' subcommand (Read Ports)"""
    show_ports_and_get_ids(args.device)

def handle_port_create(args):
    """Handles 'pc' subcommand (Create Port)"""
    print(f"Attempting to create Port '{args.name}' on Device '{args.device}'...")
    create_port(
        device_name=args.device, port_name=args.name, port_speed=args.speed, 
        fabric_port_type=args.type, port_tagging=args.tagging, service_status=args.status,
        lag_name=args.lag, customer_alias=args.alias, mac_address=args.mac,
        port_optic=args.optic, health=args.health, port_description=args.desc
    )

def handle_port_delete(args):
    """Handles 'pd' subcommand (Delete Port - Interactive)"""
    router_name = args.device
    port_map, device_id = show_ports_and_get_ids(router_name)
    
    if port_map:
        try:
            key_input = input("\nEnter the '#' (index) of the port to delete: ").strip()
            if not key_input:
                print("Deletion cancelled.")
                return
                
            key_index = int(key_input)
            
            if key_index in port_map:
                port_info_to_delete = port_map[key_index]
                port_id_to_delete = port_info_to_delete['id']
                port_name_to_delete = port_info_to_delete['name']
                
                confirm = input(f"Are you sure you want to DELETE port '{port_name_to_delete}'? (yes/no): ").lower()
                if confirm == 'yes':
                    delete_port(port_id_to_delete, port_name_to_delete)
                    show_ports_and_get_ids(router_name)
                else:
                    print("Deletion cancelled by user.")
            else:
                print(f"❌ Invalid index key: {key_index}. Please enter a number from the list.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except Exception as e:
             print(f"An error occurred during deletion setup: {e}")


def handle_port_lag_add(args):
    """Handles 'pla' subcommand (Create LAG - Interactive)"""
    router_name = args.device
    conn = None
    device_id = None
    suggestion = "ae0"
    
    try:
        # 1. Get Device ID and LAG suggestion
        conn = get_db_connection()
        cur = conn.cursor()
        
        # FIX: Use get_device_ids (plural) and extract the first ID
        device_ids = get_device_ids(cur, router_name)
        
        if device_ids:
            device_id = device_ids[0] # Use the first ID found
            suggested_index = get_next_lag_index(cur, device_id)
            suggestion = f"ae{suggested_index}"
        else:
            print(f"❌ Error: Device '{router_name}' not found. LAG creation aborted.")
            return

    except (Exception, Error) as error:
        handle_db_error(f"during LAG setup: {error}", conn)
        return
    finally:
        handle_connection_close(conn)

    # 2. Prompt for LAG name
    lag_name_input = input(f"Enter unique LAG interface name (e.g., {suggestion}): ").strip()
    
    if not lag_name_input:
        print("Operation cancelled: Interface name cannot be empty.")
        return
        
    # 3. Create LAG Interface
    new_lag_id = add_lag_interface(router_name, lag_name_input)
    
    if not new_lag_id or not device_id:
        return
        
    # 4. Interactive Port Assignment
    print("\n--- Port Assignment ---")
    available_ports = get_ports_for_lag_assignment(device_id)

    if not available_ports:
        print("INFO: No unassigned physical ports available to assign to this LAG.")
        return

    port_map = {}
    print("\nAvailable ports to assign:")
    for i, port in enumerate(available_ports, 1):
        port_map[i] = port
        print(f"  [{i}] {port['port_name']} ({port['port_speed']} / {port['port_description']}) (ID: {port['id']})")

    selection = input("\nEnter port numbers to assign (e.g., '1,3,4') or press Enter to skip: ").strip()
    if not selection:
        print("Port assignment skipped.")
        return

    try:
        selected_indices = [int(i.strip()) for i in selection.split(',') if i.strip().isdigit()]
        
        port_ids_to_assign = []
        assigned_names = []
        
        for index in selected_indices:
            if index in port_map:
                port_ids_to_assign.append(port_map[index]['id'])
                assigned_names.append(port_map[index]['port_name'])
                
        if port_ids_to_assign:
            update_port_lag_assignment(port_ids_to_assign, lag_name_input)
            print(f"✅ Ports {', '.join(assigned_names)} assigned to LAG '{lag_name_input}'.")
        else:
            print("No valid ports selected for assignment.")
            
    except ValueError:
        print("❌ Invalid input format for port selection.")
    except Exception as e:
        print(f"An unexpected error occurred during port assignment: {e}")
        
    # 5. Show final state
    show_ports_and_get_ids(router_name) 

# --- Main CLI Setup ---

def main():
    parser = argparse.ArgumentParser(
        description="Unified CLI for Network Device and Port Management (CRUD, Bulk Load, and Interactive LAG/Delete).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # --- DEVICE MANAGEMENT GROUP (dls, dc, du, dd, dbulk) ---
    
    # dls - List Devices (Read)
    subparsers.add_parser('dls', help='List all network devices in the database.')
    subparsers.choices['dls'].set_defaults(func=handle_device_list)
    
    # dc - Create Device
    parser_dc = subparsers.add_parser('dc', help='Create a new device record (Non-Interactive).')
    parser_dc.add_argument('name', type=str, help='Device Name (e.g., CORE-RTR-A).')
    parser_dc.add_argument('shortname', type=str, help='Gateway Shortname.')
    parser_dc.add_argument('role', type=str, help='Device Role (e.g., Core, Edge).')
    parser_dc.add_argument('type', type=str, help='Device Type (e.g., Router, Switch).')
    parser_dc.add_argument('az', type=str, help='Availability Zone.')
    parser_dc.add_argument('lcs', type=str, help='Lifecycle Status (e.g., Production, Decom).')
    parser_dc.add_argument('status', type=str, help='Operational Status (e.g., Active, Maintenance).')
    parser_dc.add_argument('model', type=str, help='Device Model.')
    parser_dc.add_argument('vendor', type=str, help='Device Vendor.')
    parser_dc.add_argument('health', type=int, help='Health score (1-3).')
    parser_dc.set_defaults(func=handle_device_create)
    
    # du - Update Device
    parser_du = subparsers.add_parser('du', help='Update an existing device by name (Non-Interactive).')
    parser_du.add_argument('name', type=str, help='Device name to update.')
    parser_du.add_argument('-n', '--new-name', type=str, default=None, help='New Device Name (Optional).')
    parser_du.add_argument('-s', '--shortname', type=str, default=None, help='New Gateway Shortname (Optional).')
    parser_du.add_argument('-r', '--role', type=str, default=None, help='New Device Role (Optional).')
    parser_du.add_argument('-t', '--type', type=str, default=None, help='New Device Type (Optional).')
    parser_du.add_argument('-a', '--az', type=str, default=None, help='New Availability Zone (Optional).')
    parser_du.add_argument('-l', '--lcs', type=str, default=None, help='New Lifecycle Status (Optional).')
    parser_du.add_argument('-st', '--status', type=str, default=None, help='New Operational Status (Optional).')
    parser_du.add_argument('-m', '--model', type=str, default=None, help='New Device Model (Optional).')
    parser_du.add_argument('-v', '--vendor', type=str, default=None, help='New Device Vendor (Optional).')
    parser_du.add_argument('-hl', '--health', type=int, default=None, help='New Health score (1-3) (Optional).')
    parser_du.set_defaults(func=handle_device_update)
    
    # dd - Delete Device
    parser_dd = subparsers.add_parser('dd', help='Delete a device by name (Interactive if name is omitted).')
    parser_dd.add_argument('-n', '--name', type=str, default=None, help='Device name to delete (Optional).')
    parser_dd.set_defaults(func=handle_device_delete)

    # dbulk - Bulk Load Devices
    parser_dbulk = subparsers.add_parser('dbulk', help='[Bulk Load] Loads new devices from a CSV file.')
    parser_dbulk.add_argument('-p', '--path', type=str, default=None, 
                              help='Optional: Full path to the CSV file or the directory containing add_devices.csv. Defaults to C:\\...\\python\\data\\add_devices.csv')
    parser_dbulk.set_defaults(func=handle_device_bulk_load)
    
    # --- PORT MANAGEMENT GROUP (pls, pc, pd, pla) ---

    # pls - List Ports (Read)
    parser_pls = subparsers.add_parser('pls', help='List ports for a specific device.')
    parser_pls.add_argument('device', type=str, help='Device name to query.')
    parser_pls.set_defaults(func=handle_port_list)

    # pc - Create Port
    parser_pc = subparsers.add_parser('pc', help='Create a new physical port (Non-Interactive).')
    parser_pc.add_argument('device', type=str, help='Device name the port belongs to.')
    parser_pc.add_argument('name', type=str, help='Port name (e.g., Eth1/1).')
    parser_pc.add_argument('speed', type=str, help='Port speed (e.g., 10G, 40G).')
    parser_pc.add_argument('type', type=str, help='Fabric port type (e.g., Access, Trunk, P2P).')
    parser_pc.add_argument('status', type=str, help='Service status (e.g., In-Service, Out-of-Service).')
    parser_pc.add_argument('-tg', '--tagging', type=str, default=None, help='Port tagging (e.g., Tagged, Untagged).')
    parser_pc.add_argument('-l', '--lag', type=str, default=None, help='LAG name if port is a member (Optional).')
    parser_pc.add_argument('-a', '--alias', type=str, default=None, help='Customer alias (Optional).')
    parser_pc.add_argument('-m', '--mac', type=str, default=None, help='MAC address (Optional).')
    parser_pc.add_argument('-o', '--optic', type=str, default=None, help='Optic type/model (Optional).')
    parser_pc.add_argument('-hl', '--health', type=int, default=100, help='Health score (0-100) (Optional, default 100).')
    parser_pc.add_argument('-d', '--desc', type=str, default=None, help='Port description (Optional).')
    parser_pc.set_defaults(func=handle_port_create)

    # pd - Delete Port (Interactive)
    parser_pd = subparsers.add_parser('pd', help='[Interactive] Show ports and delete by index.')
    parser_pd.add_argument('device', type=str, help='Device name to perform interactive deletion on.')
    parser_pd.set_defaults(func=handle_port_delete)

    # pla - Link Aggregation (Interactive)
    parser_pla = subparsers.add_parser('pla', help='[Interactive] Create a new LAG and assign ports to it.')
    parser_pla.add_argument('device', type=str, help='Device name to perform LAG creation on.')
    parser_pla.set_defaults(func=handle_port_lag_add)


    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()