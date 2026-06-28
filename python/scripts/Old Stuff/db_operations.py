"""File Name: 'db_operations.py' and version '1.0.18' date: 'November 28, 2025 12:00 PM MST' (Fixed UUID Array Casting) """
import psycopg2
from typing import List, Dict, Any, Tuple, Optional
from python.db_config import get_db_connection, handle_db_error, handle_connection_close

# --- Device CRUD Operations ---

def create_device(**kwargs):
    """Inserts a new device record into the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO devices (
                device_name, gw_shortname, device_role, device_type, availability_zone, 
                lifecycle_status, device_status, device_model, device_vendor, health
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            kwargs['device_name'], kwargs['gw_shortname'], kwargs['device_role'], 
            kwargs['device_type'], kwargs['availability_zone'], kwargs['lifecycle_status'], 
            kwargs['device_status'], kwargs['device_model'], kwargs['device_vendor'], 
            kwargs['health']
        ))
        conn.commit()
        print(f"✅ SUCCESS: Device '{kwargs['device_name']}' created.")

    except psycopg2.IntegrityError as e:
        handle_db_error(f"Integrity Error (Device '{kwargs['device_name']}' may already exist): {e}", conn)
    except psycopg2.Error as e:
        handle_db_error(f"Device creation failed: {e}", conn)
    finally:
        handle_connection_close(conn)

def update_device(device_name: str, updates: Dict[str, Any]):
    """Updates fields for an existing device."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            # Use 'SET key = %s' for dynamic updates
            set_clauses.append(f"{key} = %s")
            params.append(value)
        
        if not set_clauses:
            print("ℹ️ No parameters provided for update.")
            return

        params.append(device_name)
        
        update_query = f"UPDATE devices SET {', '.join(set_clauses)} WHERE device_name = %s;"
        
        cursor.execute(update_query, tuple(params))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ SUCCESS: Device '{device_name}' updated.")
        else:
            print(f"⚠️ Warning: Device '{device_name}' not found or no changes were made.")

    except psycopg2.Error as e:
        handle_db_error(f"Device update failed: {e}", conn)
    finally:
        handle_connection_close(conn)

