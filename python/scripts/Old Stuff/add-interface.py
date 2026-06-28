import psycopg2
from psycopg2 import Error
import sys
import re 
import random 
import uuid # Needed for explicit UUID generation/handling

# --- 1. Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "mydatabase",
    "user": "myuser",
    "password": "mypassword"
}

# --- 2. Utility Functions (Unchanged or Minor) ---

def get_next_lag_index(cur, device_id: str) -> int:
    """Finds the highest existing integer index (XX) from port_names starting with 'ae'."""
    query = """
    SELECT port_name 
    FROM ports 
    WHERE device_id = %s AND port_name LIKE 'ae%%';
    """
    cur.execute(query, (device_id,))
    existing_lag_names = cur.fetchall()
    
    max_index = -1
    lag_pattern = re.compile(r'^ae(\d+)$')
    
    for (port_name,) in existing_lag_names:
        match = lag_pattern.match(port_name)
        if match:
            current_index = int(match.group(1))
            if current_index > max_index:
                max_index = current_index
                
    return max_index + 1

def is_lag_name_unique(cur, device_id: str, lag_name: str) -> bool:
    """Checks if a given port_name already exists for the device."""
    query = "SELECT 1 FROM ports WHERE device_id = %s AND port_name = %s;"
    cur.execute(query, (device_id, lag_name))
    return cur.fetchone() is None

# --- 3. SHOW and DELETE CORE FUNCTIONS ---

def show_ports_and_get_ids(device_name: str) -> tuple[dict | None, str | None]:
    """
    Retrieves and displays ports. Returns a dictionary mapping index (1-based) to port_id 
    and the deviceId UUID.
    """
    conn = None
    port_map = {}
    device_id = None
    
    try:
        print(f"\n--- Displaying Ports for Device: {device_name} ---")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT device_id FROM devices WHERE device_name = %s;", (device_name,))
        device_result = cur.fetchone()

        if not device_result:
            print(f"❌ Error: Device '{device_name}' not found.")
            return None, None

        device_id = device_result[0]

        query = """
        SELECT
            port_id, port_name, port_speed, service_status, customer_alias
        FROM ports
        WHERE device_id = %s
        ORDER BY port_name;
        """
        cur.execute(query, (device_id,))
        ports = cur.fetchall()
        cur.close()

        if not ports:
            print(f"⚠️ No ports found for device '{device_name}'.")
            return None, device_id

        print(f"✅ Found {len(ports)} Ports:")
        print("-" * 120)
        print(f"{'#':<4} | {'Port Name':<20} | {'Speed':<10} | {'Service Status':<15} | {'Customer Alias':<25}")
        print("-" * 120)

        for index, port in enumerate(ports, start=1):
            port_id, port_name, port_speed, service_status, customer_alias = port
            print(f"{index:<4} | {port_name:<20} | {port_speed:<10} | {service_status:<15} | {customer_alias if customer_alias else 'N/A':<25}")
            port_map[index] = {'id': port_id, 'name': port_name, 'status': service_status} # Map index to a dict of info
            
        print("-" * 120)
        
        return port_map, device_id

    except (Exception, Error) as error:
        print(f"❌ Database error: {error}")
        return None, None
    finally:
        if conn:
            conn.close()

