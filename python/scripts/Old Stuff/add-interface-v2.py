import psycopg2
from psycopg2 import Error
import sys
import re 
import uuid 
import re 

# --- 1. Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "mydatabase",  # <-- CHANGE THIS
    "user": "myuser",          # <-- CHANGE THIS
    "password": "mypassword"   # <-- CHANGE THIS
}

# --- 2. Utility Functions ---

def get_next_lag_index(cur, device_id: str) -> int:
    """Finds the highest existing integer index (XX) from port_names starting with 'ae'."""
    query = "SELECT port_name FROM ports WHERE device_id = %s AND port_name LIKE 'ae%%';"
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

def extract_speed_in_mbps(speed_str: str) -> int:
    """Converts speed strings (e.g., '10G', '1G') to Mbps for calculation."""
    speed_str = speed_str.strip().upper()
    match = re.match(r'(\d+)([GMK])', speed_str)
    if not match:
        return 0
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == 'G':
        return value * 1000  # GB to MB
    elif unit == 'M':
        return value         # MB is already MB
    elif unit == 'K':
        return value // 1000 # KB to MB (or just 0 for practical network speeds)
    return 0
    
def format_mbps_to_network_speed(mbps: int) -> str:
    """Converts total Mbps back to a common network speed format."""
    if mbps >= 1000:
        if mbps % 1000 == 0:
            return f"{mbps // 1000}G"
        else:
            return f"{mbps / 1000:.1f}G"
    return f"{mbps}M"
    
# --- 3. SHOW, ADD, DELETE, AND ASSIGNMENT CORE FUNCTIONS ---

def show_ports_and_get_ids(device_name: str) -> tuple[dict | None, str | None]:
    """
    Retrieves and displays ports. Returns a dictionary mapping index (1-based) to port info 
    and the deviceId UUID.
    """
    conn = None
    port_map = {}
    device_id = None
    
    try:
        print(f"\n--- Displaying Ports for Device: {device_name} ---")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT deviceId FROM devices WHERE deviceName = %s;", (device_name,))
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
            port_map[index] = {'id': port_id, 'name': port_name, 'status': service_status}
            
        print("-" * 120)
        
        return port_map, device_id

    except (Exception, Error) as error:
        print(f"❌ Database error: {error}")
        return None, None
    finally:
        if conn:
            conn.close()