def delete_device(device_name: str):
    """Deletes a device and cascades deletion of associated ports."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # NOTE: Assumes CASCADE DELETE is set up in your DB schema for ports table
        cursor.execute("DELETE FROM devices WHERE device_name = %s;", (device_name,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ SUCCESS: Device '{device_name}' and associated ports deleted.")
        else:
            print(f"⚠️ Warning: Device '{device_name}' not found.")

    except psycopg2.Error as e:
        handle_db_error(f"Device deletion failed: {e}", conn)
    finally:
        handle_connection_close(conn)

def get_all_devices(silent: bool = False) -> Dict[int, Dict[str, Any]]:
    """
    Retrieves and optionally displays all devices. 
    Returns a map of index -> device data for interactive selection.
    """
    conn = get_db_connection()
    device_map = {}
    try:
        cursor = conn.cursor()
        # Ensure we select device_id, not id
        cursor.execute("""
            SELECT device_id, device_name, device_role, device_status, health 
            FROM devices 
            ORDER BY device_name;
        """)
        devices_data = cursor.fetchall()

        if not devices_data:
            if not silent:
                print("ℹ️ No devices found in the database.")
            return {}

        # Define column widths
        COLUMNS = [("#", 3), ("NAME", 16), ("ROLE", 10), ("STATUS", 16), ("HEALTH", 6)]
        
        if not silent:
            # Header Row
            header = "".join(f"{col[0]:<{col[1]}} | " for col in COLUMNS)
            print("\n" + "=" * len(header))
            print(f"ALL DEVICES ({len(devices_data)} Records)")
            print("=" * len(header))
            print(header)
            print("=" * len(header))

        for i, device in enumerate(devices_data, 1):
            # The assignment sequence must match the SELECT query order
            device_id, name, role, status, health = device
            
            device_map[i] = {"id": device_id, "name": name, "role": role}

            if not silent:
                row = (
                    f"[{i:<2}] | "
                    f"{name:<{COLUMNS[1][1]}} | "
                    f"{role:<{COLUMNS[2][1]}} | "
                    f"{status:<{COLUMNS[3][1]}} | "
                    f"{health if health is not None else 'N/A':<{COLUMNS[4][1]}}"
                )
                print(row)
        
        if not silent:
            print("=" * len(header))

        return device_map

    except psycopg2.Error as e:
        if not silent:
            handle_db_error(f"Error reading devices: {e}", conn)
        return {}
    finally:
        handle_connection_close(conn)


# --- Port/LAG Helper Functions ---

def get_device_ids(cursor, device_name: str) -> List[Any]:
    """
    Retrieves ALL device_ids based on the device_name. 
    Returns a list of IDs (e.g., UUIDs).
    """
    cursor.execute("SELECT device_id FROM devices WHERE device_name = %s;", (device_name,))
    # Fetch all device IDs that match the name
    results = cursor.fetchall() 
    return [result[0] for result in results]

def check_duplicate_port_name(device_name: str, port_name: str) -> Tuple[bool, List[Any]]:
    """
    Checks if a port name already exists for a given device name by establishing 
    its own connection and handling potential duplicate device entries.
    Returns (is_duplicate, list_of_device_ids).
    """
    conn = get_db_connection()
    is_duplicate = False
    device_ids = []
    try:
        cursor = conn.cursor()
        
        # 1. Get ALL device_ids within this fresh transaction
        device_ids = get_device_ids(cursor, device_name)
        if not device_ids:
            # Device not found
            return False, [] 
            
        # 2. Check for duplicate port using the list of device_ids
        # FIX: Explicitly cast the %s array parameter to UUID[] to prevent type mismatch error
        cursor.execute("""
            SELECT COUNT(*) FROM ports 
            WHERE device_id = ANY(%s::uuid[]) AND port_name = %s;
        """, (device_ids, port_name))
        
        count = cursor.fetchone()[0]
        is_duplicate = count > 0
        
        return is_duplicate, device_ids
        
    except psycopg2.Error as e:
        # Log error but assume no duplicate to avoid blocking if DB connection fails
        print(f"❌ DB ERROR during duplicate check: {e}")
        return False, [] 
    finally:
        handle_connection_close(conn)


def create_port(**kwargs):
    """Inserts a new port record into the database."""
    
    # NEW CHECK: Prevent duplicate ports on the same device - run outside the main transaction
    is_duplicate, device_ids = check_duplicate_port_name(kwargs['device_name'], kwargs['port_name'])
    
    if is_duplicate:
        print(f"❌ Error: Port '{kwargs['port_name']}' already exists on device '{kwargs['device_name']}'. Creation aborted.")
        return
    
    if not device_ids:
        # This means the device itself wasn't found in the check function
        print(f"❌ Error: Device '{kwargs['device_name']}' not found. Port creation aborted.")
        return

    # Use the first ID found for the insertion, assuming device_id consistency is desired
    device_id = device_ids[0] 

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # FIX: Ensure port_tagging is not NULL, defaulting to 'N/A' if not provided
        port_tagging_value = kwargs.get('port_tagging')
        if port_tagging_value is None:
            port_tagging_value = 'N/A'
            
        # NOTE: Removed 'is_lag' column from INSERT.
        cursor.execute("""
            INSERT INTO ports (
                device_id, port_name, port_speed, fabric_port_type, port_tagging, 
                service_status, lag, customer_alias, mac_address, 
                port_optic, health, port_description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            device_id, kwargs['port_name'], kwargs['port_speed'], kwargs['fabric_port_type'], 
            port_tagging_value, kwargs['service_status'], kwargs.get('lag'), 
            kwargs.get('customer_alias'), kwargs.get('mac_address'), 
            kwargs.get('port_optic'), kwargs.get('health', 100), kwargs.get('port_description')
        ))
        conn.commit()
        print(f"✅ SUCCESS: Port '{kwargs['port_name']}' created on device '{kwargs['device_name']}'.")

    except psycopg2.IntegrityError as e:
        handle_db_error(f"Integrity Error (Port may already exist or foreign key missing): {e}", conn)
    except psycopg2.Error as e:
        handle_db_error(f"Port creation failed: {e}", conn)
    finally:
        handle_connection_close(conn)