# (delete_port function remains the same)
def delete_port(port_id_to_delete: str, port_name: str):
    """Deletes a port based on its UUID."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        delete_query = "DELETE FROM ports WHERE port_id = %s;"
        cur.execute(delete_query, (port_id_to_delete,))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"\n✅ Successfully deleted port: {port_name} (ID: {port_id_to_delete[:8]}...)")
        else:
            print(f"\n❌ Error: Could not find or delete port with ID: {port_id_to_delete}")

    except (Exception, Error) as error:
        print(f"❌ Database error during port deletion: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- 4. ADD LAG AND ASSIGNMENT FUNCTIONS ---

def add_lag_interface(device_name: str, lag_name: str) -> str | None:
    """
    Adds a new unique Lag interface and returns its newly generated port_id UUID.
    """
    conn = None
    new_lag_id = str(uuid.uuid4()) # Generate UUID client-side for immediate use
    
    try:
        print(f"\n--- Attempting to Add Interface '{lag_name}' to {device_name} ---")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT device_id FROM devices WHERE device_name = %s;", (device_name,))
        device_result = cur.fetchone()

        if not device_result:
            print(f"❌ Error: Device '{device_name}' not found in the 'devices' table. Aborting.")
            return None

        device_id = device_result[0]
        
        if not is_lag_name_unique(cur, device_id, lag_name):
            print(f"❌ Error: Interface '{lag_name}' already exists on device '{device_name}'. Aborting.")
            return None

        new_port_data = {
            'port_id': new_lag_id, # Use generated UUID
            'port_name': lag_name,
            'port_speed': '10G',
            'fabric_port_type': 'AggregateEthernet',
            'port_tagging': 'Tagged', 
            'service_status': 'Configured', # LAGs are usually 'Configured' or 'In Use'
            'device_id': device_id
        }

        insert_query = """
        INSERT INTO ports (
            port_id, port_name, port_speed, fabric_port_type, port_tagging, 
            service_status, device_id
        ) 
        VALUES (
            %(port_id)s, %(port_name)s, %(port_speed)s, %(fabric_port_type)s, %(port_tagging)s, 
            %(service_status)s, %(device_id)s
        );
        """
        cur.execute(insert_query, new_port_data)
        conn.commit()
        
        print(f"✅ Successfully added Lag Interface: {lag_name} (ID: {new_lag_id[:8]}...)")
        return new_lag_id

    except (Exception, Error) as error:
        print(f"❌ Database error during LAG insertion: {error}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def assign_ports_to_lag(lag_id: str, lag_name: str, device_id: str):
    """
    Interactively prompts the user to assign member ports to the newly created LAG.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"\n--- Assigning Member Ports to {lag_name} ---")
        print("Ports must have service status 'Available' or 'Planned'.")
        
        # 1. Fetch assignable ports
        assignable_query = """
        SELECT port_id, port_name, port_speed, service_status
        FROM ports
        WHERE device_id = %s
          AND fabric_port_type != 'AggregateEthernet' -- Exclude other LAGs
          AND service_status IN ('Available', 'Planned')
        ORDER BY port_name;
        """
        cur.execute(assignable_query, (device_id,))
        assignable_ports = cur.fetchall()
        
        if not assignable_ports:
            print("⚠️ No assignable ports found with status 'Available' or 'Planned'. Skipping assignment.")
            return
            
        # 2. Display assignable ports
        assignable_map = {}
        print("-" * 80)
        print(f"{'#':<4} | {'Port Name':<20} | {'Speed':<10} | {'Status':<15}")
        print("-" * 80)
        
        for index, port in enumerate(assignable_ports, start=1):
            port_id, port_name, port_speed, service_status = port
            print(f"{index:<4} | {port_name:<20} | {port_speed:<10} | {service_status:<15}")
            assignable_map[str(index)] = {'id': port_id, 'name': port_name}
        print("-" * 80)
        
        # 3. Get user input for assignment
        while True:
            selection = input(f"Enter the index of the port to assign to {lag_name} (or type 'done'): ").strip()
            
            if selection.lower() == 'done':
                break
            
            if selection not in assignable_map:
                print("❌ Invalid selection. Please enter a valid index number or 'done'.")
                continue
                
            port_info = assignable_map[selection]
            port_id_to_assign = port_info['id']
            port_name_to_assign = port_info['name']
            
            # 4. Perform the assignment update
            update_query = """
            UPDATE ports
            SET customer_alias = %s,
                service_status = 'In Use', -- Change status as it's now part of an aggregate
                service_id = %s, -- service_id now points to the LAG's port_id (UUID)
                fabric_port_type = 'Member' -- Indicate it is a member port
            WHERE port_id = %s;
            """
            cur.execute(update_query, (f"Member of {lag_name}", lag_id, port_id_to_assign))
            
            if cur.rowcount == 1:
                conn.commit()
                print(f"✅ Assigned port {port_name_to_assign} to {lag_name}. Status updated to 'In Use'.")
                # Remove from map so user can't select it again
                del assignable_map[selection] 
                # Re-index remaining items for simplicity (optional but clearer)
                
            else:
                print(f"❌ Failed to assign port {port_name_to_assign}.")

    except (Exception, Error) as error:
        print(f"❌ Database error during port assignment: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- 5. Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_ports.py <DEVICE_NAME> [ACTION]")
        print("Actions: 'show' (default), 'add_lag', 'delete'")
        print("Example: python manage_ports.py VAR2.DEN1 add_lag")
        sys.exit(1)

    router_name = sys.argv[1]
    action = sys.argv[2].lower() if len(sys.argv) > 2 else 'show'

    if action == 'add_lag':
        try:
            # Setup/Suggestion Block
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT device_id FROM devices WHERE device_name = %s;", (router_name,))
            device_id_result = cur.fetchone()
            
            suggestion = "ae0"
            device_id = None
            if device_id_result:
                device_id = device_id_result[0]
                suggested_index = get_next_lag_index(cur, device_id)
                suggestion = f"ae{suggested_index}"
            conn.close() # Close setup connection

            # Get user input for LAG name
            lag_name_input = input(f"Enter unique LAG interface name (e.g., {suggestion}): ").strip()
            
            if lag_name_input:
                # 1. Create the LAG and get its ID
                new_lag_id = add_lag_interface(router_name, lag_name_input)
                
                if new_lag_id:
                    # 2. Assign ports to the newly created LAG
                    assign_ports_to_lag(new_lag_id, lag_name_input, device_id)
                    
                    # 3. Show the final state
                    show_ports_and_get_ids(router_name)
            else:
                print("Operation cancelled: Interface name cannot be empty.")
                
        except (Exception, Error) as e:
            print(f"An error occurred during setup: {e}")

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