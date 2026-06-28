"""File Name: 'manage_ports.py' and version '1.0.7' date: 'November 27, 2025 1:36 PM MST' """
import sys
from psycopg2 import Error
from python.db_config import get_db_connection, handle_db_error, handle_connection_close
from utils import get_next_lag_index
from db_operations import (
    show_ports_and_get_ids, delete_port, 
    add_lag_interface, assign_ports_to_lag
)

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_ports.py <DEVICE_NAME> [ACTION]")
        print("Actions: 'show' (default), 'add_lag', 'delete'")
        print("Example: python manage_ports.py VAR2.DEN1 add_lag")
        sys.exit(1)

    router_name = sys.argv[1]
    action = sys.argv[2].lower() if len(sys.argv) > 2 else 'show'

    if action == 'add_lag':
        conn = None
        device_id = None
        suggestion = "ae0"
        
        try:
            # 1. Get Device ID and LAG suggestion
            conn = get_db_connection()
            cur = conn.cursor()
            # FIX: Use 'device_id' and 'device_name' columns
            cur.execute("SELECT device_id FROM devices WHERE device_name = %s;", (router_name,))
            device_id_result = cur.fetchone()
            
            if device_id_result:
                device_id = device_id_result[0]
                suggested_index = get_next_lag_index(cur, device_id)
                suggestion = f"ae{suggested_index}"
            else:
                print(f"❌ Error: Device '{router_name}' not found.")
                return

        except (Exception, Error) as error:
            handle_db_error(f"during LAG setup: {error}", conn)
            return
        finally:
            handle_connection_close(conn)

        # 2. Prompt for LAG name and execute workflow
        lag_name_input = input(f"Enter unique LAG interface name (e.g., {suggestion}): ").strip()
        
        if lag_name_input:
            new_lag_id = add_lag_interface(router_name, lag_name_input)
            
            if new_lag_id and device_id:
                assign_ports_to_lag(new_lag_id, lag_name_input, device_id)
                show_ports_and_get_ids(router_name)
        else:
            print("Operation cancelled: Interface name cannot be empty.")

    elif action == 'delete':
        port_map, device_id = show_ports_and_get_ids(router_name)
        
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

    elif action == 'show':
        show_ports_and_get_ids(router_name)
        
    else:
        print(f"Invalid action: {action}. Use 'show', 'add_lag', or 'delete'.")

if __name__ == "__main__":
    main()