def delete_port(port_id: Any, port_name: str):
    """
    Deletes a port using its internal database ID, handling associated links 
    and clearing lag assignments if the deleted port is a LAG interface.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Handle Port Links (Resolves Foreign Key Error)
        # Delete any links referencing this port_id (either as A or B)
        cursor.execute("""
            DELETE FROM port_links 
            WHERE port_a_id = %s OR port_b_id = %s;
        """, (port_id, port_id))
        
        links_deleted = cursor.rowcount
        
        # 2. Handle LAG members if the deleted port is a LAG interface (e.g., 'ae0')
        # Check if the port name suggests it is a LAG interface (e.g., starts with 'ae')
        if port_name.startswith('ae'):
            # Clear the lag assignment for any ports that are members of this LAG
            cursor.execute("""
                UPDATE ports
                SET lag = NULL
                WHERE lag = %s;
            """, (port_name,))
            lag_members_updated = cursor.rowcount
            print(f"ℹ️ {lag_members_updated} member ports unassigned from LAG '{port_name}'.")

        # 3. Delete the port itself (using 'port_id')
        cursor.execute("DELETE FROM ports WHERE port_id = %s;", (port_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ SUCCESS: Port '{port_name}' (ID: {port_id}) deleted.")
            if links_deleted > 0:
                 print(f"ℹ️ {links_deleted} associated port links were also deleted.")
        else:
            print(f"⚠️ Warning: Port ID {port_id} not found.")

    except psycopg2.Error as e:
        handle_db_error(f"Port deletion failed: {e}", conn)
    finally:
        handle_connection_close(conn)

def show_ports_and_get_ids(device_name: str) -> Tuple[Dict[int, Dict[str, Any]], Optional[Any]]:
    """
    Retrieves and displays ports for a device, returning a map 
    of index -> port_id needed for interactive operations.
    """
    conn = get_db_connection()
    port_map = {}
    device_id = None
    try:
        cursor = conn.cursor()
        
        # Get all IDs for the device name (use the first one found for display context)
        device_ids = get_device_ids(cursor, device_name)
        if not device_ids:
            print(f"❌ Error: Device '{device_name}' not found in database.")
            return {}, None
            
        device_id = device_ids[0] # Use the first ID for filtering below
        
        # Selecting 'port_id' (The correct column name) and 'lag' column.
        cursor.execute("""
            SELECT port_id, port_name, port_speed, fabric_port_type, port_tagging, 
                   lag, service_status, health, port_description
            FROM ports 
            WHERE device_id = %s
            ORDER BY port_name;
        """, (device_id,))
        ports_data = cursor.fetchall()
        
        # Define column widths for alignment
        COLUMNS = [
            ("#", 3), ("PORT NAME", 10), ("SPEED", 8), ("TYPE", 8), 
            ("TAG", 6), ("LAG", 6), ("STATUS", 16), ("HEALTH", 6), 
            ("IS LAG", 6), ("DESCRIPTION", 20)
        ]
        
        # Header Row
        header = "".join(f"{col[0]:<{col[1]}} | " for col in COLUMNS)
        print("\n" + "=" * len(header))
        print(f"PORTS TABLE for Device: {device_name} ({len(ports_data)} Records) (Device ID: {device_id})")
        print("=" * len(header))
        print(header)
        print("=" * len(header))

        for i, port in enumerate(ports_data, 1):
            # port_id is the first element
            port_id, port_name, speed, p_type, tagging, lag, status, health, desc = port
            
            # INFERENCE: A record is a LAG if it has no 'lag' association (i.e., it is the LAG itself) 
            # AND its fabric_port_type is 'LAG'.
            is_lag = (lag is None or lag == 'N/A') and p_type == 'LAG'
            
            port_map[i] = {"id": port_id, "name": port_name, "lag": lag}
            row = (
                f"[{i:<2}] | "
                f"{port_name:<{COLUMNS[1][1]}} | "
                f"{speed:<{COLUMNS[2][1]}} | "
                f"{p_type:<{COLUMNS[3][1]}} | "
                f"{tagging if tagging else 'N/A':<{COLUMNS[4][1]}} | "
                f"{lag if lag else 'N/A':<{COLUMNS[5][1]}} | "
                f"{status:<{COLUMNS[6][1]}} | "
                f"{health if health is not None else 'N/A':<{COLUMNS[7][1]}} | "
                f"{'Yes' if is_lag else 'No':<{COLUMNS[8][1]}} | " # Use inferred is_lag
                f"{desc[:COLUMNS[9][1]] if desc else 'N/A':<{COLUMNS[9][1]}}"
            )
            print(row)
        
        print("=" * len(header))
        return port_map, device_id

    except psycopg2.Error as e:
        handle_db_error(f"Error reading ports: {e}", conn)
        return {}, None
    finally:
        handle_connection_close(conn)
        
def add_lag_interface(device_name: str, lag_name: str) -> Optional[Any]:
    """
    Creates a new LAG interface record. 
    """
    # NEW CHECK: Prevent duplicate LAG names on the same device - run outside the main transaction
    is_duplicate, device_ids = check_duplicate_port_name(device_name, lag_name)
    
    if is_duplicate:
        print(f"❌ Error: LAG interface '{lag_name}' already exists on device '{device_name}'. Creation aborted.")
        return None
    
    if not device_ids:
        # This means the device itself wasn't found in the check function
        print(f"❌ Error: Device '{device_name}' not found. LAG creation aborted.")
        return None
    
    # Use the first ID found for the insertion, assuming device_id consistency is desired
    device_id = device_ids[0] 
    
    conn = get_db_connection()
    new_lag_id = None
    try:
        cursor = conn.cursor()
            
        # The LAG interface uses the 'lag_name' (e.g., ae1) for its 'port_name'
        # Set fabric_port_type='LAG' and 'lag' to NULL to identify it as a LAG interface.
        cursor.execute("""
            INSERT INTO ports (
                device_id, port_name, port_speed, fabric_port_type, port_tagging, service_status, lag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING port_id;
        """, (device_id, lag_name, 'N/A', 'LAG', 'N/A', 'In-Service', None)) # Explicitly setting 'lag' to None
        
        new_lag_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ SUCCESS: LAG interface '{lag_name}' created (ID: {new_lag_id}).")
        return new_lag_id

    except psycopg2.IntegrityError as e:
        handle_db_error(f"LAG creation failed (Name '{lag_name}' may already exist): {e}", conn)
    except psycopg2.Error as e:
        handle_db_error(f"LAG creation failed: {e}", conn)
    finally:
        handle_connection_close(conn)
        return new_lag_id

def get_ports_for_lag_assignment(device_id: Any) -> List[Dict[str, Any]]:
    """
    Retrieves available physical ports (not already in a LAG). 
    (Inferred by lag=NULL/N/A and type!=LAG)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Selects ports where 'lag' column is NULL or 'N/A' (not a member of a LAG) 
        # AND fabric_port_type is NOT 'LAG' (not the LAG header itself)
        # NOTE: Selecting 'port_id'
        cursor.execute("""
            SELECT port_id, port_name, port_speed, port_description 
            FROM ports 
            WHERE device_id = %s 
            AND (lag IS NULL OR lag = 'N/A')
            AND fabric_port_type != 'LAG'
            ORDER BY port_name;
        """, (device_id,))
        
        ports = cursor.fetchall()
        
        result = []
        for port in ports:
            # port_id is port[0]
            result.append({
                "id": port[0], 
                "port_name": port[1], 
                "port_speed": port[2], 
                "port_description": port[3]
            })
        return result
    except psycopg2.Error as e:
        print(f"Error retrieving ports for assignment: {e}")
        return []
    finally:
        handle_connection_close(conn)

def update_port_lag_assignment(port_ids: List[Any], lag_name: str):
    """Updates a list of ports' lag association in a single transaction."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # The physical ports are implicitly identified by being a member of a LAG (not NULL/N/A) 
        # and having a fabric_port_type that is NOT 'LAG'.
        cursor.execute("""
            UPDATE ports 
            SET lag = %s, service_status = 'In-Service' 
            WHERE port_id = ANY(%s);
        """, (lag_name, port_ids))
        
        conn.commit()
        print(f"✅ SUCCESS: {cursor.rowcount} ports assigned to LAG '{lag_name}'.")

    except psycopg2.Error as e:
        handle_db_error(f"Failed to assign ports to LAG '{lag_name}': {e}", conn)
    finally:
        handle_connection_close(conn)