def delete_port(port_id_to_delete: str, port_name: str):
    """Deletes a port based on its UUID and cleans up any ports that were members of it."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Clean up member ports if this is a LAG being deleted
        # Reset member ports back to basic state
        cleanup_query = """
        UPDATE ports
        SET customer_alias = NULL,
            service_id = NULL,
            fabric_port_type = 'Physical', -- Assuming standard physical port type
            service_status = 'Available'
        WHERE service_id = %s;
        """
        cur.execute(cleanup_query, (port_id_to_delete,))
        if cur.rowcount > 0:
            print(f"🧹 Cleaned up {cur.rowcount} member ports previously assigned to {port_name}.")

        # 2. Delete the main port record
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


def update_lag_details(lag_id: str, lag_name: str):
    """
    Recalculates the total speed and updates the LAG's speed and description.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Fetch all member ports and their speeds
        member_ports_query = """
        SELECT port_name, port_speed
        FROM ports
        WHERE service_id = %s;
        """
        cur.execute(member_ports_query, (lag_id,))
        members = cur.fetchall()
        
        total_mbps = 0
        member_names = []
        for name, speed_str in members:
            total_mbps += extract_speed_in_mbps(speed_str)
            member_names.append(name)
            
        total_speed_str = format_mbps_to_network_speed(total_mbps)
        
        # 2. Build the new description
        member_count = len(member_names)
        if member_names:
            description = f"Aggregated Ethernet interface ({member_count} members): {', '.join(member_names)}"
        else:
            description = "Aggregated Ethernet interface (0 members)"

        # 3. Update the LAG interface
        update_query = """
        UPDATE ports
        SET port_speed = %s,
            port_description = %s
        WHERE port_id = %s;
        """
        cur.execute(update_query, (total_speed_str, description, lag_id))
        conn.commit()
        
        print(f"📈 LAG Update Complete: {lag_name} speed is now {total_speed_str} ({member_count} members).")

    except (Exception, Error) as error:
        print(f"❌ Database error during LAG update: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def add_lag_interface(device_name: str, lag_name: str) -> str | None:
    """
    Adds a new unique Lag interface and returns its newly generated port_id UUID.
    """
    conn = None
    new_lag_id = str(uuid.uuid4())
    
    try:
        print(f"\n--- Attempting to Add Interface '{lag_name}' to {device_name} ---")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT deviceId FROM devices WHERE deviceName = %s;", (device_name,))
        device_result = cur.fetchone()

        if not device_result:
            print(f"❌ Error: Device '{device_name}' not found in the 'devices' table. Aborting.")
            return None

        device_id = device_result[0]
        
        if not is_lag_name_unique(cur, device_id, lag_name):
            print(f"❌ Error: Interface '{lag_name}' already exists on device '{device_name}'. Aborting.")
            return None

        # LAG starts at 0 speed and status is Configured
        new_port_data = {
            'port_id': new_lag_id,
            'port_name': lag_name,
            'port_speed': '0M',
            'fabric_port_type': 'AggregateEthernet',
            'port_tagging': 'Tagged', 
            'service_status': 'Configured', 
            'device_id': device_id
        }

        insert_query = """
        INSERT INTO ports (
            port_id, port_name, port_speed, fabric_port_type, port_tagging, 
            service_status, device_id, port_description
        ) 
        VALUES (
            %(port_id)s, %(port_name)s, %(port_speed)s, %(fabric_port_type)s, %(port_tagging)s, 
            %(service_status)s, %(device_id)s, 'LAG created awaiting assignment'
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
          AND fabric_port_type NOT IN ('AggregateEthernet', 'Member')
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
            assignable_map[str(index)] = {'id': port_id, 'name': port_name, 'speed': port_speed}
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
            
            # 4. Perform the assignment update on the member port
            update_query = """
            UPDATE ports
            SET customer_alias = %s,
                service_status = 'Configured', -- Status is set to Configured
                service_id = %s, 
                fabric_port_type = 'Member'
            WHERE port_id = %s;
            """
            cur.execute(update_query, (f"Member of {lag_name}", lag_id, port_id_to_assign))
            
            if cur.rowcount == 1:
                conn.commit()
                print(f"✅ Assigned port {port_name_to_assign} to {lag_name}. Status updated to 'Configured'.")
                
                # Recalculate and update LAG details immediately after assignment
                update_lag_details(lag_id, lag_name)
                
                # Remove from map so user can't select it again
                del assignable_map[selection] 
                
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
        conn = None
        try:
            # Setup/Suggestion Block
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT deviceId FROM devices WHERE deviceName = %s;", (router_name,))
            device_id_result = cur.fetchone()
            
            suggestion = "ae0"
            device_id = None
            if device_id_result:
                device_id = device_id_result[0]
                suggested_index = get_next_lag_index(cur, device_id)
                suggestion = f"ae{suggested_index}"
            # close the cursor and connection from setup (finalizer will ensure closure if needed)
            cur.close()
            conn.close()
            conn = None

            lag_name_input = input(f"Enter unique LAG interface name (e.g., {suggestion}): ").strip()
            
            if lag_name_input:
                new_lag_id = add_lag_interface(router_name, lag_name_input)
                
                if new_lag_id and device_id:
                    assign_ports_to_lag(new_lag_id, lag_name_input, device_id)
                    show_ports_and_get_ids(router_name)
            else:
                print("Operation cancelled: Interface name cannot be empty.")
        except (Exception, Error) as error:
            print(f"❌ Error during add_lag setup: {error}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass